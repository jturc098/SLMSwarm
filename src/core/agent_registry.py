"""
Agent registry for managing multi-model routing.
"""

from typing import Dict, Optional
from dataclasses import dataclass

from src.core.config import settings
from src.core.models import AgentRole


@dataclass
class AgentConfig:
    """Configuration for a specific agent."""
    role: AgentRole
    model_url: str
    model_name: str
    context_size: int
    temperature: float
    top_p: float
    system_prompt: str


class AgentRegistry:
    """Registry for all agents in the swarm."""
    
    def __init__(self):
        self._agents: Dict[AgentRole, AgentConfig] = {}
        self._initialize_agents()
    
    def _initialize_agents(self) -> None:
        """Initialize all agents with their configurations."""
        
        # Architect Agent
        self._agents[AgentRole.ARCHITECT] = AgentConfig(
            role=AgentRole.ARCHITECT,
            model_url=settings.architect_url,
            model_name=settings.architect_model,
            context_size=settings.context_size_architect,
            temperature=0.7,
            top_p=0.9,
            system_prompt=self._load_system_prompt("architect")
        )
        
        # Backend Worker
        self._agents[AgentRole.WORKER_BACKEND] = AgentConfig(
            role=AgentRole.WORKER_BACKEND,
            model_url=settings.worker_backend_url,
            model_name=settings.worker_backend_model,
            context_size=settings.context_size_worker,
            temperature=0.6,
            top_p=0.9,
            system_prompt=self._load_system_prompt("worker_backend")
        )
        
        # Frontend Worker
        self._agents[AgentRole.WORKER_FRONTEND] = AgentConfig(
            role=AgentRole.WORKER_FRONTEND,
            model_url=settings.worker_frontend_url,
            model_name=settings.worker_frontend_model,
            context_size=settings.context_size_worker,
            temperature=0.6,
            top_p=0.9,
            system_prompt=self._load_system_prompt("worker_frontend")
        )
        
        # QA Sentinel
        self._agents[AgentRole.QA_SENTINEL] = AgentConfig(
            role=AgentRole.QA_SENTINEL,
            model_url=settings.qa_url,
            model_name=settings.qa_model,
            context_size=settings.context_size_qa,
            temperature=0.3,  # Lower temp for strict verification
            top_p=0.95,
            system_prompt=self._load_system_prompt("qa_sentinel")
        )
        
        # Consensus Judge
        self._agents[AgentRole.CONSENSUS_JUDGE] = AgentConfig(
            role=AgentRole.CONSENSUS_JUDGE,
            model_url=settings.judge_url,
            model_name=settings.judge_model,
            context_size=settings.context_size_qa,
            temperature=0.4,  # Moderate temp for judging
            top_p=0.95,
            system_prompt=self._load_system_prompt("consensus_judge")
        )
    
    def _load_system_prompt(self, agent_type: str) -> str:
        """Load system prompt for agent type."""
        # TODO: Load from prompts/*.md files
        prompts = {
            "architect": """You are a Principal Software Architect for an autonomous AI development team.

Your role:
- Analyze requirements and create detailed technical specifications
- Design system architecture and choose appropriate technologies
- Create task breakdowns with clear dependencies
- Define API contracts and data schemas
- Ensure scalability, security, and maintainability

Output format:
- Clear markdown documents
- Structured task lists with dependencies
- API schemas in OpenAPI format
- Database schemas when applicable

Constraints:
- Never write implementation code
- Focus on high-level design
- Consider multiple approaches
- Document architectural decisions""",
            
            "worker_backend": """You are a Senior Backend Developer specializing in Python, Go, and Node.js.

Your role:
- Implement backend services and APIs
- Write clean, efficient, and maintainable code
- Follow architectural specifications exactly
- Include error handling and logging
- Write clear comments for complex logic

Guidelines:
- Follow PEP 8 for Python, standard conventions for other languages
- Use type hints/annotations
- Prefer async/await for I/O operations
- Include docstrings for public functions
- Handle errors gracefully""",
            
            "worker_frontend": """You are a Senior Frontend Developer specializing in React, Vue, and modern CSS.

Your role:
- Implement user interfaces and components
- Write semantic HTML and accessible components
- Create responsive designs
- Follow component architecture
- Optimize for performance

Guidelines:
- Use modern ES6+ JavaScript/TypeScript
- Follow React/Vue best practices
- Write reusable components
- Include PropTypes/TypeScript types
- Ensure WCAG accessibility""",
            
            "qa_sentinel": """You are a Lead QA Engineer focused on code quality and security.

Your role:
- Verify code against specifications
- Identify bugs, security vulnerabilities, and edge cases
- Generate comprehensive test cases
- Provide specific, actionable feedback
- Ensure best practices are followed

Verification criteria:
- Correctness: Does it meet requirements?
- Security: Any vulnerabilities?
- Performance: Any bottlenecks?
- Maintainability: Is it readable and documented?
- Testing: Are edge cases handled?

Output: PASS or FAIL with specific issues and recommendations.""",
            
            "consensus_judge": """You are an impartial Technical Judge evaluating multiple code solutions.

Your role:
- Compare code candidates objectively
- Score based on clear criteria (correctness, performance, readability, maintainability)
- Provide reasoning for your decision
- Select the best overall solution

Scoring criteria (0-1 scale):
- Correctness (40%): Meets requirements, no bugs
- Performance (20%): Efficient algorithms, no bottlenecks
- Readability (20%): Clear code, good structure
- Maintainability (20%): Modular, documented, testable

Output: Winner selection with scores and reasoning."""
        }
        
        return prompts.get(agent_type, "You are a helpful AI assistant.")
    
    def get_agent(self, role: AgentRole) -> Optional[AgentConfig]:
        """Get agent configuration by role."""
        return self._agents.get(role)
    
    def get_all_agents(self) -> Dict[AgentRole, AgentConfig]:
        """Get all registered agents."""
        return self._agents.copy()
    
    def route_task_to_agent(self, task_description: str) -> AgentRole:
        """Route a task to the appropriate agent based on content."""
        description_lower = task_description.lower()
        
        # Keywords for routing
        if any(keyword in description_lower for keyword in [
            "plan", "architect", "design", "schema", "api", "structure"
        ]):
            return AgentRole.ARCHITECT
        
        if any(keyword in description_lower for keyword in [
            "frontend", "ui", "react", "vue", "component", "css", "html"
        ]):
            return AgentRole.WORKER_FRONTEND
        
        if any(keyword in description_lower for keyword in [
            "backend", "api", "database", "server", "python", "go"
        ]):
            return AgentRole.WORKER_BACKEND
        
        if any(keyword in description_lower for keyword in [
            "test", "verify", "qa", "validate", "check"
        ]):
            return AgentRole.QA_SENTINEL
        
        # Default to architect for ambiguous tasks
        return AgentRole.ARCHITECT


# Global registry instance
agent_registry = AgentRegistry()