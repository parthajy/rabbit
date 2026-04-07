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

## Future Training Plans

### v1.4 (Month 2)
- First retrain from real user data (production feedback)
- Add Enron email + GitHub issue training data (real-world messiness)
- Expected: significant robustness improvement

### v2.0 (Month 3)
- DPO training from thumbs up/down preference pairs
- 500K+ total training examples
- Expected: 10-20% quality jump from preference optimization
