"""
Episodic memory for tracking agent experiences and debugging.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger

from src.core.models import Task, AgentRole, ExecutionMetrics
from src.memory.persistent_memory import persistent_memory


class EpisodicMemory:
    """
    Tracks episodes (sequences of events) for learning and debugging.
    
    Features:
    - Record task execution sequences
    - Track agent interactions
    - Store debugging information
    - Enable replay and analysis
    """
    
    def __init__(self):
        self.memory = persistent_memory
        self.active_episodes = {}
    
    async def start_episode(
        self,
        task: Task,
        context: Dict
    ) -> str:
        """
        Start a new episode for a task.
        
        Args:
            task: The task being executed
            context: Additional context
        
        Returns:
            Episode ID
        """
        episode_id = str(uuid.uuid4())
        
        episode = {
            "id": episode_id,
            "task_id": task.id,
            "task_title": task.title,
            "started_at": datetime.utcnow(),
            "events": [],
            "context": context,
            "status": "active"
        }
        
        self.active_episodes[episode_id] = episode
        logger.info(f"Started episode {episode_id} for task {task.id}")
        
        return episode_id
    
    async def record_event(
        self,
        episode_id: str,
        event_type: str,
        agent_role: AgentRole,
        data: Dict,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Record an event in an episode.
        
        Args:
            episode_id: Episode ID
            event_type: Type of event (generation, verification, decision, etc.)
            agent_role: Which agent performed this action
            data: Event data
            metadata: Additional metadata
        """
        if episode_id not in self.active_episodes:
            logger.warning(f"Episode {episode_id} not found")
            return
        
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "agent": agent_role.value,
            "data": data,
            "metadata": metadata or {}
        }
        
        self.active_episodes[episode_id]["events"].append(event)
        logger.debug(f"Recorded {event_type} event in episode {episode_id}")
    
    async def end_episode(
        self,
        episode_id: str,
        success: bool,
        metrics: Optional[ExecutionMetrics] = None
    ) -> None:
        """
        End an episode and store it in persistent memory.
        
        Args:
            episode_id: Episode ID
            success: Whether the episode succeeded
            metrics: Execution metrics
        """
        if episode_id not in self.active_episodes:
            logger.warning(f"Episode {episode_id} not found")
            return
        
        episode = self.active_episodes[episode_id]
        episode["ended_at"] = datetime.utcnow()
        episode["status"] = "success" if success else "failure"
        episode["duration_seconds"] = (
            episode["ended_at"] - episode["started_at"]
        ).total_seconds()
        
        if metrics:
            episode["metrics"] = {
                "tokens_generated": metrics.tokens_generated,
                "iterations": metrics.iterations,
                "consensus_rounds": metrics.consensus_rounds
            }
        
        # Store in persistent memory
        await self._store_episode(episode)
        
        # Remove from active episodes
        del self.active_episodes[episode_id]
        
        logger.info(f"Ended episode {episode_id} - {episode['status']}")
    
    async def _store_episode(self, episode: Dict) -> None:
        """Store episode in persistent memory."""
        
        # Create summary for embedding
        summary = f"""
Task: {episode['task_title']}
Duration: {episode.get('duration_seconds', 0):.2f}s
Status: {episode['status']}
Events: {len(episode['events'])}
"""
        
        # Add event summary
        event_types = {}
        for event in episode['events']:
            event_type = event['type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        summary += "\nEvent Breakdown:\n"
        for event_type, count in event_types.items():
            summary += f"- {event_type}: {count}\n"
        
        metadata = {
            "type": "episode",
            "task_id": episode['task_id'],
            "status": episode['status'],
            "duration": episode.get('duration_seconds', 0),
            "event_count": len(episode['events']),
            "started_at": episode['started_at'].isoformat()
        }
        
        await self.memory.store(
            content=summary,
            collection_name="experiences",
            metadata=metadata
        )
    
    async def recall_similar_episodes(
        self,
        task_description: str,
        n_results: int = 3,
        success_only: bool = True
    ) -> List[Dict]:
        """
        Recall similar past episodes.
        
        Args:
            task_description: Description of current task
            n_results: Number of episodes to return
            success_only: Only return successful episodes
        
        Returns:
            List of similar episode summaries
        """
        filter_metadata = {"type": "episode"}
        if success_only:
            filter_metadata["status"] = "success"
        
        memories = await self.memory.search(
            query=task_description,
            collection_name="experiences",
            n_results=n_results,
            filter_metadata=filter_metadata
        )
        
        return [
            {
                "content": mem.content,
                "metadata": mem.metadata,
                "similarity": "high"  # Would calculate from embedding distance
            }
            for mem in memories
        ]
    
    async def analyze_failures(
        self,
        limit: int = 10
    ) -> List[Dict]:
        """
        Analyze recent failures for patterns.
        
        Args:
            limit: Number of failures to analyze
        
        Returns:
            List of failure patterns
        """
        # Query failed episodes
        filter_metadata = {
            "type": "episode",
            "status": "failure"
        }
        
        failures = await self.memory.search(
            query="",
            collection_name="experiences",
            n_results=limit,
            filter_metadata=filter_metadata
        )
        
        # Analyze patterns
        patterns = []
        for failure in failures:
            patterns.append({
                "task_id": failure.metadata.get("task_id"),
                "duration": failure.metadata.get("duration", 0),
                "events": failure.metadata.get("event_count", 0),
                "content": failure.content
            })
        
        return patterns
    
    async def get_episode_statistics(self) -> Dict:
        """Get statistics about recorded episodes."""
        
        # This would query ChromaDB for aggregate stats
        # Simplified version:
        return {
            "active_episodes": len(self.active_episodes),
            "total_recorded": "See ChromaDB stats",
            "note": "Use persistent_memory.get_statistics() for full stats"
        }


# Global episodic memory instance
episodic_memory = EpisodicMemory()