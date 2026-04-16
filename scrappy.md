# Scrappy — Rabbit/Coassist/Reattend on a Shoestring

How we run the whole stack on ~$200/mo cash + credits until the grant lands at M10.

---

## Timeline

1. **M1–M2**: Test Rabbit v2.0, train again if needed until we find the perfect spot. Cold starts OK.
2. **M2**: $2,000 GCP credit hoped to land.
3. **M3**: Start giving real demos.
4. **M5**: $5,000 extra credit hoped to land.
5. **M10**: Grant hoped to land.

## Cash + credit inventory (as of 2026-04-14)

| Source | Amount | Notes |
|---|---|---|
| GCP | $300 | Active |
| Azure | $1,000 | Untouched — pivot/insurance only |
| AWS | $200 | For utility infra |
| GCP pending | $2,000 | Hoped by M2 |
| GCP pending | $5,000 | Hoped by M5 |
| Grant | ? | Hoped by M10 |
| **Cash cap** | **$100/mo cloud + $100/mo training** | Hard ceiling |

## Workload → cloud assignment

Split workloads across clouds so no single credit pool drains fast:

| Workload | Cloud | Paid from | Est. $/mo M1–M3 |
|---|---|---|---|
| **Rabbit inference** (A100 Spot, auto-spin, ~2hrs/day) | GCP | GCP $300 credit | ~$66 |
| **Training** (RunPod A100 on-demand, 30 hrs) | RunPod | Cash ($100 training budget) | ~$57 |
| **Postgres + Redis + Reattend backend + Coassist backend** | AWS | AWS $200 credit + free tier | ~$0-15 |
| **Coassist relevance filter LLM** | Groq / Gemini free tier | Free | $0 |
| **Azure** | — | Untouched | $0 |
| **Static IPs, DNS, misc** | GCP | Credit | ~$5 |
| **Total cash burn** | | | **~$57-70/mo** |

Under the $200/mo ceiling by ~$130/mo. Room for extra training runs or demo traffic spikes.

## Why multi-cloud

- **Rabbit inference on GCP**: credits absorb the cost, A100 Spot is cheap (~$1.10/hr), auto-spin keeps it off when nobody's using it.
- **Training on RunPod**: we already have working Unsloth scripts there, RunPod is ~30% cheaper than GCP for on-demand A100, and training is bursty so credit efficiency doesn't matter — cash is fine.
- **Utility on AWS**: 24/7 small stuff (Postgres, Redis, API servers) fits perfectly in AWS free tier + $200 credit. GPU there is too expensive.
- **Coassist relevance filter on Groq/Gemini free tier**: no reason to burn GPU budget on small filter calls when Groq gives 30 req/min on Llama 3.1 8B for free.
- **Azure stays untouched**: insurance policy. If GCP A100 quota is denied or Spot is evicted constantly, pivot to Azure A100 Spot. If a M6+ enterprise customer demands Azure, we already have ready infra and $1k to stand it up.

## Credit runway scenarios

| Scenario | Runway |
|---|---|
| Only $300 GCP lands (no extra credits ever) | M1–M4.5 on GCP, then pivot to Azure $1k → M5–M9, out by M10 (grant month) |
| +$2k at M2 (M5 credits don't land) | M1–M11 comfortably |
| +$2k at M2 **and** +$5k at M5 | M1–M15+ (a full year, probably more) |
| Best case: all credits + Founders Hub ($25k Azure) | **M1 through late 2027** |

**Must-file credit apps this week** (for safety):
- Microsoft for Startups Founders Hub — $1k instant, $5-25k within 2-4 weeks. No funding needed. Zero downside.
- NVIDIA Inception — DGX credits + RunPod/Lambda discounts. Free to apply.
- AWS Activate via Hugging Face — $5-10k credits (HF is an Activate Provider).

## Auto-spin serving architecture

Cold starts are fine for M1–M3 (we're the only users). Simplest possible pattern wins:

```
Reattend / Coassist
        │
        │  HTTPS
        ▼
rabbit.reattend.ai (GCP static IP)
        │
        ▼
  ┌─────────────────┐
  │  Cloud Function │  always-on, ~$0-5/mo
  │  "rabbit-router"│
  └────┬────────────┘
       │
       │ VM running?
       ├─ yes → proxy to VM:8000
       │
       └─ no → start VM + return 503 Retry-After: 90
              (Reattend retries in 90s)
```

**Components:**

1. **GCP A100 VM with persistent disk**
   - Ubuntu 22.04, Python 3.11, Unsloth, vLLM (or FastAPI + Unsloth if vLLM is finicky)
   - Persistent disk snapshot with `reattend/rabbit-v2.0` + base Qwen pre-downloaded
   - systemd unit starts the inference server on boot, listening on :8000
   - Cold start: ~60-90 seconds (disk already has the model cached)
   - Spot instance — 30s eviction signal handled by flushing in-flight requests

2. **Cloud Function (router)**
   - Always-on, essentially free
   - Receives requests, checks VM state via Compute Engine API
   - If stopped: calls `instances.start`, returns 503 with `Retry-After: 90`
   - If running: proxies to `VM:8000`
   - Writes `last_request_at` to Firestore on every call

3. **Auto-stop cron on VM**
   - `*/5 * * * *` checks `last_request_at`
   - If > 15 min idle → `sudo shutdown -h now`
   - Spot releases, credit burn stops

4. **Optional pre-warm**
   - Slack/CLI command `rabbit-wakeup` hits the start endpoint ~5 min before demos
   - VM is warm by the time the demo starts

**Verbose logging from day one**: every request logs prompt hash, signal type, input token count, output token count, latency, VM state, LoRA adapter version, and any errors with full traceback. We need to know what's breaking in the model when quality regresses.

## What we will explicitly NOT do

- ❌ Always-on serving (15× more burn, zero value pre-customers)
- ❌ Multi-region redundancy
- ❌ Kubernetes / GKE ($73/mo control plane = waste)
- ❌ Training on GCP (quota hassle, more expensive than RunPod)
- ❌ Paying for Azure ML / SageMaker / Vertex — use plain VMs
- ❌ Hosted HF Inference Endpoints (~$0.60+/hr for smaller models, bad value)
- ❌ Touching Azure credit in M1–M2 (insurance only)

## Three must-do this week

1. **File GCP A100 Spot quota request today** (takes 5 min, 1-3 day approval). Request 1× A100 in us-central1, Spot usage, "early-stage AI startup, running inference on fine-tuned LLM for customer validation demos".
2. **Reserve a GCP static external IP** in us-central1. Point `rabbit.reattend.ai` DNS at it now. Free while attached, ~$1.50/mo when unattached.
3. **Apply to Microsoft for Startups Founders Hub**. 15 min, $1k instant, no funding required, zero downside. Insurance.

## Decision log

- **2026-04-14**: Chose GCP + RunPod + AWS multi-cloud split over single-cloud Azure. Reason: Azure A100 is $3.67/hr vs GCP Spot $1.10/hr — 3.3× more expensive for identical hardware. $1k Azure credit kept as pivot insurance, not primary infra.
- **2026-04-14**: Decided to ship Rabbit as LoRA-only (no merged model) after the transformers 5.5 × Unsloth merge bug. Upside: smaller HF storage, cleaner per-org fine-tune story later, no 4-bit merge rounding loss.
- **2026-04-14**: Verbose logging is non-negotiable from day one of serving. We are still in R&D mode — we need to see what the model is doing wrong so we can re-train.
