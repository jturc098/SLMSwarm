#!/bin/bash

# ============================================================================
# Project Hydra-Consensus - Model Download Script
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Model directory
MODEL_DIR="./models"
mkdir -p "$MODEL_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Project Hydra-Consensus Model Downloader${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if hf is installed
if ! command -v hf &> /dev/null; then
    echo -e "${YELLOW}Installing huggingface-hub CLI...${NC}"
    pip install -U "huggingface_hub[cli,hf_transfer]"
fi

# Model definitions
declare -A MODELS=(
    ["architect"]="unsloth/deepseek-r1-distill-qwen-14B-GGUF:DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf"
    ["worker_backend"]="Qwen/Qwen2.5-Coder-7B-Instruct-GGUF:qwen2.5-coder-7b-instruct-q4_k_m.gguf"
    ["worker_frontend"]="Qwen/Qwen2.5-Coder-3B-Instruct-GGUF:qwen2.5-coder-3b-instruct-q4_k_m.gguf"
    ["qa_sentinel"]="unsloth/deepseek-r1-distill-qwen-1.5B-GGUF:DeepSeek-R1-Distill-Qwen-1.5B-Q6_K.gguf"
    ["consensus_judge"]="microsoft/Phi-4-GGUF:phi-4-Q4_0.gguf"
)

download_model() {
    local role=$1
    local model_info=${MODELS[$role]}
    local repo=$(echo $model_info | cut -d: -f1)
    local filename=$(echo $model_info | cut -d: -f2)
    local output_path="$MODEL_DIR/$filename"

    if [ -f "$output_path" ]; then
        echo -e "${YELLOW}✓ $role model already exists: $filename${NC}"
        return 0
    fi

    echo -e "${GREEN}Downloading $role model...${NC}"
    echo -e "${YELLOW}  Repository: $repo${NC}"
    echo -e "${YELLOW}  File: $filename${NC}"
    
    hf download "$repo" "$filename" \
        --local-dir "$MODEL_DIR"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully downloaded $filename${NC}"
    else
        echo -e "${RED}✗ Failed to download $filename${NC}"
        return 1
    fi
    echo ""
}

# Download all models
echo -e "${GREEN}Starting model downloads...${NC}"
echo ""

for role in "${!MODELS[@]}"; do
    download_model "$role"
done

# Display summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Download Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

total_size=0
for file in "$MODEL_DIR"/*.gguf; do
    if [ -f "$file" ]; then
        size=$(du -h "$file" | cut -f1)
        filename=$(basename "$file")
        echo -e "${GREEN}✓${NC} $filename ($size)"
        # Add to total (requires bc for decimal math)
        size_mb=$(du -m "$file" | cut -f1)
        total_size=$((total_size + size_mb))
    fi
done

echo ""
echo -e "${GREEN}Total Size: $(echo "scale=2; $total_size / 1024" | bc) GB${NC}"
echo ""

# Verify VRAM requirements
expected_vram=23.6
echo -e "${YELLOW}Expected VRAM Usage: ~${expected_vram}GB${NC}"
echo -e "${YELLOW}Ensure your RTX 4090 has sufficient VRAM${NC}"
echo ""

# Check GPU
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}GPU Information:${NC}"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    echo ""
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Copy .env.example to .env and configure"
echo -e "2. Run: docker-compose up -d"
echo -e "3. Initialize: python src/hydra_control.py --init"
echo ""