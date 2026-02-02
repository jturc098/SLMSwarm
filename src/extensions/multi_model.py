"""
Multi-model routing for optimal agent selection.
"""

from typing import Optional
from loguru import logger

from src.core.agent_registry import agent_registry
from src.core.models import AgentRole, Task


class MultiModelRouter:
    """
    Routes tasks to optimal models based on complexity and content.
    
    Routing Strategy:
    - Architecture/Planning → Architect (14B)
    - Complex Backend Logic → Worker Backend (7B)
    - Frontend/UI → Worker Frontend (3B)
    - Verification/Testing → QA Sentinel (1.5B)
    - Final Judgment → Consensus Judge (3.8B)
    """
    
    def __init__(self):
        self.registry = agent_registry
        self._complexity_cache = {}
    
    def route_task(self, task: Task) -> AgentRole:
        """
        Route task to optimal agent based on content and complexity.
        
        Args:
            task: Task to route
        
        Returns:
            Agent role to handle the task
        """
        # If task has assigned agent, use that
        if task.assigned_agent:
            logger.info(f"Task {task.id} pre-assigned to {task.assigned_agent.value}")
            return task.assigned_agent
        
        # Calculate complexity score
        complexity = self._calculate_complexity(task)
        
        # Use registry's keyword-based routing as baseline
        suggested_role = self.registry.route_task_to_agent(task.description)
        
        # Adjust based on complexity
        if complexity > 0.8:
            # Very complex tasks go to Architect for planning
            if suggested_role in [AgentRole.WORKER_BACKEND, AgentRole.WORKER_FRONTEND]:
                logger.info(
                    f"Task {task.id} complexity {complexity:.2f} - routing to Architect"
                )
                return AgentRole.ARCHITECT
        
        logger.info(f"Task {task.id} routed to {suggested_role.value}")
        return suggested_role
    
    def _calculate_complexity(self, task: Task) -> float:
        """
        Calculate task complexity score (0-1).
        
        Factors:
        - Description length
        - Number of requirements
        - Presence of complexity keywords
        - Number of dependencies
        """
        score = 0.0
        
        # Description length (longer = more complex)
        desc_length = len(task.description.split())
        score += min(desc_length / 200, 0.3)  # Max 0.3 from length
        
        # Requirements count
        requirements = task.metadata.get("requirements", [])
        score += min(len(requirements) / 10, 0.2)  # Max 0.2 from requirements
        
        # Complexity keywords
        complexity_keywords = [
            "architecture", "design", "scalable", "distributed",
            "optimization", "algorithm", "performance", "security",
            "integration", "microservice", "async", "concurrent"
        ]
        
        desc_lower = task.description.lower()
        keyword_matches = sum(
            1 for keyword in complexity_keywords 
            if keyword in desc_lower
        )
        score += min(keyword_matches / 5, 0.3)  # Max 0.3 from keywords
        
        # Dependencies (more deps = more complex coordination)
        score += min(len(task.dependencies) / 5, 0.2)  # Max 0.2 from deps
        
        return min(score, 1.0)
    
    def select_worker_for_language(self, language: str) -> AgentRole:
        """
        Select appropriate worker based on programming language.
        
        Args:
            language: Programming language (python, javascript, go, etc.)
        
        Returns:
            Optimal worker role
        """
        backend_languages = {
            "python", "go", "rust", "java", "c", "cpp", "c++",
            "ruby", "php", "elixir", "scala", "kotlin"
        }
        
        frontend_languages = {
            "javascript", "typescript", "jsx", "tsx",
            "html", "css", "scss", "sass", "vue", "svelte"
        }
        
        language_lower = language.lower()
        
        if language_lower in backend_languages:
            return AgentRole.WORKER_BACKEND
        elif language_lower in frontend_languages:
            return AgentRole.WORKER_FRONTEND
        else:
            # Default to backend for unknown languages
            return AgentRole.WORKER_BACKEND
    
    def suggest_parallel_execution(self, tasks: list[Task]) -> dict[AgentRole, list[Task]]:
        """
        Group tasks by agent for parallel execution.
        
        Args:
            tasks: List of tasks to group
        
        Returns:
            Dictionary mapping agent roles to their tasks
        """
        grouped = {role: [] for role in AgentRole}
        
        for task in tasks:
            role = self.route_task(task)
            grouped[role].append(task)
        
        # Filter out empty groups
        return {role: tasks for role, tasks in grouped.items() if tasks}


# Global router instance
multi_model_router = MultiModelRouter()