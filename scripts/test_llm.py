"""Quick sanity check on the LLM connection. Run this first."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from src.llm import get_llm

load_dotenv()

print("Testing LLM connection...")
print()

try:
    llm = get_llm()
    print(f"Provider: {llm.name}")
    response = llm.complete_json(
        'Return a JSON object with one key "status" set to "ok". '
        "Return only JSON, no other text."
    )
    print(f"Response: {response}")
    print()
    print("✓ LLM works. Run: python scripts/run_pipeline.py")
except Exception as exc:  # noqa: BLE001
    print(f"✗ ERROR: {exc}")
    print()
    print("Common fixes:")
    print("  - Make sure .env exists with GROQ_API_KEY filled in")
    print("  - For Ollama: run `ollama serve` and `ollama pull llama3.1:8b`")
    sys.exit(1)