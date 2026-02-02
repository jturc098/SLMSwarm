"""
Knowledge base management and seeding.
"""

from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from src.memory.persistent_memory import persistent_memory


class KnowledgeBase:
    """
    Manages the knowledge base for the swarm.
    
    Seeds memory with:
    - Common design patterns
    - Best practices
    - Library documentation summaries
    - Error solutions
    """
    
    def __init__(self):
        self.memory = persistent_memory
        self.seed_data_dir = Path("./knowledge_seeds")
        self.seed_data_dir.mkdir(parents=True, exist_ok=True)
    
    async def seed_initial_knowledge(self) -> Dict[str, int]:
        """
        Seed the knowledge base with initial knowledge.
        
        Returns:
            Statistics about what was seeded
        """
        logger.info("Seeding knowledge base...")
        
        stats = {
            "patterns": 0,
            "best_practices": 0,
            "common_errors": 0
        }
        
        # Seed design patterns
        patterns_seeded = await self._seed_design_patterns()
        stats["patterns"] = patterns_seeded
        
        # Seed best practices
        practices_seeded = await self._seed_best_practices()
        stats["best_practices"] = practices_seeded
        
        # Seed common errors
        errors_seeded = await self._seed_common_errors()
        stats["common_errors"] = errors_seeded
        
        logger.info(f"Knowledge base seeded: {stats}")
        return stats
    
    async def _seed_design_patterns(self) -> int:
        """Seed common design patterns."""
        
        patterns = [
            {
                "name": "Singleton Pattern",
                "language": "python",
                "context": "Ensure a class has only one instance",
                "code": """
class Singleton:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
"""
            },
            {
                "name": "Factory Pattern",
                "language": "python",
                "context": "Create objects without specifying exact class",
                "code": """
class ShapeFactory:
    @staticmethod
    def create_shape(shape_type: str):
        if shape_type == "circle":
            return Circle()
        elif shape_type == "square":
            return Square()
        raise ValueError(f"Unknown shape: {shape_type}")
"""
            },
            {
                "name": "Async Context Manager",
                "language": "python",
                "context": "Resource management with async/await",
                "code": """
class AsyncResource:
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
"""
            },
            {
                "name": "Repository Pattern",
                "language": "python",
                "context": "Abstract data access layer",
                "code": """
class Repository:
    def __init__(self, db):
        self.db = db
    
    async def get(self, id: str):
        return await self.db.query(f"SELECT * WHERE id={id}")
    
    async def save(self, entity):
        return await self.db.insert(entity)
"""
            }
        ]
        
        count = 0
        for pattern in patterns:
            await self.memory.store_code_pattern(
                pattern_name=pattern["name"],
                code=pattern["code"],
                language=pattern["language"],
                context=pattern["context"],
                success_metrics={"success_rate": 1.0, "usage_count": 0}
            )
            count += 1
        
        return count
    
    async def _seed_best_practices(self) -> int:
        """Seed coding best practices."""
        
        practices = [
            {
                "title": "Error Handling Best Practices",
                "language": "python",
                "content": """
Always handle specific exceptions first, generic ones last.
Use context managers for resource cleanup.
Log errors with context for debugging.

Example:
try:
    result = await operation()
except SpecificError as e:
    logger.error(f"Specific error: {e}")
    handle_specific()
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    handle_generic()
finally:
    cleanup()
"""
            },
            {
                "title": "Async Best Practices",
                "language": "python",
                "content": """
Use asyncio.gather() for parallel execution.
Use asyncio.wait_for() for timeouts.
Avoid blocking operations in async code.

Example:
results = await asyncio.gather(
    task1(),
    task2(),
    return_exceptions=True
)
"""
            },
            {
                "title": "Type Hints Best Practices",
                "language": "python",
                "content": """
Always use type hints for function parameters and returns.
Use Optional[] for values that can be None.
Use List[], Dict[] for generic containers.

Example:
async def process(data: List[str], timeout: Optional[int] = None) -> Dict[str, any]:
    ...
"""
            }
        ]
        
        count = 0
        for practice in practices:
            await self.memory.store(
                content=practice["content"],
                collection_name="code_patterns",
                metadata={
                    "type": "best_practice",
                    "title": practice["title"],
                    "language": practice["language"]
                }
            )
            count += 1
        
        return count
    
    async def _seed_common_errors(self) -> int:
        """Seed common error resolutions."""
        
        errors = [
            {
                "error": "ModuleNotFoundError: No module named 'X'",
                "context": "Python import error",
                "resolution": """
1. Check if package is installed: pip list | grep X
2. Install if missing: pip install X
3. Verify virtual environment is activated
4. Check for typos in import statement
"""
            },
            {
                "error": "TypeError: 'NoneType' object is not iterable",
                "context": "Attempting to iterate over None",
                "resolution": """
1. Add None check before iteration
2. Use default value: for item in (items or [])
3. Ensure function returns expected type
4. Add type hints to catch early
"""
            },
            {
                "error": "asyncio.TimeoutError",
                "context": "Async operation timed out",
                "resolution": """
1. Increase timeout if operation is legitimately slow
2. Check for deadlocks in async code
3. Add progress logging to identify bottleneck
4. Consider breaking into smaller operations
"""
            },
            {
                "error": "ConnectionRefusedError: [Errno 111] Connection refused",
                "context": "Cannot connect to service",
                "resolution": """
1. Check if service is running: docker ps, systemctl status
2. Verify correct host and port
3. Check firewall rules
4. Ensure service is bound to correct interface
"""
            }
        ]
        
        count = 0
        for error in errors:
            await self.memory.store_error_resolution(
                error_message=error["error"],
                context=error["context"],
                resolution=error["resolution"],
                success=True
            )
            count += 1
        
        return count
    
    async def add_custom_knowledge(
        self,
        title: str,
        content: str,
        knowledge_type: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Add custom knowledge to the base.
        
        Args:
            title: Knowledge title
            content: Knowledge content
            knowledge_type: Type (pattern, practice, error, etc.)
            metadata: Additional metadata
        """
        full_metadata = metadata or {}
        full_metadata.update({
            "type": knowledge_type,
            "title": title,
            "custom": True
        })
        
        # Determine collection based on type
        collection_map = {
            "pattern": "code_patterns",
            "practice": "code_patterns",
            "error": "errors",
            "solution": "solutions",
            "experience": "experiences"
        }
        
        collection = collection_map.get(knowledge_type, "experiences")
        
        await self.memory.store(
            content=content,
            collection_name=collection,
            metadata=full_metadata
        )
        
        logger.info(f"Added custom knowledge: {title}")


# Global knowledge base instance
knowledge_base = KnowledgeBase()
