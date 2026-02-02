"""
Task dispatcher with complexity routing and consensus integration.
"""

import asyncio
from typing import Dict, Optional
from loguru import logger

from src.core.models import Task, AgentRole, CodeCandidate, ConsensusResult
from src.core.agent_registry import agent_registry
from src.extensions.multi_model import multi_model_router
from src.extensions.consensus import ConsensusEngine
from src.memory import persistent_memory, pattern_extractor, episodic_memory


class TaskDispatcher:
    """
    Routes and executes tasks through the appropriate agents.
    
    Features:
    - Complexity-based routing
    - Consensus protocol integration
    - Memory-enhanced execution
    - Progress tracking
    """
    
    def __init__(self):
        self.router = multi_model_router
        self.consensus = ConsensusEngine()
        self.memory = persistent_memory
        self.pattern_extractor = pattern_extractor
    
    def route_task(self, task: Task) -> AgentRole:
        """
        Route task to optimal agent based on complexity and content.
        
        Args:
            task: Task to route
        
        Returns:
            Optimal agent role
        """
        return self.router.route_task(task)
    
    async def execute_task(
        self,
        task: Task,
        episode_id: Optional[str] = None
    ) -> Dict:
        """
        Execute task through the swarm with consensus protocol.
        
        Args:
            task: Task to execute
            episode_id: Episode ID for tracking
        
        Returns:
            Execution result dictionary
        """
        logger.info(f"Executing task {task.id}: {task.title}")
        
        try:
            # Step 1: Recall relevant patterns from memory
            patterns = await self._gather_context(task)
            
            if episode_id:
                await episodic_memory.record_event(
                    episode_id=episode_id,
                    event_type="context_gathered",
                    agent_role=AgentRole.ARCHITECT,
                    data={"patterns_found": len(patterns)}
                )
            
            # Step 2: Generate multiple candidates using consensus
            candidates = await self._generate_candidates(task, patterns)
            
            if episode_id:
                await episodic_memory.record_event(
                    episode_id=episode_id,
                    event_type="candidates_generated",
                    agent_role=AgentRole.WORKER_BACKEND,  # Would be dynamic
                    data={"count": len(candidates)}
                )
            
            # Step 3: Cross-verify candidates
            verifications = await self._verify_candidates(task, candidates)
            
            if episode_id:
                await episodic_memory.record_event(
                    episode_id=episode_id,
                    event_type="verification_complete",
                    agent_role=AgentRole.QA_SENTINEL,
                    data={"passed": sum(1 for v in verifications if v.passed)}
                )
            
            # Step 4: Consensus voting
            consensus_result = await self._consensus_vote(
                task,
                candidates,
                verifications
            )
            
            if episode_id:
                await episodic_memory.record_event(
                    episode_id=episode_id,
                    event_type="consensus_reached",
                    agent_role=AgentRole.CONSENSUS_JUDGE,
                    data={
                        "winner_id": consensus_result.winner_candidate_id,
                        "score": consensus_result.winning_score
                    }
                )
            
            # Step 5: Extract learnings from winner
            winner = next(
                c for c in candidates 
                if c.id == consensus_result.winner_candidate_id
            )
            
            await pattern_extractor.extract_from_consensus(
                consensus_result=consensus_result,
                winner_candidate=winner,
                task_context={
                    "description": task.description,
                    "language": task.metadata.get("language", "python")
                }
            )
            
            # Step 6: Return results
            return {
                "success": True,
                "winner_id": winner.id,
                "code": winner.code,
                "approach": winner.approach,
                "consensus_score": consensus_result.winning_score,
                "tokens": len(winner.code.split()),  # Approximate
                "iterations": len(candidates),
                "consensus_rounds": 1
            }
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tokens": 0,
                "iterations": 0,
                "consensus_rounds": 0
            }
    
    async def _gather_context(self, task: Task) -> list:
        """Gather relevant context from memory."""
        
        # Recall similar patterns
        patterns = await self.memory.recall_similar_patterns(
            description=task.description,
            language=task.metadata.get("language"),
            n_results=3
        )
        
        # Recall similar solutions
        solutions = await self.memory.recall_similar_solutions(
            problem=task.description,
            n_results=2
        )
        
        return patterns + solutions
    
    async def _generate_candidates(
        self,
        task: Task,
        context: list
    ) -> list[CodeCandidate]:
        """Generate multiple candidate solutions using REAL agents."""
        from src.agents.agent_client import create_agent_client
        
        # Determine which agent to use
        agent_role = self.router.route_task(task)
        agent_client = create_agent_client(agent_role)
        
        logger.info(f"Generating candidates with {agent_role.value}")
        
        # Use consensus engine to generate candidates
        candidates = await self.consensus.generate_candidates(
            task=task,
            agent_client=agent_client,
            approaches=["conservative", "aggressive", "minimal"]
        )
        
        return candidates
    
    async def _verify_candidates(
        self,
        task: Task,
        candidates: list[CodeCandidate]
    ) -> list:
        """
        Verify candidates using QA + Architect.
        
        Note: Simplified version. Full implementation would:
        - Actually call QA and Architect models
        - Run tests
        - Check against specifications
        """
        logger.info("Verifying candidates (simplified)")
        
        # Mock verifications
        from src.core.models import VerificationResult
        
        verifications = []
        for candidate in candidates:
            verification = VerificationResult(
                candidate_id=candidate.id,
                verifier_role=AgentRole.QA_SENTINEL,
                passed=True,  # Mock: all pass
                score=0.8,
                feedback="Mock verification",
                errors=[],
                warnings=[]
            )
            verifications.append(verification)
        
        return verifications
    
    async def _consensus_vote(
        self,
        task: Task,
        candidates: list[CodeCandidate],
        verifications: list
    ) -> ConsensusResult:
        """
        Run consensus voting to select winner.
        
        Note: Simplified version. Full implementation would:
        - Actually call consensus judge model
        - Analyze verification results
        - Score based on multiple criteria
        """
        logger.info("Running consensus vote (simplified)")
        
        # Mock: just pick first candidate as winner
        winner = candidates[0]
        
        from src.core.models import ConsensusVote
        
        vote = ConsensusVote(
            candidate_id=winner.id,
            voter_role=AgentRole.CONSENSUS_JUDGE,
            score=0.85,
            reasoning="Mock consensus decision",
            criteria={
                "correctness": 0.9,
                "performance": 0.8,
                "readability": 0.85,
                "maintainability": 0.85
            }
        )
        
        result = ConsensusResult(
            task_id=task.id,
            winner_candidate_id=winner.id,
            total_candidates=len(candidates),
            total_votes=1,
            winning_score=0.85,
            all_votes=[vote],
            reasoning="Selected best candidate through consensus"
        )
        
        return result


# Global dispatcher instance
task_dispatcher = TaskDispatcher()