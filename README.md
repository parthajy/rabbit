# Rabbit

**Reattend's sovereign AI model for organizational memory.**

One fine-tuned model that replaces all OpenAI and Groq dependencies in Reattend. Rabbit understands, extracts, classifies, expands, and answers — all from a single set of weights running on our own infrastructure.

## What Is Rabbit?

Rabbit is a single fine-tuned small language model (Phi-3.5 Mini 3.8B) trained to do every AI task Reattend needs — classification, extraction, triage, query understanding, and answer generation — running on our own $300/month server. No per-token costs. No external data exposure. Fully owned.

**The flywheel:** More users → more memory data → better fine-tuning → better Rabbit → better product → more users. This is a compounding advantage that API wrappers can never build.

This is the prerequisite for:
- Reattend Memory API (other companies plug in our memory layer)
- Enterprise on-premise deployment
- Deep tech grant applications
- "Not a wrapper" investor positioning

---

## The 5 Tasks (One Model Does All)

Each task uses a different prompt prefix. Same model weights.

### 1. `[INTENT]` — Query Intent Classification
**Input:** User's natural language question
**Output:** One word from: `factual | entity | temporal | synthesis | actions | history | aggregation`
**Replaces:** Groq llama-3.3-70b intent classification call
**Latency target:** <500ms on CPU

```
Input:  "What did we discuss with Brian last week?"
Output: synthesis
```

### 2. `[EXTRACT]` — Entity & Fact Extraction
**Input:** Raw text (meeting transcript, note, email, Slack message)
**Output:** Structured JSON with people, organizations, decisions, action items, dates, topics
**Replaces:** Groq extraction call
**Latency target:** <3 seconds on CPU

```json
Input: "Met with Sarah from Acme on Tuesday. She agreed to send the contract by Friday.
        Budget confirmed at $45,000."

Output: {
  "people": ["Sarah"],
  "organizations": ["Acme"],
  "decisions": ["Budget confirmed at $45,000"],
  "action_items": [{"owner": "Sarah", "task": "Send contract", "due": "Friday"}],
  "dates": ["Tuesday"],
  "topics": ["contract", "budget"]
}
```

### 3. `[TRIAGE]` — Memory Classification & Summary
**Input:** Raw captured content (any format)
**Output:** Type + one-paragraph summary + tags
**Replaces:** Groq triage call
**Latency target:** <5 seconds on CPU (runs async, not real-time)

```
Input:  [raw meeting transcript or note]
Output: {
  "type": "meeting",
  "summary": "Discussion with Acme about Q2 contract. Sarah committed to $45k budget...",
  "tags": ["acme", "contract", "q2", "budget"]
}
```

### 4. `[EXPAND]` — Query Expansion & Understanding
**Input:** Short or vague user query
**Output:** Enriched, specific query that captures what the user actually means
**Replaces:** Groq query expansion call — THE MOST IMPORTANT TASK
**Latency target:** <2 seconds on CPU

```
Input:  "what about brian"
Output: "What has been discussed with Brian across all meetings and notes?
         Include decisions made, action items assigned, and recent interactions."
```

### 5. `[ANSWER]` — Conversational Q&A Over Memories
**Input:** User question + retrieved memory context (top N records)
**Output:** Conversational answer with citations [1][2][3], no markdown symbols
**Replaces:** OpenAI gpt-4o-mini final answer stream
**Latency target:** <15 seconds on CPU, <3 seconds on GPU

```
Input:  Question: "What did we decide about the Q2 launch?"
        Memories: [1] Meeting Mar 24... [2] Decision log Mar 18...
Output: "The Q2 launch was set for April 15 in the March 24 meeting [1].
         This confirmed the earlier decision on March 18 to target enterprise
         customers first [2]."
```

---

## Model Choice

**Primary: Phi-3.5 Mini Instruct (3.8B)**
- Microsoft open-source, commercially usable
- 4-bit quantized = ~2.5GB RAM
- Excellent at structured output and instruction following
- Fine-tunable with relatively small datasets

**Backup: Llama 3.2 3B Instruct (Meta)**
- Slightly faster inference
- Slightly weaker at structured tasks
- Use if Phi-3.5 quality is insufficient after fine-tuning

**Embeddings: Already solved**
- fastembed with nomic-embed-text-v1.5
- Already running in production on desktop and web server
- Do not change this

---

## Training Data Strategy

### Step 1 — Write Seed Examples (you do this)
100 real examples per task from actual Reattend usage. These are gold standard.

Files:
- `data/seeds/intent_seeds.jsonl` — 100 examples
- `data/seeds/extract_seeds.jsonl` — 100 examples
- `data/seeds/triage_seeds.jsonl` — 100 examples
- `data/seeds/expand_seeds.jsonl` — 100 examples
- `data/seeds/answer_seeds.jsonl` — 100 examples

Format for all files:
```jsonl
{"input": "...", "output": "..."}
{"input": "...", "output": "..."}
```

### Step 2 — Generate Synthetic Data via Claude API
Send seed examples to Claude with instruction: "Generate 500 more examples following the exact same format, quality, and diversity as these. Vary the topics, names, industries, and phrasing."

Target: 10,000 examples per task = 50,000 total
Cost: ~$50–80 total (Claude API)
Script: `scripts/generate_synthetic.py`

### Step 3 — Quality Filter
Automatically remove:
- Outputs that don't match expected format
- Duplicates (>90% string similarity)
- Examples where output length is an outlier

Target: keep 80% = ~40,000 clean examples

### Step 4 — Fine-tune
Tool: Unsloth (2x faster fine-tuning, 60% less VRAM)
Platform: RunPod A100 ($1.99/hr)
Time: ~6–8 hours
Cost: ~$15–20
Script: `scripts/finetune.py`

---

## Infrastructure

### Development / Testing
- RunPod GPU instance (pay per hour)
- Use for fine-tuning and initial quality testing
- Spin up, test, spin down

### Production
- **Server:** Hetzner or DigitalOcean GPU server, ~$300/month
- **Serving:** Ollama (simple) or vLLM (production, better batching)
- **API format:** OpenAI-compatible (`/v1/chat/completions`) so Reattend code changes are minimal
- **Fallback:** Groq stays in `.env` as emergency fallback, disabled by default

### Reattend Integration
The model server exposes the same interface as OpenAI. In `src/lib/ai/llm.ts`:
- `getPreProcessingLLM()` → points to our server instead of Groq
- `getAskLLM()` → points to our server instead of OpenAI
- One environment variable change: `OWN_MODEL_URL=http://your-server:11434`

---

## Rollout Plan

### Week 1 — Data
- [ ] Write 100 seed examples per task (500 total)
- [ ] Run `generate_synthetic.py` to produce 50,000 examples
- [ ] Review 200 random samples per task for quality

### Week 2 — Fine-tune
- [ ] Run fine-tuning on RunPod
- [ ] Evaluate against current Groq/OpenAI outputs on 100 test cases
- [ ] Iterate if quality gap is >20%

### Week 3 — Shadow Deploy
- [ ] Deploy model on $300 GPU server
- [ ] Run in shadow mode (parallel to Groq, log both outputs)
- [ ] Fix systematic failures

### Week 4 — Swap
- [ ] Route intent, extract, triage, expand → own model
- [ ] Monitor for 1 week
- [ ] Cut answer generation to own model if quality holds
- [ ] Disable Groq and OpenAI keys

---

## Quality Benchmarks (pass before swapping)

| Task | Minimum accuracy vs current |
|---|---|
| Intent classification | >95% match |
| Entity extraction | >85% F1 score |
| Memory triage | >90% type accuracy |
| Query expansion | Human eval: >80% "good" |
| Answer generation | Human eval: >75% "good or better than current" |

---

## Cost Comparison

| Users | OpenAI + Groq | Own model ($300 server) | Monthly saving |
|---|---|---|---|
| 500 | ~$150 | $300 | -$150 (invest phase) |
| 2,000 | ~$600 | $300 | +$300 |
| 5,000 | ~$1,500 | $300 | +$1,200 |
| 20,000 | ~$6,000 | $600 (2 servers) | +$5,400 |

Break-even: ~1,500 users.

---

## What This Enables (Beyond Cost)

1. **Memory API** — expose our model as an API. Other companies pay to use our memory infrastructure. First customer target: AI meeting tools, CRMs, project management apps.

2. **Enterprise on-premise** — ship the entire stack inside a client's firewall. Banks, law firms, hospitals. $50k–200k/year contracts. Impossible with OpenAI dependency.

3. **Deep tech positioning** — "We built and own a specialized AI model for memory extraction and retrieval, trained on the largest dataset of organizational memory in existence." Legitimate grant applications, higher valuation multiples.

4. **The flywheel** — more users → more memory data → better fine-tuning → better model → better product → more users.

---

## Repository Structure

```
reattend-model/
├── README.md                    ← this file
├── data/
│   ├── seeds/                   ← 100 hand-written examples per task
│   │   ├── intent_seeds.jsonl
│   │   ├── extract_seeds.jsonl
│   │   ├── triage_seeds.jsonl
│   │   ├── expand_seeds.jsonl
│   │   └── answer_seeds.jsonl
│   ├── synthetic/               ← Claude-generated, 50k examples
│   └── filtered/                ← quality-filtered, ready for training
├── scripts/
│   ├── generate_synthetic.py    ← calls Claude API to expand seeds
│   ├── quality_filter.py        ← removes bad examples
│   ├── finetune.py              ← Unsloth fine-tuning script
│   ├── evaluate.py              ← compare model vs Groq/OpenAI
│   └── serve.py                 ← local Ollama deployment helper
├── models/
│   └── .gitkeep                 ← model weights go here (gitignored)
├── evals/
│   └── test_cases.jsonl         ← 100 held-out test cases per task
└── deployment/
    ├── ollama_config.md         ← production server setup
    └── llm_ts_patch.md          ← exact changes needed in src/lib/ai/llm.ts
```

---

## The One-Line Vision

> Rabbit is the memory layer for the AI era — the same fine-tuned intelligence that powers individual recall, team knowledge, and organizational memory, running entirely on infrastructure we own.
