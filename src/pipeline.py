"""Orchestrates the full flow: load posts → analyze → write reports."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .exporter import export_csv, export_markdown
from .llm import get_llm
from .qualifier import Qualifier


def load_posts(input_csv: Path) -> list[dict[str, str]]:
    if not input_csv.exists():
        raise FileNotFoundError(
            f"Input CSV not found at {input_csv}. "
            f"Required columns: platform, source_url, username, date, content"
        )
    with input_csv.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run_pipeline(
    input_csv: Path,
    output_dir: Path,
    prompt_path: Path,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> tuple[Path, Path, list[dict[str, Any]]]:
    """Run full pipeline. Returns (md_path, csv_path, results)."""
    llm = get_llm()
    qualifier = Qualifier(prompt_path, llm)
    posts = load_posts(input_csv)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"LLM:    {llm.name}")
    print(f"Posts:  {len(posts)}")
    print(f"Output: {output_dir}")
    print()

    results: list[dict[str, Any]] = []
    for i, post in enumerate(posts, 1):
        label = (
            f"{post.get('platform', '?')} — "
            f"{(post.get('username', '?') or '?')[:40]}"
        )
        if progress_callback:
            progress_callback(i, len(posts), label)
        else:
            print(f"[{i}/{len(posts)}] {label}")

        results.append(qualifier.analyze(post))

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    md_path = output_dir / f"report_{timestamp}.md"
    csv_path = output_dir / f"report_{timestamp}.csv"

    export_markdown(results, md_path)
    export_csv(results, csv_path)

    print()
    print(f"✓ Markdown: {md_path}")
    print(f"✓ CSV:      {csv_path}")

    return md_path, csv_path, results