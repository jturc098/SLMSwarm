"""
Metrics collection and monitoring.
"""

import time
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass, field
from loguru import logger

from src.core.models import ExecutionMetrics, AgentRole


@dataclass
class AgentMetrics:
    """Metrics for a single agent."""
    role: AgentRole
    total_tasks: int = 0
    active_tasks: int = 0
    total_tokens: int = 0
    total_duration: float = 0.0
    errors: int = 0
    
    def add_execution(self, metrics: ExecutionMetrics) -> None:
        """Add execution metrics."""
        self.total_tasks += 1
        self.total_tokens += metrics.tokens_generated
        self.total_duration += metrics.duration_seconds
        
        if not metrics.success:
            self.errors += 1
    
    def get_average_duration(self) -> float:
        """Get average task duration."""
        if self.total_tasks == 0:
            return 0.0
        return self.total_duration / self.total_tasks
    
    def get_tokens_per_second(self) -> float:
        """Get average tokens per second."""
        if self.total_duration == 0:
            return 0.0
        return self.total_tokens / self.total_duration


class MetricsCollector:
    """
    Collects and aggregates metrics for monitoring.
    """
    
    def __init__(self):
        self.agent_metrics: Dict[AgentRole, AgentMetrics] = {
            role: AgentMetrics(role=role)
            for role in AgentRole
        }
        
        self.execution_history: List[ExecutionMetrics] = []
        self.start_time = datetime.utcnow()
    
    def record_execution(self, metrics: ExecutionMetrics, agent_role: AgentRole) -> None:
        """
        Record execution metrics.
        
        Args:
            metrics: Execution metrics
            agent_role: Which agent executed the task
        """
        self.execution_history.append(metrics)
        self.agent_metrics[agent_role].add_execution(metrics)
        
        logger.debug(
            f"Recorded metrics for {agent_role.value}: "
            f"{metrics.duration_seconds:.2f}s, "
            f"{metrics.tokens_generated} tokens"
        )
    
    def get_system_metrics(self) -> Dict:
        """Get overall system metrics."""
        
        if not self.execution_history:
            return {
                "status": "no_data",
                "message": "No executions recorded yet"
            }
        
        total_executions = len(self.execution_history)
        successful = sum(1 for m in self.execution_history if m.success)
        
        recent = self.execution_history[-10:]
        avg_duration = sum(m.duration_seconds for m in recent) / len(recent)
        total_tokens = sum(m.tokens_generated for m in self.execution_history)
        total_consensus_rounds = sum(m.consensus_rounds for m in self.execution_history)
        
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful,
            "success_rate": successful / total_executions,
            "average_duration": avg_duration,
            "total_tokens": total_tokens,
            "total_consensus_rounds": total_consensus_rounds,
            "uptime_seconds": uptime,
            "tokens_per_second": total_tokens / uptime if uptime > 0 else 0
        }
    
    def get_agent_metrics(self, role: AgentRole) -> Dict:
        """Get metrics for specific agent."""
        
        metrics = self.agent_metrics[role]
        
        return {
            "role": role.value,
            "total_tasks": metrics.total_tasks,
            "active_tasks": metrics.active_tasks,
            "total_tokens": metrics.total_tokens,
            "total_duration": metrics.total_duration,
            "errors": metrics.errors,
            "average_duration": metrics.get_average_duration(),
            "tokens_per_second": metrics.get_tokens_per_second()
        }
    
    def get_all_agent_metrics(self) -> Dict[str, Dict]:
        """Get metrics for all agents."""
        
        return {
            role.value: self.get_agent_metrics(role)
            for role in AgentRole
        }
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary for dashboard."""
        
        system = self.get_system_metrics()
        agents = self.get_all_agent_metrics()
        
        return {
            "system": system,
            "agents": agents,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global metrics collector
metrics_collector = MetricsCollector()