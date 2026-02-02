# Project Hydra-Consensus - Complete Architecture

## Executive Summary

Project Hydra-Consensus is a groundbreaking local SLM swarm that runs entirely on consumer hardware (RTX 4090). It combines multiple specialized AI agents with consensus-driven verification, web intelligence, and persistent learning to create a self-improving autonomous development system.

## Core Innovations

### 1. Consensus-Driven Verification
- Generates **3 parallel solutions** with different approaches
- Cross-verifies with independent QA + Architect agents
- Selects winner through consensus voting
- **Zero marginal cost** enables unlimited iterations

### 2. Persistent Memory System
- ChromaDB vector store with semantic search
- Learns from every consensus decision
- Recalls similar patterns for new tasks
- Compounds knowledge over time

### 3. Web-Enhanced Intelligence
- Self-hosted Searxng for unlimited search
- Jina Reader for clean documentation scraping
- Error solution lookup from Stack Overflow
- Real-time knowledge beyond training data

### 4. Filesystem-Based State
- spec.md, plan.md, tasks.md as source of truth
- Survives crashes and power outages
- Enables multi-day projects
- Human-readable and editable

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HYDRA CONTROL PLANE                                  │
│                    (FastAPI + WebSocket + Orchestration)                    │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │   TASK          │  │   STATE BUS     │  │     CHECKPOINT              │  │
│  │   DISPATCHER    │  │  (Filesystem)   │  │     MANAGER                 │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
         ┌──────────────┬───────────┴───────────┬──────────────┬──────────────┐
         ▼              ▼                       ▼              ▼              ▼
   ┌──────────┐   ┌──────────┐           ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ARCHITECT │   │ WORKER-A │           │ WORKER-B │   │    QA    │   │  JUDGE   │
   │ :8081    │   │  :8082   │           │  :8083   │   │  :8084   │   │  :8085   │
   │DeepSeek  │   │ Qwen-7B  │           │ Qwen-3B  │   │DeepSeek  │   │ Phi-4    │
   │   14B    │   │  Coder   │           │  Coder   │   │   1.5B   │   │  Mini    │
   └────┬─────┘   └────┬─────┘           └────┬─────┘   └────┬─────┘   └────┬─────┘
        │              │                       │              │              │
        └──────────────┴───────────────────────┴──────────────┴──────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌────────────┐  ┌────────────┐  ┌────────────┐
            │  CHROMADB  │  │  SEARXNG   │  │   REDIS    │
            │  :8000     │  │  :8888     │  │  :6379     │
            │ (Memory)   │  │ (Search)   │  │ (Cache)    │
            └────────────┘  └────────────┘  └────────────┘
```

## VRAM Budget (Perfect Fit)

| Component | Model | Size | Quant | VRAM |
|-----------|-------|------|-------|------|
| Architect | DeepSeek-R1-Distill-Qwen-14B | 14B | Q4_K_M | 8.5 GB |
| Worker Backend | Qwen2.5-Coder-7B | 7B | Q4_K_M | 4.5 GB |
| Worker Frontend | Qwen2.5-Coder-3B | 3B | Q4_K_M | 2.0 GB |
| QA Sentinel | DeepSeek-R1-Distill-1.5B | 1.5B | Q6_K | 1.4 GB |
| Consensus Judge | Phi-4-Mini | 3.8B | Q4_K_M | 2.2 GB |
| **KV Cache** | All agents | - | Q8_0 | ~3.5 GB |
| **CUDA Overhead** | 5 processes | - | - | ~1.5 GB |
| **TOTAL** | - | - | - | **23.6 GB** |

**Buffer**: 400 MB safety margin (98.3% utilization) ✅

## Component Details

### Phase 1: Foundation
- **Docker Infrastructure**: 5 llama.cpp servers + 3 supporting services
- **Configuration**: Pydantic settings with validation
- **Data Models**: Complete type system for all entities
- **Agent Registry**: Role-based configuration and routing

### Phase 2: Extensions
- **ConsensusEngine**: Multi-candidate generation and verification
- **SpecHydration**: Filesystem state management
- **MultiModelRouter**: Complexity-based agent selection
- **Web Tools**: Search, scraping, documentation lookup

### Phase 3: Memory
- **PersistentMemory**: ChromaDB with 4 collections
- **PatternExtractor**: Automatic pattern recognition
- **KnowledgeBase**: Pre-seeded best practices
- **EpisodicMemory**: Event tracking and replay

### Phase 4: Orchestration
- **HydraControl**: FastAPI control plane with WebSocket
- **TaskDispatcher**: Executes consensus protocol
- **ExecutionSandbox**: Docker-based code execution
- **StateBus**: Filesystem IPC for agents
- **CheckpointManager**: Crash recovery system

## Execution Flow

### Single Task Execution

```
1. USER submits task
       ↓
2. DISPATCHER routes to optimal agent (complexity-based)
       ↓
3. MEMORY recalls similar patterns
       ↓
4. CONSENSUS generates 3 candidates (parallel)
   - Conservative approach
   - Aggressive approach  
   - Minimal approach
       ↓
5. CROSS-VERIFY each candidate
   - QA Sentinel checks correctness
   - Architect reviews design
       ↓
6. CONSENSUS JUDGE selects winner
   - Scores on 4 criteria
   - Provides reasoning
       ↓
7. PATTERN EXTRACTOR learns from winner
   - Identifies reusable patterns
   - Stores in memory
       ↓
8. RESULT returned to user
   - Code + metrics + reasoning
```

### Parallel Multi-Task Execution

```
DISPATCHER analyzes task list
       ↓
   Groups by agent type
       ↓
┌─────────┬─────────┬─────────┐
│ Backend │Frontend │   QA    │
│ Tasks   │ Tasks   │ Tasks   │
└────┬────┴────┬────┴────┬────┘
     │         │         │
     ▼         ▼         ▼
Execute in parallel (3-4 tasks)
     │         │         │
     └────┬────┴────┬────┘
          ▼         
     Merge results
```

## Memory Learning Cycle

```
Task Execution
     ↓
Consensus Selection
     ↓
Pattern Extraction
     ↓
Store in ChromaDB
     ↓
Next Task → Recalls patterns
     ↓
Better Solutions!
     ↓
[Cycle repeats]
```

After 100 tasks, the system has learned:
- 100+ code patterns
- 100+ solutions
- Error resolutions
- Best approaches for each problem type

## Agent Specialization

### Architect (DeepSeek-R1-14B)
- **Reasoning-optimized** with "thinking" capability
- Plans architecture and designs systems
- Creates task breakdowns with dependencies
- Reviews code for architectural soundness

### Worker Backend (Qwen2.5-Coder-7B)
- **Code-specialized** for Python, Go, Rust
- Implements backend services and APIs
- Handles complex business logic
- Fast generation (~60-80 tokens/sec)

### Worker Frontend (Qwen2.5-Coder-3B)
- **Optimized for UI frameworks** (React, Vue)
- Lightweight and fast (~100+ tokens/sec)
- Handles HTML/CSS/JavaScript
- Responsive design patterns

### QA Sentinel (DeepSeek-R1-1.5B)
- **Verification-focused** reasoning model
- Finds bugs and edge cases
- Generates test cases
- Low temperature for strict checking

### Consensus Judge (Phi-4-Mini)
- **Logic and reasoning** specialist
- Objective candidate evaluation
- Scores on multiple criteria
- Explains decisions clearly

## Performance Characteristics

### Throughput
- **Single Active Agent**: ~80-100 tokens/sec
- **Dual Active Agents**: ~30-40 tokens/sec each
- **Orchestration Latency**: <0.5 seconds

### Parallelism
- **Max Parallel Tasks**: 4 (configurable)
- **Memory Bandwidth Split**: Dynamic
- **VRAM Allocation**: Static per agent

### Latency
- **Model Switching**: <100ms (all resident in VRAM)
- **Memory Retrieval**: <50ms (ChromaDB)
- **Checkpoint Save**: ~200ms
- **State Bus Publish**: <10ms

## Cost Analysis

### Traditional Cloud (e.g., Claude Code)
- **Monthly API**: $9,000 - $12,000 for heavy usage
- **Per Token**: $15 / 1M tokens
- **Limitations**: Rate limits, privacy concerns

### Local Hydra-Consensus
- **Hardware**: $3,000 one-time (RTX 4090 + workstation)
- **Electricity**: ~$50/month (24/7 operation)
- **Per Token**: $0 marginal cost
- **ROI**: <2 weeks of heavy usage

## Scalability

### Current (Single RTX 4090)
- 5 agents
- ~24GB VRAM
- 3-4 parallel tasks

### Future (Dual RTX 5090)
- 10 agents
- ~64GB VRAM
- 8-10 parallel tasks
- Can run 30B+ models

## Security & Privacy

### Air-Gapped Capable
- All processing on-device
- No cloud API calls required
- Complete data sovereignty

### Sandboxed Execution
- Docker isolation
- Resource limits
- Network restrictions
- Temporary filesystems

## File Structure

```
SLMSwarm/
├── src/
│   ├── core/              # Configuration, models, registry
│   ├── extensions/        # Consensus, hydration, routing
│   ├── tools/             # Web search, scraping, docs
│   ├── memory/            # ChromaDB, patterns, knowledge
│   ├── orchestration/     # Control plane, dispatcher
│   └── hydra_control.py   # Main entry point
├── docker-compose.yml     # All 8 services
├── requirements.txt       # Python dependencies
├── models/                # GGUF models (90GB)
├── specs/                 # Project specifications
├── memory/                # ChromaDB data
├── .hydra/                # State, checkpoints, messages
└── docs/                  # Documentation
```

## Technology Stack

### Core
- **Python 3.12** with async/await
- **FastAPI** for REST API
- **Pydantic** for data validation
- **Loguru** for logging

### AI/ML
- **llama.cpp** for model serving
- **ChromaDB** for vector storage
- **sentence-transformers** for embeddings

### Orchestration
- **LangGraph** (planned for Phase 5)
- **Docker** for sandboxing
- **Redis** for caching

### Web
- **Searxng** for search
- **httpx** for HTTP client
- **Playwright** (optional) for browser automation

## Extension Points

### Adding New Agents
1. Add model to `docker-compose.yml`
2. Register in `src/core/agent_registry.py`
3. Add to `AgentRole` enum
4. Update VRAM budget

### Custom Tools
1. Create tool in `src/tools/`
2. Register in `__init__.py`
3. Agents can auto-discover via tool registry

### Custom Memory Collections
1. Add collection in `PersistentMemory.__init__()`
2. Create specialized store/recall methods
3. Update knowledge base seeder

## Future Enhancements (Phase 5)

- WebSocket monitoring dashboard
- Performance benchmarking suite
- Integration test framework
- Evolutionary code refinement
- LangGraph state machine
- Multi-GPU support
- Advanced RAG for massive codebases

## References

Based on research from:
- "Building a Parallel SLM Agent Swarm" (2026)
- "Autonomous Coding SLM Swarm Design" (2026)
- "Local Claude Code Tasks" (2026)
- "Building a Local