"""Tests for scraper orchestrator."""

from unittest.mock import MagicMock, patch

import pytest

from src.scraper.orchestrator import run_scrape


@pytest.fixture
def mock_db() -> MagicMock:
    """Create a mock database."""
    db = MagicMock()
    db.is_seen.return_value = False
    db.mark_seen_batch.return_value = None
    return db


def test_combines_multiple_sources(mock_db: MagicMock) -> None:
    """Test combining results from multiple scrapers."""
    with patch("src.scraper.reddit_scraper.RedditScraper") as mock_reddit, \
         patch("src.scraper.g2_scraper.G2Scraper") as mock_g2, \
         patch("src.scraper.hackernews_scraper.HackerNewsScraper") as mock_hn:
        
        # Set up mocks
        mock_reddit_inst = MagicMock()
        mock_reddit_inst.scrape.return_value = (
            [{"post_id": "r1", "platform": "Reddit"}],
            []
        )
        mock_reddit.return_value = mock_reddit_inst
        
        mock_g2_inst = MagicMock()
        mock_g2_inst.scrape.return_value = (
            [{"post_id": "g1", "platform": "G2"}],
            []
        )
        mock_g2.return_value = mock_g2_inst
        
        mock_hn_inst = MagicMock()
        mock_hn_inst.scrape.return_value = (
            [{"post_id": "h1", "platform": "Hacker News"}],
            []
        )
        mock_hn.return_value = mock_hn_inst
        
        # Run
        result = run_scrape(
            sources=["reddit", "g2", "hackernews"],
            freshness_days=7,
            dedup_mode="all",
            db=mock_db,
        )
        
        # Verify
        assert len(result["posts"]) == 3
        assert result["stats"]["reddit_count"] == 1
        assert result["stats"]["g2_count"] == 1
        assert result["stats"]["hn_count"] == 1


def test_partial_failure_does_not_abort(mock_db: MagicMock) -> None:
    """Test that one scraper failure doesn't kill entire scrape."""
    with patch("src.scraper.reddit_scraper.RedditScraper") as mock_reddit, \
         patch("src.scraper.g2_scraper.G2Scraper") as mock_g2:
        
        # Reddit succeeds
        mock_reddit_inst = MagicMock()
        mock_reddit_inst.scrape.return_value = (
            [{"post_id": "r1"}],
            []
        )
        mock_reddit.return_value = mock_reddit_inst
        
        # G2 fails
        mock_g2_inst = MagicMock()
        mock_g2_inst.scrape.side_effect = Exception("G2 network error")
        mock_g2.return_value = mock_g2_inst
        
        # Run
        result = run_scrape(
            sources=["reddit", "g2"],
            freshness_days=7,
            dedup_mode="all",
            db=mock_db,
        )
        
        # Verify Reddit succeeded
        assert len(result["posts"]) == 1
        assert result["posts"][0]["post_id"] == "r1"
        
        # Verify G2 failure recorded
        assert len(result["failures"]) == 1
        assert "G2 network error" in result["failures"][0]


def test_dedup_filters_seen_posts(mock_db: MagicMock) -> None:
    """Test that new_only dedup filters out seen posts."""
    with patch("src.scraper.reddit_scraper.RedditScraper") as mock_reddit:
        # Set up mock
        mock_reddit_inst = MagicMock()
        mock_reddit_inst.scrape.return_value = (
            [
                {"post_id": "new_post", "platform": "Reddit"},
                {"post_id": "seen_post", "platform": "Reddit"},
            ],
            []
        )
        mock_reddit.return_value = mock_reddit_inst
        
        # Mock DB: new_post is not seen, seen_post is seen
        def is_seen_side_effect(post_id: str) -> bool:
            return post_id == "seen_post"
        
        mock_db.is_seen.side_effect = is_seen_side_effect
        
        # Run with new_only dedup
        result = run_scrape(
            sources=["reddit"],
            freshness_days=7,
            dedup_mode="new_only",
            db=mock_db,
        )
        
        # Only new_post should be returned
        assert len(result["posts"]) == 1
        assert result["posts"][0]["post_id"] == "new_post"
        
        # 1 post was deduped out
        assert result["stats"]["deduped_out"] == 1


def test_test_mode_limits_scope() -> None:
    """Test that test_mode limits Reddit scrape to r/sales."""
    with patch("src.scraper.reddit_scraper.RedditScraper") as mock_reddit:
        mock_reddit_inst = MagicMock()
        mock_reddit_inst.scrape.return_value = ([], [])
        mock_reddit.return_value = mock_reddit_inst
        
        # Run test_mode
        run_scrape(
            sources=["reddit"],
            freshness_days=7,
            dedup_mode="all",
            test_mode=True,
        )
        
        # Verify test_mode was passed to Reddit scraper
        mock_reddit_inst.scrape.assert_called_once()
        call_kwargs = mock_reddit_inst.scrape.call_args[1]
        assert call_kwargs.get("test_mode") is True
