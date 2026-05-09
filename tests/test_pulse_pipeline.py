"""Tests for pulse pipeline."""

from unittest.mock import MagicMock, patch
import tempfile
from pathlib import Path

import pytest

from src.db import PulseDB
from src.pulse_pipeline import run_pulse_scrape


@pytest.fixture
def temp_db() -> PulseDB:
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        db = PulseDB(db_path)
        yield db
        db.close()


@pytest.fixture
def mock_qualifier() -> MagicMock:
    """Create a mock qualifier."""
    qualifier = MagicMock()
    qualifier.analyze.return_value = {
        "intent_score": 5,
        "pain_point": "Test pain",
        "suggested_opener": "Test opener",
        "why_this_matters": "Test reason",
    }
    return qualifier


def test_pipeline_uses_qualifier_cache(temp_db: PulseDB, mock_qualifier: MagicMock) -> None:
    """Test that pipeline uses cached qualifier results."""
    with patch("src.pulse_pipeline.run_scrape") as mock_scrape:
        # Set up mock scrape
        mock_scrape.return_value = {
            "posts": [
                {
                    "post_id": "p1",
                    "platform": "Reddit",
                    "content": "Test post",
                    "signal_types": [],
                }
            ],
            "failures": [],
            "stats": {
                "reddit_count": 1,
                "g2_count": 0,
                "hn_count": 0,
                "deduped_out": 0,
                "total_unique": 1,
            },
        }
        
        # Pre-populate cache
        cached_result = {
            "intent_score": 4,
            "pain_point": "Cached pain",
        }
        temp_db.set_qualifier_cache("p1", cached_result)
        
        # Run pipeline
        result = run_pulse_scrape(
            sources=["reddit"],
            freshness_days=7,
            dedup_mode="new_only",
            db=temp_db,
            qualifier=mock_qualifier,
            demo_mode=False,
        )
        
        # Verify cache was used (qualifier.analyze not called)
        mock_qualifier.analyze.assert_not_called()
        
        # Verify result used cached value
        assert result["posts"][0]["intent_score"] == 4
        assert result["posts"][0]["pain_point"] == "Cached pain"


def test_pipeline_buckets_results_correctly(temp_db: PulseDB, mock_qualifier: MagicMock) -> None:
    """Test that pipeline buckets results by intent score."""
    with patch("src.pulse_pipeline.run_scrape") as mock_scrape:
        # Set up mock scrape with varied scores
        mock_scrape.return_value = {
            "posts": [
                {
                    "post_id": "high",
                    "platform": "Reddit",
                    "content": "Test",
                    "signal_types": [],
                },
                {
                    "post_id": "med",
                    "platform": "Reddit",
                    "content": "Test",
                    "signal_types": [],
                },
                {
                    "post_id": "low",
                    "platform": "Reddit",
                    "content": "Test",
                    "signal_types": [],
                },
            ],
            "failures": [],
            "stats": {
                "reddit_count": 3,
                "g2_count": 0,
                "hn_count": 0,
                "deduped_out": 0,
                "total_unique": 3,
            },
        }
        
        # Set up qualifier to return different scores
        def analyze_side_effect(post: dict) -> dict:
            if post["post_id"] == "high":
                return {"intent_score": 5}
            elif post["post_id"] == "med":
                return {"intent_score": 3}
            else:
                return {"intent_score": 1}
        
        mock_qualifier.analyze.side_effect = analyze_side_effect
        
        # Run pipeline
        result = run_pulse_scrape(
            sources=["reddit"],
            freshness_days=7,
            dedup_mode="all",
            db=temp_db,
            qualifier=mock_qualifier,
            demo_mode=False,
        )
        
        # Verify bucketing
        assert len(result["buckets"]["HIGH"]) == 1
        assert len(result["buckets"]["MEDIUM"]) == 1
        assert len(result["buckets"]["LOW"]) == 1
        assert result["stats"]["high_count"] == 1
        assert result["stats"]["medium_count"] == 1
        assert result["stats"]["low_count"] == 1


def test_demo_mode_skips_scraping(temp_db: PulseDB, mock_qualifier: MagicMock) -> None:
    """Test that demo_mode bypasses scraping."""
    with patch("src.pulse_pipeline.run_scrape") as mock_scrape:
        # Run with demo_mode
        result = run_pulse_scrape(
            sources=["reddit", "g2"],
            freshness_days=7,
            dedup_mode="all",
            db=temp_db,
            qualifier=mock_qualifier,
            demo_mode=True,
        )
        
        # Verify run_scrape was never called
        mock_scrape.assert_not_called()
        
        # Verify we got demo posts
        assert len(result["posts"]) == 12
