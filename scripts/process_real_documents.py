"""
Process REAL organizational documents into Rabbit v2.0 training data.

Takes PDFs and text files of:
- Annual reports
- Meeting transcripts
- Project proposals
- Strategy documents
- Any long organizational content

For each document:
1. Extract text (from PDF or .txt)
2. Chunk into 3000-char sections
3. Call Claude/OpenAI API to generate extraction output
4. Write to data/filtered/real_documents_filtered.jsonl

Input: data/seeds/real/*.pdf or *.txt
Output: data/filtered/real_documents_filtered.jsonl

Usage:
  # Install deps
  pip install pypdf requests

  # Drop your PDFs/txts in data/seeds/real/
  # Then run:
  export OPENAI_API_KEY=sk-...
  python3 scripts/process_real_documents.py
"""

import json
import os
import sys
import random
import time
import requests
from pathlib import Path

API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = "gpt-4o-mini"
CHUNK_SIZE = 3500  # chars per chunk
INPUT_DIR = Path("data/seeds/real")
OUTPUT_FILE = Path("data/filtered/real_documents_filtered.jsonl")


def call_api(system: str, user: str, max_tokens: int = 1500) -> str:
    """Call OpenAI API with retries."""
    for attempt in range(3):
        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.3,
                    "max_tokens": max_tokens,
                },
                timeout=120,
            )
            if resp.ok:
                return resp.json()["choices"][0]["message"]["content"]
            time.sleep(2 ** attempt)
        except Exception as e:
            print(f"  Retry {attempt+1}: {e}")
            time.sleep(2 ** attempt)
    return ""


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except ImportError:
        print("  ERROR: Install pypdf: pip install pypdf")
        sys.exit(1)
    except Exception as e:
        print(f"  ERROR reading {pdf_path.name}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks at paragraph boundaries."""
    text = text.strip()
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    paragraphs = text.split("\n\n")
    current = ""

    for para in paragraphs:
        if len(current) + len(para) > chunk_size and current:
            chunks.append(current.strip())
            current = para
        else:
            current += "\n\n" + para if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


def generate_extraction(content: str, doc_type: str) -> dict:
    """Generate EXTRACT signal output for a content chunk."""
    prompt = f"""Extract all structured information from this {doc_type} excerpt. Return ONLY valid JSON.

TEXT:
{content}

Return JSON with these exact keys:
- people: array of full names mentioned
- organizations: array of company/org names
- decisions: array of specific decisions, approvals, or conclusions
- action_items: array of objects with "owner", "task", "due" (if mentioned)
- dates: array of all specific dates mentioned
- topics: array of key topics and themes"""

    output = call_api("Return only valid JSON, no markdown.", prompt, max_tokens=1500)
    if not output:
        return None

    output = output.strip()
    if output.startswith("```"):
        output = output.split("```")[1]
        if output.startswith("json"):
            output = output[4:]
        output = output.strip()

    try:
        parsed = json.loads(output)
        return parsed
    except json.JSONDecodeError:
        return None


def generate_summary(content: str, doc_type: str) -> dict:
    """Generate SUMMARIZE + TRIAGE outputs."""
    prompt = f"""Analyze this {doc_type} excerpt. Return ONLY valid JSON.

TEXT:
{content}

Return JSON with:
- type: one of "meeting", "decision", "note", "task", "idea", "insight", "context", "report"
- summary: 2-4 sentence summary capturing key points
- tags: array of 4-8 relevant tags"""

    output = call_api("Return only valid JSON.", prompt, max_tokens=800)
    if not output:
        return None

    output = output.strip()
    if output.startswith("```"):
        output = output.split("```")[1]
        if output.startswith("json"):
            output = output[4:]
        output = output.strip()

    try:
        return json.loads(output)
    except:
        return None


def detect_doc_type(filename: str, content_preview: str) -> str:
    """Guess document type from filename or content."""
    name = filename.lower()
    if "annual" in name or "10-k" in name or "10k" in name:
        return "annual report"
    if "meeting" in name or "transcript" in name:
        return "meeting transcript"
    if "proposal" in name or "rfp" in name:
        return "project proposal"
    if "strategy" in name:
        return "strategy document"
    if "budget" in name:
        return "budget document"
    if "report" in name:
        return "business report"
    if "contract" in name or "agreement" in name:
        return "contract"
    return "organizational document"


def process_file(file_path: Path, output_f) -> int:
    """Process one file, write extractions to output."""
    print(f"\nProcessing: {file_path.name}")

    # Read content
    if file_path.suffix.lower() == ".pdf":
        text = extract_pdf_text(file_path)
    else:
        text = file_path.read_text(encoding="utf-8", errors="replace")

    if len(text) < 500:
        print(f"  SKIP: too short ({len(text)} chars)")
        return 0

    print(f"  Text length: {len(text)} chars")

    # Detect type
    doc_type = detect_doc_type(file_path.name, text[:500])
    print(f"  Type: {doc_type}")

    # Chunk
    chunks = chunk_text(text)
    print(f"  Chunks: {len(chunks)}")

    count = 0
    for i, chunk in enumerate(chunks):
        if len(chunk) < 500:
            continue

        # Generate EXTRACT example
        extraction = generate_extraction(chunk, doc_type)
        if extraction:
            output_f.write(json.dumps({
                "input": f"[EXTRACT] {chunk}",
                "output": json.dumps(extraction),
            }) + "\n")
            count += 1

        # Generate TRIAGE + SUMMARIZE
        triage = generate_summary(chunk, doc_type)
        if triage:
            output_f.write(json.dumps({
                "input": f"[TRIAGE] {chunk}",
                "output": json.dumps(triage),
            }) + "\n")
            count += 1

            # Also create a SUMMARIZE example
            if triage.get("summary"):
                output_f.write(json.dumps({
                    "input": f"[SUMMARIZE] {chunk}",
                    "output": triage["summary"],
                }) + "\n")
                count += 1

        output_f.flush()
        time.sleep(0.3)  # Rate limit

        if (i + 1) % 10 == 0:
            print(f"    Processed {i+1}/{len(chunks)} chunks ({count} examples)")

    print(f"  DONE: {count} training examples from {file_path.name}")
    return count


def main():
    if not API_KEY:
        print("ERROR: Set OPENAI_API_KEY")
        sys.exit(1)

    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Find all files
    files = list(INPUT_DIR.glob("*.pdf")) + list(INPUT_DIR.glob("*.txt")) + list(INPUT_DIR.glob("*.md"))

    if not files:
        print(f"No files found in {INPUT_DIR}")
        print(f"Drop your PDFs/txts in {INPUT_DIR}/ and run again")
        sys.exit(0)

    print(f"Found {len(files)} files to process")
    print(f"Output: {OUTPUT_FILE}")

    total = 0
    with open(OUTPUT_FILE, "a") as output_f:
        for file_path in files:
            try:
                count = process_file(file_path, output_f)
                total += count
            except Exception as e:
                print(f"  ERROR processing {file_path.name}: {e}")

    print(f"\n{'='*60}")
    print(f"  TOTAL: {total} training examples generated")
    print(f"  Output: {OUTPUT_FILE}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
