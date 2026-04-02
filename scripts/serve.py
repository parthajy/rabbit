"""
Rabbit — Local Deployment Helper
Creates an Ollama Modelfile and sets up local serving for testing.

Usage:
    python scripts/serve.py --model-path models/rabbit-v1-q4
    python scripts/serve.py --model-path models/rabbit-v1-q4 --port 11434
"""

import argparse
import subprocess
import sys
from pathlib import Path

MODELFILE_TEMPLATE = """FROM {model_path}

PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER num_ctx 2048
PARAMETER stop <|end|>
PARAMETER stop <|endoftext|>

SYSTEM You are Rabbit, Reattend's memory AI. You perform classification, extraction, triage, query expansion, and answer generation for organizational memory.
"""


def create_modelfile(model_path: str) -> Path:
    """Generate an Ollama Modelfile for Rabbit."""
    modelfile_path = Path("models/Modelfile")
    modelfile_path.parent.mkdir(parents=True, exist_ok=True)

    content = MODELFILE_TEMPLATE.format(model_path=model_path)
    modelfile_path.write_text(content)
    print(f"  Created Modelfile at {modelfile_path}")
    return modelfile_path


def main():
    parser = argparse.ArgumentParser(
        description="Rabbit — Set up local Ollama serving"
    )
    parser.add_argument(
        "--model-path",
        required=True,
        help="Path to the GGUF model file",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=11434,
        help="Port for Ollama server (default: 11434)",
    )
    parser.add_argument(
        "--name",
        default="rabbit",
        help="Model name in Ollama (default: rabbit)",
    )

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  RABBIT — Local Deployment Setup")
    print(f"{'='*60}")

    # Check Ollama is installed
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        print(f"\n  Ollama version: {result.stdout.strip()}")
    except FileNotFoundError:
        print("\n  Error: Ollama not found. Install from https://ollama.ai")
        sys.exit(1)

    # Create Modelfile
    modelfile = create_modelfile(args.model_path)

    # Create the model in Ollama
    print(f"\n  Creating Ollama model '{args.name}'...")
    result = subprocess.run(
        ["ollama", "create", args.name, "-f", str(modelfile)],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(f"  Model '{args.name}' created successfully!")
    else:
        print(f"  Error creating model: {result.stderr}")
        sys.exit(1)

    print(f"\n  To start serving:")
    print(f"    ollama serve  (if not already running)")
    print(f"\n  To test:")
    print(f"    ollama run {args.name} '[INTENT] What did we discuss last week?'")
    print(f"\n  API endpoint:")
    print(f"    http://localhost:{args.port}/v1/chat/completions")
    print(f"\n  Set in Reattend .env:")
    print(f"    OWN_MODEL_URL=http://localhost:{args.port}")

    print(f"\n{'='*60}")
    print(f"  RABBIT — Ready to serve!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
