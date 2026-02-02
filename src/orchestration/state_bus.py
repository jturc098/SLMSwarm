"""
Filesystem-based state bus for agent communication.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from src.core.models import AgentMessage, AgentRole


class StateBus:
    """
    Filesystem-based message bus for agent communication.
    
    Uses filesystem as IPC mechanism:
    - Agents write messages to .hydra/messages/
    - File watchers trigger reads
    - Enables parallel agent communication
    """
    
    def __init__(self, bus_dir: Path = Path("./.hydra/bus")):
        self.bus_dir = bus_dir
        self.bus_dir.mkdir(parents=True, exist_ok=True)
        
        self.messages_dir = self.bus_dir / "messages"
        self.messages_dir.mkdir(exist_ok=True)
        
        self.state_file = self.bus_dir / "state.json"
        self.message_queue: List[AgentMessage] = []
        self.subscribers: Dict[AgentRole, asyncio.Queue] = {}
    
    async def publish(
        self,
        message: AgentMessage
    ) -> None:
        """
        Publish message to the bus.
        
        Args:
            message: Message to publish
        """
        # Write to filesystem
        message_file = self.messages_dir / f"{message.id}.json"
        message_file.write_text(message.model_dump_json(indent=2))
        
        # Add to in-memory queue
        self.message_queue.append(message)
        
        # Notify subscribers
        if message.recipient:
            # Direct message
            if message.recipient in self.subscribers:
                await self.subscribers[message.recipient].put(message)
        else:
            # Broadcast to all subscribers
            for queue in self.subscribers.values():
                await queue.put(message)
        
        logger.debug(f"Published message {message.id} from {message.sender.value}")
    
    async def subscribe(
        self,
        agent_role: AgentRole
    ) -> asyncio.Queue:
        """
        Subscribe to messages for specific agent role.
        
        Args:
            agent_role: Role to subscribe as
        
        Returns:
            Queue for receiving messages
        """
        if agent_role not in self.subscribers:
            self.subscribers[agent_role] = asyncio.Queue()
        
        logger.info(f"Agent {agent_role.value} subscribed to state bus")
        return self.subscribers[agent_role]
    
    async def get_messages(
        self,
        recipient: Optional[AgentRole] = None,
        sender: Optional[AgentRole] = None,
        limit: int = 10
    ) -> List[AgentMessage]:
        """
        Get messages from the bus.
        
        Args:
            recipient: Filter by recipient
            sender: Filter by sender
            limit: Maximum messages to return
        
        Returns:
            List of messages
        """
        messages = self.message_queue[-limit:]
        
        # Apply filters
        if recipient:
            messages = [m for m in messages if m.recipient == recipient]
        
        if sender:
            messages = [m for m in messages if m.sender == sender]
        
        return messages
    
    async def save_state(self, state: Dict) -> None:
        """
        Save global state to filesystem.
        
        Args:
            state: State dictionary
        """
        state_with_timestamp = {
            **state,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        self.state_file.write_text(json.dumps(state_with_timestamp, indent=2))
        logger.debug("State saved to filesystem")
    
    async def load_state(self) -> Optional[Dict]:
        """
        Load global state from filesystem.
        
        Returns:
            State dictionary or None if not found
        """
        if not self.state_file.exists():
            return None
        
        try:
            content = self.state_file.read_text()
            state = json.loads(content)
            logger.debug("State loaded from filesystem")
            return state
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None
    
    async def clear_old_messages(self, max_age_hours: int = 24) -> int:
        """
        Clear old messages from filesystem.
        
        Args:
            max_age_hours: Maximum age of messages to keep
        
        Returns:
            Number of messages cleared
        """
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        cleared = 0
        
        for message_file in self.messages_dir.glob("*.json"):
            if message_file.stat().st_mtime < cutoff:
                message_file.unlink()
                cleared += 1
        
        if cleared > 0:
            logger.info(f"Cleared {cleared} old messages")
        
        return cleared


# Global state bus instance
state_bus = StateBus()