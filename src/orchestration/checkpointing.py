"""
Checkpointing system for crash recovery and state persistence.
"""

import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from src.core.models import Task, TaskStatus


class CheckpointManager:
    """
    Manages checkpoints for crash recovery.
    
    Features:
    - Automatic checkpointing after each task
    - State recovery on restart
    - Incremental checkpoints
    - Cleanup of old checkpoints
    """
    
    def __init__(self, checkpoint_dir: Path = Path("./.hydra/checkpoints")):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.latest_checkpoint_file = self.checkpoint_dir / "latest.json"
        self.max_checkpoints = 10
    
    async def create_checkpoint(
        self,
        tasks: List[Task],
        global_state: Dict,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a new checkpoint.
        
        Args:
            tasks: Current tasks
            global_state: Global system state
            metadata: Additional metadata
        
        Returns:
            Checkpoint ID
        """
        checkpoint_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{checkpoint_id}.pkl"
        
        checkpoint_data = {
            "id": checkpoint_id,
            "timestamp": datetime.utcnow().isoformat(),
            "tasks": [self._serialize_task(task) for task in tasks],
            "global_state": global_state,
            "metadata": metadata or {}
        }
        
        try:
            # Save as pickle for full object serialization
            with open(checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint_data, f)
            
            # Update latest pointer
            self.latest_checkpoint_file.write_text(checkpoint_id)
            
            logger.info(f"Created checkpoint {checkpoint_id}")
            
            # Cleanup old checkpoints
            await self._cleanup_old_checkpoints()
            
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            raise
    
    async def load_checkpoint(
        self,
        checkpoint_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Load checkpoint from disk.
        
        Args:
            checkpoint_id: Specific checkpoint to load, or None for latest
        
        Returns:
            Checkpoint data or None if not found
        """
        if checkpoint_id is None:
            # Load latest
            if not self.latest_checkpoint_file.exists():
                logger.warning("No checkpoints found")
                return None
            
            checkpoint_id = self.latest_checkpoint_file.read_text().strip()
        
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{checkpoint_id}.pkl"
        
        if not checkpoint_file.exists():
            logger.warning(f"Checkpoint {checkpoint_id} not found")
            return None
        
        try:
            with open(checkpoint_file, 'rb') as f:
                checkpoint_data = pickle.load(f)
            
            logger.info(f"Loaded checkpoint {checkpoint_id}")
            return checkpoint_data
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    async def list_checkpoints(self) -> List[Dict]:
        """
        List available checkpoints.
        
        Returns:
            List of checkpoint metadata
        """
        checkpoints = []
        
        for checkpoint_file in sorted(self.checkpoint_dir.glob("checkpoint_*.pkl")):
            try:
                with open(checkpoint_file, 'rb') as f:
                    data = pickle.load(f)
                
                checkpoints.append({
                    "id": data["id"],
                    "timestamp": data["timestamp"],
                    "tasks_count": len(data["tasks"]),
                    "file_size": checkpoint_file.stat().st_size
                })
            except Exception as e:
                logger.warning(f"Failed to read checkpoint {checkpoint_file.name}: {e}")
        
        return checkpoints
    
    async def restore_from_checkpoint(
        self,
        checkpoint_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Restore system state from checkpoint.
        
        Args:
            checkpoint_id: Checkpoint to restore, or None for latest
        
        Returns:
            Restored state or None
        """
        checkpoint_data = await self.load_checkpoint(checkpoint_id)
        
        if not checkpoint_data:
            return None
        
        # Deserialize tasks
        tasks = [
            self._deserialize_task(task_data)
            for task_data in checkpoint_data["tasks"]
        ]
        
        restored_state = {
            "tasks": tasks,
            "global_state": checkpoint_data["global_state"],
            "checkpoint_timestamp": checkpoint_data["timestamp"]
        }
        
        logger.info(
            f"Restored {len(tasks)} tasks from checkpoint "
            f"{checkpoint_data['id']}"
        )
        
        return restored_state
    
    def _serialize_task(self, task: Task) -> Dict:
        """Serialize task to dict."""
        return task.model_dump()
    
    def _deserialize_task(self, task_data: Dict) -> Task:
        """Deserialize task from dict."""
        return Task(**task_data)
    
    async def _cleanup_old_checkpoints(self) -> None:
        """Remove old checkpoints, keeping only the most recent."""
        
        checkpoints = sorted(
            self.checkpoint_dir.glob("checkpoint_*.pkl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # Keep only max_checkpoints most recent
        for old_checkpoint in checkpoints[self.max_checkpoints:]:
            try:
                old_checkpoint.unlink()
                logger.debug(f"Removed old checkpoint {old_checkpoint.name}")
            except Exception as e:
                logger.warning(f"Failed to remove old checkpoint: {e}")


# Global checkpoint manager instance
checkpoint_manager = CheckpointManager()