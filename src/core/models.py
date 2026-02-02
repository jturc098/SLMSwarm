"""
Pydantic models for Project Hydra-Consensus.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Agent role types."""
    ARCHITECT = "architect"
    WORKER_BACKEND = "worker_backend"
    WORKER_FRONTEND = "worker_frontend"
    QA_SENTINEL = "qa_sentinel"
    CONSENSUS_JUDGE = "consensus_judge"


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(BaseModel):
    """Represents a single task in the system."""
    id: str = Field(description="Unique task identifier")
    title: str = Field(description="Task title")
    description: str = Field(description="Detailed task description")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    assigned_agent: Optional[AgentRole] = None
    dependencies: List[str] = Field(default_factory=list, description="Task IDs this task depends on")
    blocked_by: List[str] = Field(default_factory=list, description="Task IDs blocking this task")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "task_001",
                "title": "Implement user authentication",
                "description": "Create JWT-based authentication system",
                "status": "pending",
                "priority": "high",
                "dependencies": [],
            }
        }


class CodeCandidate(BaseModel):
    """Represents a code generation candidate."""
    id: str = Field(description="Candidate identifier")
    task_id: str = Field(description="Associated task ID")
    agent_role: AgentRole = Field(description="Agent that generated this")
    code: str = Field(description="Generated code")
    approach: str = Field(description="Approach description (e.g., 'conservative', 'aggressive')")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VerificationResult(BaseModel):
    """Result of code verification."""
    candidate_id: str
    verifier_role: AgentRole
    passed: bool
    score: float = Field(ge=0.0, le=1.0, description="Quality score (0-1)")
    feedback: str
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    verified_at: datetime = Field(default_factory=datetime.utcnow)


class ConsensusVote(BaseModel):
    """A vote in the consensus protocol."""
    candidate_id: str
    voter_role: AgentRole
    score: float = Field(ge=0.0, le=1.0, description="Vote score (0-1)")
    reasoning: str
    criteria: Dict[str, float] = Field(
        default_factory=dict,
        description="Scores for different criteria (correctness, performance, readability)"
    )
    voted_at: datetime = Field(default_factory=datetime.utcnow)


class ConsensusResult(BaseModel):
    """Result of consensus protocol."""
    task_id: str
    winner_candidate_id: str
    total_candidates: int
    total_votes: int
    winning_score: float
    all_votes: List[ConsensusVote]
    reasoning: str
    decided_at: datetime = Field(default_factory=datetime.utcnow)


class AgentMessage(BaseModel):
    """Message exchanged between agents."""
    id: str
    sender: AgentRole
    recipient: Optional[AgentRole] = None  # None means broadcast
    content: str
    message_type: str = Field(default="chat", description="Message type (chat, command, response)")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SearchResult(BaseModel):
    """Web search result."""
    url: str
    title: str
    snippet: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    source: str = Field(description="Search engine used (searxng, etc.)")
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class ScrapedContent(BaseModel):
    """Scraped web content."""
    url: str
    title: Optional[str] = None
    content: str = Field(description="Clean markdown content")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class MemoryEntry(BaseModel):
    """Entry in the persistent memory system."""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accessed_count: int = Field(default=0)
    last_accessed: Optional[datetime] = None


class ProjectSpec(BaseModel):
    """Project specification from spec.md."""
    title: str
    description: str
    requirements: List[str]
    constraints: List[str]
    acceptance_criteria: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectPlan(BaseModel):
    """Project plan from plan.md."""
    architecture: str
    tech_stack: Dict[str, str]
    file_structure: Dict[str, Any]
    api_schema: Optional[Dict[str, Any]] = None
    database_schema: Optional[Dict[str, Any]] = None
    tasks: List[Task]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionMetrics(BaseModel):
    """Metrics for task execution."""
    task_id: str
    duration_seconds: float
    tokens_generated: int
    iterations: int
    consensus_rounds: int
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)