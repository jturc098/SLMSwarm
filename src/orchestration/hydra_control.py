"""
Main control plane for Hydra-Consensus swarm.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.models import Task, TaskStatus, AgentRole, ExecutionMetrics
from src.orchestration.task_dispatcher import TaskDispatcher
from src.memory import knowledge_base, episodic_memory
from src.extensions.hydration import SpecHydration


class HydraControl:
    """
    Main orchestration and control plane for the swarm.
    
    Responsibilities:
    - Initialize all swarm components
    - Route tasks to appropriate agents
    - Coordinate consensus protocol
    - Track execution metrics
    - Provide REST API for control
    """
    
    def __init__(self):
        self.app = FastAPI(
            title="Hydra-Consensus Control Plane",
            description="Multi-agent swarm orchestration system",
            version="0.1.0"
        )
        
        self.dispatcher = TaskDispatcher()
        self.spec_hydration = SpecHydration()
        
        self.active_tasks: Dict[str, Task] = {}
        self.execution_metrics: List[ExecutionMetrics] = []
        self.websocket_connections: List[WebSocket] = []
        
        self._setup_middleware()
        self._setup_routes()
    
    def _setup_middleware(self):
        """Configure FastAPI middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "active_tasks": len(self.active_tasks),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.post("/tasks")
        async def create_task(task: Task):
            """Create a new task."""
            self.active_tasks[task.id] = task
            logger.info(f"Created task: {task.id}")
            
            # Start task execution asynchronously
            asyncio.create_task(self._execute_task(task))
            
            return {
                "task_id": task.id,
                "status": "queued",
                "message": "Task created and queued for execution"
            }
        
        @self.app.get("/tasks/{task_id}")
        async def get_task(task_id: str):
            """Get task status."""
            if task_id not in self.active_tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            task = self.active_tasks[task_id]
            return {
                "task_id": task.id,
                "status": task.status.value,
                "title": task.title,
                "created_at": task.created_at.isoformat(),
                "assigned_agent": task.assigned_agent.value if task.assigned_agent else None
            }
        
        @self.app.get("/tasks")
        async def list_tasks():
            """List all tasks."""
            return {
                "tasks": [
                    {
                        "task_id": task.id,
                        "title": task.title,
                        "status": task.status.value,
                        "priority": task.priority.value
                    }
                    for task in self.active_tasks.values()
                ],
                "total": len(self.active_tasks)
            }
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get execution metrics."""
            if not self.execution_metrics:
                return {"message": "No metrics available yet"}
            
            recent = self.execution_metrics[-10:]
            return {
                "recent_executions": len(recent),
                "average_duration": sum(m.duration_seconds for m in recent) / len(recent),
                "success_rate": sum(1 for m in recent if m.success) / len(recent),
                "total_tokens": sum(m.tokens_generated for m in recent)
            }
        
        @self.app.post("/initialize")
        async def initialize():
            """Initialize the swarm (seed knowledge, etc.)."""
            try:
                stats = await knowledge_base.seed_initial_knowledge()
                return {
                    "status": "initialized",
                    "knowledge_seeded": stats
                }
            except Exception as e:
                logger.error(f"Initialization failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/dashboard")
        async def dashboard():
            """Serve monitoring dashboard."""
            from fastapi.responses import FileResponse
            dashboard_path = Path(__file__).parent.parent / "monitoring" / "dashboard.html"
            return FileResponse(dashboard_path)
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    # Keep connection alive and send heartbeat
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
    
    async def _execute_task(self, task: Task):
        """
        Execute a task through the swarm.
        
        Full workflow:
        1. Start episode
        2. Route to appropriate agent
        3. Execute with consensus
        4. Record results
        5. Update task status
        """
        start_time = datetime.utcnow()
        episode_id = None
        
        try:
            # Update task status
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = start_time
            
            # Start episode for tracking
            episode_id = await episodic_memory.start_episode(
                task=task,
                context={"mode": "auto", "priority": task.priority.value}
            )
            
            # Route task to appropriate agent
            agent_role = self.dispatcher.route_task(task)
            task.assigned_agent = agent_role
            
            await self._broadcast_update({
                "type": "task_started",
                "task_id": task.id,
                "agent": agent_role.value
            })
            
            # Execute task through dispatcher
            result = await self.dispatcher.execute_task(task, episode_id)
            
            # Update task status
            task.status = TaskStatus.COMPLETED if result["success"] else TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            
            # Record metrics
            duration = (task.completed_at - start_time).total_seconds()
            metrics = ExecutionMetrics(
                task_id=task.id,
                duration_seconds=duration,
                tokens_generated=result.get("tokens", 0),
                iterations=result.get("iterations", 1),
                consensus_rounds=result.get("consensus_rounds", 0),
                success=result["success"],
                error_message=result.get("error"),
                timestamp=datetime.utcnow()
            )
            self.execution_metrics.append(metrics)
            
            # End episode
            if episode_id:
                await episodic_memory.end_episode(
                    episode_id=episode_id,
                    success=result["success"],
                    metrics=metrics
                )
            
            await self._broadcast_update({
                "type": "task_completed",
                "task_id": task.id,
                "success": result["success"],
                "duration": duration
            })
            
            logger.info(f"Task {task.id} completed - Success: {result['success']}")
            
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            
            if episode_id:
                await episodic_memory.end_episode(
                    episode_id=episode_id,
                    success=False,
                    metrics=None
                )
            
            await self._broadcast_update({
                "type": "task_failed",
                "task_id": task.id,
                "error": str(e)
            })
    
    async def _broadcast_update(self, message: Dict):
        """Broadcast update to all WebSocket connections."""
        if not self.websocket_connections:
            return
        
        disconnected = []
        for ws in self.websocket_connections:
            try:
                await ws.send_json(message)
            except:
                disconnected.append(ws)
        
        # Remove disconnected clients
        for ws in disconnected:
            self.websocket_connections.remove(ws)
    
    async def start(self):
        """Start the control plane."""
        settings.create_directories()
        logger.info("Hydra Control Plane started")
        logger.info(f"Listening on http://localhost:8090")
        logger.info(f"WebSocket available at ws://localhost:8090/ws")
    
    async def shutdown(self):
        """Shutdown the control plane gracefully."""
        logger.info("Shutting down Hydra Control Plane...")
        
        # Close all WebSocket connections
        for ws in self.websocket_connections:
            await ws.close()
        
        logger.info("Shutdown complete")


# Global control plane instance
hydra_control = HydraControl()