#!/bin/bash
# Runs INSIDE the bake VM, sets everything up so future VMs boot directly to a
# working Rabbit server. Invoked from 00_bake_disk.sh via `gcloud compute ssh`.
set -euo pipefail

echo "===> [install.sh] starting"

# ------------------------------------------------------------
# Read bake-time metadata (HF token + Rabbit API token)
# ------------------------------------------------------------
MD="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
HF_TOKEN=$(curl -sf -H "Metadata-Flavor: Google" "$MD/HF_TOKEN" || echo "")
RABBIT_TOKEN=$(curl -sf -H "Metadata-Flavor: Google" "$MD/RABBIT_TOKEN" || echo "")

if [ -z "$HF_TOKEN" ]; then
    echo "ERROR: HF_TOKEN missing from instance metadata — cannot download Rabbit model"
    exit 1
fi
if [ -z "$RABBIT_TOKEN" ]; then
    echo "ERROR: RABBIT_TOKEN missing from instance metadata"
    exit 1
fi

# ------------------------------------------------------------
# System packages
# ------------------------------------------------------------
echo "===> [install.sh] apt packages"
apt-get update -qq
apt-get install -y -qq python3-venv python3-pip git curl

# ------------------------------------------------------------
# Rabbit user + directories
# ------------------------------------------------------------
echo "===> [install.sh] creating rabbit user and dirs"
id -u rabbit &>/dev/null || useradd -r -m -d /opt/rabbit -s /bin/bash rabbit
mkdir -p /opt/rabbit /var/lib/rabbit /var/log/rabbit /opt/rabbit/hfcache
chown -R rabbit:rabbit /opt/rabbit /var/lib/rabbit /var/log/rabbit

# ------------------------------------------------------------
# Save the Rabbit API token (both developers use this)
# ------------------------------------------------------------
echo "$RABBIT_TOKEN" > /opt/rabbit/token
chown rabbit:rabbit /opt/rabbit/token
chmod 600 /opt/rabbit/token

# ------------------------------------------------------------
# Python venv + deps
# ------------------------------------------------------------
echo "===> [install.sh] creating venv"
sudo -u rabbit python3 -m venv /opt/rabbit/venv
sudo -u rabbit /opt/rabbit/venv/bin/pip install --upgrade pip wheel

echo "===> [install.sh] installing Python requirements (~3-5 min)"
cp /tmp/requirements.txt /opt/rabbit/requirements.txt
chown rabbit:rabbit /opt/rabbit/requirements.txt
sudo -u rabbit /opt/rabbit/venv/bin/pip install -r /opt/rabbit/requirements.txt

# ------------------------------------------------------------
# Rabbit server code
# ------------------------------------------------------------
cp /tmp/rabbit_server.py /opt/rabbit/rabbit_server.py
chown rabbit:rabbit /opt/rabbit/rabbit_server.py

# ------------------------------------------------------------
# Pre-download Qwen 32B (4-bit) + Rabbit v2.0 LoRA
# This is the reason the bake takes ~10-15 min
# ------------------------------------------------------------
echo "===> [install.sh] pre-downloading model (~15 min, ~21 GB)"
sudo -u rabbit HF_TOKEN="$HF_TOKEN" HF_HOME=/opt/rabbit/hfcache HF_HUB_ENABLE_HF_TRANSFER=1 \
    /opt/rabbit/venv/bin/python - <<'PY'
import os
from huggingface_hub import snapshot_download
tok = os.environ["HF_TOKEN"]
print(">>> Downloading reattend/rabbit-v2.0 (LoRA adapter ~1.1 GB)...")
snapshot_download("reattend/rabbit-v2.0", token=tok)
print(">>> Downloading unsloth/Qwen2.5-32B-Instruct-bnb-4bit (~20 GB)...")
snapshot_download("unsloth/Qwen2.5-32B-Instruct-bnb-4bit")
print(">>> Done.")
PY

# ------------------------------------------------------------
# Persist HF token to rabbit user's cache so systemd + CLI can read it
# ------------------------------------------------------------
sudo -u rabbit mkdir -p /opt/rabbit/hfcache /opt/rabbit/.cache/huggingface
echo "$HF_TOKEN" | sudo -u rabbit tee /opt/rabbit/.cache/huggingface/token >/dev/null
chmod 600 /opt/rabbit/.cache/huggingface/token

# Pre-create unsloth compile cache dir so the smoke test doesn't warn
sudo -u rabbit mkdir -p /opt/rabbit/unsloth_compiled_cache

# ------------------------------------------------------------
# Smoke test: can Unsloth actually load Rabbit?
# ------------------------------------------------------------
echo "===> [install.sh] smoke-testing model load (this will hit the GPU)"
sudo -u rabbit \
    HF_TOKEN="$HF_TOKEN" \
    HUGGING_FACE_HUB_TOKEN="$HF_TOKEN" \
    HF_HUB_TOKEN="$HF_TOKEN" \
    HF_HOME=/opt/rabbit/hfcache \
    HOME=/opt/rabbit \
    /opt/rabbit/venv/bin/python - <<'PY'
import os, time
t0 = time.time()
from unsloth import FastLanguageModel

# Explicit token — PEFT/HF cascade sometimes ignores env vars for fallback lookups
tok_env = os.environ.get("HF_TOKEN", "")

model, tok = FastLanguageModel.from_pretrained(
    "reattend/rabbit-v2.0",
    max_seq_length=2048,
    dtype=None,
    load_in_4bit=True,
    token=tok_env,
)
FastLanguageModel.for_inference(model)
msgs = [
    {"role": "system", "content": "You are Rabbit. Reply with OK."},
    {"role": "user", "content": "ping"},
]
ids = tok.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True, return_tensors="pt").to("cuda")
out = model.generate(input_ids=ids, max_new_tokens=8, use_cache=True)
print(">>> SMOKE OK — response:", tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True))
print(f">>> Load+gen took {time.time()-t0:.1f}s")
PY

# ------------------------------------------------------------
# Systemd units
# ------------------------------------------------------------
echo "===> [install.sh] installing systemd units"
cp /tmp/systemd/rabbit.service /etc/systemd/system/rabbit.service
cp /tmp/systemd/auto-stop.service /etc/systemd/system/auto-stop.service
cp /tmp/systemd/auto-stop.timer /etc/systemd/system/auto-stop.timer

cp /tmp/auto_stop.sh /opt/rabbit/auto_stop.sh
chown rabbit:rabbit /opt/rabbit/auto_stop.sh
chmod +x /opt/rabbit/auto_stop.sh

systemctl daemon-reload
systemctl enable rabbit.service
systemctl enable auto-stop.timer

echo "===> [install.sh] DONE"
