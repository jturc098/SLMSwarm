"""
Evolutionary code refinement system.
"""

import asyncio
import random
from typing import List, Dict, Optional
from loguru import logger

from src.core.models import CodeCandidate, Task
from src.orchestration import execution_sandbox


class EvolutionaryRefiner:
    """
    Evolutionary system for iterative code improvement.
    
    Process:
    1. Start with consensus winner
    2. Generate mutations
    3. Test all variants
    4. Select fittest
    5. Repeat until convergence
    """
    
    def __init__(self):
        self.max_generations = 10
        self.population_size = 5
        self.mutation_rate = 0.3
        self.sandbox = execution_sandbox
    
    async def refine(
        self,
        initial_code: CodeCandidate,
        task: Task,
        fitness_criteria: Dict[str, float]
    ) -> CodeCandidate:
        """
        Refine code through evolutionary process.
        
        Args:
            initial_code: Starting point (consensus winner)
            task: Original task
            fitness_criteria: Weights for fitness scoring
        
        Returns:
            Refined code candidate
        """
        logger.info(f"Starting evolutionary refinement for task {task.id}")
        
        current_best = initial_code
        generation = 0
        
        while generation < self.max_generations:
            logger.info(f"  Generation {generation + 1}/{self.max_generations}")
            
            # Generate mutations
            population = await self._generate_mutations(current_best, task)
            
            # Evaluate fitness
            fitness_scores = await self._evaluate_population(
                population,
                task,
                fitness_criteria
            )
            
            # Select best
            best_idx = fitness_scores.index(max(fitness_scores))
            generation_best = population[best_idx]
            best_score = fitness_scores[best_idx]
            
            logger.info(f"  Best fitness: {best_score:.3f}")
            
            # Check for improvement
            if best_score <= await self._calculate_fitness(current_best, task, fitness_criteria):
                logger.info("  No improvement, stopping evolution")
                break
            
            current_best = generation_best
            generation += 1
        
        logger.info(f"Evolution complete after {generation + 1} generations")
        return current_best
    
    async def _generate_mutations(
        self,
        parent: CodeCandidate,
        task: Task
    ) -> List[CodeCandidate]:
        """
        Generate mutations of parent code.
        
        Mutation strategies:
        - Refactor for performance
        - Refactor for readability
        - Add error handling
        - Optimize algorithms
        - Add type hints
        """
        mutations = [parent]  # Include parent in population
        
        mutation_prompts = [
            "Refactor for better performance",
            "Refactor for better readability",
            "Add comprehensive error handling",
            "Optimize algorithms and data structures",
            "Add type hints and documentation"
        ]
        
        # Generate mutations (simplified - would use actual agents)
        for i, prompt in enumerate(mutation_prompts[:self.population_size - 1]):
            mutation = CodeCandidate(
                id=f"mutation_{i}",
                task_id=task.id,
                agent_role=parent.agent_role,
                code=parent.code,  # Would actually mutate via agent
                approach=f"mutation_{prompt.split()[2]}",
                metadata={"generation": 1, "mutation": prompt}
            )
            mutations.append(mutation)
        
        return mutations
    
    async def _evaluate_population(
        self,
        population: List[CodeCandidate],
        task: Task,
        fitness_criteria: Dict[str, float]
    ) -> List[float]:
        """
        Evaluate fitness of all candidates in population.
        
        Args:
            population: List of candidates
            task: Task being solved
            fitness_criteria: Weights for different criteria
        
        Returns:
            List of fitness scores
        """
        scores = []
        
        for candidate in population:
            score = await self._calculate_fitness(candidate, task, fitness_criteria)
            scores.append(score)
        
        return scores
    
    async def _calculate_fitness(
        self,
        candidate: CodeCandidate,
        task: Task,
        criteria: Dict[str, float]
    ) -> float:
        """
        Calculate fitness score for a candidate.
        
        Criteria:
        - correctness: Does it work?
        - performance: How fast?
        - readability: How clean?
        - maintainability: How modular?
        """
        score = 0.0
        
        # Correctness (run tests)
        test_result = await self._test_correctness(candidate)
        score += criteria.get("correctness", 0.4) * (1.0 if test_result["passed"] else 0.0)
        
        # Performance (measure execution time)
        perf_score = await self._measure_performance(candidate)
        score += criteria.get("performance", 0.2) * perf_score
        
        # Readability (line count, complexity)
        read_score = self._measure_readability(candidate.code)
        score += criteria.get("readability", 0.2) * read_score
        
        # Maintainability (modularity, documentation)
        maint_score = self._measure_maintainability(candidate.code)
        score += criteria.get("maintainability", 0.2) * maint_score
        
        return score
    
    async def _test_correctness(self, candidate: CodeCandidate) -> Dict:
        """Test if code is correct."""
        
        # Would run actual tests in sandbox
        # For now, simplified
        return {
            "passed": True,
            "tests_run": 0,
            "tests_passed": 0
        }
    
    async def _measure_performance(self, candidate: CodeCandidate) -> float:
        """Measure code performance."""
        
        # Would benchmark execution time
        # Shorter = better, normalized to 0-1
        return 0.8  # Mock
    
    def _measure_readability(self, code: str) -> float:
        """Measure code readability."""
        
        lines = len(code.split('\n'))
        
        # Prefer shorter, cleaner code
        # 50 lines = ideal, normalize around that
        if lines < 20:
            return 0.6  # Too terse
        elif lines < 50:
            return 1.0  # Ideal
        elif lines < 100:
            return 0.8  # Acceptable
        else:
            return 0.5  # Too long
    
    def _measure_maintainability(self, code: str) -> float:
        """Measure code maintainability."""
        
        score = 0.0
        
        # Check for docstrings
        if '"""' in code or "'''" in code:
            score += 0.3
        
        # Check for type hints
        if '->' in code or ': str' in code or ': int' in code:
            score += 0.3
        
        # Check for error handling
        if 'try:' in code and 'except' in code:
            score += 0.2
        
        # Check for modularity (multiple functions)
        function_count = code.count('def ')
        if function_count > 1:
            score += 0.2
        
        return min(score, 1.0)


# Global evolutionary refiner instance
evolutionary_refiner = EvolutionaryRefiner()