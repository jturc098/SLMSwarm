# Alternative Judge Models for Consensus

## Problem
Phi-4 needs 7.7GB, too large for our VRAM budget.

## Recommended Alternatives

### Option 1: Reuse DeepSeek-R1-1.5B (✅ Already Downloaded!)
**Best option** - we already have this for QA!

**Specs:**
- Size: ~1.4GB
- Reasoning: Excellent (R1 distilled)
- VRAM: Minimal
- File: `DeepSeek-R1-Distill-Qwen-1.5B-Q6_K.gguf`

**Use both QA and Judge with same model:**
```yaml
qa-sentinel:
  command: -m /models/DeepSeek-R1-Distill-Qwen-1.5B-Q6_K.gguf ...

consensus-judge:
  command: -m /models/DeepSeek-R1-Distill-Qwen-1.5B-Q6_K.gguf ...
```

### Option 2: Qwen2.5-1.5B-Instruct
**Download command:**
```bash
hf download Qwen/Qwen2.5-1.5B-Instruct-GGUF qwen2.5-1.5b-instruct-q4_k_m.gguf --local-dir ./models
```

**Specs:**
- Size: ~1.0GB
- Good reasoning
- Fast inference

### Option 3: Llama-3.2-1B-Instruct
**Download:**
```bash
hf download hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF llama-3.2-1b-instruct-q4_k_m.gguf --local-dir ./models
```

**Specs:**
- Size: ~0.7GB
- Meta's latest tiny model
- Good instruction following

---

## Recommended: Use DeepSeek-R1-1.5B for Both

**Advantages:**
- Already downloaded!
- Excellent reasoning capability
- Proven in testing
- Tiny VRAM footprint

Just point consensus-judge to same model as QA.

---

## Updated VRAM Budget

With DeepSeek-1.5B as judge:

```
Architect:      8.1GB + 0.8GB = 8.9GB
Worker Backend: 4.5GB + 0.8GB = 5.3GB
Worker Frontend:2.0GB + 0.4GB = 2.4GB
QA Sentinel:    1.4GB + 0.4GB = 1.8GB
Judge:          1.4GB + 0.4GB = 1.8GB (same model as QA)
───────────────────────────────────────
Total:                         20.2GB ✅
```

**Buffer: 3.8GB - Perfect fit!**

---

## Quick Fix

Change docker-compose.yml consensus-judge section:
```yaml
consensus-judge:
  command: >
    -m /models/DeepSeek-R1-Distill-Qwen-1.5B-Q6_K.gguf
    --ctx-size 4096
    ...
```

That's it! No new downloads needed.