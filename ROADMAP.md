# Rabbit — Roadmap

Reattend's proprietary AI model for organizational memory.

---

## The Stack (How It All Works)

```
Raw Signal (email, Slack, meeting, note, calendar)
  ↓
┌─────────────────────────────────────────────────────┐
│                 RABBIT MODEL (8 signals)             │
│                                                      │
│  [TRIAGE]     → What is this? Type + quick tags      │
│  [EXTRACT]    → People, orgs, dates, decisions,      │
│                 action items, topics                  │
│  [SUMMARIZE]  → Rich standalone summary              │
│  [SENTIMENT]  → Tone: positive/negative/neutral/     │
│                 tense/urgent                          │
│  [IMPORTANCE] → Score 1-5 + reason                   │
│  [LINK]       → Connect to related memories          │
│  [EXPAND]     → Turn vague query into precise search │
│  [INTENT]     → Classify query type                  │
│  [ANSWER]     → Conversational response with [1][2]  │
│                 citations from retrieved memories     │
└─────────────────────────────────────────────────────┘
  ↓
Stored: structured memory + embedding + graph edges
```

### The 8 Signals

| # | Signal | When | Input | Output |
|---|---|---|---|---|
| 1 | TRIAGE | Memory arrives | Raw text | type + quick summary + tags |
| 2 | EXTRACT | Memory arrives | Raw text | people, orgs, dates, decisions, actions, topics (JSON) |
| 3 | SUMMARIZE | Memory arrives | Raw text | Rich 2-4 sentence standalone summary |
| 4 | SENTIMENT | Memory arrives | Raw text | One word: positive, negative, neutral, tense, urgent |
| 5 | IMPORTANCE | Memory arrives | Raw text | Score 1-5 + one-line reason |
| 6 | INTENT | User searches | User query | One word: factual, entity, temporal, synthesis, actions, history, aggregation |
| 7 | EXPAND | User searches | Vague query | Precise expanded search query |
| 8 | ANSWER | After retrieval | Query + memories | Conversational answer with [1][2][3] citations, no markdown |

Signals 1-5 run at **ingestion time** (async, not blocking).
Signals 6-7 run at **query time** (must be fast, <500ms).
Signal 8 runs at **response time** (user-facing, must be good).

---

## Architecture

```
┌─────────────────────────────────────┐
│         RABBIT SERVER               │
│         (GPU, proprietary)          │
│                                     │
│  ┌──────────┐  ┌──────────────┐    │
│  │ Rabbit   │  │ fastembed    │    │
│  │ Model    │  │ (embeddings) │    │
│  │ (8 tasks)│  └──────────────┘    │
│  └──────────┘                       │
│                                     │
│  API: /v1/chat/completions          │
│       /v1/embeddings                │
│       (OpenAI-compatible format)    │
└──────────────┬──────────────────────┘
               │ HTTPS (internal)
               │
┌──────────────┴──────────────────────┐
│         WEB APP SERVER              │
│         (regular server)            │
│                                     │
│  ┌──────────┐  ┌──────────────┐    │
│  │ Reattend │  │ Database     │    │
│  │ Web App  │  │ (Postgres +  │    │
│  │ (Next.js)│  │  Vector DB)  │    │
│  └──────────┘  └──────────────┘    │
│                                     │
│  User-facing: app.reattend.com      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         TRAY / DESKTOP APP          │
│         (ships to user's machine)   │
│                                     │
│  ┌──────────────────────────────┐  │
│  │ Rabbit (quantized, 4-bit)    │  │
│  │ ~2.5GB download after install│  │
│  │ Runs locally on CPU          │  │
│  │ + fastembed bundled          │  │
│  └──────────────────────────────┘  │
│                                     │
│  100% offline capable               │
│  Syncs with cloud when connected    │
└─────────────────────────────────────┘
```

**Rabbit Server** = proprietary brain. Weights never leave our control.
**Web App** = stateless. Sends text, gets answers. Doesn't know how AI works.
**Tray App** = ships quantized Rabbit (~2.5GB). Everything runs locally. No internet needed.
**Enterprise** = give them Rabbit Server as docker image. Runs inside their firewall. $50k-200k/year.

---

## Training Data Plan — 100,000 Examples

### Current State (April 2026)

| Task | Seeds | Synthetic | Filtered | Status |
|---|---|---|---|---|
| Intent | 2,428 | 1,000 | 3,367 | Done |
| Extract | 5 | 855 | 776 | Needs more |
| Triage | 5 | 926 | 515 | Needs more |
| Expand | 10 | 2,000 | 1,149 | Needs more |
| Answer | 5 | 351 | 161 | Needs much more |
| Summarize | — | — | — | New signal |
| Sentiment | — | — | — | New signal |
| Importance | — | — | — | New signal |
| **Total** | | | **5,968** | |

### Target: 100,000 Clean Examples

| Source | Volume | Cost | Tasks It Feeds |
|---|---|---|---|
| **Enron Email Dataset** | 30,000 | Free | extract, triage, summarize, sentiment, importance |
| **GitHub Issues/PRs** | 15,000 | Free | extract, triage, summarize, intent, expand |
| **AMI + ICSI Meeting Corpus** | 5,000 | Free | extract, triage, summarize, answer |
| **Reddit (workplace subs)** | 10,000 | Free | expand, intent, answer (filtered) |
| **Synthetic (GPT-4o-mini)** | 40,000 | ~$60-80 | all 8 tasks, universe-based |
| **Total** | **100,000** | **~$70** | |

### Per-Task Targets

| Task | Target | Source Mix |
|---|---|---|
| Intent | 10,000 | 3,367 existing + synthetic + Reddit |
| Extract | 15,000 | Enron + GitHub + AMI + synthetic |
| Triage | 10,000 | Enron + GitHub + AMI + synthetic |
| Expand | 15,000 | Synthetic + Reddit + GitHub |
| Answer | 15,000 | Synthetic + AMI (hardest task, needs most care) |
| Summarize | 15,000 | Enron + GitHub + AMI + synthetic |
| Sentiment | 10,000 | Enron + Reddit + synthetic |
| Importance | 10,000 | Enron + GitHub + synthetic |
| **Total** | **100,000** | |

---

## Dataset Details

### Enron Email Dataset (30,000 examples)
- 500,000+ real corporate emails, legally public (released in FERC investigation)
- Email threads with replies, forwards, CC chains
- Real people, real decisions, real organizational dynamics
- Perfect for: extract (pull out people, dates, decisions), triage (classify email threads), summarize, sentiment
- Download: https://www.cs.cmu.edu/~enron/

### GitHub Issues/PRs (15,000 examples)
- Public repos with active discussions
- Issues = bug reports, feature requests, decisions
- PRs = code reviews, technical discussions, approvals
- Real team dynamics: assignments, deadlines, blockers, follow-ups
- Perfect for: extract, triage, intent, expand

### AMI + ICSI Meeting Corpus (5,000 examples)
- Real recorded meetings with human-written summaries
- AMI: ~170 meetings (scenario-based team meetings)
- ICSI: ~75 meetings (academic research meetings)
- Includes speaker labels, topics, decisions
- Perfect for: extract, triage, summarize, answer

### Reddit Workplace Subs (10,000 examples)
- r/projectmanagement, r/startups, r/consulting, r/ExperiencedDevs
- How people describe work situations, ask for advice
- Good for understanding vague queries and workplace language
- Needs heavy filtering — only take posts that look like real org memory
- Perfect for: expand (vague query understanding), intent

### Synthetic Generation (40,000 examples)
- Universe-based: 10 fictional orgs with consistent characters
- Diverse memory sources: meetings, Gmail, Slack, standups, calendar, CRM, voice memos
- Connected examples: follow-ups, contradictions, decision evolution
- Generated via GPT-4o-mini (~$60-80 for 40K)
- Fills gaps in all 8 tasks, especially answer + new signals

---

## Execution Phases

### Phase 1: Data at Scale (Now → 2 weeks)

- [ ] Add 3 new signals to training pipeline (summarize, sentiment, importance)
- [ ] Download and process Enron email dataset → 30,000 examples
- [ ] Process GitHub Issues from public repos → 15,000 examples
- [ ] Download and process AMI + ICSI meeting corpus → 5,000 examples
- [ ] Process Reddit workplace subs → 10,000 examples
- [ ] Scale synthetic generation → 40,000 examples
- [ ] Run quality filter on everything
- [ ] Target: 100,000 clean training examples

### Phase 2: Fine-tune Rabbit v1 (Week 3)

- [ ] Fine-tune Phi-3.5 Mini on RunPod A100 (~$15-20, 6-8 hours)
- [ ] All 8 signals, single model, prompt prefix routing
- [ ] Export GGUF (4-bit quantized) for Ollama/local deployment
- [ ] Evaluate against current Groq/OpenAI on 100 held-out test cases per task
- [ ] Iterate if quality gap > 20% on any task

### Phase 3: Shadow Deploy (Week 4)

- [ ] Deploy Rabbit v1 on GPU server ($300/month)
- [ ] Run alongside Groq — both process every query, log both outputs
- [ ] Compare quality on real user queries
- [ ] Fix systematic failures
- [ ] Build the memory linking engine (graph-based relationships)

### Phase 4: Swap + Flywheel (Week 5-6)

- [ ] Route easy tasks first (intent, triage, extract, summarize, sentiment, importance) → Rabbit
- [ ] Keep answer + expand on Groq as fallback until quality matches
- [ ] Start collecting user feedback (thumbs up/down on answers)
- [ ] Log all queries and responses for v2 training data
- [ ] The flywheel begins: users generate training data by using the product

### Phase 5: Rabbit v2 — Real Data (Month 2-3)

- [ ] Fine-tune on production user data (queries, memories, feedback)
- [ ] Implement DPO (Direct Preference Optimization) using thumbs up/down
- [ ] Full swap: all 8 tasks on Rabbit
- [ ] Disable Groq and OpenAI API keys
- [ ] Rabbit is now better than generic models for organizational memory

### Phase 6: The Moat (Month 3+)

- [ ] Continuous fine-tuning as data grows
- [ ] Memory linking improvements
- [ ] Rabbit becomes the Memory API — license to other companies
- [ ] Enterprise on-prem: ship Rabbit Server as docker image
- [ ] Tray app: bundle quantized Rabbit for offline use
- [ ] The flywheel compounds: more users → more data → better model → more users

---

## Quality Benchmarks

| Task | Minimum for v1 | Target for v2 |
|---|---|---|
| Intent classification | >95% accuracy | >98% |
| Entity extraction | >85% F1 score | >92% |
| Triage classification | >90% type accuracy | >95% |
| Query expansion | >80% human eval "good" | >90% |
| Answer generation | >75% human eval "good or better" | >90% |
| Summarization | >80% human eval "captures essence" | >90% |
| Sentiment | >85% accuracy | >92% |
| Importance scoring | >80% within ±1 of human score | >90% |

---

## Cost Projections

### Training
| Item | Cost |
|---|---|
| Synthetic data generation (100K via GPT-4o-mini) | ~$70 |
| RunPod A100 fine-tuning (8 hours) | ~$16 |
| Evaluation runs | ~$5 |
| **Total training cost** | **~$90** |

### Production (Monthly)
| Users | OpenAI + Groq | Rabbit Server | Saving |
|---|---|---|---|
| 500 | ~$150 | $300 | -$150 (invest) |
| 2,000 | ~$600 | $300 | +$300 |
| 5,000 | ~$1,500 | $300 | +$1,200 |
| 20,000 | ~$6,000 | $600 (2 servers) | +$5,400 |

Break-even: ~1,500 users.

---

## What's Proprietary (Never Publish)

1. **Rabbit model weights** — the fine-tuned delta on top of Phi-3.5
2. **Training data** — seeds, processed datasets, synthetic examples
3. **Task architecture** — the 8-signal design and prompt templates
4. **Linking engine** — memory graph construction logic
5. **Production user data** — the flywheel data
6. **Evaluation benchmarks** — our quality standards and test cases

---

## The One-Line Vision

> Rabbit is the memory layer for the AI era — a proprietary model that understands, extracts, links, and recalls organizational knowledge, running entirely on infrastructure we own, getting smarter with every user.
