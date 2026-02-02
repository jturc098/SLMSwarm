"""
Integration tests for Project Hydra-Consensus.
"""

import pytest
import uuid
from pathlib import Path

from src.core.models import Task, TaskPriority, TaskStatus, AgentRole
from src.core.config import settings
from src.orchestration import task_dispatcher
from src.extensions.consensus import ConsensusEngine
from src.extensions.hydration import SpecHydration
from src.memory import persistent_memory, knowledge_base


@pytest.fixture
async def clean_state():
    """Clean state before each test."""
    # Would clean test databases, etc.
    yield
    # Cleanup after test


@pytest.mark.asyncio
async def test_task_routing():
    """Test that tasks are routed to correct agents."""
    
    # Backend task
    backend_task = Task(
        id=str(uuid.uuid4()),
        title="Create API endpoint",
        description="Implement REST API with Python FastAPI",
        priority=TaskPriority.MEDIUM
    )
    
    role = task_dispatcher.route_task(backend_task)
    assert role == AgentRole.WORKER_BACKEND
    
    # Frontend task
    frontend_task = Task(
        id=str(uuid.uuid4()),
        title="Create React component",
        description="Build a user profile component with React",
        priority=TaskPriority.MEDIUM
    )
    
    role = task_dispatcher.route_task(frontend_task)
    assert role == AgentRole.WORKER_FRONTEND
    
    # Architecture task
    arch_task = Task(
        id=str(uuid.uuid4()),
        title="Design system",
        description="Design microservice architecture",
        priority=TaskPriority.HIGH
    )
    
    role = task_dispatcher.route_task(arch_task)
    assert role == AgentRole.ARCHITECT


@pytest.mark.asyncio
async def test_memory_persistence():
    """Test that memory persists patterns correctly."""
    
    # Store a pattern
    await persistent_memory.store_code_pattern(
        pattern_name="Test Pattern",
        code="def test(): pass",
        language="python",
        context="Test context",
        success_metrics={"success_rate": 1.0}
    )
    
    # Recall it
    patterns = await persistent_memory.recall_similar_patterns(
        description="test function",
        language="python",
        n_results=5
    )
    
    assert len(patterns) > 0
    assert any("Test Pattern" in p.metadata.get("pattern_name", "") for p in patterns)


@pytest.mark.asyncio
async def test_spec_hydration():
    """Test spec hydration loads and saves correctly."""
    
    hydration = SpecHydration(spec_dir=Path("./tests/test_specs"))
    
    from src.core.models import ProjectSpec
    
    # Create test spec
    spec = ProjectSpec(
        title="Test Project",
        description="Test description",
        requirements=["Req 1", "Req 2"],
        constraints=["Constraint 1"],
        acceptance_criteria=["Criteria 1"]
    )
    
    # Save it
    await hydration.save_spec(spec)
    
    # Load it back
    loaded_spec = await hydration.load_spec()
    
    assert loaded_spec is not None
    assert loaded_spec.title == "Test Project"
    assert len(loaded_spec.requirements) == 2
    
    # Cleanup
    import shutil
    shutil.rmtree("./tests/test_specs", ignore_errors=True)


@pytest.mark.asyncio
async def test_consensus_generation():
    """Test consensus engine generates multiple candidates."""
    
    consensus = ConsensusEngine()
    
    task = Task(
        id=str(uuid.uuid4()),
        title="Test task",
        description="Simple test",
        priority=TaskPriority.MEDIUM
    )
    
    # Mock agent client
    class MockAgent:
        role = AgentRole.WORKER_BACKEND
        model_name = "test-model"
        
        async def generate(self, prompt):
            class Response:
                content = "# Test code"
            return Response()
    
    agent = MockAgent()
    
    candidates = await consensus.generate_candidates(
        task,
        agent,
        approaches=["conservative", "aggressive"]
    )
    
    assert len(candidates) == 2
    assert candidates[0].approach == "conservative"
    assert candidates[1].approach == "aggressive"


@pytest.mark.asyncio
async def test_knowledge_base_seeding():
    """Test knowledge base seeds correctly."""
    
    stats = await knowledge_base.seed_initial_knowledge()
    
    assert stats["patterns"] >= 4
    assert stats["best_practices"] >= 3
    assert stats["common_errors"] >= 4


@pytest.mark.asyncio
async def test_web_tools():
    """Test web tools (search, scrape, docs)."""
    
    from src.tools import web_search_tool, scraper_tool, doc_lookup_tool
    
    # Test search (if Searxng is running)
    try:
        results = await web_search_tool.search("python fastapi", num_results=3)
        # May fail if Searxng not running - that's okay
        if results:
            assert len(results) <= 3
    except:
        pytest.skip("Searxng not available")
    
    # Test scraping (using Jina Reader)
    try:
        content = await scraper_tool.scrape("https://python.org")
        if content:
            assert content.url == "https://python.org"
            assert len(content.content) > 0
    except:
        pytest.skip("Scraping not available")


@pytest.mark.asyncio
async def test_checkpoint_recovery():
    """Test checkpoint save and restore."""
    
    from src.orchestration import checkpoint_manager
    
    tasks = [
        Task(
            id="test_1",
            title="Test task 1",
            description="Test",
            priority=TaskPriority.MEDIUM
        )
    ]
    
    state = {"test": "data"}
    
    # Create checkpoint
    checkpoint_id = await checkpoint_manager.create_checkpoint(
        tasks=tasks,
        global_state=state
    )
    
    assert checkpoint_id is not None
    
    # Restore checkpoint
    restored = await checkpoint_manager.restore_from_checkpoint(checkpoint_id)
    
    assert restored is not None
    assert len(restored["tasks"]) == 1
    assert restored["global_state"]["test"] == "data"


@pytest.mark.asyncio
async def test_state_bus():
    """Test state bus message passing."""
    
    from src.orchestration import state_bus
    from src.core.models import AgentMessage
    
    # Create message
    message = AgentMessage(
        id=str(uuid.uuid4()),
        sender=AgentRole.ARCHITECT,
        recipient=AgentRole.WORKER_BACKEND,
        content="Test message",
        message_type="command"
    )
    
    # Publish message
    await state_bus.publish(message)
    
    # Verify it's in the queue
    messages = await state_bus.get_messages(sender=AgentRole.ARCHITECT)
    
    assert len(messages) > 0
    assert messages[0].content == "Test message"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])