#!/bin/bash
# rabbit status — quick VM state + IP + health + last request time
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

gcloud config set project "$PROJECT_ID" >/dev/null

if ! gcloud compute instances describe "$VM_NAME" --zone="$ZONE" >/dev/null 2>&1; then
    echo "VM:        NOT CREATED"
    echo "Next step: rabbit wake"
    exit 0
fi

STATE=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --format="value(status)")
echo "VM:        $STATE"

if gcloud compute addresses describe "$STATIC_IP_NAME" --region="$REGION" >/dev/null 2>&1; then
    IP=$(gcloud compute addresses describe "$STATIC_IP_NAME" --region="$REGION" --format="value(address)")
    echo "Static IP: $IP"
fi

if [ "$STATE" = "RUNNING" ]; then
    echo -n "Health:    "
    if curl -sf "http://$IP:$RABBIT_PORT/health" 2>/dev/null; then
        echo
    else
        echo "UNREACHABLE (VM up but server not ready)"
    fi
    echo
    echo "Last request (from VM):"
    gcloud compute ssh "$VM_NAME" --zone="$ZONE" --command="
        if [ -f /var/lib/rabbit/last_request ]; then
            TS=\$(cat /var/lib/rabbit/last_request)
            NOW=\$(date +%s)
            echo '  timestamp: '\$(date -d @\$TS 2>/dev/null || date -r \$TS)
            echo '  idle:      '\$((NOW - TS))'s'
        else
            echo '  no requests since boot'
        fi
    " 2>/dev/null || echo "  (ssh failed)"
fi
