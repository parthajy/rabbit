#!/bin/bash
# One-time: create a GCP image with Rabbit v2.0 pre-installed.
# Future VMs boot directly to a working Rabbit server in ~90s.
#
# Expected runtime: ~20 min.  Expected cost: ~$1-2 (temporary L4 Spot during bake).
#
# Usage:
#   export HF_TOKEN=hf_xxx
#   bash 00_bake_disk.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVING_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/config.sh"

# ------------------------------------------------------------
# Preflight
# ------------------------------------------------------------
if [ -z "${HF_TOKEN:-}" ]; then
    echo "ERROR: set HF_TOKEN before running (export HF_TOKEN=hf_xxx)"
    exit 1
fi

gcloud config set project "$PROJECT_ID" >/dev/null

# Use a temp VM name to avoid colliding with the main VM
TEMP_VM="rabbit-bake-$(date +%s)"

# Generate the API token that both you and your friend will use
RABBIT_TOKEN=$(openssl rand -hex 32)
echo "$RABBIT_TOKEN" > "$HOME/.rabbit_token"
chmod 600 "$HOME/.rabbit_token"

echo "=================================================="
echo "  Rabbit v2.0 Disk Bake"
echo "=================================================="
echo "  Project:     $PROJECT_ID"
echo "  Zone:        $ZONE"
echo "  Temp VM:     $TEMP_VM"
echo "  Machine:     $MACHINE_TYPE + $ACCELERATOR"
echo "  Base image:  $BASE_IMAGE_FAMILY"
echo "  Rabbit token saved to: ~/.rabbit_token"
echo "=================================================="

# ------------------------------------------------------------
# Create bake VM (Spot L4 — cheapest)
# ------------------------------------------------------------
echo "===> Creating bake VM..."
gcloud compute instances create "$TEMP_VM" \
    --zone="$ZONE" \
    --machine-type="$MACHINE_TYPE" \
    --accelerator="$ACCELERATOR" \
    --image-family="$BASE_IMAGE_FAMILY" \
    --image-project="$BASE_IMAGE_PROJECT" \
    --boot-disk-size="$DISK_SIZE" \
    --boot-disk-type="$DISK_TYPE" \
    --maintenance-policy=TERMINATE \
    --provisioning-model=SPOT \
    --instance-termination-action=STOP \
    --metadata="install-nvidia-driver=True,HF_TOKEN=$HF_TOKEN,RABBIT_TOKEN=$RABBIT_TOKEN" \
    --tags="$NETWORK_TAG"

# ------------------------------------------------------------
# Wait for nvidia driver install + SSH readiness
# ------------------------------------------------------------
echo "===> Waiting for VM to boot + drivers (~2-3 min)..."
sleep 90
for i in $(seq 1 30); do
    if gcloud compute ssh "$TEMP_VM" --zone="$ZONE" --command="echo ssh_ok && nvidia-smi -L" 2>/dev/null; then
        echo "===> SSH + GPU ready"
        break
    fi
    echo "   ...not ready yet ($i/30)"
    sleep 15
done

# ------------------------------------------------------------
# Upload install payload
# ------------------------------------------------------------
echo "===> Uploading install payload..."
gcloud compute scp "$SERVING_DIR/scripts/install.sh" "$TEMP_VM:/tmp/install.sh" --zone="$ZONE"
gcloud compute scp "$SERVING_DIR/scripts/auto_stop.sh" "$TEMP_VM:/tmp/auto_stop.sh" --zone="$ZONE"
gcloud compute scp "$SERVING_DIR/rabbit_server.py" "$TEMP_VM:/tmp/rabbit_server.py" --zone="$ZONE"
gcloud compute scp "$SERVING_DIR/requirements.txt" "$TEMP_VM:/tmp/requirements.txt" --zone="$ZONE"
gcloud compute scp --recurse "$SERVING_DIR/systemd" "$TEMP_VM:/tmp/" --zone="$ZONE"

# ------------------------------------------------------------
# Run install.sh inside the VM
# ------------------------------------------------------------
echo "===> Running install.sh (pip install + model download, ~15 min)..."
gcloud compute ssh "$TEMP_VM" --zone="$ZONE" --command="sudo bash /tmp/install.sh 2>&1"

# ------------------------------------------------------------
# Start the service once to verify it comes up
# ------------------------------------------------------------
echo "===> Starting rabbit.service to verify..."
gcloud compute ssh "$TEMP_VM" --zone="$ZONE" --command="sudo systemctl start rabbit && sleep 30 && curl -sf http://localhost:8000/health && echo"

echo "===> Stopping rabbit.service before image capture..."
gcloud compute ssh "$TEMP_VM" --zone="$ZONE" --command="sudo systemctl stop rabbit || true"

# ------------------------------------------------------------
# Stop VM → create image → delete VM
# ------------------------------------------------------------
echo "===> Stopping bake VM..."
gcloud compute instances stop "$TEMP_VM" --zone="$ZONE"

IMAGE_NAME="${IMAGE_NAME_PREFIX}-$(date +%Y%m%d-%H%M)"
echo "===> Creating image: $IMAGE_NAME (family: $IMAGE_FAMILY)..."
gcloud compute images create "$IMAGE_NAME" \
    --source-disk="$TEMP_VM" \
    --source-disk-zone="$ZONE" \
    --family="$IMAGE_FAMILY"

echo "===> Deleting bake VM..."
gcloud compute instances delete "$TEMP_VM" --zone="$ZONE" --quiet

# ------------------------------------------------------------
# Done
# ------------------------------------------------------------
cat <<EOF

==========================================================
  BAKE COMPLETE
==========================================================
  Image family:    $IMAGE_FAMILY
  Latest image:    $IMAGE_NAME
  Rabbit API token (shared with friend):
    $RABBIT_TOKEN
  (also saved to ~/.rabbit_token, chmod 600)

  Next step:
    rabbit wake
    rabbit health
    rabbit extract "Tom said we'd ship v2 by May 15"
==========================================================
EOF
