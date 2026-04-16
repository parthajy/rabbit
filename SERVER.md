# Rabbit Server — Start / Stop / Reconnect

Everything you need to bring Rabbit back online after terminating the RunPod pod.

---

## 1. Start a new RunPod pod

1. Go to [runpod.io/console/pods](https://www.runpod.io/console/pods)
2. Click **Deploy** → pick **A40 48GB** (Secure Cloud, EU-RO preferred for latency to BLR1 droplet)
3. Template: use your saved **rabbit-v2.0** template, or configure manually:
   - **Container Image**: `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04`
   - **Volume**: attach your **Network Volume** if you have one (keeps model weights across restarts)
   - **Expose HTTP port**: `8000`
   - **Docker command / start script**: see Step 2 below
4. Wait for pod status → **Running**

## 2. Start the Rabbit API server inside the pod

SSH into the pod or use the RunPod web terminal:

```bash
# If weights are already on the network volume, skip the download
cd /workspace

# Clone the serving code (if not already present)
git clone https://github.com/Reattend/rabbit.git 2>/dev/null || true
cd rabbit/deployment

# Install dependencies (first boot only)
pip install -r requirements.txt 2>/dev/null

# Start the server
# MODEL_PATH should point to wherever your merged v2.0 weights live.
# If using a network volume, this is typically /workspace/models/rabbit-v2-merged
python -m uvicorn server:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 1 \
  2>&1 | tee /tmp/rabbit.log &

# Verify it's alive
sleep 30
curl http://localhost:8000/v1/raw \
  -H "Authorization: Bearer rab_live_Arcs9ujChXZnixCyY5xEfje5" \
  -H "Content-Type: application/json" \
  -d '{"model":"rabbit-v2.0","messages":[{"role":"user","content":"hello"}],"max_tokens":10}'
```

You should see a JSON response with `"content": "Hello! ..."`.

## 3. Get the new proxy URL

Every new pod gets a fresh subdomain. Find it:

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

SSH into the DigitalOcean droplet (`157.245.110.176`):

```bash
ssh root@157.245.110.176

# Replace the old RunPod URL with the new one
NEW_URL="https://XXXXXXXX-8000.proxy.runpod.net"   # ← paste your new URL here
sed -i "s|^RABBIT_API_URL=.*|RABBIT_API_URL=$NEW_URL|" /var/www/reattend/.env.local

# Verify
grep RABBIT_API_URL /var/www/reattend/.env.local

# Restart Reattend so it picks up the new URL
pm2 restart reattend

# Wait for boot, then test
sleep 10
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3000/          # expect 200
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3000/api/user  # expect 401
```

## 5. Verify end-to-end

Test that the droplet can reach Rabbit through the new URL:

```bash
# From the droplet — quick smoke test
curl -sS --max-time 60 \
  $(grep RABBIT_API_URL /var/www/reattend/.env.local | cut -d= -f2-)/v1/raw \
  -H "Authorization: Bearer $(grep RABBIT_API_KEY /var/www/reattend/.env.local | cut -d= -f2-)" \
  -H "Content-Type: application/json" \
  -d '{"model":"rabbit-v2.0","messages":[{"role":"user","content":"Say hello"}],"max_tokens":20}'
```

If you see a valid JSON response, Reattend is fully connected to Rabbit.

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

---

## Quick reference

| What | Value |
|------|-------|
| **Droplet IP** | `157.245.110.176` (BLR1, 2GB RAM, 25GB SSD) |
| **Droplet SSH** | `ssh root@157.245.110.176` |
| **Reattend URL** | `https://reattend.com` |
| **Rabbit marketing** | `https://rabbit.reattend.com` |
| **RunPod GPU** | A40 48GB, Secure Cloud, EU-RO |
| **Rabbit port** | `8000` |
| **Rabbit API key** | `rab_live_Arcs9ujChXZnixCyY5xEfje5` |
| **PM2 processes** | `reattend` (port 3000), `rabbit-web` (port 3001) |
| **DB path** | `/var/www/reattend/data/reattend.db` |
| **Embedding model** | `/var/www/reattend/data/models/fast-bge-base-en-v1.5/` |
| **Deploy script** | `/tmp/deploy_reattendv2.sh` (preserves DB on redeploy) |
| **Cron secret** | stored in `.env.local` as `CRON_SECRET` |

## Stopping (to save money overnight)

1. **Terminate** the RunPod pod (Lock/Edit/Restart all keep billing)
2. Network volume charges ~$0.07/GB/month (pennies) — leave it
3. The droplet stays running ($12/mo flat) — Reattend serves the homepage fine, just `/api/ask` and memory enrichment fail gracefully until Rabbit is back
