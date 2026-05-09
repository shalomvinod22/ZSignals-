"""Pulse pipeline: orchestrates scraping, classification, and qualification.

Combines scraper output with signal classifier and Groq qualifier.
Handles caching and deduplication.
"""

import time
from pathlib import Path
from typing import Callable, Optional

from src.db import PulseDB
from src.demo_data import get_demo_posts
from src.qualifier import Qualifier
from src.scraper.orchestrator import run_scrape
from src.signal_classifier import SignalClassifier


def _is_v13_qualifier_result(result: dict | None) -> bool:
    """Return True only for cached qualifier rows using the V1.3 schema."""
    if not result:
        return False
    return (
        "score" in result
        and "pain_stage" in result
        and "conversation_kit" in result
        and "intent_score" not in result
        and "buyer_type" not in result
    )


def _to_v13_qualifier_result(result: dict, post: dict) -> dict:
    """Coerce legacy or mock qualifier output into the V1.3 schema."""
    if _is_v13_qualifier_result(result):
        return result
    normalized = Qualifier._normalize(result, post)
    if "_post" in result:
        normalized["_post"] = result["_post"]
    return normalized


def run_pulse_scrape(
    sources: list[str],
    freshness_days: int,
    dedup_mode: str,
    db: PulseDB,
    qualifier: Qualifier,
    progress_callback: Optional[Callable[..., None]] = None,
    test_mode: bool = False,
    demo_mode: bool = False,
) -> dict:
    """Run full pulse scrape + qualify pipeline.
    
    Flow:
    1. If demo_mode: use demo posts, skip scraping
    2. Else: scrape via orchestrator
    3. Run signal classifier on each post
    4. For each post:
       a. Check cache; if cached, use cached result
       b. Else call qualifier.analyze(post)
       c. Save to cache
    5. Bucket results by V1.3 score
    6. Compute stats, save scrape_history row
    7. Return full result dict
    
    Args:
        sources: List of source names ("reddit", "g2", "hackernews").
        freshness_days: Include posts from last N days.
        dedup_mode: "all" (ignore seen) or "new_only" (filter seen).
        db: PulseDB instance.
        qualifier: Qualifier instance.
        progress_callback: Called as (current_idx, total, source_name, status).
        test_mode: Run scrapers in test mode.
        demo_mode: Skip scraping, use demo posts.
        
    Returns:
        Dict with keys: posts, buckets, stats, failures, run_id, runtime_seconds.
    """
    start_time = time.time()
    
    # Start scrape run
    run_id = db.start_scrape_run(sources, freshness_days)
    
    # Phase 1: Scraping or demo
    if progress_callback:
        progress_callback(0, 1, "scraping", "Starting scrape...")
    
    if demo_mode:
        raw_posts = get_demo_posts()
        failures = []
        scrape_stats = {
            "reddit_count": 0,
            "g2_count": 0,
            "hn_count": 0,
            "deduped_out": 0,
            "total_unique": len(raw_posts),
        }
    else:
        result = run_scrape(
            sources=sources,
            freshness_days=freshness_days,
            dedup_mode=dedup_mode,
            progress_callback=progress_callback,
            db=db,
            test_mode=test_mode,
        )
        raw_posts = result["posts"]
        failures = result["failures"]
        scrape_stats = result["stats"]
    
    if progress_callback:
        progress_callback(0, 1, "classifying", f"Classifying {len(raw_posts)} posts...")
    
    # Phase 2: Signal classification
    for post in raw_posts:
        signals = SignalClassifier.classify(post.get("content", ""))
        post["signal_types"] = signals
    
    if progress_callback:
        progress_callback(0, 1, "qualifying", f"Qualifying with Groq...")
    
    # Phase 3: Qualification with caching
    qualified_posts = []
    qualifier_calls = 0
    cache_hits = 0
    error_count = 0
    
    for idx, post in enumerate(raw_posts):
        post_id = post["post_id"]
        legacy_result_for_post = {}
        
        # Check cache. Legacy V1.2 rows are intentionally ignored so every
        # source, including already-seen LinkedIn posts, gets V1.3-qualified.
        cached_result = db.get_qualifier_cache(post_id)
        if cached_result:
            if not _is_v13_qualifier_result(cached_result):
                legacy_result_for_post = cached_result
            result = _to_v13_qualifier_result(cached_result, post)
            cache_hits += 1
            if not _is_v13_qualifier_result(cached_result):
                db.set_qualifier_cache(post_id, result)
        else:
            # Call qualifier
            try:
                result = _to_v13_qualifier_result(qualifier.analyze(post), post)
                qualifier_calls += 1
                # Save to cache
                db.set_qualifier_cache(post_id, result)
            except Exception as e:
                error_msg = f"Qualifier error on {post_id}: {type(e).__name__}: {str(e)[:100]}"
                failures.append(error_msg)
                error_count += 1
                result = {
                    "score": 0,
                    "tier": "LOW",
                    "is_disqualified": True,
                    "pain_stage": None,
                    "pain_type": None,
                    "pain_evidence": None,
                    "persona": {
                        "inferred_role": "Unknown",
                        "decision_authority": "Unknown",
                        "geography": "Unknown",
                    },
                    "signal_stack": {
                        "fit": None,
                        "opportunity": None,
                        "intent": None,
                    },
                    "conversation_kit": {
                        "cold_opener_email": None,
                        "linkedin_dm": None,
                        "talking_points": None,
                    },
                    "likely_objections": None,
                    "outbound_strategy": {
                        "primary_channel": None,
                        "expected_response_rate": None,
                        "follow_up_timeline": None,
                    },
                    "reasoning": f"Qualifier error: {str(e)[:100]}",
                    "ae_priority": "Low - monitor",
                }
        
        # Attach result to post
        post.update(result)
        post.update(legacy_result_for_post)
        if "score" in post and "intent_score" not in post:
            post["intent_score"] = post["score"]
        qualified_posts.append(post)
        
        # Progress update
        if progress_callback and idx % 5 == 0:
            progress_callback(
                idx + 1,
                len(raw_posts),
                "qualifying",
                f"Qualified {idx + 1}/{len(raw_posts)}",
            )
    
    if progress_callback:
        progress_callback(0, 1, "bucketing", "Bucketing results...")
    
    # Phase 4: Bucket by intent
    buckets = {
        "HIGH": [],
        "MEDIUM": [],
        "LOW": [],
        "DISQUALIFIED": [],
        "ERROR": [],
    }
    
    stats = {
        "high_count": 0,
        "medium_count": 0,
        "low_count": 0,
        "dq_count": 0,
        "error_count": error_count,
    }
    
    for post in qualified_posts:
        if post.get("is_disqualified"):
            buckets["DISQUALIFIED"].append(post)
            stats["dq_count"] += 1
        elif "score" not in post:
            buckets["ERROR"].append(post)
            stats["error_count"] += 1
        else:
            score = post.get("score", 0)
            if score >= 5:
                buckets["HIGH"].append(post)
                stats["high_count"] += 1
            elif score >= 3:
                buckets["MEDIUM"].append(post)
                stats["medium_count"] += 1
            else:
                buckets["LOW"].append(post)
                stats["low_count"] += 1
    
    # Phase 5: Finalize
    runtime_seconds = time.time() - start_time
    
    final_stats = {
        "posts_scraped": scrape_stats["total_unique"],
        "posts_qualified": len(qualified_posts),
        "high_count": stats["high_count"],
        "medium_count": stats["medium_count"],
        "low_count": stats["low_count"],
        "dq_count": stats["dq_count"],
        "error_count": stats["error_count"],
        "failures": failures,
        "runtime_seconds": runtime_seconds,
    }
    
    db.finish_scrape_run(run_id, final_stats)
    
    if progress_callback:
        progress_callback(1, 1, "complete", "Done!")
    
    return {
        "posts": qualified_posts,
        "buckets": buckets,
        "stats": final_stats,
        "failures": failures,
        "run_id": run_id,
        "runtime_seconds": runtime_seconds,
        "cache_hits": cache_hits,
        "qualifier_calls": qualifier_calls,
    }
