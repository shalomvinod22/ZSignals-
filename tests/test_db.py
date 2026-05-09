"""Tests for PulseDB database layer."""

import tempfile
from pathlib import Path

import pytest

from src.db import PulseDB


@pytest.fixture
def temp_db() -> PulseDB:
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        db = PulseDB(db_path)
        yield db
        db.close()


def test_pulsedb_creates_tables(temp_db: PulseDB) -> None:
    """Test that all required tables are created."""
    cursor = temp_db.conn.cursor()
    
    # Check seen_posts
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='seen_posts'")
    assert cursor.fetchone() is not None
    
    # Check lead_status
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lead_status'")
    assert cursor.fetchone() is not None
    
    # Check qualifier_cache
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='qualifier_cache'")
    assert cursor.fetchone() is not None

    # Check new V1.3 tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lead_outcomes'")
    assert cursor.fetchone() is not None
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='linkedin_watchlist'")
    assert cursor.fetchone() is not None
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='source_quality'")
    assert cursor.fetchone() is not None


def test_seen_post_tracking(temp_db: PulseDB) -> None:
    """Test marking posts as seen."""
    post_id = "reddit_test_123"
    
    assert not temp_db.is_seen(post_id)
    
    temp_db.mark_seen_batch([(post_id, "reddit")])
    
    assert temp_db.is_seen(post_id)


def test_status_transitions(temp_db: PulseDB) -> None:
    """Test setting and getting lead status."""
    post_id = "reddit_test_456"
    
    # Default status is Pending
    assert temp_db.get_status(post_id) == "Pending"
    
    # Set status
    temp_db.set_status(post_id, "Contacted", "Called 2pm")
    assert temp_db.get_status(post_id) == "Contacted"
    
    # Update status
    temp_db.set_status(post_id, "Replied")
    assert temp_db.get_status(post_id) == "Replied"


def test_qualifier_cache_roundtrip(temp_db: PulseDB) -> None:
    """Test saving and retrieving qualifier cache."""
    post_id = "reddit_test_789"
    cache_data = {
        "intent_score": 5,
        "pain_point": "Bouncing emails",
        "suggested_opener": "Hi there",
    }
    
    # Cache miss
    assert temp_db.get_qualifier_cache(post_id) is None
    
    # Save cache
    temp_db.set_qualifier_cache(post_id, cache_data)
    
    # Cache hit
    cached = temp_db.get_qualifier_cache(post_id)
    assert cached == cache_data


def test_scrape_history_logging(temp_db: PulseDB) -> None:
    """Test scrape history recording."""
    run_id = temp_db.start_scrape_run(["reddit", "g2"], 7)
    assert run_id is not None
    
    stats = {
        "posts_scraped": 42,
        "posts_qualified": 40,
        "high_count": 5,
        "medium_count": 12,
        "low_count": 23,
        "dq_count": 0,
        "error_count": 0,
        "failures": ["g2 timeout"],
        "runtime_seconds": 45.2,
    }
    
    temp_db.finish_scrape_run(run_id, stats)
    
    history = temp_db.get_scrape_history(1)
    assert len(history) == 1
    assert history[0]["posts_scraped"] == 42
    assert history[0]["high_count"] == 5


def test_user_config_persistence(temp_db: PulseDB) -> None:
    """Test user config get/set."""
    temp_db.set_config("default_freshness", "Last 14 days")
    
    value = temp_db.get_config("default_freshness")
    assert value == "Last 14 days"
    
    # Default value
    assert temp_db.get_config("missing_key", "fallback") == "fallback"


def test_get_all_leads_with_status(temp_db: PulseDB) -> None:
    """Test retrieving leads by status."""
    # Set up some leads
    temp_db.set_status("lead1", "Pending")
    temp_db.set_status("lead2", "Contacted")
    temp_db.set_status("lead3", "Contacted")
    
    # Get by status
    contacted = temp_db.get_all_leads_with_status(["Contacted"])
    assert len(contacted) == 2
    
    # Get all
    all_leads = temp_db.get_all_leads_with_status()
    assert len(all_leads) == 3


def test_linkedin_watchlist_and_source_quality_methods(temp_db: PulseDB) -> None:
    # Add a watchlist entry
    temp_db.add_linkedin_watchlist(
        profile_url="https://linkedin.com/in/test-user",
        name="Test User",
        company="TestCo",
        reason="Monitor public LinkedIn signal",
    )

    # Get watchlist and find our entry (auto-seed adds 6 founder profiles)
    watchlist = temp_db.get_linkedin_watchlist()
    assert len(watchlist) >= 1
    test_row = [r for r in watchlist if "test-user" in r["profile_url"]]
    assert len(test_row) == 1
    assert test_row[0]["display_name"] == "Test User"
    assert test_row[0]["source"] == "manual"

    # Test source quality tracking (alternative to the old schema)
    temp_db.record_source_quality("linkedin", "watchlist_scrape", posts_scraped=5, posts_qualified=2)
    quality = temp_db.get_source_quality_summary(days=7)
    assert len(quality) > 0
    assert any(q["source"] == "linkedin" for q in quality)
