# Rabbit Training Journey

Living document tracking the training of the Rabbit memory model — decisions, dead-ends, wins, and what's next.

---

## Vision

Rabbit is a proprietary organizational memory LLM. It replaces all third-party AI providers (Groq, OpenAI, Claude) with a single model we own, can deploy on-prem to banks / law firms / healthcare, and that powers Reattend.

**Target deployment**: 1 instance each in India, USA, and EU. Become the default memory layer for organizations that cannot let data leave their perimeter.

---

## Model history

### v1.0–v1.5 — Phi-3.5 Mini (3.8B)
- Base: `microsoft/Phi-3.5-mini-instruct`
- Method: LoRA r=16 via Unsloth
- Data: ~40K → 82K examples across v1.0–v1.5
- Outcome: **Too small.** Weak extraction quality on long docs, poor JSON discipline, hallucinated entities under load.
- Decision (2026-04-08): abandon Phi, upgrade to Qwen 2.5 32B.

### v2.0 — Qwen 2.5 32B (trained 2026-04-13 → 2026-04-14)
- Base: `Qwen/Qwen2.5-32B-Instruct`
- Method: QLoRA r=32 α=32 via Unsloth, 4-bit base
- Data: **90,049 examples** (82K existing + 4K real meeting datasets + 3.7K real annual reports)
- Hardware: 1× H100 80GB SXM on RunPod (got upgraded from A100)
- Config: 1 epoch, batch=1, grad_accum=16 (effective 16), seq=2048, bf16, LR=1e-4
- Wall-clock: **~26 hrs** end-to-end (11,032 steps @ ~6.9s/step + setup + upload)
- Cost: **~$70** (H100 @ ~$2.69/hr)
- Output: LoRA adapter only at [reattend/rabbit-v2.0](https://huggingface.co/reattend/rabbit-v2.0) on HuggingFace (private, 1.1 GB adapter + tokenizer)
- **Shipping decision: LoRA-only, no merged model.** Merge step hit a transformers 5.5 × Unsloth compatibility bug (`NotImplementedError` in `revert_weight_conversion`). Worked around by uploading only the LoRA adapter, which is how we want to deploy anyway (swap adapters per customer for future per-org fine-tunes, smaller HF storage, no 4-bit merge rounding loss).

### Inference pattern for v2.0
Load base Qwen + LoRA adapter together at serve time. Unsloth auto-resolves base from `adapter_config.json`:

```python
from unsloth import FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="reattend/rabbit-v2.0",  # LoRA repo
    max_seq_length=2048,
    load_in_4bit=True,
)
FastLanguageModel.for_inference(model)
```

Memory footprint: ~20 GB VRAM, same as merged 4-bit.

---

## Data corpus (90K total)

| Source | Count | Notes |
|---|---|---|
| Existing v1.x filtered | 82,314 | 19 jsonl files covering all 12 signals |
| BillSum + GovReport + DialogSum | 4,000 | Public domain, via HF datasets |
| Real SEC 10-K filings | 3,735 | 118 annual reports → chunked + gpt-4o-mini extraction |
| **Total** | **90,049** | Stored at `reattend/rabbit-v2-training-data` (HF private) |

**Signals covered**: TRIAGE, EXTRACT, SUMMARIZE, SENTIMENT, IMPORTANCE, INTENT, EXPAND, ANSWER, LINK, AMBIENT, MULTITURN, DONTKNOW, COMPILE, LINT

**Real document sources**:
- 103 SEC EDGAR companies (US tech, finance, healthcare, consumer, industrial, energy, Indian ADRs, UK/EU ADRs, Canadian dual-listed)
- 40 user-supplied real company files (via Dropbox)
- BillSum (Congressional bills)
- GovReport (government reports)
- DialogSum (dialogue summarization)

---

## What went wrong (and how we fixed it)

### Infrastructure / data pipeline
1. **Python 3.9 `dict | None` syntax error on CPU pods** → sed-fixed to `-> dict`
2. **OpenAI API key not persisting across subprocess / new web terminals** → persisted to `/root/.openai_env`, sourced in `.bashrc`
3. **urllib SSL issues on Python 3.8** → switched to `requests` for realistic content generation
4. **pandas circular import on Python 3.13** → force-reinstalled `datasets pandas pyarrow six` on Python 3.10
5. **AMI Corpus + QMSum datasets failed to load** → dropped them, kept BillSum + GovReport + DialogSum (still hit 4K target)
6. **CPU pod hung for 3+ hrs (294 examples stuck)** → root cause was env var loss on new terminal; fixed with persistent env + nohup
7. **SSH key permission denied on pod** → never got working; used RunPod web terminal + Dropbox/HF transfers
8. **HF upload `RepositoryNotFoundError`** → old token was read-only; user provided write token

### Training pipeline (ongoing)
1. **PyArrow `cannot mix struct and non-struct values`** — some examples had dict output, others string. Patched `format_for_chat()` to JSON-serialize dict/list outputs.
2. **Script run from wrong directory (`//scripts/...`)** → always `cd /workspace/rabbit && ...`
3. **`fp16=True` on A100** → A100 uses bfloat16 natively. Changed to `bf16=True`.
4. **TRL 0.24 SFTTrainer API drift — `formatting_func` required** → spent significant time on this. Final fix: drop `formatting_func` entirely, pre-render dataset to a `text` column via `dataset.map(apply_chat_template)`.
5. **OOM on 2× A100 80GB at batch=2 seq=4096** → Unsloth free tier is **single-GPU only**, so GPU 1 was idle the whole time. Wasting ~$2/hr on unused GPU.

---

## Key decisions

### 2026-04-08 — Phi-3.5 → Qwen 2.5 32B
Phi-3.5 at 3.8B was too small for the extraction quality enterprise customers need. Qwen 2.5 32B is the minimum viable size for reliable multi-entity extraction + reasoning. Chose 32B over 7B/14B because enterprise reliability > training cost.

### 2026-04-10 — Rabbit as core infra product
Rabbit is the proprietary LLM + memory layer we sell to enterprises. Reattend is the SaaS built on top. (See memory: project_strategic_pivot.md)

### 2026-04-12 — LoRA averaging rejected
Considered splitting 90K into 3 stratified shards × 3 pods to train in parallel and LoRA-soup the results. Rejected: even a 1-3% quality hit is too much when betting on enterprise reliability. Quality > parallelism.

### 2026-04-13 — Single 1× A100 80GB overnight run
Picked Option E (stay on Unsloth, downsize to 1× A100, run longer) over Axolotl/LLaMA-Factory multi-GPU because:
- Unsloth kernels are ~2× faster per-GPU than Axolotl, so single-GPU Unsloth ≈ dual-GPU Axolotl on wall-clock
- Zero risk of new framework bugs (already debugged Unsloth path fully)
- Same final quality as any ZeRO-3 setup — just slower wall-clock
- Fits $50 budget comfortably (~$35)

---

## Training config (v2.0 final)

```python
BASE_MODEL = "Qwen/Qwen2.5-32B-Instruct"
LOAD_IN_4BIT = True
LORA_R = 32
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
EPOCHS = 2
BATCH_SIZE = 1
GRADIENT_ACCUMULATION = 16  # effective batch = 16
LEARNING_RATE = 1e-4
MAX_SEQ_LENGTH = 2048
WARMUP_RATIO = 0.05
PRECISION = "bf16"
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
GRADIENT_CHECKPOINTING = "unsloth"
```

---

## TODO

### Now
- [ ] Kill 2× A100 pod (burning money on idle GPU 1)
- [ ] Spin up 1× A100 80GB pod
- [ ] Apply batch=1 / grad_accum=16 / seq=2048 patch
- [ ] Start training in background via nohup
- [ ] Sleep, wake up, verify loss curve

### After training
- [ ] Download LoRA adapter + merged 4-bit model
- [ ] Upload to `reattend/rabbit-v2.0` on HuggingFace
- [ ] Benchmark v2.0 vs v1.5 on held-out eval set
- [ ] Deploy to Rabbit API server (replace Phi-3.5)
- [ ] Update `rabbit/core/llm.py` to use Qwen tokenizer
- [ ] Test Reattend.com end-to-end with new model
- [ ] Kill training pod

### v2.1 backlog
- [ ] Collect real user failures from production and add to training set
- [ ] Longer context training (8K+) once base model is proven
- [ ] Multi-turn conversation improvements
- [ ] Deploy first on-prem instance (target: India region)

---

## Cost ledger

| Item | Estimated | Actual |
|---|---|---|
| CPU pod (data generation) | $5 | ~$8 |
| 2× A100 80GB (failed runs) | $0 | ~$12 |
| 1× A100 80GB (v2.0 training) | $35 | TBD |
| OpenAI API (gpt-4o-mini extractions) | $10 | ~$12 |
| **Total** | **~$50** | **TBD** |

---

## References

- **Training data**: `reattend/rabbit-v2-training-data` (HF dataset, private)
- **Model output**: `reattend/rabbit-v2.0` (HF model, private, TBD)
- **Base model**: `Qwen/Qwen2.5-32B-Instruct`
- **Unsloth**: https://github.com/unslothai/unsloth
- **Scripts**:
  - `scripts/finetune_qwen32b.py` — main training
  - `scripts/download_public_reports.py` — SEC EDGAR scraper
  - `scripts/download_meeting_datasets.py` — HF meeting datasets
  - `scripts/process_real_documents.py` — PDF/text → training examples
  - `scripts/generate_v2_realistic.py` — synthetic realistic corporate content
