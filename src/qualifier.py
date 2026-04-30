"""Sends each post to the LLM and parses the JSON response."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .llm import LLMClient


class Qualifier:
    """Wraps the LLM with the qualifier prompt and JSON parsing."""

    def __init__(self, prompt_path: Path, llm: LLMClient) -> None:
        self._template = prompt_path.read_text(encoding="utf-8")
        self._llm = llm

    @staticmethod
    def format_post(post: dict[str, str]) -> str:
        return (
            f"Source: {post.get('platform', 'Unknown')} — "
            f"{post.get('source_url', 'Unknown')}\n"
            f"Author: {post.get('username', 'Unknown')}\n"
            f"Date: {post.get('date', 'Unknown')}\n\n"
            f"Post:\n{(post.get('content') or '').strip()}"
        )

    def analyze(self, post: dict[str, str]) -> dict[str, Any]:
        post_text = self.format_post(post)
        full_prompt = self._template.replace("{INSERT POST HERE}", post_text)

        try:
            raw = self._llm.complete_json(full_prompt)
        except Exception as exc:  # noqa: BLE001
            return {"error": f"LLM call failed: {exc}", "_post": post}

        parsed = self._extract_json(raw)
        if parsed is None:
            return {
                "error": "Could not parse JSON from LLM response",
                "raw": raw[:500],
                "_post": post,
            }

        parsed["_post"] = post
        return parsed

    @staticmethod
    def _extract_json(raw: str) -> dict[str, Any] | None:
        """Try strict parse; fall back to extracting the first {...} block."""
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                return None
        return None