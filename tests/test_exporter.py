"""Unit tests for the exporter — verifies markdown and CSV output."""

import csv
from pathlib import Path

import pytest

from src.exporter import export_csv, export_markdown


@pytest.fixture
def sample_results() -> list[dict]:
    return [
        {
            "disqualified": False,
            "intent_score": 5,
            "specificity": "SPECIFIC",
            "pain_category": "Bounce Rate / Deliverability",
            "pain_in_words": "Apollo bouncing",
            "buyer_type": "SDR/BDR",
            "identity": {
                "name": None, "company": "Acme",
                "role": "SDR", "location": "Bangalore",
                "industry": "SaaS", "linkedin_url": None,
                "twitter_handle": None, "email": None,
                "username": "u/test", "platform": "Reddit",
            },
            "company_context": {
                "size": "Startup", "geography": "India", "stage": "Hiring/scaling"
            },
            "why_matters": "High intent",
            "recommended_action": "BOTH",
            "opening_line": "saw your note about apollo",
            "confidence": "HIGH",
            "_post": {
                "platform": "Reddit",
                "username": "u/test",
                "content": "Apollo is broken",
                "source_url": "https://reddit.com",
            },
        },
        {
            "disqualified": True,
            "disqualifier_reason": "Apollo employee",
            "_post": {
                "platform": "LinkedIn",
                "username": "marcus",
                "content": "I work at Apollo",
                "source_url": "https://linkedin.com",
            },
        },
    ]


def test_export_markdown(tmp_path: Path, sample_results: list[dict]) -> None:
    out = tmp_path / "report.md"
    export_markdown(sample_results, out)
    content = out.read_text(encoding="utf-8")
    assert "Zintlr Intent Radar" in content
    assert "Score 5" in content
    assert "DISQUALIFIED" in content
    assert "Apollo employee" in content
    assert "Acme" in content


def test_export_csv(tmp_path: Path, sample_results: list[dict]) -> None:
    out = tmp_path / "report.csv"
    export_csv(sample_results, out)

    with out.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    # Highest score first
    assert rows[0]["score"] == "5"
    assert rows[0]["action"] == "BOTH"
    assert rows[0]["company"] == "Acme"
    # Disqualified at the end
    assert rows[1]["disqualified"] == "True"
    assert rows[1]["disqualifier_reason"] == "Apollo employee"


def test_csv_has_all_required_columns(tmp_path: Path, sample_results: list[dict]) -> None:
    out = tmp_path / "report.csv"
    export_csv(sample_results, out)

    with out.open(encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

    expected = {"score", "action", "company", "opening_line",
                "source_url", "disqualified"}
    assert expected.issubset(set(headers))