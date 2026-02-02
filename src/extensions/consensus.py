"""
Consensus protocol for multi-agent verification and selection.
"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Optional
from loguru import logger

from src.core.config import settings
from src.core.models import (
    AgentRole,
    CodeCandidate,
    ConsensusResult,
    ConsensusVote,
    Task,
    VerificationResult,
)


class ConsensusEngine:
    """
    Implements the consensus protocol for code verification.
    
    Process:
    1. Parallel Generation: Generate N candidate solutions
    2. Cross-Verification: Each candidate verified by QA + Architect
    3. Consensus Voting: Judge selects best from surviving candidates
    4. Evolution (Optional): Mutate winner and re-test
    """
    
    def __init__(self):
        self.n_candidates = settings.consensus_n_candidates
        self.min_votes = settings.consensus_min_votes
        self.timeout = settings.consensus_timeout_seconds
    
    async def generate_candidates(
        self,
        task: Task,
        agent_client,
        approaches: Optional[List[str]] = None
    ) -> List[CodeCandidate]:
        """
        Generate multiple candidate solutions in parallel.
        
        Args:
            task: Task to solve
            agent_client: Agent client for generation
            approaches: List of approaches (e.g., ["conservative", "aggressive", "minimal"])
        
        Returns:
            List of code candidates
        """
        if approaches is None:
            approaches = ["conservative", "aggressive", "minimal"][:self.n_candidates]
        
        logger.info(f"Generating {len(approaches)} candidates for task {task.id}")
        
        # Generate candidates in parallel
        candidate_coros = []
        for approach in approaches:
            candidate_coros.append(
                self._generate_single_candidate(task, agent_client, approach)
            )
        
        try:
            candidates = await asyncio.wait_for(
                asyncio.gather(*candidate_coros, return_exceptions=True),
                timeout=self.timeout
            )
            
            # Filter out exceptions
            valid_candidates = [
                c for c in candidates 
                if isinstance(c, CodeCandidate)
            ]
            
            logger.info(
                f"Generated {len(valid_candidates)}/{len(approaches)} valid candidates"
            )
            return valid_candidates
            
        except asyncio.TimeoutError:
            logger.error(f"Candidate generation timed out after {self.timeout}s")
            return []
    
    async def _generate_single_candidate(
        self,
        task: Task,
        agent_client,
        approach: str
    ) -> CodeCandidate:
        """Generate a single candidate with specific approach."""
        
        prompt = self._build_generation_prompt(task, approach)
        
        # Call agent to generate code
        response = await agent_client.generate(prompt)
        
        return CodeCandidate(
            id=str(uuid.uuid4()),
            task_id=task.id,
            agent_role=agent_client.role,
            code=response.content,
            approach=approach,
            generated_at=datetime.utcnow(),
            metadata={"model": agent_client.model_name}
        )
    
    def _build_generation_prompt(self, task: Task, approach: str) -> str:
        """Build prompt for code generation with specific approach."""
        
        approach_instructions = {
            "conservative": "Prioritize safety, error handling, and robustness. Include extensive validation.",
            "aggressive": "Prioritize performance and efficiency. Use optimized algorithms.",
            "minimal": "Prioritize simplicity and readability. Use the most straightforward approach.",
            "defensive": "Prioritize security and input validation. Assume hostile inputs.",
        }
        
        instruction = approach_instructions.get(approach, approach_instructions["conservative"])
        
        return f"""Task: {task.title}

Description: {task.description}

Approach: {approach}
{instruction}

Requirements:
{chr(10).join('- ' + str(req) for req in task.metadata.get('requirements', []))}

Generate the implementation following the {approach} approach.
"""
    
    async def cross_verify(
        self,
        candidates: List[CodeCandidate],
        task: Task,
        qa_client,
        architect_client
    ) -> List[VerificationResult]:
        """
        Cross-verify all candidates using QA and Architect agents.
        
        Args:
            candidates: List of code candidates
            task: Original task
            qa_client: QA agent client
            architect_client: Architect agent client
        
        Returns:
            List of verification results
        """
        logger.info(f"Cross-verifying {len(candidates)} candidates")
        
        verification_coros = []
        for candidate in candidates:
            # Each candidate verified by both QA and Architect
            verification_coros.append(
                self._verify_candidate(candidate, task, qa_client, AgentRole.QA_SENTINEL)
            )
            verification_coros.append(
                self._verify_candidate(candidate, task, architect_client, AgentRole.ARCHITECT)
            )
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*verification_coros, return_exceptions=True),
                timeout=self.timeout
            )
            
            # Filter out exceptions
            valid_results = [
                r for r in results 
                if isinstance(r, VerificationResult)
            ]
            
            logger.info(f"Completed {len(valid_results)} verifications")
            return valid_results
            
        except asyncio.TimeoutError:
            logger.error(f"Verification timed out after {self.timeout}s")
            return []
    
    async def _verify_candidate(
        self,
        candidate: CodeCandidate,
        task: Task,
        verifier_client,
        verifier_role: AgentRole
    ) -> VerificationResult:
        """Verify a single candidate."""
        
        prompt = f"""Verify this code solution:

Task: {task.title}
Description: {task.description}

Code:
```
{candidate.code}
```

Verify against requirements and provide:
1. PASS or FAIL
2. Score (0-1)
3. Specific feedback
4. List of errors (if any)
5. List of warnings (if any)
"""
        
        response = await verifier_client.generate(prompt)
        
        # Parse response (simplified - would need better parsing)
        passed = "PASS" in response.content.upper()
        score = self._extract_score(response.content)
        
        return VerificationResult(
            candidate_id=candidate.id,
            verifier_role=verifier_role,
            passed=passed,
            score=score,
            feedback=response.content,
            errors=[],  # Would parse from response
            warnings=[],  # Would parse from response
            verified_at=datetime.utcnow()
        )
    
    def _extract_score(self, content: str) -> float:
        """Extract score from verification response."""
        # Simple heuristic - would implement better parsing
        if "excellent" in content.lower():
            return 0.9
        elif "good" in content.lower():
            return 0.75
        elif "acceptable" in content.lower():
            return 0.6
        elif "poor" in content.lower():
            return 0.3
        return 0.5
    
    async def consensus_vote(
        self,
        candidates: List[CodeCandidate],
        verifications: List[VerificationResult],
        task: Task,
        judge_client
    ) -> ConsensusResult:
        """
        Use consensus judge to select best candidate.
        
        Args:
            candidates: All generated candidates
            verifications: Verification results
            task: Original task
            judge_client: Judge agent client
        
        Returns:
            Consensus result with winner
        """
        logger.info(f"Running consensus vote for {len(candidates)} candidates")
        
        # Filter to candidates that passed verification
        passing_candidates = self._get_passing_candidates(candidates, verifications)
        
        if not passing_candidates:
            logger.warning("No candidates passed verification!")
            # Return least-bad candidate
            passing_candidates = candidates
        
        # Get judge to vote on all passing candidates
        votes = await self._collect_votes(passing_candidates, verifications, task, judge_client)
        
        # Select winner
        winner = self._select_winner(votes, passing_candidates)
        
        return ConsensusResult(
            task_id=task.id,
            winner_candidate_id=winner.id,
            total_candidates=len(candidates),
            total_votes=len(votes),
            winning_score=max(v.score for v in votes if v.candidate_id == winner.id),
            all_votes=votes,
            reasoning=self._build_consensus_reasoning(winner, votes),
            decided_at=datetime.utcnow()
        )
    
    def _get_passing_candidates(
        self,
        candidates: List[CodeCandidate],
        verifications: List[VerificationResult]
    ) -> List[CodeCandidate]:
        """Filter candidates that passed verification."""
        
        passing_ids = set()
        for verification in verifications:
            if verification.passed:
                passing_ids.add(verification.candidate_id)
        
        return [c for c in candidates if c.id in passing_ids]
    
    async def _collect_votes(
        self,
        candidates: List[CodeCandidate],
        verifications: List[VerificationResult],
        task: Task,
        judge_client
    ) -> List[ConsensusVote]:
        """Collect votes from consensus judge."""
        
        prompt = self._build_judging_prompt(candidates, verifications, task)
        response = await judge_client.generate(prompt)
        
        # Parse judge's response into votes
        votes = []
        for candidate in candidates:
            # Would implement better parsing
            score = self._extract_score(response.content)
            
            vote = ConsensusVote(
                candidate_id=candidate.id,
                voter_role=AgentRole.CONSENSUS_JUDGE,
                score=score,
                reasoning=response.content,
                criteria={
                    "correctness": score,
                    "performance": score * 0.9,
                    "readability": score * 0.95,
                    "maintainability": score * 0.85,
                },
                voted_at=datetime.utcnow()
            )
            votes.append(vote)
        
        return votes
    
    def _build_judging_prompt(
        self,
        candidates: List[CodeCandidate],
        verifications: List[VerificationResult],
        task: Task
    ) -> str:
        """Build prompt for consensus judge."""
        
        prompt = f"""Task: {task.title}

You must judge {len(candidates)} code candidates and select the best one.

"""
        for i, candidate in enumerate(candidates, 1):
            prompt += f"""
Candidate {i} (Approach: {candidate.approach}):
```
{candidate.code[:500]}...
```

Verifications:
"""
            candidate_verifications = [
                v for v in verifications if v.candidate_id == candidate.id
            ]
            for v in candidate_verifications:
                prompt += f"- {v.verifier_role.value}: {'PASS' if v.passed else 'FAIL'} (Score: {v.score:.2f})\n"
        
        prompt += """
Score each candidate on:
- Correctness (40%)
- Performance (20%)  
- Readability (20%)
- Maintainability (20%)

Select the winner and explain your reasoning.
"""
        return prompt
    
    def _select_winner(
        self,
        votes: List[ConsensusVote],
        candidates: List[CodeCandidate]
    ) -> CodeCandidate:
        """Select winning candidate based on votes."""
        
        # Calculate average score per candidate
        candidate_scores = {}
        for candidate in candidates:
            candidate_votes = [v for v in votes if v.candidate_id == candidate.id]
            if candidate_votes:
                avg_score = sum(v.score for v in candidate_votes) / len(candidate_votes)
                candidate_scores[candidate.id] = avg_score
        
        # Select highest scoring candidate
        winner_id = max(candidate_scores, key=candidate_scores.get)
        return next(c for c in candidates if c.id == winner_id)
    
    def _build_consensus_reasoning(
        self,
        winner: CodeCandidate,
        votes: List[ConsensusVote]
    ) -> str:
        """Build explanation for consensus decision."""
        
        winner_votes = [v for v in votes if v.candidate_id == winner.id]
        avg_score = sum(v.score for v in winner_votes) / len(winner_votes)
        
        return f"""
Winner: Candidate with {winner.approach} approach
Average Score: {avg_score:.2f}
Reasons: Strong verification results, balanced implementation
"""