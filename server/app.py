"""
Rabbit API Server
Serves Rabbit v1.2 with 12 signals + FastEmbed embeddings.
OpenAI-compatible chat completions format.

Usage:
    python server/app.py
    # or with uvicorn:
    uvicorn server.app:app --host 0.0.0.0 --port 8000
"""

import json
import os
import time
from pathlib import Path

import torch
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

# ── Config ──────────────────────────────────────────────────────────────────

HF_TOKEN = os.environ.get("HF_TOKEN", "")
RABBIT_REPO = os.environ.get("RABBIT_REPO", "reattend/rabbit-v1.2")
API_KEY = os.environ.get("RABBIT_API_KEY", "rab_default_key_change_me")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

TASK_SYSTEM_PROMPTS = {
    "intent": "You are Rabbit, Reattend's memory AI. Classify the user's query intent. Respond with exactly one word: factual, entity, temporal, synthesis, actions, history, or aggregation.",
    "extract": "You are Rabbit, Reattend's memory AI. Extract structured information from the given text. Return a JSON object with keys: people, organizations, decisions, action_items, dates, topics.",
    "triage": "You are Rabbit, Reattend's memory AI. Classify and summarize the given content. Return a JSON object with keys: type, summary, tags.",
    "expand": "You are Rabbit, Reattend's memory AI. Expand the user's vague query into a precise, comprehensive search query that captures their likely intent.",
    "answer": "You are Rabbit, Reattend's memory AI. Answer the user's question conversationally. Tell a story with insight and reasoning. Use phrases like 'What's interesting is...', 'This suggests...', 'The pattern here is...'. Cite sources inline as [1][2][3]. Use **bold** for key names and decisions. You MUST end your response with exactly these two sections:\n\nSources:\n[1] Type, Date — Description\n[2] Type, Date — Description\n\nFollow-up questions:\n→ First question\n→ Second question\n→ Third question",
    "summarize": "You are Rabbit, Reattend's memory AI. Generate a rich 2-4 sentence standalone summary of the given content. Capture the essence, key decisions, and action items.",
    "sentiment": "You are Rabbit, Reattend's memory AI. Classify the tone of the given content. Respond with exactly one word: positive, negative, neutral, tense, or urgent.",
    "importance": "You are Rabbit, Reattend's memory AI. Score the importance of the given content for organizational memory. Return a JSON object with keys: score (1-5) and reason (one sentence).",
    "multiturn": "You are Rabbit, Reattend's memory AI. Continue the conversation, building on what was already discussed. Cite sources inline as [1][2][3]. Use **bold** for key names and decisions. You MUST end with Sources: and Follow-up questions: sections.",
    "dontknow": "You are Rabbit, Reattend's memory AI. Answer using the provided memories. If they don't fully answer the question, be honest about what's missing and suggest where to find it. Cite sources as [1][2][3]. Use **bold** for key names. You MUST end with Sources: and Follow-up questions: sections.",
    "link": 'You are Rabbit, Reattend\'s memory AI. Given a source record and candidate records, determine which candidates are meaningfully related. Return JSON with a links array. Each link: target_id, kind (same_topic/depends_on/contradicts/continuation_of/same_people/causes/temporal), weight (0-1), explanation. Max 8 links. If none related, return {"links": []}.',
    "ambient": 'You are Rabbit, Reattend\'s memory AI. You see what the user is doing (screen text) and related memories. Decide whether to alert. Return {"show": false} if no alert. Or {"show": true, "reason": "contradiction|forgotten_commitment|critical_context", "memory_indices": [1,2], "context": "explanation"} if they need to know. Only alert for genuine issues.',
}

SIGNAL_PREFIXES = {
    "intent": "[INTENT]",
    "extract": "[EXTRACT]",
    "triage": "[TRIAGE]",
    "expand": "[EXPAND]",
    "answer": "[ANSWER]",
    "summarize": "[SUMMARIZE]",
    "sentiment": "[SENTIMENT]",
    "importance": "[IMPORTANCE]",
    "multiturn": "[ANSWER]",
    "dontknow": "[ANSWER]",
    "link": "[LINK]",
    "ambient": "[AMBIENT]",
}

# ── Models ──────────────────────────────────────────────────────────────────

model = None
tokenizer = None
embed_model = None


def load_models():
    global model, tokenizer, embed_model

    print("Loading Rabbit v1.2...")
    from transformers import BitsAndBytesConfig
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    base = AutoModelForCausalLM.from_pretrained(
        "microsoft/Phi-3.5-mini-instruct",
        quantization_config=bnb_config,
        device_map="auto",
    )
    tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3.5-mini-instruct")

    print("Loading LoRA adapters...")
    model = PeftModel.from_pretrained(base, RABBIT_REPO, token=HF_TOKEN)
    model.eval()
    print(f"Rabbit loaded on {model.device}")

    print("Loading FastEmbed...")
    from fastembed import TextEmbedding
    embed_model = TextEmbedding(model_name="nomic-ai/nomic-embed-text-v1.5")
    print("FastEmbed loaded")

    print("\nRabbit API Server ready!")


# ── API Models ──────────────────────────────────────────────────────────────


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "rabbit-v1.2"
    messages: list[ChatMessage]
    max_tokens: int = 512
    temperature: float = 0.1
    signal: str | None = None  # Optional: explicitly set signal type


class EmbedRequest(BaseModel):
    input: str | list[str]
    model: str = "rabbit-embed"


class IngestRequest(BaseModel):
    content: str
    metadata: dict | None = None


class QueryRequest(BaseModel):
    question: str
    memories: list[dict] | None = None
    signal: str = "answer"


# ── Auth ────────────────────────────────────────────────────────────────────

security = HTTPBearer()


def verify_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials


# ── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(title="Rabbit API", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Per-signal optimal settings
SIGNAL_SETTINGS = {
    "intent":     {"max_tokens": 10,   "temperature": 0.01},
    "sentiment":  {"max_tokens": 10,   "temperature": 0.01},
    "importance": {"max_tokens": 128,  "temperature": 0.05},
    "extract":    {"max_tokens": 512,  "temperature": 0.05},
    "triage":     {"max_tokens": 512,  "temperature": 0.05},
    "link":       {"max_tokens": 512,  "temperature": 0.05},
    "ambient":    {"max_tokens": 256,  "temperature": 0.05},
    "summarize":  {"max_tokens": 256,  "temperature": 0.2},
    "expand":     {"max_tokens": 256,  "temperature": 0.2},
    "answer":     {"max_tokens": 1024, "temperature": 0.2},
    "multiturn":  {"max_tokens": 1024, "temperature": 0.2},
    "dontknow":   {"max_tokens": 1024, "temperature": 0.2},
}


def clean_output(text: str, signal: str) -> str:
    """Post-process model output: strip markdown, clean whitespace."""
    import re
    # Strip markdown code blocks
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()

    # For JSON signals, try to extract valid JSON
    if signal in ("extract", "triage", "importance", "link", "ambient"):
        # Find JSON object in the text
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                parsed = json.loads(match.group())
                text = json.dumps(parsed)
            except json.JSONDecodeError:
                pass

    return text


def generate(signal: str, user_content: str, max_tokens: int = None, temperature: float = None) -> str:
    """Generate a response from Rabbit for a given signal."""
    settings = SIGNAL_SETTINGS.get(signal, {"max_tokens": 512, "temperature": 0.1})
    if max_tokens is None:
        max_tokens = settings["max_tokens"]
    if temperature is None:
        temperature = settings["temperature"]

    system_prompt = TASK_SYSTEM_PROMPTS.get(signal, TASK_SYSTEM_PROMPTS["answer"])
    prefix = SIGNAL_PREFIXES.get(signal, "[ANSWER]")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{prefix} {user_content}"},
    ]

    inputs = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True,
        return_tensors="pt", return_dict=True,
    ).to(model.device)

    input_len = inputs["input_ids"].shape[-1]

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=max(temperature, 0.01),
            do_sample=temperature > 0.01,
        )

    raw = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
    return clean_output(raw, signal)


# ── Endpoints ───────────────────────────────────────────────────────────────


@app.get("/health")
def health():
    return {"status": "ok", "model": "rabbit-v1.2", "signals": 12}


@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest, key: str = Depends(verify_key)):
    """OpenAI-compatible chat completions endpoint."""
    start = time.time()

    # Extract signal from the first user message prefix, or use explicit signal
    signal = req.signal or "answer"
    user_content = ""

    for msg in req.messages:
        if msg.role == "user":
            content = msg.content
            # Auto-detect signal from prefix
            for sig, prefix in SIGNAL_PREFIXES.items():
                if content.startswith(prefix):
                    signal = sig
                    content = content[len(prefix):].strip()
                    break
            user_content = content
            break

    if not user_content:
        raise HTTPException(status_code=400, detail="No user message found")

    response_text = generate(signal, user_content, req.max_tokens, req.temperature)

    return {
        "id": f"rabbit-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "rabbit-v1.2",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": response_text},
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
        "signal": signal,
        "latency_ms": int((time.time() - start) * 1000),
    }


@app.post("/v1/embeddings")
def embeddings(req: EmbedRequest, key: str = Depends(verify_key)):
    """Generate embeddings using FastEmbed."""
    texts = req.input if isinstance(req.input, list) else [req.input]
    vectors = list(embed_model.embed(texts))

    return {
        "object": "list",
        "data": [
            {"object": "embedding", "index": i, "embedding": v.tolist()}
            for i, v in enumerate(vectors)
        ],
        "model": "nomic-embed-text-v1.5",
    }


@app.post("/v1/ingest")
def ingest(req: IngestRequest, key: str = Depends(verify_key)):
    """Full ingestion pipeline: triage + extract + summarize + sentiment + importance + embed."""
    start = time.time()
    content = req.content

    # Run all ingestion signals
    triage = generate("triage", content, 512, 0.1)
    extract = generate("extract", content, 512, 0.1)
    summary = generate("summarize", content, 256, 0.1)
    sentiment = generate("sentiment", content, 10, 0.1)
    importance = generate("importance", content, 128, 0.1)

    # Generate embedding
    embedding = list(embed_model.embed([content]))[0].tolist()

    # Parse JSON outputs
    def safe_json(text):
        try:
            return json.loads(text)
        except Exception:
            return text

    return {
        "triage": safe_json(triage),
        "extract": safe_json(extract),
        "summary": summary,
        "sentiment": sentiment.strip().lower(),
        "importance": safe_json(importance),
        "embedding": embedding,
        "latency_ms": int((time.time() - start) * 1000),
    }


@app.post("/v1/query")
def query(req: QueryRequest, key: str = Depends(verify_key)):
    """Query pipeline: intent + expand + answer."""
    start = time.time()
    question = req.question

    # Classify intent
    intent = generate("intent", question, 10, 0.1).strip().lower()

    # Expand query
    expanded = generate("expand", question, 128, 0.1)

    # Generate answer if memories provided
    answer = None
    if req.memories:
        memory_text = "\n".join(
            f"[{i+1}] {m.get('title', '')}: {m.get('summary', m.get('content', ''))}"
            for i, m in enumerate(req.memories)
        )
        answer_input = f"Question: {question}\nMemories: {memory_text}"
        answer = generate(req.signal, answer_input, 512, 0.2)

    return {
        "intent": intent,
        "expanded_query": expanded,
        "answer": answer,
        "latency_ms": int((time.time() - start) * 1000),
    }


@app.post("/v1/link")
def link(req: dict, key: str = Depends(verify_key)):
    """Memory linking: find relationships between records."""
    start = time.time()
    content = req.get("content", "")
    result = generate("link", content, 512, 0.1)

    try:
        parsed = json.loads(result)
    except Exception:
        parsed = {"links": [], "raw": result}

    return {
        "result": parsed,
        "latency_ms": int((time.time() - start) * 1000),
    }


@app.post("/v1/ambient")
def ambient(req: dict, key: str = Depends(verify_key)):
    """Ambient recall: detect contradictions/forgotten commitments."""
    start = time.time()
    content = req.get("content", "")
    result = generate("ambient", content, 256, 0.1)

    try:
        parsed = json.loads(result)
    except Exception:
        parsed = {"show": False, "raw": result}

    return {
        "result": parsed,
        "latency_ms": int((time.time() - start) * 1000),
    }


# ── Startup ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    load_models()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
