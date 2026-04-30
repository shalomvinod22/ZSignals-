"""CLI entry point for running the pipeline on data/raw/posts.csv."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from src.pipeline import run_pipeline

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    print("Zintlr Intent Radar — Pipeline Run")
    print("=" * 50)
    try:
        run_pipeline(
            input_csv=PROJECT_ROOT / "data" / "raw" / "posts.csv",
            output_dir=PROJECT_ROOT / "data" / "qualified",
            prompt_path=PROJECT_ROOT / "prompts" / "qualifier.md",
        )
    except Exception as exc:  # noqa: BLE001
        print(f"\n✗ Pipeline failed: {exc}")
        sys.exit(1)