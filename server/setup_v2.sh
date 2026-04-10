#!/bin/bash
# ============================================================
# Rabbit Platform — GCP L4 Server Setup
# Run this on your new GCP VM after SSH'ing in.
#
# This sets up the full Rabbit platform:
#   - NVIDIA drivers + CUDA
#   - Python 3.11 + venv
#   - Rabbit package (rabbit/api/server.py)
#   - Qdrant for vector storage
#   - systemd service with auto-restart
# ============================================================

set -e

echo "=========================================="
echo "  Rabbit Platform Setup (v2)"
echo "=========================================="

# ── Step 1: System deps ──
echo ""
echo "[1/7] System dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq build-essential python3.11 python3.11-venv python3.11-dev git curl wget

# ── Step 2: NVIDIA drivers ──
echo ""
echo "[2/7] NVIDIA drivers..."
if ! nvidia-smi &> /dev/null; then
    sudo apt-get install -y -qq linux-headers-$(uname -r)
    sudo apt-get install -y -qq nvidia-driver-535
    echo ""
    echo ">>> NVIDIA drivers installed. REBOOT REQUIRED. <<<"
    echo ">>> Run: sudo reboot"
    echo ">>> Then re-run this script."
    exit 0
fi
echo "GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"

# ── Step 3: CUDA ──
echo ""
echo "[3/7] CUDA toolkit..."
if ! nvcc --version &> /dev/null; then
    wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
    sudo dpkg -i cuda-keyring_1.1-1_all.deb
    sudo apt-get update -qq
    sudo apt-get install -y -qq cuda-toolkit-12-4
    export PATH=/usr/local/cuda/bin:$PATH
    echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
fi
echo "CUDA OK"

# ── Step 4: Python venv ──
echo ""
echo "[4/7] Python environment..."
sudo mkdir -p /opt/rabbit
sudo chown $USER:$USER /opt/rabbit
python3.11 -m venv /opt/rabbit-env
source /opt/rabbit-env/bin/activate
pip install --upgrade pip -q

# ── Step 5: Install Rabbit ──
echo ""
echo "[5/7] Installing Rabbit platform..."
cd /opt/rabbit
git clone https://github.com/parthajy/rabbit.git . 2>/dev/null || git pull

# Install PyTorch with CUDA
pip install torch --index-url https://download.pytorch.org/whl/cu124 -q

# Install Rabbit with all server dependencies
pip install -e ".[server]" -q

# Install additional processors
pip install faster-whisper -q       # Audio transcription
pip install qdrant-client -q        # Vector storage

echo "Rabbit installed: $(pip show rabbit-memory 2>/dev/null | grep Version || echo 'dev')"

# ── Step 6: Create data directories ──
echo ""
echo "[6/7] Setting up storage..."
mkdir -p /opt/rabbit-data/qdrant
mkdir -p /opt/rabbit-data/keys

# ── Step 7: Systemd service ──
echo ""
echo "[7/7] Creating systemd service..."

# Source the .env file if it exists
HF_TOKEN="${HF_TOKEN:-}"
if [ -f /opt/rabbit/.env ]; then
    export $(grep -v '^#' /opt/rabbit/.env | xargs)
fi

sudo tee /etc/systemd/system/rabbit.service > /dev/null << EOF
[Unit]
Description=Rabbit API Platform
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/rabbit
Environment="PATH=/opt/rabbit-env/bin:/usr/local/cuda/bin:/usr/bin"
Environment="HF_TOKEN=${HF_TOKEN}"
Environment="RABBIT_MODEL=reattend/rabbit-v1.4-merged"
Environment="RABBIT_STORAGE=/opt/rabbit-data"
Environment="RABBIT_KEYS_DB=/opt/rabbit-data/keys/keys.db"
Environment="HOST=0.0.0.0"
Environment="PORT=8000"
ExecStart=/opt/rabbit-env/bin/uvicorn rabbit.api.server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable rabbit
sudo systemctl start rabbit

# Wait for startup
echo ""
echo "Waiting for model to load (this takes 2-3 minutes)..."
for i in {1..60}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        break
    fi
    sleep 5
    echo "  ...loading ($((i*5))s)"
done

echo ""
echo "=========================================="
echo "  Rabbit Platform is running!"
echo "=========================================="
echo ""
echo "  URL:    http://$(curl -s ifconfig.me):8000"
echo "  Health: curl http://localhost:8000/health"
echo ""
echo "  Generate your first API key:"
echo "    curl -X POST http://localhost:8000/v1/keys/generate?tier=test"
echo ""
echo "  Test it:"
echo '    KEY="rab_test_YOUR_KEY"'
echo '    curl -X POST http://localhost:8000/v1/remember \'
echo '      -H "Authorization: Bearer $KEY" \'
echo '      -H "Content-Type: application/json" \'
echo '      -d '"'"'{"content": "Sarah delayed launch to March 15. Budget is $50K.", "source": "meeting"}'"'"
echo ""
echo "  Logs: sudo journalctl -u rabbit -f"
echo "=========================================="
