#!/bin/bash
# ============================================================
# Rabbit Server — Google Cloud Setup Script
# Run this on your GCP VM after SSH'ing in.
# ============================================================

set -e

echo "=========================================="
echo "  Rabbit Server Setup"
echo "=========================================="

# ── Step 1: Install NVIDIA drivers ──
echo ""
echo "[1/5] Installing NVIDIA drivers..."
if ! nvidia-smi &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y linux-headers-$(uname -r)
    sudo apt-get install -y nvidia-driver-535
    echo "NVIDIA drivers installed. REBOOT REQUIRED."
    echo "Run: sudo reboot"
    echo "Then re-run this script."
    exit 0
fi
echo "NVIDIA drivers OK: $(nvidia-smi --query-gpu=name --format=csv,noheader)"

# ── Step 2: Install CUDA toolkit ──
echo ""
echo "[2/5] Installing CUDA..."
if ! nvcc --version &> /dev/null; then
    wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
    sudo dpkg -i cuda-keyring_1.1-1_all.deb
    sudo apt-get update
    sudo apt-get install -y cuda-toolkit-12-4
    export PATH=/usr/local/cuda/bin:$PATH
    echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
fi
echo "CUDA OK"

# ── Step 3: Install Python dependencies ──
echo ""
echo "[3/5] Installing Python dependencies..."
sudo apt-get install -y python3-pip python3-venv
python3 -m venv /opt/rabbit-env
source /opt/rabbit-env/bin/activate
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install -r /opt/rabbit/server/requirements.txt

# ── Step 4: Clone repo ──
echo ""
echo "[4/5] Setting up Rabbit..."
sudo mkdir -p /opt/rabbit
sudo chown $USER:$USER /opt/rabbit
cd /opt/rabbit
git clone https://github.com/parthajy/rabbit.git . 2>/dev/null || git pull

# ── Step 5: Create systemd service ──
echo ""
echo "[5/5] Creating systemd service..."
sudo tee /etc/systemd/system/rabbit.service > /dev/null << EOF
[Unit]
Description=Rabbit API Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/rabbit
Environment="PATH=/opt/rabbit-env/bin:/usr/local/cuda/bin:/usr/bin"
Environment="HF_TOKEN=${HF_TOKEN}"
Environment="RABBIT_API_KEY=${RABBIT_API_KEY}"
Environment="RABBIT_REPO=reattend/rabbit-v1.2"
ExecStart=/opt/rabbit-env/bin/python server/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable rabbit
sudo systemctl start rabbit

echo ""
echo "=========================================="
echo "  Rabbit Server is running!"
echo "  URL: http://$(curl -s ifconfig.me):8000"
echo "  Health: curl http://localhost:8000/health"
echo "=========================================="
