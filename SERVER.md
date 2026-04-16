# Rabbit Server — Start / Stop / Reconnect

Everything you need to bring Rabbit back online after terminating the RunPod pod.
Each boot is treated as a clean start: wipe old keys, generate a fresh one, update the droplet.

---

## 1. Start a new RunPod pod

1. Go to [runpod.io/console/pods](https://www.runpod.io/console/pods)
2. Click **Deploy** → pick **A40 48GB** (or A6000/4090 — anything with 24GB+ VRAM works)
   - **Community Cloud**: ~$0.38/hr (cheaper, can be preempted)
   - **Secure Cloud**: ~$0.76/hr (dedicated, no preemption — use for demos)
   - Region: **EU-RO** or **EU-SE** preferred (closest to BLR1 droplet)
3. Configure:
   - **Container Image**: `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04`
   - **Container Disk**: **50 GB** (default 20GB is too small — pip packages ~8GB + model weights ~18GB)
   - **Volume**: attach `rabbit-data` network volume (150GB, keeps model weights cached)
   - **Expose HTTP port**: `8000`
   - **Env variables**: none needed
4. Wait for pod status → **Running**

## 2. Start the Rabbit API server

Open the RunPod **web terminal** (Connect → Start Web Terminal) or SSH in.

Copy-paste this entire block:

```bash
# ── 1. Clone / update repo ──
cd /workspace
git clone https://github.com/parthajy/rabbit.git 2>/dev/null || (cd rabbit && git pull)
cd rabbit

# ── 2. Install dependencies (first boot only, ~3-5 min) ──
pip install -e ".[server]" 2>&1 | tail -5
pip install fastembed qdrant-client 2>&1 | tail -3

# ── 3. Set HuggingFace token (read-only, needed for private model) ──
export HF_TOKEN="<your-huggingface-token>"

# ── 4. Wipe old API keys so we start clean ──
rm -f /workspace/rabbit-data/keys.db
echo "Old keys wiped."

# ── 5. Start the server ──
cd /workspace/rabbit
RABBIT_STORAGE=/workspace/rabbit-data python -m uvicorn rabbit.api.server:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 1 \
  2>&1 | tee /tmp/rabbit.log &

# ── 6. Wait for model to load ──
echo "Waiting for model to load (~2-3 min)..."
for i in $(seq 1 40); do
  sleep 5
  if curl -s http://localhost:8000/health 2>/dev/null | grep -q '"status"'; then
    echo "Server is up!"
    break
  fi
  echo "  ...loading ($((i*5))s)"
done

# ── 7. Generate a fresh API key ──
echo ""
echo "=== GENERATING NEW API KEY ==="
curl -s -X POST "http://localhost:8000/v1/keys/generate?tier=live"
echo ""
echo ""
echo ">>> COPY THE KEY ABOVE — you'll need it in Step 4 <<<"
```

You'll see output like:
```
{"key":"rab_live_XXXXXXXXXXXX","tenant_id":"...","tier":"live",...}
```

**Copy the `rab_live_...` key.** It's only shown once.

## 3. Get the new proxy URL + verify

1. In RunPod console → your pod → **Connect** tab
2. Copy the **HTTP [Port 8000]** URL — looks like:
   `https://XXXXXXXX-8000.proxy.runpod.net`
3. Test it from the pod terminal (replace the key with your new one):
   ```bash
   curl -s http://localhost:8000/v1/raw \
     -H "Authorization: Bearer rab_live_XXXXXXXXXXXX" \
     -H "Content-Type: application/json" \
     -d '{"model":"rabbit-v2.0","messages":[{"role":"user","content":"hello"}],"max_tokens":10}'
   ```
   You should see: `{"id":"rabbit-...","choices":[{"message":{"content":"Hello! ..."}}]}`

## 4. Update the droplet

SSH into the DigitalOcean droplet and update both the URL and key:

```bash
ssh root@157.245.110.176

# ── Set these two values (paste your new ones) ──
NEW_URL="https://XXXXXXXX-8000.proxy.runpod.net"
NEW_KEY="rab_live_XXXXXXXXXXXX"

# ── Update .env.local ──
sed -i "s|^RABBIT_API_URL=.*|RABBIT_API_URL=$NEW_URL|" /var/www/reattend/.env.local
sed -i "s|^RABBIT_API_KEY=.*|RABBIT_API_KEY=$NEW_KEY|" /var/www/reattend/.env.local

# ── Verify ──
grep '^RABBIT_API' /var/www/reattend/.env.local

# ── Restart Reattend ──
pm2 restart reattend
sleep 10

# ── Health check ──
curl -s -o /dev/null -w 'homepage: %{http_code}\n' http://127.0.0.1:3000/
curl -s -o /dev/null -w 'api/user: %{http_code}\n' http://127.0.0.1:3000/api/user
# expect: homepage 200, api/user 401
```

## 5. Verify end-to-end (droplet → Rabbit)

```bash
# Still on the droplet
curl -sS --max-time 60 \
  $(grep RABBIT_API_URL /var/www/reattend/.env.local | cut -d= -f2-)/v1/raw \
  -H "Authorization: Bearer $(grep RABBIT_API_KEY /var/www/reattend/.env.local | cut -d= -f2-)" \
  -H "Content-Type: application/json" \
  -d '{"model":"rabbit-v2.0","messages":[{"role":"user","content":"Say hello"}],"max_tokens":20}'
```

Should return a JSON response with `"content"`. If yes, Reattend is fully connected.

## 6. Reprocess any failed jobs

If memories were added while Rabbit was down:

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

All should show `completed`. If any show `failed`:
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
| **RunPod GPU** | A40 48GB (or any 24GB+ GPU) |
| **RunPod image** | `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04` |
| **RunPod volume** | `rabbit-data` (150GB, EU-SE-1) |
| **Container disk** | 50 GB minimum |
| **Rabbit server code** | `rabbit/api/server.py` (start via `uvicorn rabbit.api.server:app`) |
| **Rabbit port** | `8000` |
| **Rabbit API key** | Generated fresh each boot (Step 2) |
| **HF model repo** | `reattend/rabbit-v2.0` (private, needs HF_TOKEN with read access) |
| **PM2 processes** | `reattend` (port 3000), `rabbit-web` (port 3001) |
| **DB path** | `/var/www/reattend/data/reattend.db` |
| **Embedding model** | `/var/www/reattend/data/models/fast-bge-base-en-v1.5/` |
| **Deploy script** | `/tmp/deploy_reattendv2.sh` (preserves DB on redeploy) |
| **Cron secret** | stored in `.env.local` as `CRON_SECRET` |

## Stopping (to save money overnight)

1. **Terminate** the RunPod pod (Lock/Edit/Restart all keep billing active)
2. Network volume charges ~$0.07/GB/month (~$10.50/mo for 150GB) — leave it
3. The droplet stays running ($12/mo flat) — Reattend serves the homepage fine, just `/api/ask` and memory enrichment fail gracefully until Rabbit is back
4. Next time: start a new pod and repeat from Step 1

## Cost reference

| Plan | GPU | Monthly (24/7) |
|------|-----|----------------|
| RunPod Community | A40 | ~$278/mo |
| RunPod Secure | A40 | ~$555/mo |
| RunPod Reserved (1yr) | A40 | ~$161/mo |
| Start/stop (dev) | A40 | ~$5-10/day when active |
