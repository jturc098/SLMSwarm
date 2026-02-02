"""
Pattern extraction from successful code implementations.
"""

import re
from typing import Dict, List, Optional
from loguru import logger

from src.core.models import CodeCandidate, ConsensusResult
from src.memory.persistent_memory import persistent_memory


class PatternExtractor:
    """
    Extracts reusable patterns from successful code implementations.
    
    Learns from:
    - Consensus winners (best solutions)
    - Frequently used code structures
    - Error-free implementations
    """
    
    def __init__(self):
        self.memory = persistent_memory
        self.pattern_cache = {}
    
    async def extract_from_consensus(
        self,
        consensus_result: ConsensusResult,
        winner_candidate: CodeCandidate,
        task_context: Dict
    ) -> None:
        """
        Extract learnings from consensus winner.
        
        Args:
            consensus_result: The consensus decision
            winner_candidate: The winning candidate
            task_context: Context about the task
        """
        logger.info(f"Extracting patterns from consensus winner for task {consensus_result.task_id}")
        
        # Extract code patterns
        patterns = self._identify_patterns(winner_candidate.code)
        
        for pattern in patterns:
            await self._store_pattern(
                pattern,
                winner_candidate,
                consensus_result,
                task_context
            )
        
        # Store the full solution
        await self.memory.store_solution(
            problem=task_context.get("description", ""),
            solution=winner_candidate.code,
            approach=winner_candidate.approach,
            verified=True
        )
    
    def _identify_patterns(self, code: str) -> List[Dict]:
        """
        Identify reusable patterns in code.
        
        Patterns include:
        - Function/class definitions
        - Common algorithmic approaches
        - Error handling patterns
        - API usage patterns
        """
        patterns = []
        
        # Extract functions
        function_pattern = r'(async\s+)?def\s+(\w+)\s*\([^)]*\):\s*(?:"""[^"]*"""\s*)?(.*?)(?=\n(?:async\s+)?def\s+|\nclass\s+|\Z)'
        functions = re.finditer(function_pattern, code, re.DOTALL)
        
        for match in functions:
            is_async = bool(match.group(1))
            func_name = match.group(2)
            func_body = match.group(3).strip()
            
            if len(func_body) > 50:  # Only meaningful functions
                patterns.append({
                    "type": "function",
                    "name": func_name,
                    "async": is_async,
                    "code": match.group(0),
                    "complexity": self._estimate_complexity(func_body)
                })
        
        # Extract classes
        class_pattern = r'class\s+(\w+)(?:\([^)]*\))?:\s*(?:"""[^"]*"""\s*)?(.*?)(?=\nclass\s+|\Z)'
        classes = re.finditer(class_pattern, code, re.DOTALL)
        
        for match in classes:
            class_name = match.group(1)
            class_body = match.group(2).strip()
            
            if len(class_body) > 50:
                patterns.append({
                    "type": "class",
                    "name": class_name,
                    "code": match.group(0),
                    "methods": self._count_methods(class_body)
                })
        
        # Extract error handling patterns
        try_pattern = r'try:\s*(.+?)except\s+(.+?):\s*(.+?)(?=\n(?:try:|def|class|\Z))'
        error_handlers = re.finditer(try_pattern, code, re.DOTALL)
        
        for match in error_handlers:
            patterns.append({
                "type": "error_handling",
                "exception": match.group(2).strip(),
                "code": match.group(0)
            })
        
        return patterns
    
    async def _store_pattern(
        self,
        pattern: Dict,
        candidate: CodeCandidate,
        consensus: ConsensusResult,
        context: Dict
    ) -> None:
        """Store extracted pattern in memory."""
        
        pattern_name = f"{pattern['type']}_{pattern.get('name', 'anonymous')}"
        
        # Determine language from context or file extension
        language = context.get("language", "python")
        
        # Build context description
        pattern_context = f"""
Task: {context.get('description', 'N/A')}
Approach: {candidate.approach}
Consensus Score: {consensus.winning_score:.2f}
Pattern Type: {pattern['type']}
"""
        
        # Success metrics from consensus
        success_metrics = {
            "consensus_score": consensus.winning_score,
            "total_votes": consensus.total_votes,
            "approach": candidate.approach
        }
        
        await self.memory.store_code_pattern(
            pattern_name=pattern_name,
            code=pattern['code'],
            language=language,
            context=pattern_context,
            success_metrics=success_metrics
        )
    
    def _estimate_complexity(self, code: str) -> str:
        """Estimate code complexity."""
        lines = len(code.split('\n'))
        
        if lines < 10:
            return "low"
        elif lines < 30:
            return "medium"
        else:
            return "high"
    
    def _count_methods(self, class_body: str) -> int:
        """Count methods in a class."""
        method_pattern = r'def\s+\w+\s*\('
        return len(re.findall(method_pattern, class_body))
    
    async def suggest_patterns(
        self,
        task_description: str,
        language: Optional[str] = None
    ) -> List[str]:
        """
        Suggest relevant patterns for a new task.
        
        Args:
            task_description: What the user wants to accomplish
            language: Programming language
        
        Returns:
            List of pattern suggestions
        """
        # Recall similar patterns from memory
        patterns = await self.memory.recall_similar_patterns(
            task_description,
            language=language,
            n_results=5
        )
        
        suggestions = []
        for pattern in patterns:
            suggestion = f"""
Pattern: {pattern.metadata.get('pattern_name', 'Unknown')}
Language: {pattern.metadata.get('language', 'Unknown')}
Success Rate: {pattern.metadata.get('success_rate', 0):.2f}
Usage Count: {pattern.metadata.get('usage_count', 0)}

{pattern.content[:500]}...
"""
            suggestions.append(suggestion)
        
        return suggestions


# Global pattern extractor instance
pattern_extractor = PatternExtractor()