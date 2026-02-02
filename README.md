# Project Hydra-Consensus

A groundbreaking local SLM swarm architecture that combines Agent Zero with consensus-driven verification, web intelligence, and persistent learning on consumer hardware (RTX 4090).

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AGENT ZERO FRAMEWORK                                │
│                    (Meta-Orchestrator + Memory Layer)                       │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │   PERSISTENT    │  │   KNOWLEDGE     │  │     TOOL FACTORY            │  │
│  │     MEMORY      │  │     BASE        │  │  (Dynamic Tool Creation)    │  │
│  │  (ChromaDB)     │  │  (Vector Store) │  │                             │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │   AGENT 0   │ │   AGENT 1   │ │   AGENT 2   │
            │  ARCHITECT  │ │   WORKER    │ │     QA      │
            │  (Primary)  │ │ (Delegated) │ │ (Delegated) │
            └─────────────┘ └─────────────┘ └─────────────┘
```

## Key Features

- **Multi-Model Swarm**: Heterogeneous models optimized for different roles
- **Consensus Verification**: Multiple agents verify each code output
- **Web Intelligence**: Integrated search (Searxng) and scraping (Jina Reader)
- **Persistent Learning**: ChromaDB-based memory that improves over time
- **Spec-Driven Development**: Filesystem-based state management
- **Zero Marginal Cost**: Runs entirely on local hardware

## Hardware Requirements

- **GPU**: NVIDIA RTX 4090 (24GB VRAM)
- **CPU**: High-performance (e.g., AMD 9800X3D or equivalent)
- **RAM**: 64GB recommended
- **Storage**: 1TB NVMe SSD

## Model Architecture

| Agent | Model | Size | Quant | VRAM |
|-------|-------|------|-------|------|
| Architect | DeepSeek-R1-Distill-Qwen-14B | 14B | Q4_K_M | 8.5 GB |
| Worker Backend | Qwen2.5-Coder-7B | 7B | Q4_K_M | 4.5 GB |
| Worker Frontend | Qwen2.5-Coder-3B | 3B | Q4_K_M | 2.0 GB |
| QA Sentinel | DeepSeek-R1-Distill-1.5B | 1.5B | Q6_K | 1.4 GB |
| Consensus Judge | Phi-4-Mini | 3.8B | Q4_K_M | 2.2 GB |
| **KV Cache** | - | - | Q8_0 | ~3.5 GB |
| **Total** | - | - | - | **~23.6 GB** |

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/SLMSwarm.git
cd SLMSwarm
cp .env.example .env
```

### 2. Download Models

```bash
chmod +x scripts/download_models.sh
./scripts/download_models.sh
```

### 3. Start Services

```bash
docker-compose up -d
```

### 4. Initialize Agent Zero

```bash
python src/hydra_control.py --init
```

### 5. Run Your First Task

```bash
python src/hydra_control.py --task "Build a REST API for a todo app"
```

## Project Structure

```
SLMSwarm/
├── agent-zero/              # Forked Agent Zero with extensions
├── models/                  # GGUF model storage
├── specs/                   # Project specifications
├── memory/                  # ChromaDB persistence
├── src/                     # Custom orchestration layer
├── docker-compose.yml       # All services
└── scripts/                 # Utility scripts
```

## Documentation

- [Architecture Deep Dive](docs/architecture.md)
- [Consensus Protocol](docs/consensus.md)
- [Memory System](docs/memory.md)
- [Web Tools](docs/web-tools.md)
- [API Reference](docs/api.md)

## Performance

- **Planning Speed**: ~15-25 tokens/sec (Architect)
- **Code Generation**: ~60-100 tokens/sec (Workers)
- **Verification**: ~80-120 tokens/sec (QA)
- **Full Task Cycle**: 30-120 seconds
- **Parallel Capacity**: 3-4 tasks simultaneously

## License

MIT License - See [LICENSE](LICENSE) for details

## Acknowledgments

- Based on [Agent Zero](https://github.com/frdel/agent-zero)
- Inspired by Claude Code and Atoms.dev
- Research papers in `/docs/research/`