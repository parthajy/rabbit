# Rabbit — Master Document

> The proprietary memory AI for organizations. Built by Reattend.
> Single source of truth. All other docs (ROADMAP, UPDATE, V1.2_PLAN, LAUNCH_CHECKLIST) are archived.

---

## Current State (April 7, 2026)

### What's Live

| Component | Status | Location |
|---|---|---|
| Rabbit v1.2 (12 signals) | LIVE | Google Cloud Mumbai, 34.93.210.241:8000 |
| FastEmbed (embeddings) | LIVE | Bundled in Rabbit server |
| FastAPI server | LIVE | Port 8000, API key protected |
| Model weights backup | Safe | HuggingFace (reattend/rabbit-v1.2, private) |
| Training data + scripts | Safe | GitHub (parthajy/rabbit, private) |

### What's Not Live Yet

| Component | When | Effort |
|---|---|---|
| Cohere Transcribe (audio) | After v1.3 ships | 2 days |
| Jina Reranker (search quality) | After v1.3 ships | 1 day |
| ColPali (visual docs) | Month 3 | 2 days |
| BGE-M3 (multilingual embeddings) | Enterprise only | 1 day |

### The 12 Signals

| # | Signal | What It Does | When It Runs |
|---|---|---|---|
| 1 | INTENT | Classify query type (factual/entity/temporal/synthesis/actions/history/aggregation) | Query time |
| 2 | EXTRACT | Pull people, orgs, dates, decisions, action items, topics | Ingestion |
| 3 | TRIAGE | Classify content type + summary + tags | Ingestion |
| 4 | EXPAND | Turn vague queries into precise search | Query time |
| 5 | ANSWER | Conversational response with narrative, reasoning, citations, sources, follow-ups | Response |
| 6 | SUMMARIZE | Rich 2-4 sentence standalone summary | Ingestion |
| 7 | SENTIMENT | Tone: positive/negative/neutral/tense/urgent | Ingestion |
| 8 | IMPORTANCE | Score 1-5 with reason | Ingestion |
| 9 | MULTITURN | Follow-up questions with context from previous turn | Response |
| 10 | DONTKNOW | Graceful handling when memories don't answer | Response |
| 11 | LINK | Memory relationship detection (same_topic/contradicts/continuation_of/etc.) | Ingestion |
| 12 | AMBIENT | Contradiction/forgotten commitment detection from screen context | Real-time |

### Training History

| Version | Data | Signals | Status |
|---|---|---|---|
| v1.0 | 55,750 examples | 8 | Archived on HuggingFace |
| v1.1 | 53,901 examples | 10 | Archived on HuggingFace |
| v1.2 | 61,178 examples | 12 | **LIVE on Google Cloud** |
| v1.3 | ~77,000 examples (planned) | 12 | **NEXT — fixes quality gaps** |

---

## Known Quality Gaps (From Benchmark April 7)

Benchmark: Rabbit v1.2 vs Groq (llama-3.3-70b) vs OpenAI (gpt-4o-mini)

### What Rabbit Does Well
- Intent classification: 5/5 correct (better than OpenAI 4/5)
- Sentiment: Matches Groq and OpenAI
- Conversational tone in answers
- Faster than OpenAI on simple signals (500ms vs 1000ms)

### What Needs Fixing

| Problem | Example | Root Cause | Fix Type |
|---|---|---|---|
| **Hallucinated names** | "Sarcis" instead of "Sarah" | Training data + temperature too high | Immediate + Retrain |
| **Missing citations** | Answer without [1][2] inline | Inconsistent training examples | Retrain |
| **Missing Sources section** | Answer without "Sources:" block | Not enforced in training data | Retrain |
| **Missing Follow-up questions** | Answer without "Follow-up:" block | Not enforced in training data | Retrain |
| **Markdown code blocks** | Output wrapped in ```json | Model learned to add markdown | Immediate (strip) + Retrain |
| **Answer too short** | Similar length to Groq/OpenAI | Training examples not long enough | Retrain |
| **Answer latency** | 36 seconds vs Groq's 1.9s | Model size + no optimization | Immediate |
| **No formatting** | Plain text, no bold/structure | Trained with "no markdown" | Retrain |
| **Extract inconsistency** | Sometimes wraps in ```, sometimes not | Inconsistent training examples | Retrain |

---

## Immediate Fixes (No Retraining — Deploy Today)

### Server-Side Changes

1. **Per-signal temperature**
   - Intent, sentiment, importance: `temperature=0.01` (deterministic)
   - Extract, triage, link, ambient: `temperature=0.05` (minimal creativity)
   - Answer, summarize, expand, multiturn: `temperature=0.2` (conversational)

2. **Per-signal max_new_tokens**
   - Intent: 10 tokens
   - Sentiment: 10 tokens
   - Importance: 128 tokens
   - Extract, triage, link, ambient: 512 tokens
   - Summarize, expand: 256 tokens
   - Answer, multiturn, dontknow: 1024 tokens

3. **Post-processing**
   - Strip markdown code blocks (```json ... ```) from all outputs
   - Trim whitespace
   - For JSON signals: validate and re-parse output

4. **Enhanced system prompt for ANSWER**
   - Add: "You MUST include a 'Sources:' section listing each cited memory."
   - Add: "You MUST include a 'Follow-up questions:' section with 3 questions."
   - Add: "Use bold for key names and decisions. No headers or code blocks."

### Expected Impact
- Latency: 36s → 10-15s (via lower max_tokens for non-answer signals)
- Hallucination: Reduced (lower temperature)
- Formatting: Cleaner (post-processing strips markdown)
- Citations: More consistent (enhanced system prompt)

---

## Retraining Fixes (v1.3 — This Week)

### New Training Data

| Category | Count | What It Fixes |
|---|---|---|
| Answer with MANDATORY Sources + Follow-ups | 5,000 | Missing sections |
| Faithful extraction (exact names/numbers reproduction) | 3,000 | Hallucination |
| Longer narrative answers (4+ paragraphs, rich detail) | 3,000 | Short answers |
| Formatted answers (bold names, bold decisions, structured) | 3,000 | No formatting |
| Conversational follow-ups ("summarize last message", "tell me more") | 2,000 | Conversational queries |
| **Total new data** | **16,000** | |
| **Combined with v1.2 data** | **~77,000** | |

### Training Process
1. Generate 16K on RunPod CPU pod (~$1, ~4 hours)
2. Quality filter
3. Merge with v1.2 filtered data
4. Train on RunPod A100 (~$2, ~1-2 hours)
5. Upload to HuggingFace (reattend/rabbit-v1.3)
6. Update GCP server (change repo, restart)

### v1.3 Quality Targets

| Signal | Current | Target | How Measured |
|---|---|---|---|
| Intent accuracy | 100% (5/5) | Maintain | Auto-score vs expected |
| Sentiment accuracy | 80% (4/5) | 90%+ | Auto-score vs expected |
| Extract faithfulness | 70% (names garbled) | 95%+ | Manual check: no hallucinated entities |
| Answer has Sources section | ~50% | 100% | Check for "Sources:" in output |
| Answer has Follow-ups | ~50% | 100% | Check for "Follow-up" in output |
| Answer length | ~200 words | 300+ words | Word count |
| Answer has inline citations | ~70% | 95%+ | Check for [1][2] in output |
| Answer latency | 36 seconds | 10-15 seconds | API timing |

---

## Future Fixes (v1.4+ — After Swap)

### Engineering Features (No Retraining, Code in Reattend)

1. **Compile on Ingest**
   - When memory arrives, Rabbit updates pre-built entity/topic pages
   - 90% of queries become instant reads (10ms vs seconds)
   - Uses existing EXTRACT + SUMMARIZE + LINK signals
   - Effort: 1 week

2. **Answers Become Knowledge**
   - Great synthesized answers saved as compiled memories
   - Same question never recomputed
   - Knowledge compounds with every interaction
   - Effort: 2 days

3. **Lint Pass (Self-Healing Knowledge Base)**
   - Daily 2AM cron: scan for contradictions, stale info, missing links, orphans
   - Uses existing AMBIENT + LINK + ANSWER signals
   - Zero human maintenance
   - Effort: 1 week

### Additional Models on Same Server

| Model | What | VRAM | When |
|---|---|---|---|
| Jina Reranker (137M) | Re-rank search results for better retrieval | 500MB | Month 2 |
| Cohere Transcribe (2B) | Audio → text (replaces AssemblyAI) | 4GB | Month 2 |
| ColPali (3B) | Visual doc understanding (PDFs, slides) | 3GB | Month 3 |
| BGE-M3 (567M) | Multilingual embeddings | 1GB | Enterprise only |

Total VRAM after all: ~13GB / 16GB available on T4.

### Automated Retraining Flywheel

```
Users interact with Rabbit
  → Thumbs up/down on answers
  → Logged as training data
  → Monthly: collect positive examples + DPO pairs
  → Retrain on RunPod (~$2, ~1 hour)
  → Deploy to GCP (5 min swap)
  → Better model
  → Better answers
  → More trust
  → More usage
  → More data
  → Repeat
```

---

## What Rabbit Replaces in Reattend

| Task | Was (Provider) | Now (Rabbit) | Swap Phase |
|---|---|---|---|
| Intent classification | Groq llama-3.3-70b | [INTENT] | Phase 1 (easy, background) |
| Query expansion | Groq | [EXPAND] | Phase 1 |
| Sentiment (NEW) | — | [SENTIMENT] | Phase 1 |
| Importance (NEW) | — | [IMPORTANCE] | Phase 1 |
| Entity profile summaries | Groq | [SUMMARIZE] | Phase 2 (shadow test) |
| Triage + extraction | Groq | [TRIAGE] + [EXTRACT] | Phase 2 |
| Ask / Q&A | OpenAI gpt-4o-mini | [ANSWER] | Phase 2 |
| Weekly digest | Groq | [ANSWER] | Phase 2 |
| Meeting brief | Groq | [ANSWER] | Phase 2 |
| Memory compression | Groq | [SUMMARIZE] | Phase 2 |
| Memory linking | Groq | [LINK] | Phase 3 |
| Ambient recall | Groq | [AMBIENT] | Phase 3 |
| Embeddings | FastEmbed (local) | FastEmbed (bundled) | No change |
| Audio transcription | AssemblyAI | Cohere Transcribe (future) | Month 2 |

---

## Execution Plan (Updated April 7)

### TODAY: Immediate Server Fixes

| # | Task | Time |
|---|---|---|
| 1 | Update server: per-signal temperature + max_tokens | 1 hour |
| 2 | Add post-processing (strip markdown, validate JSON) | 1 hour |
| 3 | Enhance ANSWER system prompt (mandatory Sources + Follow-ups) | 30 min |
| 4 | Re-run benchmark to measure improvement | 1 hour |
| 5 | Set up systemd auto-restart on GCP | 30 min |

### THIS WEEK: Generate v1.3 Data + Retrain

| # | Task | Time |
|---|---|---|
| 6 | Generate 16K targeted training examples on RunPod CPU | 4-6 hours (overnight) |
| 7 | Quality filter | 1 hour |
| 8 | Train v1.3 on RunPod A100 | 1-2 hours, ~$2 |
| 9 | Deploy v1.3 to GCP, re-benchmark | 1 hour |
| 10 | Verify all quality targets met | 1 hour |

### NEXT WEEK: Swap + Landing Page

| # | Task | Time |
|---|---|---|
| 11 | Phase 1 swap in Reattend (intent, sentiment, importance, expand) | 1 day |
| 12 | Shadow test Phase 2 (answer, triage, extract) | 3 days |
| 13 | Build rabbit.reattend.com landing page with benchmarks | 2 days |
| 14 | Add feedback logging (thumbs up/down) | 1 day |

### MONTH 1: Full Swap + Enterprise

| # | Task | Time |
|---|---|---|
| 15 | Full swap: all signals to Rabbit, Groq as fallback only | 1 day |
| 16 | Compile on ingest (entity pages) | 1 week |
| 17 | Answers become knowledge | 2 days |
| 18 | Lint pass (self-healing KB) | 1 week |
| 19 | Publish "How We Built Rabbit" blog | 2 days |
| 20 | Create MemoryBench (public benchmark dataset) | 3 days |
| 21 | Apply to incubators (Google Accelerator, YC, NASSCOM, 100X.VC) | 2 days |

### MONTH 2: Scale + Revenue

| # | Task | Time |
|---|---|---|
| 22 | First monthly retrain from real user data | 1 day |
| 23 | Add Cohere Transcribe + Jina Reranker to server | 3 days |
| 24 | Rabbit Python SDK | 3 days |
| 25 | First enterprise pilot (free, for case study) | 1 week |

### MONTH 3: Enterprise Revenue

| # | Task | Time |
|---|---|---|
| 26 | Docker image for on-prem deployment | 3 days |
| 27 | First paying enterprise customer | 2 weeks |
| 28 | DPO training from feedback pairs | 3 days |
| 29 | Rabbit v2 (trained on real production data) | 1 week |

---

## Benchmarking Strategy

### Internal (We Do It)

Python script sends identical queries to Rabbit, Groq, OpenAI. Human scoring for complex signals, auto-scoring for simple ones.

**Already built:** `scripts/benchmark.py` — 50 test cases across all signals.

### Third-Party Validation (Month 2-3)

| Platform | What | Cost |
|---|---|---|
| HuggingFace Open LLM Leaderboard | General model benchmarks | Free |
| LMSys Chatbot Arena | Blind human preference | Free |
| MemoryBench (we create it) | Memory-specific benchmark we publish | Free |
| Customer testimonials | Real-world validation | Free |

### MemoryBench: Own the Category

We publish a benchmark dataset:
- 500 test cases: extraction, triage, linking, Q&A, contradiction detection
- Any model can be tested against it
- Rabbit wins because we trained for it
- Other companies compete on OUR terms

---

## Enterprise Strategy

### The Pitch

> "Your organization makes 10,000 decisions a month. How many are remembered? Rabbit runs on your server, captures every decision, detects contradictions, and answers any question with cited sources. Nothing leaves your firewall."

### Target Verticals

| Vertical | Why | Deal Size |
|---|---|---|
| Banking / Financial Services | Compliance, audit trails | $100-200K/year |
| Law Firms | Case history, precedent recall | $50-100K/year |
| Consulting | Project knowledge retention | $50-100K/year |
| Large Tech | Engineering decision logs, on-prem requirement | $100-200K/year |
| Pharma / Healthcare | Clinical trial decisions, documentation | $100-200K/year |

### Pricing

| Tier | Price | For |
|---|---|---|
| Reattend Free | $0 | Teams, unlimited (powered by Rabbit) |
| Rabbit API Free | $0 | Developers, 1,000 calls/month |
| Rabbit API Pro | $29/month | 50,000 calls/month |
| Rabbit API Team | $99/month | 500,000 calls/month |
| Rabbit On-Prem | $50-200K/year | Enterprise, Docker image |

### What Enterprise Gets

```
One Docker container:
  Rabbit LLM (3.8B, 4-bit)
  FastEmbed (embeddings)
  Cohere Transcribe (audio)
  Jina Reranker (search quality)
  FastAPI server
  
  docker run --gpus all -p 8000:8000 reattend/rabbit-server
  
  Client's data NEVER leaves this box.
```

---

## Developer Community Strategy

### The Hook: MCP Server for Cursor/Claude

```
Developer coding in Cursor
  → "What was the auth architecture decision?"
  → Cursor calls Rabbit MCP → retrieves org memory
  → Developer gets cited answer while coding
```

### Developer Marketing

1. Blog: "How We Built a Memory LLM in 3 Days for $100" → HN, Dev.to
2. Open-source training scripts (NOT weights/data)
3. Python + TypeScript SDKs
4. Discord community
5. "Built with Rabbit" showcase

---

## Financial Summary

### Costs

| Item | Monthly |
|---|---|
| Google Cloud (T4 Spot, Mumbai) | $127 |
| Reattend hosting | $20 |
| Monthly retrain (RunPod) | $2 |
| Misc (domains, etc.) | $10 |
| **Total** | **~$160** |

### Revenue Targets

| Month | Revenue | Source |
|---|---|---|
| 1 | $0 | Benchmarking + swap + landing page |
| 2 | $500 | 1-2 API customers |
| 3 | $2,000 | 5 API customers |
| 4 | $5,000 | 10 API + 1 enterprise pilot |
| 6 | $15,000 | 20 API + 1 paying enterprise |
| 12 | $50,000 | 50 API + 3 enterprise |

### Unit Economics

```
Break-even: 1 API customer at $500/month (covers $160 costs)
Gross margin at scale: 98%+
Enterprise on-prem: 88% margin ($50K revenue, ~$6K support cost)
```

---

## Competitive Landscape

| | Rabbit | Glean | Notion AI | Cohere |
|---|---|---|---|---|
| Owns the model | **YES** | No | No | Yes |
| Auto-captures memories | **YES** | Partial | No | No |
| Memory graph | **YES** | No | No | No |
| On-prem | **YES** | No | No | Yes |
| Offline capable | **YES** | No | No | N/A |
| Memory-specialized | **YES (12 signals)** | No | No | No |
| Self-healing KB | **YES (lint pass)** | No | No | No |
| Data flywheel | **YES** | No | No | Partial |

---

## Legal: Proprietary vs Open-Source

| Component | License | Proprietary? |
|---|---|---|
| Phi-3.5 Mini (base) | MIT | Base is open, our fine-tuned weights are OURS |
| Our LoRA weights | 100% ours | YES — never publish |
| Our training data | 100% ours | YES — never publish |
| 12-signal architecture | 100% ours | YES — trade secret |
| Cohere Transcribe | Apache 2.0 | Open, free commercial use |
| FastEmbed / nomic | Apache 2.0 | Open, free commercial use |
| Jina Reranker | Apache 2.0 | Open, free commercial use |

---

## The Story

> "Every AI system in the world has amnesia. ChatGPT forgets. Copilot forgets. Your organization's collective intelligence degrades every day.
>
> We built Rabbit — a proprietary AI that doesn't just store memories. It extracts decisions, detects contradictions, links context, and reasons over your team's entire history. 12 signals, one model, one server.
>
> It runs on-premise. Nothing leaves your firewall. And it gets smarter with every interaction.
>
> We built this in 3 days for $100. We're building the memory layer for the AI era."

---

*Last updated: April 7, 2026*
*Rabbit v1.2 live — v1.3 quality fixes in progress*
*Next: immediate server fixes → v1.3 retrain → swap → landing page → enterprise*
