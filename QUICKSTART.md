# Hydra-Consensus Quick Start Guide

## Prerequisites

- NVIDIA RTX 4090 (24GB VRAM)
- Docker with NVIDIA runtime
- Python 3.12+
- 100GB free disk space for models

## Installation Steps

### 1. Clone Repository

```bash
git clone <repository-url>
cd SLMSwarm
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env if needed (defaults should work)
```

### 4. Download Models (~90GB)

```bash
chmod +x scripts/download_models.sh
./scripts/download_models.sh
```

This will download:
- DeepSeek-R1-Distill-Qwen-14B (8.5GB)
- Qwen2.5-Coder-7B (4.5GB)
- Qwen2.5-Coder-3B (2.0GB)
- DeepSeek-R1-Distill-1.5B (1.4GB)
- Phi-4-Mini (2.2GB)

### 5. Start All Services

```bash
docker-compose up -d
```

This starts:
- 5 model servers (llama.cpp)
- ChromaDB (persistent memory)
- Searxng (web search)
- Redis (caching)
- Hydra Control Plane

### 6. Verify Services

```bash
docker-compose ps
```

All services should show "Up" status.

### 7. Initialize Knowledge Base

```bash
python src/hydra_control.py --init
```

Seeds the system with:
- Design patterns
- Best practices
- Common error solutions

## Usage

### Start the Control Plane

```bash
python src/hydra_control.py --serve
```

Access at: http://localhost:8090

### Quick Task Execution

```bash
python src/hydra_control.py --task "Build a REST API for a todo app"
```

### API Usage

```bash
# Health check
curl http://localhost:8090/health

# Create task
curl -X POST http://localhost:8090/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "id": "task_001",
    "title": "Implement user authentication",
    "description": "Create JWT-based auth system",
    "priority": "high"
  }'

# Get task status
curl http://localhost:8090/tasks/task_001

# Get metrics
curl http://localhost:8090/metrics
```

### WebSocket Monitoring

```javascript
const ws = new WebSocket('ws://localhost:8090/ws');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Swarm update:', update);
};
```

## Architecture

### Model Servers
- **Port 8081**: Architect (DeepSeek-14B)
- **Port 8082**: Worker Backend (Qwen-7B)
- **Port 8083**: Worker Frontend (Qwen-3B)
- **Port 8084**: QA Sentinel (DeepSeek-1.5B)
- **Port 8085**: Consensus Judge (Phi-4-Mini)

### Supporting Services
- **Port 8000**: ChromaDB
- **Port 8888**: Searxng
- **Port 6379**: Redis

### Control Plane
- **Port 8090**: FastAPI + REST API
- **Port 8091**: WebSocket (real-time updates)

## Workflow Example

```python
from src.core.models import Task, TaskPriority
from src.orchestration import task_dispatcher
import uuid

# Create task
task = Task(
    id=str(uuid.uuid4()),
    title="Create user registration endpoint",
    description="Implement POST /api/users endpoint with validation",
    priority=TaskPriority.HIGH,
    metadata={
        "language": "python",
        "framework": "fastapi"
    }
)

# Execute with consensus protocol
result = await task_dispatcher.execute_task(task)

# Result includes:
# - winner_id: Which candidate won
# - code: The actual code
# - approach: Which approach was used
# - consensus_score: Quality score
# - iterations: How many candidates generated
```

## How It Works

1. **Task Created** → Routed to optimal agent based on complexity
2. **Memory Recall** → Searches for similar past solutions
3. **Parallel Generation** → Creates 3 candidates (conservative, aggressive, minimal)
4. **Cross-Verification** → QA + Architect verify each candidate
5. **Consensus Vote** → Judge selects winner
6. **Pattern Extraction** → Learns from winner, stores in memory
7. **Next Task** → Benefits from learned patterns!

## Monitoring

### Check VRAM Usage

```bash
nvidia-smi
```

Should show ~23.6GB / 24GB when all models loaded.

### View Logs

```bash
# Control plane logs
docker-compose logs -f hydra-control

# Model server logs
docker-compose logs -f architect-model
docker-compose logs -f worker-backend
```

### Memory Statistics

```bash
curl http://localhost:8090/metrics
```

## Troubleshooting

### Out of Memory Errors

If you get OOM errors:
1. Reduce context sizes in `.env`
2. Enable more aggressive KV cache quantization
3. Reduce parallel task limit

### Model Not Loading

Check Docker logs:
```bash
docker-compose logs architect-model
```

Common issues:
- Model file not found → Re-run download script
- CUDA error → Update NVIDIA drivers
- Port conflict → Change ports in docker-compose.yml

### Slow Performance

- Check VRAM usage (should be ~98%)
- Ensure Flash Attention is enabled
- Verify KV cache quantization is working
- Check CPU isn't bottleneck (9800X3D should be fine)

## Advanced Usage

### Custom System Prompts

Edit prompts in `src/core/agent_registry.py`

### Add Custom Knowledge

```python
from src.memory import knowledge_base

await knowledge_base.add_custom_knowledge(
    title="Your Pattern",
    content="Your code pattern here",
    knowledge_type="pattern",
    metadata={"language": "python"}
)
```

### Checkpoint/Restore

```python
from src.orchestration import checkpoint_manager

# Create checkpoint
checkpoint_id = await checkpoint_manager.create_checkpoint(
    tasks=current_tasks,
    global_state=state
)

# Restore from checkpoint
state = await checkpoint_manager.restore_from_checkpoint()
```

## Performance Expectations

- **Planning**: ~15-25 tokens/sec (Architect)
- **Coding**: ~60-100 tokens/sec (Workers)
- **Verification**: ~80-120 tokens/sec (QA)
- **Full Task**: 30-120 seconds
- **Parallel**: 3-4 tasks simultaneously

## Next Steps

- Read [Architecture Documentation](docs/architecture.md)
- Review [Consensus Protocol](docs/consensus.md)
- Explore [Memory System](docs/PHASE3_SUMMARY.md)
- Check [API Reference](docs/api.md)

## Support

- GitHub Issues: <repository-url>/issues
- Documentation: `docs/`
- Examples: `examples/`