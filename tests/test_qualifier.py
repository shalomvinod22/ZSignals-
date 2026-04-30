"""Unit tests for the Qualifier — uses a fake LLM client (no network)."""

import json
from pathlib import Path

import pytest

from src.llm import LLMClient
from src.qualifier import Qualifier


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "qualifier.md"


class FakeLLM(LLMClient):
    """Returns a canned response for testing — no network calls."""

    def __init__(self, response: str) -> None:
        self._response = response

    def complete_json(self, prompt: str) -> str:
        return self._response

    @property
    def name(self) -> str:
        return "FakeLLM"


def test_qualifier_parses_clean_json() -> None:
    canned = json.dumps({
        "disqualified": False,
        "intent_score": 5,
        "pain_category": "Bounce Rate / Deliverability",
        "recommended_action": "BOTH",
        "confidence": "HIGH",
    })
    q = Qualifier(PROMPT_PATH, FakeLLM(canned))
    result = q.analyze({"platform": "Reddit", "content": "test"})
    assert result["intent_score"] == 5
    assert result["recommended_action"] == "BOTH"
    assert result["_post"]["platform"] == "Reddit"


def test_qualifier_handles_messy_json_with_prose() -> None:
    canned = (
        "Sure, here's the JSON: "
        '{"disqualified": false, "intent_score": 4, '
        '"recommended_action": "BULK EMAIL"} '
        "Hope that helps!"
    )
    q = Qualifier(PROMPT_PATH, FakeLLM(canned))
    result = q.analyze({"platform": "G2", "content": "x"})
    assert result["intent_score"] == 4


def test_qualifier_handles_unparseable_response() -> None:
    q = Qualifier(PROMPT_PATH, FakeLLM("definitely not json"))
    result = q.analyze({"platform": "Reddit", "content": "x"})
    assert "error" in result
    assert "raw" in result


def test_qualifier_handles_llm_exception() -> None:
    class BrokenLLM(LLMClient):
        def complete_json(self, prompt: str) -> str:
            raise ConnectionError("network down")

        @property
        def name(self) -> str:
            return "Broken"

    q = Qualifier(PROMPT_PATH, BrokenLLM())
    result = q.analyze({"platform": "Reddit", "content": "x"})
    assert "error" in result
    assert "network down" in result["error"]


def test_format_post_includes_all_fields() -> None:
    formatted = Qualifier.format_post({
        "platform": "Reddit",
        "source_url": "https://reddit.com/r/sales",
        "username": "u/test",
        "date": "2026-04-26",
        "content": "Apollo is broken",
    })
    assert "Reddit" in formatted
    assert "u/test" in formatted
    assert "Apollo is broken" in formatted