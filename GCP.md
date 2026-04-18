# Rabbit on GCP — Always-On L4 Spot

Rabbit v2.0 runs permanently on a GCP L4 Spot VM. No more RunPod start/stop cycles, no Cloudflare proxy timeouts, no URL/key rotation.

---

## What we have

| What | Value |
|------|-------|
| **GCP Project** | `rabbit-492510` |
| **VM Name** | `rabbit-v2` |
| **Zone** | `asia-southeast1-a` (Singapore) |
| **Machine** | `g2-standard-8` (1x L4 24GB, 8 vCPU, 32GB RAM) |
| **IP** | `34.143.190.54` (static — `rabbit-sg-static`, never changes) |
| **Provisioning** | Spot (~$0.31/hr, ~$226/mo) |
| **Disk** | 150GB `pd-balanced` (baked image with model weights pre-downloaded) |
| **Baked Image** | `rabbit-v2-20260414-1202` (family: `rabbit-v2`) |
| **Server** | `rabbit.api.server:app` via systemd, port 8000 |
| **API Key** | `rab_live_cc_KwnSD9TIyknKII43c0_nT` |
| **Auto-stop** | Disabled (always-on) |
| **Model** | `reattend/rabbit-v2.0` (LoRA on Qwen 2.5 32B 4-bit) |

## Why GCP over RunPod

| Problem with RunPod | Fixed on GCP |
|---|---|
| Cloudflare proxy has 100s timeout → 524 errors on long prompts | Direct IP, no proxy, no timeout |
| New pod = new URL + new API key every time | Static IP, persistent disk, key survives reboots |
| Pod termination = GPU billing stops but setup takes 10 min | VM stops but disk persists, restart takes 2 min |
| No auto-restart on crash | systemd `Restart=always` |

## Cost breakdown

| Component | Cost |
|---|---|
| **L4 Spot compute** | ~$0.31/hr → ~$226/mo |
| **150GB disk** | ~$15/mo (persists even when VM is stopped) |
| **Static IP (if reserved)** | $7.30/mo when unattached, free when attached |
| **Network egress** | Negligible at current traffic |
| **Total** | **~$241/mo** (~₹20K/mo) |
| **Budget** | ₹25K GCP credit → ~40 days |

## Architecture

```
User → reattend.com (DO droplet, BLR1)
         ↓ /api/ask, /api/records
       Rabbit API (GCP L4, Singapore)
         http://34.143.190.54:8000/v1/raw
         ↓
       Qwen 2.5 32B + LoRA (4-bit, ~18GB VRAM)
```

- **Droplet** (157.245.110.176): Next.js app, SQLite DB, FastEmbed embeddings
- **GCP VM** (34.143.190.54): Rabbit LLM only — stateless inference, no user data

## Day-to-day operations

### It's always running. You don't need to do anything.

The server starts on boot via systemd. If it crashes, systemd restarts it in 10s.

### If spot preemption happens (~1-2x/week)

GCP may reclaim the VM for ~5-30 minutes. The VM stops, Reattend's /api/ask returns errors gracefully, and you restart it:

```bash
gcloud compute instances start rabbit-v2 --zone=asia-southeast1-a
```

That's it. Same static IP (`34.143.190.54`), same disk, same API key. Model reloads in ~2 min. No droplet update needed.

To check if it's running:
```bash
gcloud compute instances describe rabbit-v2 --zone=asia-southeast1-a --format="value(status)"
# Should say: RUNNING

curl -s http://34.143.190.54:8000/health
# Should return: {"status":"ok",...}
```

### SSH into the VM

```bash
gcloud compute ssh rabbit-v2 --zone=asia-southeast1-a
```

### View server logs

```bash
gcloud compute ssh rabbit-v2 --zone=asia-southeast1-a --command="sudo journalctl -u rabbit -f"
```

### Restart the server (without rebooting VM)

```bash
gcloud compute ssh rabbit-v2 --zone=asia-southeast1-a --command="sudo systemctl restart rabbit"
```

## Decisions made

1. **Singapore over Mumbai**: All 3 Mumbai zones (asia-south1-a/b/c) had L4 spot stockouts. Singapore (asia-southeast1-a) had capacity. Latency to BLR1 droplet is ~50ms vs ~10ms — negligible for our use.

2. **Spot over on-demand**: $226/mo vs $766/mo. Risk is preemption ~1-2x/week, but restart takes 2 min and is a single command.

3. **No Cloudflare proxy**: Direct HTTP to port 8000. This eliminated the 524 timeout errors that plagued RunPod. Trade-off: no DDoS protection, but we're not a public API — only our droplet calls it.

4. **Auto-stop disabled**: We want 24/7 uptime. The old auto-stop timer (shutdown after 20 min idle) is disabled via systemd.

5. **Baked image**: Model weights are pre-downloaded into the boot disk image. This means VM startup = boot + model load (~2 min), not boot + download (~20 min).

6. **API key persists**: Generated once, stored in the VM's SQLite keys DB on the persistent boot disk. No rotation needed unless you want to.

## Future: what to do when credits run out

| Option | Cost | Notes |
|---|---|---|
| **Continue L4 Spot** | ~₹20K/mo | Pay out of pocket |
| **Switch to on-demand** | ~₹64K/mo | Only if spot becomes unreliable |
| **RunPod Reserved A40 (1yr)** | ~₹13.5K/mo ($161) | Cheaper but back to RunPod |
| **Hetzner dedicated** | ~₹17K/mo (~$200) | Own hardware, no preemption |

## Files

| File | Purpose |
|------|---------|
| `serving/gcp/config.sh` | Shared config (project, zone, machine type) |
| `serving/gcp/00_bake_disk.sh` | Bake a new disk image with model weights |
| `serving/gcp/vm_spawn.sh` | Create or start the VM |
| `serving/gcp/vm_stop.sh` | Stop the VM (preserves disk) |
| `serving/gcp/vm_status.sh` | Check VM status |
| `serving/systemd/rabbit.service` | systemd unit for the API server |
| `serving/scripts/install.sh` | First-time setup script (runs during bake) |
| `rabbit/api/server.py` | The actual API server code |
