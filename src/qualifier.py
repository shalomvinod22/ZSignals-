"""Sends each post to the LLM and parses the JSON response."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .llm import GroqClient, LLMClient


class Qualifier:
    """Wraps the LLM with the qualifier prompt and JSON parsing."""

    def __init__(self, prompt_path: Path | None = None, llm: LLMClient | None = None) -> None:
        if prompt_path is None:
            prompt_path = Path(__file__).parent.parent / "prompts" / "qualifier.md"
        self._prompt_path = prompt_path
        self._llm = llm or GroqClient()

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
        full_prompt = self._build_prompt(post)

        try:
            raw = self._llm.complete_json(full_prompt)
        except Exception as exc:  # noqa: BLE001
            result = self._fallback_result(post, str(exc))
            result["_post"] = post
            return result

        parsed = self._extract_json(raw)
        if parsed is None:
            return {
                "error": "Could not parse JSON from LLM response",
                "raw": raw[:500],
                "_post": post,
            }

        if not isinstance(parsed, dict):
            return {
                "error": "LLM returned JSON that is not an object",
                "raw": raw[:500],
                "_post": post,
            }

        normalized = self._normalize(parsed, post)
        normalized["_post"] = post
        return normalized

    def qualify(self, post: dict[str, str]) -> dict[str, Any]:
        """Analyze a post and return the V1.3 qualifier schema."""
        return self.analyze(post)

    def _build_prompt(self, post: dict[str, str]) -> str:
        """Load the V1.3 prompt fresh and insert the post text."""
        template = self._prompt_path.read_text(encoding="utf-8")
        return template.replace("{INSERT POST HERE}", self.format_post(post))

    @staticmethod
    def _normalize(result: dict[str, Any], post: dict[str, str]) -> dict[str, Any]:
        """Normalize the qualifier output to the V1.3 schema only."""
        score = result.get("score")
        if score is None:
            score = result.get("intent_score", 0)

        persona = result.get("persona")
        if not isinstance(persona, dict):
            persona = {}

        signal_stack = result.get("signal_stack")
        if not isinstance(signal_stack, dict):
            signal_stack = {}

        conversation_kit = result.get("conversation_kit")
        if not isinstance(conversation_kit, dict):
            conversation_kit = {}

        outbound_strategy = result.get("outbound_strategy")
        if not isinstance(outbound_strategy, dict):
            outbound_strategy = {}

        normalized = {
            "score": int(score or 0),
            "tier": result.get("tier", "LOW"),
            "is_disqualified": bool(result.get("is_disqualified", False) or result.get("disqualified", False)),
            "pain_stage": result.get("pain_stage"),
            "pain_type": result.get("pain_type") or result.get("pain_category"),
            "pain_evidence": result.get("pain_evidence") or result.get("pain_in_words"),
            "persona": {
                "inferred_role": persona.get("inferred_role") or result.get("buyer_type") or "Unknown",
                "decision_authority": persona.get("decision_authority") or "Unknown",
                "geography": persona.get("geography") or "Unknown",
            },
            "signal_stack": {
                "fit": signal_stack.get("fit"),
                "opportunity": signal_stack.get("opportunity"),
                "intent": signal_stack.get("intent"),
            },
            "conversation_kit": {
                "cold_opener_email": conversation_kit.get("cold_opener_email") or result.get("opening_line"),
                "linkedin_dm": conversation_kit.get("linkedin_dm"),
                "talking_points": conversation_kit.get("talking_points"),
            },
            "likely_objections": result.get("likely_objections", []),
            "outbound_strategy": {
                "primary_channel": outbound_strategy.get("primary_channel"),
                "expected_response_rate": outbound_strategy.get("expected_response_rate"),
                "follow_up_timeline": outbound_strategy.get("follow_up_timeline"),
            },
            "reasoning": result.get("reasoning") or result.get("why_matters"),
            "ae_priority": result.get("ae_priority") or result.get("recommended_action"),
        }

        # If disqualified, set tier to LOW and score to 0
        if normalized["is_disqualified"]:
            normalized["tier"] = "LOW"
            normalized["score"] = 0

        return normalized

    @staticmethod
    def _fallback_result(post: dict[str, str], error: str) -> dict[str, Any]:
        """Return a conservative V1.3 result when the LLM is unavailable."""
        content = (post.get("content") or "").lower()
        platform = post.get("platform", "Unknown")
        has_competitor = any(
            term in content for term in ("apollo", "zoominfo", "lusha", "cognism")
        )
        has_india = any(term in content for term in ("india", "apac", "bangalore", "mumbai"))
        has_hiring = any(term in content for term in ("hiring", "sdr", "bdr", "outbound"))
        has_pain = any(
            term in content
            for term in (
                "bad",
                "terrible",
                "struggling",
                "reply rate",
                "bounce",
                "alternative",
                "recommendations",
                "scaling outbound",
            )
        )

        score = 1
        if has_competitor and has_india and has_pain:
            score = 5
        elif platform.lower() == "linkedin" and has_hiring and has_competitor:
            score = 4
        elif has_hiring and has_pain:
            score = 3
        elif has_competitor or has_pain:
            score = 2

        tier = "HIGH" if score >= 5 else "MEDIUM" if score >= 4 else "LOW"
        geography = "India" if has_india else "Unknown"
        inferred_role = "Founder" if "founder" in content or "founder" in str(post).lower() else "Unknown"
        if "sdr" in content or "bdr" in content:
            inferred_role = "SDR/BDR"

        return {
            "error": f"LLM call failed: {error}",
            "score": score,
            "tier": tier,
            "is_disqualified": False,
            "pain_stage": "Evaluation" if score >= 4 else "Awareness",
            "pain_type": (
                "Poor India / APAC Coverage"
                if has_india and has_competitor
                else "General Frustration"
            ),
            "pain_evidence": (post.get("content") or "")[:180],
            "persona": {
                "inferred_role": inferred_role,
                "decision_authority": "Founder" if inferred_role == "Founder" else "Unknown",
                "geography": geography,
            },
            "signal_stack": {
                "fit": "India/APAC outbound signal" if has_india else "Outbound signal",
                "opportunity": "Hiring or scaling outbound" if has_hiring else "Public competitor pain",
                "intent": "High" if score >= 4 else "Moderate" if score >= 3 else "Low",
            },
            "conversation_kit": {
                "cold_opener_email": "saw your note on outbound data quality for india",
                "linkedin_dm": "Saw your outbound hiring post. Curious how you are handling India contact accuracy today?",
                "talking_points": [
                    "India/APAC contact accuracy",
                    "Outbound hiring plans",
                    "Apollo data quality gap",
                ],
            },
            "likely_objections": [],
            "outbound_strategy": {
                "primary_channel": "LinkedIn DM" if platform.lower() == "linkedin" else "Email sequence",
                "expected_response_rate": "10-15%",
                "follow_up_timeline": "3-5 days",
            },
            "reasoning": f"Fallback V1.3 scoring used because LLM call failed: {error[:120]}",
            "ae_priority": "High - ready buyer" if score >= 5 else "Medium - nurture" if score >= 3 else "Low - monitor",
        }

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


# Module-level singleton for backward compat
_default_qualifier = None


def qualify_post(post: dict) -> dict:
    """Backward-compat wrapper around Qualifier class.
    
    Both APIs work:
        from src.qualifier import qualify_post
        result = qualify_post(post)
    
    OR:
        from src.qualifier import Qualifier
        result = Qualifier().qualify(post)
    """
    global _default_qualifier
    if _default_qualifier is None:
        from .llm import GroqClient
        prompt_path = Path(__file__).parent.parent / "prompts" / "qualifier.md"
        llm = GroqClient()
        _default_qualifier = Qualifier(prompt_path, llm)
    return _default_qualifier.analyze(post)
