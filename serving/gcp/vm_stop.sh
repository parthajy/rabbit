#!/bin/bash
# rabbit stop — stop the Rabbit VM (preserves boot disk, kills compute billing)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

gcloud config set project "$PROJECT_ID" >/dev/null

if ! gcloud compute instances describe "$VM_NAME" --zone="$ZONE" >/dev/null 2>&1; then
    echo "===> VM $VM_NAME does not exist — nothing to stop"
    exit 0
fi

STATE=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --format="value(status)")
if [ "$STATE" = "TERMINATED" ]; then
    echo "===> VM $VM_NAME already stopped"
    exit 0
fi

echo "===> Stopping $VM_NAME ..."
gcloud compute instances stop "$VM_NAME" --zone="$ZONE"
echo "===> Stopped. Boot disk preserved. Static IP preserved."
echo "     rabbit wake  → bring it back in ~90s"
