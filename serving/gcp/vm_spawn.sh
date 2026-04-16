#!/bin/bash
# rabbit wake — create or start the Rabbit Spot VM from the baked image.
# Idempotent: if VM already running, prints URL; if stopped, starts it; if
# missing, creates from image. Either way ends with a healthy /health check.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

gcloud config set project "$PROJECT_ID" >/dev/null

# ------------------------------------------------------------
# 1. Reserve static IP if missing
# ------------------------------------------------------------
if ! gcloud compute addresses describe "$STATIC_IP_NAME" --region="$REGION" >/dev/null 2>&1; then
    echo "===> Reserving static IP $STATIC_IP_NAME..."
    gcloud compute addresses create "$STATIC_IP_NAME" --region="$REGION"
fi
STATIC_IP=$(gcloud compute addresses describe "$STATIC_IP_NAME" --region="$REGION" --format="value(address)")
echo "===> Static IP: $STATIC_IP"

# ------------------------------------------------------------
# 2. Firewall rule for :8000 if missing
# ------------------------------------------------------------
if ! gcloud compute firewall-rules describe "$FIREWALL_RULE" >/dev/null 2>&1; then
    echo "===> Creating firewall rule $FIREWALL_RULE..."
    gcloud compute firewall-rules create "$FIREWALL_RULE" \
        --allow="tcp:$RABBIT_PORT" \
        --target-tags="$NETWORK_TAG" \
        --description="Rabbit API"
fi

# ------------------------------------------------------------
# 3. If VM already exists, handle it
# ------------------------------------------------------------
wait_for_health() {
    local url="http://$STATIC_IP:$RABBIT_PORT/health"
    echo "===> Waiting for $url ..."
    for i in $(seq 1 40); do
        if curl -sf "$url" >/dev/null 2>&1; then
            echo "===> Rabbit is LIVE at http://$STATIC_IP:$RABBIT_PORT"
            curl -sf "$url"
            echo
            return 0
        fi
        printf '   ...not ready yet (%d/40)\r' "$i"
        sleep 6
    done
    echo
    echo "===> TIMEOUT waiting for health"
    echo "     Debug: rabbit ssh → sudo journalctl -u rabbit -n 100"
    return 1
}

if gcloud compute instances describe "$VM_NAME" --zone="$ZONE" >/dev/null 2>&1; then
    STATE=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --format="value(status)")
    echo "===> VM $VM_NAME exists (status: $STATE)"
    case "$STATE" in
        RUNNING)
            wait_for_health
            exit 0
            ;;
        TERMINATED|STOPPING)
            echo "===> Starting VM..."
            gcloud compute instances start "$VM_NAME" --zone="$ZONE"
            wait_for_health
            exit 0
            ;;
        *)
            echo "===> Unexpected state $STATE — aborting. Fix manually."
            exit 1
            ;;
    esac
fi

# ------------------------------------------------------------
# 4. Create fresh Spot VM from baked image
# ------------------------------------------------------------
echo "===> Creating Spot VM $VM_NAME from image family $IMAGE_FAMILY..."
gcloud compute instances create "$VM_NAME" \
    --zone="$ZONE" \
    --machine-type="$MACHINE_TYPE" \
    --accelerator="$ACCELERATOR" \
    --image-family="$IMAGE_FAMILY" \
    --image-project="$PROJECT_ID" \
    --boot-disk-size="$DISK_SIZE" \
    --boot-disk-type="$DISK_TYPE" \
    --maintenance-policy=TERMINATE \
    --provisioning-model=SPOT \
    --instance-termination-action=STOP \
    --restart-on-failure \
    --address="$STATIC_IP" \
    --tags="$NETWORK_TAG"

# Disable auto-stop (we want always-on) and ensure correct server entrypoint
echo "===> Disabling auto-stop, updating rabbit.service..."
sleep 30  # wait for SSH to be ready
gcloud compute ssh "$VM_NAME" --zone="$ZONE" --command="
  sudo systemctl disable auto-stop.timer 2>/dev/null || true
  sudo systemctl stop auto-stop.timer 2>/dev/null || true
  sudo sed -i 's|rabbit_server:app|rabbit.api.server:app|' /etc/systemd/system/rabbit.service
  sudo sed -i 's|Restart=on-failure|Restart=always|' /etc/systemd/system/rabbit.service
  sudo systemctl daemon-reload
  sudo systemctl restart rabbit
" 2>/dev/null || true

wait_for_health
