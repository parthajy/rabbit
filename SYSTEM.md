# Rabbit v2.0 — Serving System Overview

**Who this is for:** one doc that a non-technical cofounder, a technical cofounder, an investor, or a future engineer can read and understand exactly what we built, how it works, what it costs, and where it's going.

**Last updated:** 2026-04-14 — day of first live deployment on Google Cloud.

---

## 1. The TL;DR (60 seconds)

We trained our own AI model, Rabbit v2.0 — a 32-billion parameter language model fine-tuned on 90,000 organizational memory examples. It runs on one Google Cloud Spot GPU, costs us about $40–60 per month while we test it, and wakes up in 90 seconds when we need to use it, sleeps when we don't. Our CLI `rabbit wake` / `rabbit stop` / `rabbit extract "..."` makes all of it feel like a local tool, even though the model runs on a GPU in a data center in Iowa. The whole thing is designed so that when we have real customers and real funding, we flip two config lines and it scales to 24/7 production without rewriting a single piece of code.

---

## 2. What Rabbit actually is

**Rabbit v2.0** is a large language model specialized for **organizational memory** — turning the firehose of information that flows through a company (meetings, emails, Slack, docs, reports) into structured, searchable, answerable memory.

It was built by:
1. Starting from **Qwen 2.5 32B Instruct**, an open-source base model (Apache 2.0 license, commercial use allowed — we own what we build on top).
2. Fine-tuning it with **LoRA** (low-rank adaptation) on a proprietary dataset of **90,049 training examples** that we curated ourselves, spanning 19 different "memory signals" — things like:
   - **EXTRACT**: pull people, decisions, action items, dates from text
   - **TRIAGE**: classify and summarize content
   - **ANSWER**: answer questions with citations from memory
   - **IMPORTANCE**: score how significant something is
   - **LINK**: find related items across memories
   - ...and 14 more
3. Training on a single H100 GPU on RunPod for ~26 hours.
4. Shipping the result as a **LoRA adapter** (a 1.1 GB add-on file) plus the base Qwen model. Together they form Rabbit.

The model is stored privately on Hugging Face at `reattend/rabbit-v2.0`. Nobody else can download it.

**What makes Rabbit "ours":**
- 100% of the training data is ours — we collected, generated, and curated it
- 100% of the fine-tuned LoRA weights are ours — we own them outright
- 100% of the signal architecture, inference stack, and system prompts are ours
- The base model (Qwen) is free for commercial use — we owe nothing for using it

---

## 3. What we built on Google Cloud this session

We built a **scrappy, credit-efficient serving system** so that two developers (Partha + cofounder) in different time zones can test Rabbit from their laptops without running it locally (it's 32B parameters — it would take 20+ GB of GPU memory, which neither of our Macs has).

### The goal

- Make Rabbit reachable from anywhere via one shell command
- Cost as close to zero as possible while we're testing (not demo-ing to customers)
- Wake up fast, sleep automatically when idle
- Log everything verbosely so when Rabbit says something wrong, we can trace exactly what it saw and what it produced, then re-train
- Be designed so that scaling to production is a config change, not a rewrite

### What we actually have

```
Partha's Mac              Cofounder's Mac
     │                         │
     │  rabbit extract "..."   │
     │                         │
     └─────────┬───────────────┘
               │
               ▼
       Static IP 34.60.19.201
       (Google Cloud, us-central1)
               │
               ▼
  ┌──────────────────────────────┐
  │ rabbit-v2 (Spot GPU VM)      │
  │                              │
  │  • 1× NVIDIA L4 24GB         │
  │  • Ubuntu 22.04              │
  │  • Qwen 32B 4-bit + Rabbit   │
  │    LoRA already on disk      │
  │  • FastAPI server on :8000   │
  │  • 19 endpoints (1 per       │
  │    signal)                   │
  │  • Auto-stops after 20 min   │
  │    of no requests            │
  │  • Verbose JSON logs for     │
  │    every request             │
  └──────────────────────────────┘
```

**Hardware**: one `g2-standard-8` Google Cloud VM — 8 CPUs, 32 GB RAM, 1 NVIDIA L4 GPU (24 GB VRAM). The L4 has exactly enough VRAM to run Rabbit in 4-bit quantization with a little headroom. It's cheap because (a) L4 is not a top-tier GPU and (b) we run it as a **Spot instance** (see below).

**Software**: a FastAPI web server that loads Rabbit once on startup (about 35–45 seconds), then exposes 19 HTTP endpoints — one per memory signal. All communication is JSON. All requests log a structured record to a log file on disk.

**Access**: a shell CLI called `rabbit` that lives on each developer's Mac and talks to the server. It looks like a local tool but every command is just a `curl` under the hood.

---

## 4. The CLI — what `rabbit wake` and friends actually do

Every command starts with `rabbit`. Here's the full map.

### VM management

| Command | What it does |
|---|---|
| `rabbit wake` | Create or start the GPU VM. If it doesn't exist, create it from our pre-baked image. If it's stopped, start it. Either way, waits until `/health` returns 200, then prints the URL. ~90 seconds from cold. |
| `rabbit stop` | Stop the VM. The disk stays, the static IP stays, but the GPU billing stops. |
| `rabbit status` | Show VM state, static IP, health, and last request time. |
| `rabbit ssh` | SSH into the VM (for debugging). |
| `rabbit logs` | Tail the server log over SSH — watch every request in real time. |
| `rabbit url` | Print the Rabbit API URL. |
| `rabbit health` | Curl the /health endpoint. |

### Signal commands — this is how you actually use Rabbit

```bash
rabbit extract "Tom said we'd ship Rabbit v2 by May 15 and Priya will handle the rollout"
# Returns: {people: [Tom, Priya], decisions: [ship v2 by May 15], action_items: [Priya: rollout]}

rabbit triage "quarterly board meeting at 3pm discussing Q2 revenue targets"
# Returns: {type: "meeting", summary: "...", tags: [board, quarterly, revenue]}

rabbit summarize "... long text ..."
# Returns: 2-4 sentence summary

rabbit answer "What did Tom commit to last week?" --stream
# Streams tokens back as they generate — feels fast even though the model is slow

rabbit sentiment "the launch is going great"
# Returns: positive

rabbit intent "what did we decide about pricing?"
# Returns: history

rabbit importance "Tom mentioned he's leaving the company next month"
# Returns: {score: 5, reason: "key departure, significant organizational impact"}
```

There are 19 signals total. Each maps to one HTTP endpoint on the server. The CLI just builds a JSON payload and curls it.

### Flags

```bash
--stream                  Stream tokens live instead of waiting for full response
--max <n>                 Max tokens to generate (default 512)
--temp <0.0-1.0>          Sampling temperature (default 0.3, low = more predictable)
--file <path>             Read input from a file instead of command line
cat meeting.txt | rabbit triage          # or pipe from stdin
```

---

## 5. The magic trick — the "baked image"

Here's the clever part. When a Spot VM gets evicted (Google takes the GPU back because someone else is willing to pay full price), we need to be able to bring Rabbit back up in ~90 seconds, not 20 minutes. The trick is that we **pre-install everything on a disk image and freeze it**.

### What's on the baked image

```
/opt/rabbit/
├── venv/                       ← Python 3.10 with Unsloth, FastAPI, PyTorch 2.10 (~5 GB)
├── hfcache/                    ← Qwen 2.5 32B in 4-bit (~20 GB)
│                                   + Rabbit v2.0 LoRA adapter (~1.1 GB)
├── .cache/huggingface/token    ← HF token for private model access
├── rabbit_server.py            ← the FastAPI server we wrote
├── token                       ← the shared API token (developers auth with this)
└── auto_stop.sh                ← idle-kill script

/etc/systemd/system/
├── rabbit.service              ← runs the FastAPI server on boot
├── auto-stop.service           ← runs auto_stop.sh once
└── auto-stop.timer             ← triggers auto-stop every 5 minutes

/var/log/rabbit/server.log      ← verbose per-request JSON logs
```

All of this is frozen into one disk image called `rabbit-v2-20260414-1202` (family: `rabbit-v2`). Every future VM we create just attaches this image as its boot disk — no downloads, no installs, just boot straight to a working Rabbit server.

### How we built the image (the "bake")

One script, `00_bake_disk.sh`, did the whole thing:

1. Created a temporary GPU VM with a base Deep Learning image (comes with NVIDIA drivers pre-installed)
2. Uploaded our server code, install script, and systemd units
3. Ran the install script inside the VM:
   - Installed Python deps via pip
   - Downloaded Qwen 32B 4-bit + Rabbit LoRA from Hugging Face
   - Ran a smoke test — actually loaded the model onto the L4 GPU and generated one token to prove everything works
   - Installed the systemd units so the server starts automatically on boot
4. Stopped the temp VM
5. Snapshotted the boot disk into a reusable image
6. Deleted the temp VM

**The bake took ~30 minutes and cost about $1-2 of GCP credit.** It is a one-time cost. Every future `rabbit wake` is free until you re-bake (only needed when you want to ship a new version of Rabbit, like v2.1 after retraining).

---

## 6. Spot instances — why we're using them and what can go wrong

### What Spot means

Google (and every cloud) sells GPUs two ways:

- **On-demand**: $3.67/hour for an L4, you own it, nobody can touch it, 100% reliable.
- **Spot**: $0.22–$1.00/hour for the *same* L4, but Google can take it back with 30 seconds' notice if another customer is willing to pay full price. Roughly 80% cheaper.

We chose Spot because we're testing, not demoing to paying customers. Getting evicted 1-3 times a day is annoying, not catastrophic. When it happens:

1. The VM shuts down (graceful — Google gives a 30s warning)
2. The boot disk + static IP are preserved
3. We run `rabbit wake` again → a fresh Spot VM is created from the same baked image → attached to the same static IP → back online in 90 seconds

So "eviction" just looks like "accidentally closed my laptop" — annoying but not catastrophic.

### What can go wrong with Spot (and what we just hit)

**Stockouts.** Sometimes the zone literally doesn't have a free L4 to give you, even at full price. You get an error like:

> A g2-standard-8 VM instance with 1 nvidia-l4 accelerator(s) is currently unavailable in the us-central1-a zone.

This is exactly what happened on our first `rabbit wake`. Google's us-central1-a had no free L4 at that moment. **Fix**: try another zone. We have fallback zones wired in: us-central1-b, c, f. If all of us-central1 is out, we try us-west1 or us-east1. The region doesn't really matter — our users are us.

---

## 7. Auto-sleep — how we save money when we're not testing

The VM runs a **systemd timer** that fires every 5 minutes. It checks a file `/var/lib/rabbit/last_request`, which gets updated every time a request hits the server. If that file hasn't been touched in 20 minutes, the script runs `shutdown -h now` — the VM stops, the GPU is released, billing stops.

So a typical day looks like:

- 9:00am — Partha runs `rabbit wake`, VM boots in 90s, he starts testing
- 9:00am–12:30pm — continuous testing, VM stays up
- 12:30pm — lunch break
- 12:50pm — auto-stop fires, VM shuts down
- 2:00pm — back from lunch, `rabbit wake` again
- 2:00pm–6:00pm — testing + cofounder in a different timezone joins
- 6:20pm — everyone done, auto-stop fires
- Overnight — VM off, billing stops entirely

The only thing you pay for overnight is the static IP ($3/month) and the boot disk ($15/month). **About $18/month of baseline cost.** Add another ~$40/month for actual GPU hours while testing, total is ~$60/month.

Our $300 credit covers ~5 months of this pattern.

---

## 8. Verbose logging — how we debug the model

Every single request that hits Rabbit writes a structured JSON line to `/var/log/rabbit/server.log`. Every line contains:

- `request_id` — unique per request
- `signal` — which endpoint was called (extract, triage, etc.)
- `prompt_hash` — SHA of the input (lets us group duplicate asks)
- `prompt_preview` — first 200 chars of the input
- `input_tokens` — how many tokens went in
- `output_tokens` — how many came out
- `latency_ms` — how long it took
- `tokens_per_sec` — inference speed
- `lora_hash` — which version of Rabbit handled it
- `response_preview` — first 200 chars of what Rabbit said
- On errors: the full Python traceback

**Why this matters:** when Rabbit produces a bad output (wrong extraction, hallucinated fact, malformed JSON), we can find the exact prompt that caused it, add it to our training data, retrain Rabbit on RunPod, ship v2.1, redeploy. This is how the model gets better every week.

The loop:

```
bad output in production
        │
        ▼
find it in server.log via request_id
        │
        ▼
add prompt + correct output to training data
        │
        ▼
train LoRA v2.1 on RunPod (1-2 hrs, ~$15-30)
        │
        ▼
upload new LoRA to Hugging Face
        │
        ▼
run 00_bake_disk.sh to refresh image
        │
        ▼
rabbit wake → new VM uses v2.1
        │
        ▼
bad output is now fixed
```

---

## 9. What we paid to build this

| Line item | Paid by |
|---|---|
| RunPod H100 × 26 hours for training Rabbit v2.0 | ~$70 cash |
| GCP image bake (temporary L4 for ~30 min) | ~$1-2 GCP credit |
| GCP static IP (monthly) | ~$3/month credit |
| GCP boot disk 150 GB (monthly) | ~$15/month credit |
| GCP L4 Spot GPU (~6 hrs/day × 30 days = ~180 hrs) | ~$40/month credit |
| Hugging Face model hosting | $0 (free) |
| **Total first month** | ~$60 credit + $70 cash already spent |
| **Remaining GCP credit after month 1** | ~$240 |
| **Runway on $300 credit alone** | ~5 months |

Compared to:
- Azure equivalent: ~$150/month on Spot, ~$280/month on-demand
- AWS equivalent: ~$300/month even on Spot
- Running it always-on on GCP (no auto-stop): ~$160/month

We are paying **about a third of what a naive "always-on" setup would cost**.

---

## 10. The file layout (for the technical reader)

```
~/Desktop/rabbit/
├── serving/
│   ├── README.md                    Runbook + command cheatsheet
│   ├── rabbit_server.py             FastAPI + Unsloth + 19 signals + streaming + verbose JSON logging
│   ├── requirements.txt             Python deps (unsloth, fastapi, etc.)
│   ├── systemd/
│   │   ├── rabbit.service           FastAPI as a Linux service
│   │   ├── auto-stop.service        Idle-check oneshot
│   │   └── auto-stop.timer          Runs every 5 minutes
│   ├── scripts/
│   │   ├── install.sh               Runs INSIDE the bake VM — pip install, download model, smoke test
│   │   └── auto_stop.sh             Shuts VM down after 20 min idle
│   └── gcp/
│       ├── config.sh                Shared env vars (project, zone, machine type, image family)
│       ├── 00_bake_disk.sh          ONE-TIME: builds the reusable image
│       ├── vm_spawn.sh              rabbit wake backend
│       ├── vm_stop.sh               rabbit stop backend
│       └── vm_status.sh             rabbit status backend
├── cli/
│   └── rabbit                       The CLI wrapper — one bash script, no dependencies
├── scripts/
│   └── finetune_qwen32b.py          The training script we ran on RunPod
├── data/
│   ├── filtered/                    90K training examples (21 JSONL files)
│   └── synthetic/                   Raw generation outputs
├── training.md                      Full record of training v1.0 → v2.0
├── scrappy.md                       Credit + cloud strategy
└── SYSTEM.md                        This file
```

---

## 11. The scaling plan — when we have $10k+ in credits

The whole design decision we made is: **ship scrappy now, scale with one config change later.** Here's what changes at each funding tier.

### Today: $300 GCP credit — "scrappy dev" mode (where we are)

- 1× L4 Spot VM, auto-stop after 20 min
- Only up when we're actively testing
- Expected: ~$60/month, ~5 months runway
- Tolerates Spot evictions
- Two-developer access, shared bearer token
- **Goal**: figure out if Rabbit v2.0 is good enough, re-train if not

### M2: +$2,000 GCP credit lands — "demo ready" mode

Almost no change to the architecture. What changes:

- Switch from L4 (24 GB) to **A100 40GB** — 5× faster inference (~50-70 tok/s vs ~15-25 tok/s)
- Still Spot, still auto-stop
- **Now we can show Rabbit to prospects without embarrassment** — demos don't stall on slow generation
- Expected: ~$150-250/month, ~10 months runway on the extra credit
- We change one line in `config.sh`: `MACHINE_TYPE="a2-highgpu-1g"`, rebake the image, done.

### M5: +$5,000 GCP credit — "early alpha with design partners" mode

- Keep A100 Spot but **always-on during business hours** (no more 90s cold starts for prospects)
- Add a **warm pool**: a second cheap VM running the relevance filter on Gemini Flash so Coassist can ingest 24/7
- Add **structured logging to Cloud Logging** (not just the local file) so we have metrics and alerts
- Expected: ~$500-700/month
- Still no code changes — just scheduled wake/stop instead of idle-wake

### M10: grant + $10k+ in credit lands — "early production" mode

This is where we stop being scrappy and become serious. Changes:

- Switch to **on-demand A100** (no more Spot evictions) for demo-critical deployments
- Reserve a **second region** (europe-west4) for European design partners — one `config.sh` per region, same image
- Add a **Cloud Run front-end** that handles auth, rate limiting, and load-balances between zones
- Spin up a **Postgres + Redis** utility stack on Cloud SQL for Coassist's state (~$50/month)
- Add **per-customer LoRA adapters** — each paying customer gets their own fine-tune on their corpus, stacked on base Rabbit. Their memory, their model.
- Expected: ~$1,500-2,500/month
- Still the same Rabbit API, the same CLI works, the same rabbit_server.py runs. We just upgrade the instance type and add redundancy.

### When we have real revenue — "real production" mode

- **vLLM with continuous batching** for throughput — serves 10-100 customers per GPU instead of 1
- **Kubernetes (GKE)** for multi-zone orchestration
- **A100 80GB or H100** for larger context windows and faster inference
- **On-prem Docker bundles** for banks/hospitals that can't send data to a cloud — same Rabbit image, deployed to customer hardware, they manage it
- **Automatic retraining pipeline**: bad outputs flagged in production → queued → weekly retrain → automatic redeploy

The key point: **the work we did today is not throwaway code.** Every line of `rabbit_server.py`, the CLI, the bake script, the systemd units — all of it survives into every future tier. We just swap one config file to go from "2 devs on Spot L4" to "100 customers on vLLM A100 fleet across 3 regions."

---

## 12. What could still go wrong (and what we'll do)

| Risk | What it looks like | Mitigation |
|---|---|---|
| **Zone stockout on `rabbit wake`** | "capacity unavailable" error | CLI already tries alternate zones. Worst case: 15 minutes of trying different zones, or pivot to us-west1. |
| **Spot eviction mid-demo** | VM disappears during a customer call | Upgrade to on-demand for the duration of the demo (one command). Cost $3.67/hr instead of ~$1. |
| **Rabbit gives a bad output** | Wrong extraction, hallucinated name, malformed JSON | Grep `server.log` for the prompt_hash → add to training data → retrain on RunPod → redeploy in 2 days |
| **GCP credit runs out before next credit lands** | Static IP + boot disk still cost money (~$18/month even with VM off) | Delete static IP + boot disk, pivot to Azure ($1000 credit untouched). ~1 day of work to re-bake image on Azure. |
| **L4 isn't fast enough for demos** | Customer watching live extraction, 20 tok/s feels slow | Ship with streaming mode on (already done), or upgrade to A100 via config change |
| **Hugging Face is down** | Model download fails during bake | Non-issue at runtime — the baked image has everything. Only hits us when re-baking, and we can retry |

---

## 13. The one-paragraph version for your non-technical cofounder

> We trained our own AI model called Rabbit. It lives on Hugging Face in a private repo we own. Today we deployed it to Google Cloud in a cheap way that costs us about $60/month during testing. When we want to use Rabbit, we type `rabbit wake` on our laptop and 90 seconds later it's running in the cloud. When we're done, it turns itself off automatically. Every test we run writes a detailed log so when Rabbit gets something wrong, we can find exactly what went wrong and fix it by retraining. The whole setup is designed so that when we raise money and get more cloud credits, we flip a switch and Rabbit goes from "two people testing" to "real customers" without rewriting anything. The total cost to build it today was about $72 (training run + image bake). We have ~5 months of testing runway on the GCP credit we already have.

---

## 14. The one-paragraph version for a technical cofounder or engineer

> Rabbit v2.0 is a QLoRA fine-tune of Qwen 2.5 32B Instruct (Apache 2.0 base, LoRA adapter is ours), trained on 90K proprietary examples across 19 memory signals for 1 epoch on a single H100 for ~26 hours. Inference runs via Unsloth + 4-bit bnb on a g2-standard-8 (1× L4 24GB) Spot VM in GCP us-central1. We baked a reusable Compute Engine image containing the venv, the HF cache, and systemd units, so fresh VMs boot to a healthy FastAPI server in ~90 seconds regardless of Spot churn. A CLI wrapper (`rabbit wake/stop/extract/...`) gives local-feeling access via a single static IP. Auto-stop runs every 5 min via systemd timer and shuts the VM if `last_request` file is >20 min stale. All requests emit structured JSON logs (request_id, prompt_hash, tokens in/out, latency, lora_hash, response preview, errors with full traceback) to `/var/log/rabbit/server.log` — grep this file when the model misbehaves and feed the prompts back into training. Streaming is on for interactive feel on L4. The whole stack — rabbit_server.py, the CLI, the bake script, the systemd units — is cloud-agnostic; swapping to Azure or AWS is a `config.sh` change and a re-bake. When credits arrive we flip `MACHINE_TYPE` to A100 for 5× speed and that's it. Total first-build cost: ~$72.

---

## 15. Credits and thanks

- **Rabbit's base model**: Qwen 2.5 32B Instruct by Alibaba Cloud (Apache 2.0 license)
- **Training framework**: Unsloth (the fastest LoRA training stack in the OSS world)
- **Inference framework**: Unsloth + Hugging Face Transformers + FastAPI
- **Training GPU**: RunPod (cash, ~$70)
- **Serving GPU**: Google Cloud (credits, ~$60/month)
- **Storage**: Hugging Face Hub (free)

Built by Partha + [cofounder] with pairing help from Claude.
