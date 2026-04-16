# Rabbit Server — Start / Stop / Reconnect

Everything you need to bring Rabbit back online after terminating the RunPod pod.

---

## 1. Start a new RunPod pod

1. Go to [runpod.io/console/pods](https://www.runpod.io/console/pods)
2. Click **Deploy** → pick **A40 48GB**
   - **Community Cloud**: ~$0.38/hr (cheaper, can be preempted)
   - **Secure Cloud**: ~$0.76/hr (dedicated, no preemption — use for demos)
   - Region: **EU-RO** preferred (closest to BLR1 droplet)
3. Configure:
   - **Container Image**: `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04`
   - **Container Disk**: **50 GB** (default 20GB is too small — pip packages ~8GB + model weights ~18GB)
   - **Volume**: attach your **Network Volume** if you have one (keeps model weights across pod restarts, saves ~20 min re-download next time)
   - **Expose HTTP port**: `8000`
   - **Env variables**: none needed (API key is handled in the server code)
4. Wait for pod status → **Running**

## 2. Start the Rabbit API server inside the pod

Open the RunPod **web terminal** (Connect → Start Web Terminal) or SSH in:

```bash
cd /workspace

# Clone the repo (skip if already on network volume)
git clone https://github.com/parthajy/rabbit.git 2>/dev/null || (cd rabbit && git pull)
cd rabbit

# Install dependencies (first boot only, ~3-5 min)
pip install -e ".[server]" 2>&1 | tail -5
pip install fastembed qdrant-client 2>&1 | tail -3

# Set your HuggingFace token (needed to download private model weights)
export HF_TOKEN="<your-huggingface-token>"

# Start the server (model loads in ~2-3 min on A40)
# The actual server is rabbit/api/server.py — it serves:
#   /v1/raw       — OpenAI-compatible chat completions (what Reattend uses for /api/ask + triage)
#   /v1/ingest    — multi-signal pipeline (triage+extract+summarize+sentiment+importance)
#   /v1/keys/generate — API key management
#   /health       — health check
cd /workspace/rabbit
python -m uvicorn rabbit.api.server:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 1 \
  2>&1 | tee /tmp/rabbit.log &

# Wait for model to load, then verify
echo "Waiting for model to load (~2-3 min)..."
for i in $(seq 1 40); do
  sleep 5
  if curl -s http://localhost:8000/health 2>/dev/null | grep -q '"status"'; then
    echo "Server is up!"
    break
  fi
  echo "  ...loading ($((i*5))s)"
done

# Quick smoke test
curl -s http://localhost:8000/v1/raw \
  -H "Authorization: Bearer rab_live_Arcs9ujChXZnixCyY5xEfje5" \
  -H "Content-Type: application/json" \
  -d '{"model":"rabbit-v2.0","messages":[{"role":"user","content":"hello"}],"max_tokens":10}'
```

You should see a JSON response with `"content": "Hello! ..."`.

## 3. Get the new proxy URL

Every new pod gets a fresh subdomain:

1. In RunPod console → your pod → **Connect** tab
2. Copy the **HTTP [Port 8000]** URL — it looks like:
   `https://XXXXXXXX-8000.proxy.runpod.net`
3. Test it from your laptop:
   ```bash
   curl https://XXXXXXXX-8000.proxy.runpod.net/v1/raw \
     -H "Authorization: Bearer rab_live_Arcs9ujChXZnixCyY5xEfje5" \
     -H "Content-Type: application/json" \
     -d '{"model":"rabbit-v2.0","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
   ```

## 4. Update the droplet to point at the new URL

SSH into the DigitalOcean droplet:

```bash
ssh root@157.245.110.176

# Replace the old RunPod URL with the new one
NEW_URL="https://XXXXXXXX-8000.proxy.runpod.net"   # ← paste your new URL here
sed -i "s|^RABBIT_API_URL=.*|RABBIT_API_URL=$NEW_URL|" /var/www/reattend/.env.local

# Verify it stuck
grep RABBIT_API_URL /var/www/reattend/.env.local

# Restart Reattend so it picks up the new URL
pm2 restart reattend

# Wait for boot, then test
sleep 10
curl -s -o /dev/null -w 'homepage: %{http_code}\n' http://127.0.0.1:3000/
curl -s -o /dev/null -w 'api/user: %{http_code}\n' http://127.0.0.1:3000/api/user
# expect: homepage 200, api/user 401
```

## 5. Verify end-to-end (droplet → Rabbit)

```bash
# Still on the droplet — test that Reattend can reach Rabbit
curl -sS --max-time 60 \
  $(grep RABBIT_API_URL /var/www/reattend/.env.local | cut -d= -f2-)/v1/raw \
  -H "Authorization: Bearer $(grep RABBIT_API_KEY /var/www/reattend/.env.local | cut -d= -f2-)" \
  -H "Content-Type: application/json" \
  -d '{"model":"rabbit-v2.0","messages":[{"role":"user","content":"Say hello"}],"max_tokens":20}'
```

If you see a valid JSON response with `"content"`, Reattend is fully connected.

## 6. Reprocess any failed jobs

If memories were added while Rabbit was down, their enrichment jobs failed. Reset and retry:

```bash
# On the droplet
sqlite3 /var/www/reattend/data/reattend.db \
  "UPDATE job_queue SET status='pending', attempts=0 WHERE status='failed';"

# Trigger the worker
curl -sS -X POST http://127.0.0.1:3000/api/jobs/cron \
  -H "Authorization: Bearer $(grep CRON_SECRET /var/www/reattend/.env.local | cut -d= -f2-)" \
  --max-time 600

# Check results
sqlite3 /var/www/reattend/data/reattend.db \
  "SELECT substr(id,1,8), type, status, attempts FROM job_queue ORDER BY created_at DESC LIMIT 20;"
```

All jobs should show `completed`. If any show `failed`, check the error column:
```bash
sqlite3 /var/www/reattend/data/reattend.db \
  "SELECT substr(id,1,8), status, substr(error,1,80) FROM job_queue WHERE status='failed';"
```

---

## Quick reference

| What | Value |
|------|-------|
| **Droplet IP** | `157.245.110.176` (BLR1, 2GB RAM, 25GB SSD) |
| **Droplet SSH** | `ssh root@157.245.110.176` |
| **Reattend URL** | `https://reattend.com` |
| **Rabbit marketing** | `https://rabbit.reattend.com` |
| **RunPod GPU** | A40 48GB |
| **RunPod image** | `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04` |
| **Rabbit server code** | `rabbit/api/server.py` (start via `uvicorn rabbit.api.server:app`) |
| **Rabbit port** | `8000` |
| **Rabbit API key** | `rab_live_Arcs9ujChXZnixCyY5xEfje5` |
| **HF model repo** | `reattend/rabbit-v2.0` (private, needs HF_TOKEN) |
| **PM2 processes** | `reattend` (port 3000), `rabbit-web` (port 3001) |
| **DB path** | `/var/www/reattend/data/reattend.db` |
| **Embedding model** | `/var/www/reattend/data/models/fast-bge-base-en-v1.5/` |
| **Deploy script** | `/tmp/deploy_reattendv2.sh` (preserves DB on redeploy) |
| **Cron secret** | stored in `.env.local` as `CRON_SECRET` |

## Stopping (to save money overnight)

1. **Terminate** the RunPod pod (Lock/Edit/Restart all keep billing active)
2. Network volume charges ~$0.07/GB/month (pennies) — leave it
3. The droplet stays running ($12/mo flat) — Reattend serves the homepage fine, just `/api/ask` and memory enrichment fail gracefully until Rabbit is back
