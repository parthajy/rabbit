# Rabbit — Training Logbook

Every training run documented. Never lose context on what changed and why.

---

## v1.0 — April 3, 2026

**Base:** Phi-3.5 Mini (3.8B params)
**Method:** LoRA (r=16, alpha=16) via Unsloth
**Data:** 55,750 filtered examples (from 62,000 raw)
**Signals:** 8 (intent, extract, triage, expand, answer, summarize, sentiment, importance)
**Training:** 3 epochs, RunPod A100, ~6 hours (T4 first attempt crashed)
**Cost:** ~$15 (Colab + RunPod)
**Loss:** 0.737 → 0.590
**Result:** Basic 8-signal model. Flat answers, no citations format. Worked but not production quality.
**Uploaded:** HuggingFace reattend/rabbit-v1

---

## v1.1 — April 5, 2026

**Data:** 53,901 filtered examples (newly generated, replaced v1.0 data)
**Signals:** 10 (added multiturn, dontknow)
**Changes:**
- Conversational answer format with Sources + Follow-ups
- Multi-turn conversation support
- Graceful "I don't know" handling
- Reasoning phrases ("What's interesting is...", "This suggests...")
**Training:** 3 epochs, RunPod A100, ~2 hours
**Cost:** ~$3
**Result:** Major quality jump in answers. Conversational tone. Citations present. First answer that felt like a smart colleague.
**Uploaded:** HuggingFace reattend/rabbit-v1.1

---

## v1.2 — April 6, 2026

**Data:** 61,178 filtered examples (v1.1 data + 4,430 link + 2,847 ambient)
**Signals:** 12 (added link, ambient)
**Changes:**
- Memory relationship detection (7 link types)
- Contradiction/forgotten commitment detection
- Same answer quality as v1.1 + new capabilities
**Training:** 3 epochs, RunPod A100, ~8 hours (21,795 steps)
**Cost:** ~$3
**Loss:** Started ~0.6, ended ~0.5
**Result:** Full 12-signal model. Linking works correctly. Ambient catches contradictions. Deployed to Google Cloud.
**Uploaded:** HuggingFace reattend/rabbit-v1.2
**Deployed:** Google Cloud Mumbai (34.93.210.241:8000)

### v1.2 Benchmark (April 7)
- Intent: 5/5 correct (100%)
- Sentiment: 4/5 correct (80%)
- Extract: Works but hallucinated "Sarcis" for "Sarah"
- Answer: Good narrative + reasoning, but missing bold formatting
- Link: Correct relationships, but messy JSON output
- Latency: Simple signals 270-700ms, answers 36-48s

---

## v1.3 — April 7, 2026 (PLANNED)

**Data:** ~77,000 examples (v1.2 data + 16,000 new targeted)
**Signals:** 15 (existing 12 + compile, lint, compile_answer)
**Changes:**
- Fix hallucination (faithful extraction training)
- Fix formatting (bold names/decisions)
- Fix follow-up format (proper "Follow-up questions:" header)
- Fix LINK/AMBIENT JSON output (no trailing text)
- NEW: COMPILE signal (update wiki pages with new info)
- NEW: LINT signal (detect contradictions, stale info, gaps)
- NEW: COMPILE_ANSWER signal (convert answers to wiki entries)

### New Training Data Breakdown
| Category | Count | Fixes |
|---|---|---|
| Faithful extraction | 3,000 | Hallucination |
| Formatted answers (bold) | 3,000 | No formatting |
| Correct follow-up format | 2,000 | Wrong format |
| Clean JSON (no trailing text) | 2,000 | Messy LINK/AMBIENT output |
| COMPILE (wiki page updates) | 3,000 | New signal |
| LINT (issue detection) | 2,000 | New signal |
| COMPILE_ANSWER (answer → wiki) | 1,000 | New signal |
| **Total** | **16,000** | |

**Training:** 3 epochs, RunPod A100, ~2 hours (estimated)
**Cost:** ~$2-3 (training) + ~$20 (data generation via OpenAI)

### Quality Targets
| Metric | v1.2 | v1.3 Target |
|---|---|---|
| Extract faithfulness | 70% | 95%+ |
| Answer has Sources section | 50% | 100% |
| Answer has Follow-ups | 50% | 100% |
| Answer has bold formatting | 0% | 90%+ |
| LINK clean JSON | 0% (trailing text) | 95%+ |
| Answer length | 317 words | 350+ words |
| New: COMPILE works | N/A | 85%+ |
| New: LINT works | N/A | 85%+ |

---

## v1.4 — April 9, 2026 (COMPLETE)

**Data:** 82,314 filtered examples (v1.3 data + 7K faithful_extract + 2K formatted_answer + 2K clean_json)
**Signals:** 19 task types (same as v1.3)
**Training:** 3 full epochs, RunPod A100, ~10 hours, 29,325 steps
**Cost:** ~$15 (training) + ~$20 (data generation)
**Changes:**
- 8,000 faithful extraction examples (fix hallucination)
- 5,000 formatted answer examples (bold + sources + followups)
- 4,000 clean JSON examples (no trailing text)
**Deployed:** Google Cloud Mumbai (34.47.236.12:8000, static IP)

### v1.4 Benchmark Results
| Signal | Score | vs Groq |
|---|---|---|
| Intent | 4/5 | TIE |
| Sentiment | 3/5 | Groq wins (4/5) |
| Extract names | 100% faithful | TIE |
| Extract numbers | 73% faithful | Groq slight edge |
| Answer quality | Excellent (bold, citations, sources, followups) | Rabbit wins |
| Answer latency | 38s | Groq wins (2s) — FIX WITH vLLM |
| Linking | 3/4 correct, 0 false positive | Rabbit only |
| Ambient | 2/2 correct | Rabbit only |
| Simple signal latency | 240ms | Rabbit wins (Groq 600ms) |

---

## v1.5 — PLANNED (Continuous Training)

**New training data target: 50,000 additional examples**
**Total after v1.5: ~132,000 filtered examples**

### What v1.5 Fixes
| Issue | Data Needed | Priority |
|---|---|---|
| Sentiment edge cases (neutral/tense) | 3,000 targeted sentiment examples | HIGH |
| Number hallucination ($, ₹, %) | 3,000 number-heavy extraction examples | HIGH |
| Intent confusion (synthesis vs aggregation) | 1,000 intent examples | MEDIUM |
| Longer, richer answers | 5,000 answer examples (500+ words) | MEDIUM |
| Real-world messiness | Process 5K NexusAI memories into training pairs | HIGH |
| Enron emails | 15,000 real corporate email examples | MEDIUM |
| GitHub issues | 10,000 real team discussion examples | MEDIUM |
| More compile/lint examples | 5,000 wiki signal examples | MEDIUM |
| User feedback (when available) | Ongoing from production | FUTURE |

### Training approach
- Generate 50K in parallel on CPU pod while other work continues
- Train v1.5 when data is ready (~1 week)
- Monthly retraining cycle from this point forward

---

## v2.0 — April 13–14, 2026 (COMPLETE)

**Base:** Qwen 2.5 32B Instruct (Apache 2.0, ~10× larger than Phi-3.5)
**Method:** QLoRA r=32 α=32 via Unsloth, 4-bit base, bf16 training
**Data:** **90,049 examples** (82,314 v1.4 filtered + 4,000 real meeting datasets from HF + 3,735 real SEC 10-K extractions)
**Signals:** 19 task types (same surface as v1.4, but trained on bigger base with more real-world documents)
**Hardware:** 1× H100 80GB SXM on RunPod (upgraded from A100 mid-session)
**Training:** 1 epoch, batch=1 grad_accum=16 (effective 16), seq=2048, LR=1e-4
**Wall-clock:** ~26 hours end-to-end (11,032 steps @ ~6.9s/step + setup + upload)
**Cost:** ~$70 cash (H100 @ ~$2.69/hr)
**Output:** LoRA adapter only (1.1 GB) at [reattend/rabbit-v2.0](https://huggingface.co/reattend/rabbit-v2.0) on HuggingFace (private)

### Key decisions

- **LoRA-only shipping, no merged model.** The post-training merge hit a transformers 5.5 × Unsloth compatibility bug (`NotImplementedError` in `revert_weight_conversion`). Worked around by uploading only the LoRA adapter. This is actually the better architecture anyway — it enables per-org LoRA stacking in the future, keeps HF storage small, and avoids 4-bit merge rounding loss.
- **Qwen 32B over staying on Phi-3.5.** Phi-3.5 at 3.8B was too small for reliable extraction on long real-world documents. Qwen 32B is the minimum viable size for enterprise-grade organizational memory reasoning.
- **Real SEC 10-K filings in training data.** 3,735 chunks from 118 real annual reports (US tech, finance, healthcare, consumer, industrial, energy, Indian ADRs, UK/EU ADRs, Canadian dual-listed). This is the biggest quality jump over v1.x — the model has actually seen long real corporate language with real entities, real financials, real decisions.
- **HF dataset upload.** 90K examples stored at `reattend/rabbit-v2-training-data` (private, 145 MB). Never lose the training corpus again.

### Serving architecture (built April 14, 2026)

- **Platform:** GCP Compute Engine, `g2-standard-8` + 1× NVIDIA L4 24GB, Spot mode
- **Zone:** us-central1-a (first try, but stockout-prone — need zone-hop retry)
- **Baked image:** `rabbit-v2-20260414-1202` (family `rabbit-v2`) — pre-loaded with Qwen 32B 4-bit + Rabbit LoRA + Unsloth venv + FastAPI server + systemd units. Future VMs boot to a working Rabbit in ~90 seconds.
- **Inference:** Unsloth + 4-bit bnb, one FastAPI endpoint per signal, streaming via `TextIteratorStreamer`, verbose structured JSON logging per request.
- **CLI:** `rabbit wake/stop/status/extract/triage/...` — single bash wrapper around `gcloud` + `curl`, both developers share one bearer token.
- **Auto-stop:** systemd timer checks `/var/lib/rabbit/last_request` every 5 min, shuts down VM after 20 min idle.
- **First inference:** April 14, 2026 — "Pong! I'm here and ready" (42.6s load + gen time on L4, ~35s pure load).

### Blockers encountered

- Transformers 5.5 SFTTrainer API drift (`formatting_func` required → solved by pre-rendering text column).
- OOM on 2× A100 80GB at batch=2 seq=4096 (Unsloth free is single-GPU only → dropped to batch=1 seq=2048).
- Merge bug as noted above (shipped LoRA-only instead).
- GCP us-central1-a Spot L4 stockouts on first `rabbit wake` and again after first VM stop. **Takeaway: Spot churn eats flow state during R&D.** Pivoting to 24/7 RunPod Reserved L4 (~$195/mo cash) for M1 until Microsoft Founders Hub credits land, then switching back to always-on Azure on-demand funded by credit.

### Inference pattern

```python
from unsloth import FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="reattend/rabbit-v2.0",  # LoRA repo — base Qwen auto-resolved from adapter_config.json
    max_seq_length=2048,
    load_in_4bit=True,
    token=HF_TOKEN,
)
FastLanguageModel.for_inference(model)
```

Memory footprint: ~20 GB VRAM (fits on L4 24GB with headroom).

---

## Future Training Plans

### v2.1 — failure-driven retraining (continuous)

The verbose server logs (`/var/log/rabbit/server.log`) capture every request: prompt hash, signal, input/output tokens, latency, LoRA version, response preview, full traceback on errors. When Rabbit produces bad outputs in testing or demos, we grep the log by prompt_hash → collect failing cases → add to training data → retrain LoRA on RunPod (1-2 hrs, ~$15-30) → upload as `reattend/rabbit-v2.1` → `rabbit wake` picks up the new version on the next bake.

Target: one v2.X version every 2-4 weeks, driven by real failures not synthetic drills.

### v3.0 (Month 6+)

- DPO training from thumbs up/down preference pairs collected via Reattend UI
- Per-org LoRA adapters — each enterprise customer gets their own fine-tune on their corpus, stacked on base Rabbit v2.X
- 500K+ total training examples
- Expected: 10-20% quality jump from preference optimization + per-tenant alignment
