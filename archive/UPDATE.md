# Rabbit v1.1 → Reattend Integration Plan

## Current LLM Usage in Reattend vs Rabbit Replacement

| Task | Current Provider | Model | Rabbit Signal | Can Replace? | Phase |
|---|---|---|---|---|---|
| Triage (classify + extract) | Groq | llama-3.3-70b | [TRIAGE] + [EXTRACT] | YES | 2 |
| Intent Classification | Groq | llama-3.3-70b | [INTENT] | YES | 1 |
| Query Expansion | Groq | llama-3.3-70b | [EXPAND] | YES | 1 |
| Ask / Q&A | OpenAI | gpt-4o-mini | [ANSWER] | YES | 2 |
| Linking (related memories) | Groq | llama-3.3-70b | Not trained yet | PARTIAL — needs [LINK] signal | 3 |
| Entity Profile Summary | Groq | llama-3.3-70b | [SUMMARIZE] | YES | 2 |
| Memory Compression | Groq | llama-3.3-70b | [SUMMARIZE] | YES | 2 |
| Weekly Digest | Groq | llama-3.3-70b | [ANSWER] | YES | 2 |
| Meeting Brief | Groq | llama-3.3-70b | [ANSWER] | YES | 2 |
| Ambient Recall | Groq | llama-3.3-70b | Not trained yet | PARTIAL — needs [AMBIENT] signal | 3 |
| Sentiment (NEW) | — | — | [SENTIMENT] | NEW FEATURE | 1 |
| Importance (NEW) | — | — | [IMPORTANCE] | NEW FEATURE | 1 |
| Don't Know | — | — | [DONTKNOW] | NEW FEATURE | 1 |
| Multi-turn | — | — | [MULTITURN] | NEW FEATURE | 2 |
| Embeddings | FastEmbed (local) | BGE-base | Keep as-is, bundle in API | NO CHANGE | — |
| Audio Transcription | AssemblyAI | Nano | Keep AssemblyAI | NO (not LLM) | — |

## Swap Phases

### Phase 1: Background tasks (zero user risk)
- Intent classification → [INTENT]
- Query expansion → [EXPAND]  
- Sentiment → [SENTIMENT] (new)
- Importance → [IMPORTANCE] (new)
- Entity profile summaries → [SUMMARIZE]

### Phase 2: Shadow test → swap
- Triage → [TRIAGE] + [EXTRACT]
- Ask/Q&A → [ANSWER]
- Weekly digest → [ANSWER]
- Meeting brief → [ANSWER]
- Memory compression → [SUMMARIZE]

### Phase 3: New signals needed
- Linking → train [LINK] signal
- Ambient Recall → train [AMBIENT] signal

## Code Change Required

In `src/lib/ai/llm.ts`, add Rabbit as first provider:
```
getLLM(): Rabbit → Groq → Ollama → error
getAskLLM(): Rabbit → OpenAI → Anthropic → Groq → Ollama
```

Rabbit serves OpenAI-compatible API format. Point to Rabbit server URL.

## Cost Comparison

| Provider | Current est. | After Rabbit |
|---|---|---|
| OpenAI | $50-150/mo | $0 |
| Groq | $20-50/mo | $0-5/mo |
| Anthropic | $30-80/mo | $0 |
| Rabbit server | — | $300/mo |
| Break-even | — | ~1,500 users |

## Training Data

| Version | Examples | Signals |
|---|---|---|
| v1 | 55,750 | 8 signals |
| v1.1 | 53,901 | 10 signals (+ multiturn, dontknow) |
| Total generated | ~115,000 | — |
