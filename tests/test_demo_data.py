"""Tests for demo data."""

from datetime import datetime

import pytest

from src.demo_data import get_demo_posts


def test_demo_posts_have_required_fields() -> None:
    """Test that all demo posts have required fields."""
    posts = get_demo_posts()
    
    required_fields = [
        "platform",
        "source_url",
        "username",
        "date",
        "content",
        "post_id",
        "has_tier1_keyword",
        "has_tier2_keyword",
        "raw_score",
    ]
    
    for post in posts:
        for field in required_fields:
            assert field in post, f"Missing field {field} in post {post.get('post_id')}"
            assert post[field] is not None, f"Field {field} is None in post {post.get('post_id')}"


def test_demo_posts_cover_all_score_levels() -> None:
    """Test that demo posts cover various intent levels."""
    posts = get_demo_posts()
    
    # We expect a mix of HIGH, MEDIUM, LOW, and DISQUALIFIED posts
    assert len(posts) == 12
    
    # Posts should have mix of tier1 keywords (HIGH intent signal)
    has_tier1 = [p for p in posts if p["has_tier1_keyword"]]
    has_no_tier1 = [p for p in posts if not p["has_tier1_keyword"]]
    
    # Most should have tier1 keywords
    assert len(has_tier1) > len(has_no_tier1)
    
    # Verify at least one disqualifier
    assert len(has_no_tier1) >= 1


def test_demo_posts_have_unique_ids() -> None:
    """Test that demo posts have unique post_ids."""
    posts = get_demo_posts()
    post_ids = [p["post_id"] for p in posts]
    
    assert len(post_ids) == len(set(post_ids)), "Demo posts have duplicate post_ids"


def test_demo_posts_have_valid_platforms() -> None:
    """Test that demo posts use valid platform names."""
    posts = get_demo_posts()
    valid_platforms = ["Reddit", "Reddit (comment)", "G2", "Hacker News"]
    
    for post in posts:
        assert post["platform"] in valid_platforms, f"Invalid platform: {post['platform']}"


def test_demo_posts_have_valid_dates() -> None:
    """Test that demo posts have valid ISO date strings."""
    posts = get_demo_posts()
    
    for post in posts:
        date_str = post["date"]
        
        # Should be ISO format with Z suffix
        assert date_str.endswith("Z"), f"Date doesn't end with Z: {date_str}"
        
        # Should be parseable
        try:
            datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"Invalid ISO date: {date_str}")
