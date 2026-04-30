"""Converts qualifier output into a markdown report and a flat CSV."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

SCORE_EMOJI = {5: "🔥", 4: "✅", 3: "🟡", 2: "⚪", 1: "⚪", 0: "🚫"}


def _sort_key(r: dict[str, Any]) -> int:
    """Higher rank = appears first. Errors and DQ at the bottom."""
    if r.get("error"):
        return -2
    if r.get("disqualified"):
        return -1
    return r.get("intent_score") or 0


def export_markdown(results: list[dict[str, Any]], output_path: Path) -> None:
    """Write a human-readable markdown report sorted by score desc."""
    sorted_results = sorted(results, key=_sort_key, reverse=True)

    with output_path.open("w", encoding="utf-8") as f:
        f.write("# Zintlr Intent Radar — Daily Report\n\n")
        f.write(f"_Generated: {datetime.now().isoformat()}_  \n")
        f.write(f"_Posts processed: {len(results)}_\n\n")

        # Summary
        score_counts = {i: 0 for i in range(0, 6)}
        dq = err = 0
        for r in results:
            if r.get("error"):
                err += 1
            elif r.get("disqualified"):
                dq += 1
            else:
                score_counts[r.get("intent_score") or 0] += 1

        f.write("## Summary\n\n")
        f.write(f"- 🔥 Score 5: **{score_counts[5]}**\n")
        f.write(f"- ✅ Score 4: **{score_counts[4]}**\n")
        f.write(f"- 🟡 Score 3: **{score_counts[3]}**\n")
        f.write(f"- ⚪ Score 1–2: **{score_counts[1] + score_counts[2]}**\n")
        f.write(f"- 🚫 Disqualified: **{dq}**\n")
        if err:
            f.write(f"- ⚠️ Errors: **{err}**\n")
        f.write("\n---\n\n")

        for i, r in enumerate(sorted_results, 1):
            post = r.get("_post", {})
            label = f"{post.get('platform', '?')} — {post.get('username', '?')}"

            if r.get("error"):
                f.write(f"## {i}. ⚠️ ERROR — {label}\n\n")
                f.write(f"**Error:** {r['error']}\n\n")
                if "raw" in r:
                    f.write(f"```\n{r['raw'][:500]}\n```\n\n")
                f.write("---\n\n")
                continue

            if r.get("disqualified"):
                f.write(f"## {i}. 🚫 DISQUALIFIED — {label}\n\n")
                f.write(f"**Reason:** {r.get('disqualifier_reason', '—')}\n\n")
                f.write("---\n\n")
                continue

            score = r.get("intent_score", 0)
            emoji = SCORE_EMOJI.get(score, "⚪")
            f.write(f"## {i}. {emoji} Score {score} — {label}\n\n")
            f.write(f"**Action:** `{r.get('recommended_action', '—')}`  \n")
            f.write(
                f"**Pain:** {r.get('pain_category', '—')} "
                f"({r.get('specificity', '—')})  \n"
            )
            f.write(f"**Buyer type:** {r.get('buyer_type', '—')}  \n")
            f.write(f"**Confidence:** {r.get('confidence', '—')}\n\n")
            f.write(
                f"**Pain in their words:**\n> {r.get('pain_in_words', '—')}\n\n"
            )
            f.write(f"**Why it matters:** {r.get('why_matters', '—')}\n\n")

            opener = r.get("opening_line")
            if opener:
                f.write(f"**Suggested opener:**\n```\n{opener}\n```\n\n")

            ident = r.get("identity") or {}
            f.write("**Identity signals:**\n")
            for key in [
                "name", "company", "role", "location", "industry",
                "linkedin_url", "twitter_handle", "email",
            ]:
                val = ident.get(key)
                if val:
                    f.write(f"- {key}: {val}\n")
            f.write(
                f"- username: {ident.get('username', '—')} "
                f"on {ident.get('platform', '—')}\n\n"
            )

            ctx = r.get("company_context") or {}
            f.write(
                f"**Company context:** {ctx.get('size', '?')} | "
                f"{ctx.get('geography', '?')} | {ctx.get('stage', '?')}\n\n"
            )
            f.write(
                f"**Original:**\n```\n{(post.get('content') or '').strip()}\n```\n\n"
            )
            f.write(f"**Source:** {post.get('source_url', '—')}\n\n---\n\n")


def export_csv(results: list[dict[str, Any]], output_path: Path) -> None:
    """Flat CSV — sortable/filterable in Google Sheets."""
    sorted_results = sorted(results, key=_sort_key, reverse=True)

    headers = [
        "score", "action", "specificity", "pain_category", "buyer_type",
        "platform", "username", "name", "company", "role", "location",
        "industry", "linkedin_url", "email", "company_size", "geography",
        "stage", "pain_in_words", "why_matters", "opening_line",
        "confidence", "source_url", "original_content", "disqualified",
        "disqualifier_reason", "error",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()

        for r in sorted_results:
            post = r.get("_post", {})
            ident = r.get("identity") or {}
            ctx = r.get("company_context") or {}
            writer.writerow({
                "score": (
                    0 if r.get("disqualified") or r.get("error")
                    else (r.get("intent_score") or 0)
                ),
                "action": r.get("recommended_action", ""),
                "specificity": r.get("specificity", ""),
                "pain_category": r.get("pain_category", ""),
                "buyer_type": r.get("buyer_type", ""),
                "platform": post.get("platform", ""),
                "username": ident.get("username") or post.get("username", ""),
                "name": ident.get("name", ""),
                "company": ident.get("company", ""),
                "role": ident.get("role", ""),
                "location": ident.get("location", ""),
                "industry": ident.get("industry", ""),
                "linkedin_url": ident.get("linkedin_url", ""),
                "email": ident.get("email", ""),
                "company_size": ctx.get("size", ""),
                "geography": ctx.get("geography", ""),
                "stage": ctx.get("stage", ""),
                "pain_in_words": r.get("pain_in_words", ""),
                "why_matters": r.get("why_matters", ""),
                "opening_line": r.get("opening_line", ""),
                "confidence": r.get("confidence", ""),
                "source_url": post.get("source_url", ""),
                "original_content": (post.get("content") or "").strip(),
                "disqualified": r.get("disqualified", False),
                "disqualifier_reason": r.get("disqualifier_reason", ""),
                "error": r.get("error", ""),
            })