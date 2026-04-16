"""
Rabbit v2.0 FastAPI server.

One endpoint per memory signal. Verbose structured JSON logging per request.
Streaming responses for interactive testing feel.

Runs on the baked GCP image as a systemd unit. See ../gcp/00_bake_disk.sh.
"""

import hashlib
import json
import logging
import os
import time
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ------------------------------------------------------------
# Config
# ------------------------------------------------------------

MODEL_REPO = "reattend/rabbit-v2.0"
MAX_SEQ_LENGTH = 2048
TOKEN_FILE = Path("/opt/rabbit/token")
LAST_REQUEST_FILE = Path("/var/lib/rabbit/last_request")
LOG_FILE = Path("/var/log/rabbit/server.log")

SHARED_TOKEN = (
    TOKEN_FILE.read_text().strip()
    if TOKEN_FILE.exists()
    else os.environ.get("RABBIT_TOKEN", "")
)

# System prompts per signal. These match the ones used during training
# (see scripts/finetune_qwen32b.py → signal_prompts).
SIGNAL_PROMPTS = {
    "extract": "You are Rabbit, a memory AI. Extract structured information from the given text. Return a JSON object with keys: people, organizations, decisions, action_items, dates, topics.",
    "faithful_extract": "You are Rabbit, a memory AI. Extract only information explicitly present in the text. Do not infer. Return JSON with keys: people, organizations, decisions, action_items, dates, topics.",
    "triage": "You are Rabbit, a memory AI. Classify and summarize the given content. Return a JSON object with keys: type, summary, tags.",
    "summarize": "You are Rabbit, a memory AI. Generate a rich 2-4 sentence standalone summary.",
    "answer": "You are Rabbit, a memory AI. Answer the user's question conversationally with citations.",
    "followup_answer": "You are Rabbit, a memory AI. Answer the followup question using the prior conversation context.",
    "formatted_answer": "You are Rabbit, a memory AI. Answer the question with clear structure: headings, bullets, and a short summary.",
    "compile": "You are Rabbit, a memory AI. Compile the relevant context from multiple memories into a coherent brief.",
    "compile_answer": "You are Rabbit, a memory AI. Use the provided memories to answer the question. Cite which memory supports each claim.",
    "intent": "You are Rabbit, a memory AI. Classify the user's query intent. Respond with exactly one word: factual, entity, temporal, synthesis, actions, history, or aggregation.",
    "expand": "You are Rabbit, a memory AI. Expand the user's vague query into a precise, comprehensive search query.",
    "sentiment": "You are Rabbit, a memory AI. Classify the tone. Respond with exactly one word: positive, negative, neutral, tense, or urgent.",
    "importance": "You are Rabbit, a memory AI. Score the importance 1-5 with reason. Return JSON with keys: score and reason.",
    "link": "You are Rabbit, a memory AI. Determine which candidates are meaningfully related. Return JSON with a links array.",
    "ambient": "You are Rabbit, a memory AI. Detect contradictions or forgotten commitments in the given content. Return JSON.",
    "multiturn": "You are Rabbit, a memory AI. Continue the multi-turn conversation naturally.",
    "dontknow": "You are Rabbit, a memory AI. If the answer is not in the given memories, say so clearly and suggest what would need to be added.",
    "lint": "You are Rabbit, a memory AI. Fix any malformed JSON in the given text and return valid JSON only.",
    "clean_json": "You are Rabbit, a memory AI. Return only strictly valid JSON for the given content. No prose, no markdown.",
}

# ------------------------------------------------------------
# Logging (structured JSON, one line per event)
# ------------------------------------------------------------

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("rabbit")


def logj(event: str, **fields) -> None:
    """Emit one JSON line."""
    record = {"ts": time.time(), "event": event, **fields}
    log.info(json.dumps(record, default=str))


# ------------------------------------------------------------
# Model loading (Unsloth)
# ------------------------------------------------------------

model = None
tokenizer = None
lora_hash: str = "unknown"
model_ready = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tokenizer, lora_hash, model_ready

    logj("startup_begin", model=MODEL_REPO, max_seq=MAX_SEQ_LENGTH)
    t0 = time.time()

    from unsloth import FastLanguageModel

    # Load HF token from rabbit's cache (written by install.sh), fall back to env
    hf_token = ""
    hf_token_file = Path("/opt/rabbit/.cache/huggingface/token")
    if hf_token_file.exists():
        hf_token = hf_token_file.read_text().strip()
    else:
        hf_token = os.environ.get("HF_TOKEN", "")

    try:
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=MODEL_REPO,
            max_seq_length=MAX_SEQ_LENGTH,
            dtype=None,
            load_in_4bit=True,
            token=hf_token or None,
        )
        FastLanguageModel.for_inference(model)  # 2x faster inference
        lora_hash = hashlib.sha256(MODEL_REPO.encode()).hexdigest()[:12]
        model_ready = True
        logj(
            "startup_ready",
            model=MODEL_REPO,
            lora_hash=lora_hash,
            load_seconds=round(time.time() - t0, 1),
        )
    except Exception as e:
        logj("startup_error", error=str(e), traceback=traceback.format_exc())
        raise

    yield
    logj("shutdown")


app = FastAPI(title="Rabbit v2.0", lifespan=lifespan)


# ------------------------------------------------------------
# Utils
# ------------------------------------------------------------


def touch_last_request() -> None:
    try:
        LAST_REQUEST_FILE.parent.mkdir(parents=True, exist_ok=True)
        LAST_REQUEST_FILE.write_text(str(int(time.time())))
    except Exception as e:
        logj("touch_error", error=str(e))


def check_auth(auth: str | None) -> None:
    if not SHARED_TOKEN:
        return  # dev mode, no auth
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    if auth.removeprefix("Bearer ") != SHARED_TOKEN:
        raise HTTPException(403, "invalid token")


def make_request_id() -> str:
    return hashlib.sha256(f"{time.time_ns()}".encode()).hexdigest()[:12]


# ------------------------------------------------------------
# Schemas
# ------------------------------------------------------------


class SignalRequest(BaseModel):
    text: str
    max_new_tokens: int = 512
    temperature: float = 0.3
    stream: bool = False


class HealthResponse(BaseModel):
    status: str
    model: str
    lora_hash: str
    signals: list[str]


# ------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Cheap, doesn't touch the GPU — always fast."""
    return HealthResponse(
        status="ok" if model_ready else "loading",
        model=MODEL_REPO,
        lora_hash=lora_hash,
        signals=list(SIGNAL_PROMPTS.keys()),
    )


@app.get("/signals")
async def list_signals() -> dict:
    return {"signals": list(SIGNAL_PROMPTS.keys())}


@app.post("/signal/{signal}")
async def signal(
    signal: str,
    req: SignalRequest,
    request: Request,
    authorization: str | None = Header(None),
):
    check_auth(authorization)
    touch_last_request()

    if not model_ready:
        raise HTTPException(503, "model still loading")

    if signal not in SIGNAL_PROMPTS:
        raise HTTPException(
            404,
            f"unknown signal: {signal}. available: {list(SIGNAL_PROMPTS.keys())}",
        )

    request_id = make_request_id()
    prompt_hash = hashlib.sha256(req.text.encode()).hexdigest()[:12]
    client_ip = request.client.host if request.client else "?"

    log_base = {
        "request_id": request_id,
        "signal": signal,
        "prompt_hash": prompt_hash,
        "prompt_preview": req.text[:200],
        "prompt_len": len(req.text),
        "lora_hash": lora_hash,
        "client_ip": client_ip,
    }
    logj("request", **log_base)

    try:
        messages = [
            {"role": "system", "content": SIGNAL_PROMPTS[signal]},
            {"role": "user", "content": req.text},
        ]
        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to("cuda")
        input_tokens = int(inputs.shape[1])

        if req.stream:
            return StreamingResponse(
                _stream_generate(inputs, req, log_base, input_tokens, request_id, signal),
                media_type="text/event-stream",
            )

        t0 = time.time()
        outputs = model.generate(
            input_ids=inputs,
            max_new_tokens=req.max_new_tokens,
            use_cache=True,
            temperature=req.temperature,
            do_sample=req.temperature > 0,
        )
        latency_ms = int((time.time() - t0) * 1000)
        output_tokens = int(outputs.shape[1] - input_tokens)
        response_text = tokenizer.decode(
            outputs[0][input_tokens:], skip_special_tokens=True
        )

        logj(
            "response",
            **log_base,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            tokens_per_sec=round(output_tokens / max(1, latency_ms / 1000), 1),
            response_preview=response_text[:200],
        )

        return {
            "request_id": request_id,
            "signal": signal,
            "response": response_text,
            "meta": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": latency_ms,
                "lora_hash": lora_hash,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logj(
            "error",
            **log_base,
            error=str(e),
            traceback=traceback.format_exc(),
        )
        raise HTTPException(500, f"inference error: {type(e).__name__}: {e}")


async def _stream_generate(
    inputs,
    req: SignalRequest,
    log_base: dict,
    input_tokens: int,
    request_id: str,
    signal: str,
) -> AsyncGenerator[str, None]:
    """Token-by-token streaming via TextIteratorStreamer."""
    import asyncio
    from threading import Thread
    from transformers import TextIteratorStreamer

    streamer = TextIteratorStreamer(
        tokenizer,
        skip_prompt=True,
        skip_special_tokens=True,
        timeout=60,
    )
    gen_kwargs = dict(
        input_ids=inputs,
        max_new_tokens=req.max_new_tokens,
        use_cache=True,
        temperature=req.temperature,
        do_sample=req.temperature > 0,
        streamer=streamer,
    )

    t0 = time.time()
    thread = Thread(target=model.generate, kwargs=gen_kwargs)
    thread.start()

    collected = []
    output_tokens = 0
    try:
        for chunk in streamer:
            if not chunk:
                continue
            collected.append(chunk)
            output_tokens += 1
            yield f"data: {json.dumps({'chunk': chunk, 'request_id': request_id})}\n\n"
            await asyncio.sleep(0)  # let event loop breathe

        latency_ms = int((time.time() - t0) * 1000)
        full_response = "".join(collected)

        logj(
            "stream_response",
            **log_base,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            tokens_per_sec=round(output_tokens / max(1, latency_ms / 1000), 1),
            response_preview=full_response[:200],
        )

        yield f"data: {json.dumps({'done': True, 'request_id': request_id, 'latency_ms': latency_ms, 'output_tokens': output_tokens})}\n\n"
    except Exception as e:
        logj("stream_error", **log_base, error=str(e), traceback=traceback.format_exc())
        yield f"data: {json.dumps({'error': str(e), 'request_id': request_id})}\n\n"
    finally:
        thread.join(timeout=5)
