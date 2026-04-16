#!/bin/bash
# Runs every 5 minutes via systemd timer.
# If no request for >20 min, shut down the VM (preserves boot disk, stops billing).
set -euo pipefail

LAST_REQUEST_FILE="/var/lib/rabbit/last_request"
IDLE_MAX=1200  # seconds (20 min)

# Bootstrap: if no request yet since boot, use the server.log mtime as "last seen"
if [ ! -f "$LAST_REQUEST_FILE" ]; then
    if [ -f /var/log/rabbit/server.log ]; then
        BOOT=$(stat -c %Y /var/log/rabbit/server.log)
    else
        BOOT=$(date +%s)
    fi
    echo "$BOOT" > "$LAST_REQUEST_FILE"
fi

LAST=$(cat "$LAST_REQUEST_FILE")
NOW=$(date +%s)
IDLE=$((NOW - LAST))

logger -t rabbit-auto-stop "idle=${IDLE}s threshold=${IDLE_MAX}s"

if [ "$IDLE" -gt "$IDLE_MAX" ]; then
    logger -t rabbit-auto-stop "idle exceeded — shutting down"
    shutdown -h now
fi
