#!/bin/bash
# ============================================================
# Rabbit v2.0 — Data Generation on RunPod CPU
#
# Run this on TWO RunPod CPU pods:
#   Pod 1: bash runpod_generate.sh 1
#   Pod 2: bash runpod_generate.sh 2
#
# Pod spec: CPU only, 8 vCPU, 16GB RAM, ~$0.19/hr
# ============================================================

set -e

PART=${1:-1}
OPENAI_KEY=${OPENAI_API_KEY:-""}

if [ -z "$OPENAI_KEY" ]; then
    echo "ERROR: Set OPENAI_API_KEY first"
    echo "  export OPENAI_API_KEY=sk-proj-YOUR_KEY"
    exit 1
fi

echo "=========================================="
echo "  Rabbit v2.0 Data Generation"
echo "  Part: $PART of 2"
echo "=========================================="

# Step 1: Clone repo
echo ""
echo "[1/4] Cloning repo..."
cd /workspace
if [ -d "rabbit" ]; then
    cd rabbit && git pull
else
    git clone https://github.com/parthajy/rabbit.git
    cd rabbit
fi

# Step 2: Install deps
echo ""
echo "[2/4] Installing dependencies..."
pip install -q openai

# Step 3: Generate
echo ""
echo "[3/4] Generating examples (part $PART)..."
echo "  This will take 6-8 hours."
echo "  Progress is printed every 50 examples."
echo ""

export OPENAI_API_KEY=$OPENAI_KEY
python3 scripts/generate_v2_data.py --part $PART 2>&1 | tee /workspace/generate_part${PART}.log

# Step 4: Show results
echo ""
echo "[4/4] Results:"
wc -l data/synthetic/v2_*.jsonl 2>/dev/null
echo ""
echo "Files saved in data/synthetic/"
echo "Download them and add to your training data."
echo "=========================================="
