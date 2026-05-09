"""Scraper orchestrator for Zintlr Pulse.

Coordinates multiple scrapers, applies deduplication, and handles failures gracefully.
One source failure never kills the entire scrape.
"""

import logging
import os
from typing import Callable, Optional

from dotenv import load_dotenv

from src.db import PulseDB


load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)


def run_scrape(
    sources: list[str],
    freshness_days: int,
    dedup_mode: str,
    progress_callback: Optional[Callable] = None,
    db: Optional[PulseDB] = None,
    test_mode: bool = False,
) -> dict:
    """Run multi-source scrape with deduplication.
    
    Args:
        sources: List of source names: "reddit", "g2", "hackernews", "linkedin".
        freshness_days: Include posts from last N days.
        dedup_mode: "all" (ignore seen) or "new_only" (filter seen).
        progress_callback: Called as (current_idx, total, source_name, status).
        db: PulseDB instance for tracking seen posts.
        test_mode: If True, run in test mode (limited scope).
        
    Returns:
        Dict with keys: posts (list), failures (list), stats (dict).
        Posts are NOT deduplicated — that happens at caller level if needed.
    """
    all_posts = []
    all_failures = []
    stats_map = {
        "reddit": "reddit_count",
        "g2": "g2_count",
        "hackernews": "hn_count",
        "linkedin": "linkedin_count",
    }
    stats = {
        "reddit_count": 0,
        "g2_count": 0,
        "hn_count": 0,
        "linkedin_count": 0,
        "deduped_out": 0,
        "total_unique": 0,
    }
    
    # REDDIT
    if "reddit" in sources:
        logger.info("Starting Reddit scraper...")
        try:
            from src.scraper.reddit_scraper import RedditScraper
            reddit = RedditScraper()
            reddit_posts, reddit_failures = reddit.scrape(
                freshness_days,
                progress_callback=progress_callback,
                test_mode=test_mode
            )
            all_posts.extend(reddit_posts)
            all_failures.extend(reddit_failures)
            stats["reddit_count"] = len(reddit_posts)
            logger.info(f"Reddit done: {len(reddit_posts)} posts, {len(reddit_failures)} failures")
        except ImportError as e:
            error_msg = f"Reddit scraper import failed: {type(e).__name__}: {str(e)[:200]}"
            logger.error(error_msg)
            all_failures.append(error_msg)
            stats["reddit_count"] = 0
        except Exception as e:
            error_msg = f"Reddit scraper crashed: {type(e).__name__}: {str(e)[:200]}"
            logger.error(error_msg)
            all_failures.append(error_msg)
            stats["reddit_count"] = 0
    
    # G2
    # Known issue: G2 is Cloudflare-blocked in V1.2 and may fail often without paid proxy support.
    if "g2" in sources:
        logger.info("Starting G2 scraper...")
        try:
            from src.scraper.g2_scraper import G2Scraper
            g2 = G2Scraper()
            g2_posts, g2_failures = g2.scrape(
                freshness_days,
                progress_callback=progress_callback
            )
            all_posts.extend(g2_posts)
            all_failures.extend(g2_failures)
            stats["g2_count"] = len(g2_posts)
            logger.info(f"G2 done: {len(g2_posts)} posts, {len(g2_failures)} failures")
        except ImportError as e:
            error_msg = f"G2 scraper import failed: {type(e).__name__}: {str(e)[:200]}"
            logger.error(error_msg)
            all_failures.append(error_msg)
            stats["g2_count"] = 0
        except Exception as e:
            error_msg = f"G2 scraper crashed: {type(e).__name__}: {str(e)[:200]}"
            logger.error(error_msg)
            all_failures.append(error_msg)
            stats["g2_count"] = 0
    
    # HACKERNEWS
    if "hackernews" in sources:
        logger.info("Starting Hacker News scraper...")
        try:
            from src.scraper.hackernews_scraper import HackerNewsScraper
            hn = HackerNewsScraper()
            hn_posts, hn_failures = hn.scrape(
                freshness_days,
                progress_callback=progress_callback
            )
            all_posts.extend(hn_posts)
            all_failures.extend(hn_failures)
            stats["hn_count"] = len(hn_posts)
            logger.info(f"HN done: {len(hn_posts)} posts, {len(hn_failures)} failures")
        except ImportError as e:
            error_msg = f"HN scraper import failed: {type(e).__name__}: {str(e)[:200]}"
            logger.error(error_msg)
            all_failures.append(error_msg)
            stats["hn_count"] = 0
        except Exception as e:
            error_msg = f"HN scraper crashed: {type(e).__name__}: {str(e)[:200]}"
            logger.error(error_msg)
            all_failures.append(error_msg)
            stats["hn_count"] = 0

    # LINKEDIN
    if "linkedin" in sources:
        logger.info("Starting LinkedIn scraper...")
        try:
            from src.scraper.linkedin_scraper import LinkedInScraper
            linkedin = LinkedInScraper()
            li_posts, li_failures = linkedin.scrape(
                freshness_days,
                progress_callback=progress_callback,
                test_mode=test_mode,
            )
            all_posts.extend(li_posts)
            all_failures.extend(li_failures)
            stats["linkedin_count"] = len(li_posts)
            logger.info(f"LinkedIn done: {len(li_posts)} posts, {len(li_failures)} failures")
        except ImportError as e:
            error_msg = f"LinkedIn scraper import failed: {type(e).__name__}: {str(e)[:200]}"
            logger.error(error_msg)
            all_failures.append(error_msg)
            stats["linkedin_count"] = 0
        except Exception as e:
            error_msg = f"LinkedIn scraper crashed: {type(e).__name__}: {str(e)[:200]}"
            logger.error(error_msg)
            all_failures.append(error_msg)
            stats["linkedin_count"] = 0

    # Filter out seen posts when requested, but keep seen posts that still need
    # V1.3 qualification. This lets a cache clear or stale V1.2 cache repair
    # flow qualify LinkedIn posts that were already inserted into seen_posts.
    if dedup_mode == "new_only" and db:
        filtered_posts = []
        for post in all_posts:
            cached = db.get_qualifier_cache(post["post_id"])
            has_v13_cache = not isinstance(cached, dict) or (
                cached
                and "score" in cached
                and "pain_stage" in cached
                and "conversation_kit" in cached
                and "intent_score" not in cached
                and "buyer_type" not in cached
            )
            if not db.is_seen(post["post_id"]) or not has_v13_cache:
                filtered_posts.append(post)
            else:
                stats["deduped_out"] += 1
        all_posts = filtered_posts

    if db:
        db.mark_seen_batch([
            (post["post_id"], post.get("platform", "unknown"))
            for post in all_posts
        ])
    
    # Dedupe posts within this scrape
    seen_ids = set()
    deduped_posts = []
    for post in all_posts:
        pid = post["post_id"]
        if pid not in seen_ids:
            deduped_posts.append(post)
            seen_ids.add(pid)
    
    stats["total_unique"] = len(deduped_posts)
    
    logger.info(f"Scrape complete: {len(deduped_posts)} total unique posts, {len(all_failures)} total failures")
    
    return {
        "posts": deduped_posts,
        "failures": all_failures,
        "stats": stats,
    }
