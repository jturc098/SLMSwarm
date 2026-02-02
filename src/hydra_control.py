"""
Main entry point for Project Hydra-Consensus.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from loguru import logger
import uvicorn

from src.core.config import settings
from src.orchestration import hydra_control
from src.memory import knowledge_base


def setup_logging():
    """Configure logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.log_level
    )
    
    if settings.log_file:
        settings.log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            settings.log_file,
            rotation="100 MB",
            retention="30 days",
            level=settings.log_level
        )


async def initialize_system():
    """Initialize the Hydra system."""
    logger.info("Initializing Hydra-Consensus system...")
    
    # Create necessary directories
    settings.create_directories()
    
    # Seed knowledge base
    try:
        stats = await knowledge_base.seed_initial_knowledge()
        logger.info(f"Knowledge base seeded: {stats}")
    except Exception as e:
        logger.warning(f"Knowledge base seeding failed (will retry): {e}")
    
    # Start control plane
    await hydra_control.start()
    
    logger.info("✓ Hydra-Consensus initialized successfully")


def serve():
    """Start the FastAPI server."""
    logger.info("Starting Hydra Control Plane server...")
    
    uvicorn.run(
        hydra_control.app,
        host="0.0.0.0",
        port=8090,
        log_level=settings.log_level.lower(),
        access_log=True
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Project Hydra-Consensus - Local SLM Swarm"
    )
    
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize the system (seed knowledge base, create directories)"
    )
    
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the FastAPI control plane server"
    )
    
    parser.add_argument(
        "--task",
        type=str,
        help="Execute a single task (for testing)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Override log level if specified
    if args.log_level:
        settings.log_level = args.log_level
    
    setup_logging()
    
    # Handle commands
    if args.init:
        logger.info("Initializing Hydra-Consensus...")
        asyncio.run(initialize_system())
        logger.info("✓ Initialization complete")
        sys.exit(0)
    
    elif args.serve:
        # Initialize then serve
        asyncio.run(initialize_system())
        serve()
    
    elif args.task:
        # Quick task execution
        logger.info(f"Executing task: {args.task}")
        from src.core.models import Task, TaskPriority
        import uuid
        
        task = Task(
            id=str(uuid.uuid4()),
            title=args.task,
            description=args.task,
            priority=TaskPriority.HIGH
        )
        
        async def run_task():
            await initialize_system()
            from src.orchestration import task_dispatcher
            result = await task_dispatcher.execute_task(task)
            logger.info(f"Task result: {result}")
        
        asyncio.run(run_task())
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()