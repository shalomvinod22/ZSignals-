"""LinkedIn scraper for Zintlr Pulse - V1.3.

Uses Apify's harvestapi/linkedin-post-search ACTOR.
Uses CORRECT field names: searchQueries, maxPosts.
"""

import os
import logging
from typing import Optional, Callable
from datetime import datetime, timezone

from apify_client import ApifyClient

logger = logging.getLogger(__name__)

SEARCH_STRATEGIES = {
    "india_saas_us_shift_sdrs": {
        "label": "Indian SaaS hiring SDRs for US market",
        "enabled_default": True,
        "actor": "harvestapi/linkedin-post-search",
        "max_items": 25,
        "queries": [
            "hiring SDR US shift India",
            "looking for BDR US market India",
        ],
        "estimated_cost_per_run_usd": 1.25,
    },
    "stack_named_hiring": {
        "label": "Job posts naming Apollo/ZoomInfo/Lusha",
        "enabled_default": False,
        "actor": "harvestapi/linkedin-post-search",
        "max_items": 30,
        "queries": [
            "hiring SDR Apollo experience required",
            "BDR ZoomInfo Salesforce required",
        ],
        "estimated_cost_per_run_usd": 1.50,
    },
    "founder_outbound_pain": {
        "label": "Founder/VP posts about outbound pain",
        "enabled_default": False,
        "actor": "harvestapi/linkedin-post-search",
        "max_items": 40,
        "queries": [
            "1% reply rate outbound",
            "outbound is dead 2026",
            "data quality cold email problems",
        ],
        "estimated_cost_per_run_usd": 2.00,
    },
    "funded_indian_b2b": {
        "label": "Funded Indian B2B SaaS posts",
        "enabled_default": False,
        "actor": "harvestapi/linkedin-post-search",
        "max_items": 30,
        "queries": [
            "Series A India SaaS B2B",
            "we just raised India startup",
        ],
        "estimated_cost_per_run_usd": 1.50,
    },
    "stack_frustration_general": {
        "label": "General Apollo/ZoomInfo/Lusha frustration",
        "enabled_default": False,
        "actor": "harvestapi/linkedin-post-search",
        "max_items": 50,
        "queries": [
            "Apollo data quality bad",
            "ZoomInfo APAC inaccurate",
        ],
        "estimated_cost_per_run_usd": 2.50,
    },
}

INDIAN_B2B_SEED_PROFILES = [
    "https://www.linkedin.com/in/aneeshreddy/",
    "https://www.linkedin.com/in/avinashraghava/",
    "https://www.linkedin.com/in/girishmathrubootham/",
    "https://www.linkedin.com/in/sridharvembu/",
    "https://www.linkedin.com/in/krishsubramanian/",
    "https://www.linkedin.com/in/abhinavasthana/",
]


class LinkedInScraper:
    """LinkedIn scraper via Apify harvestapi actor.
    Uses CORRECT field names per harvestapi docs.
    """

    def __init__(self) -> None:
        token = os.environ.get("APIFY_API_TOKEN")
        if not token:
            raise RuntimeError(
                "APIFY_API_TOKEN not set in .env"
            )
        self._client = ApifyClient(token)

    def scrape(
        self,
        freshness_days: int = 7,
        progress_callback: Optional[Callable] = None,
        test_mode: bool = False,
        enabled_strategies: Optional[list] = None,
        watchlist_profiles: Optional[list] = None,
    ):
        if enabled_strategies is None:
            enabled_strategies = [
                k for k, v in SEARCH_STRATEGIES.items()
                if v["enabled_default"]
            ]
        if test_mode:
            enabled_strategies = enabled_strategies[:1]

        all_posts = []
        failures = []
        total = len(enabled_strategies) + (1 if watchlist_profiles else 0)
        step = 0

        for key in enabled_strategies:
            step += 1
            strategy = SEARCH_STRATEGIES.get(key)
            if not strategy:
                continue
            if progress_callback:
                try:
                    progress_callback(
                        step, total,
                        f"LinkedIn: {strategy['label']}", "scraping",
                    )
                except Exception:
                    pass
            try:
                posts = self._run_search(strategy, test_mode)
                all_posts.extend(posts)
                logger.info("LinkedIn %s: %d posts", key, len(posts))
            except Exception as e:
                failures.append(
                    f"LinkedIn {key}: {type(e).__name__}: {str(e)[:120]}"
                )
                logger.exception("LinkedIn scrape failed for %s", key)

        if watchlist_profiles:
            step += 1
            if progress_callback:
                try:
                    progress_callback(
                        step, total,
                        f"LinkedIn watchlist ({len(watchlist_profiles)} accts)",
                        "scraping",
                    )
                except Exception:
                    pass
            try:
                limit = 20 if test_mode else 50
                posts = self._scrape_watchlist(
                    watchlist_profiles[:limit],
                )
                all_posts.extend(posts)
            except Exception as e:
                failures.append(
                    f"LinkedIn watchlist: "
                    f"{type(e).__name__}: {str(e)[:120]}"
                )

        if progress_callback:
            try:
                progress_callback(
                    total, total, "LinkedIn",
                    f"done ({len(all_posts)} posts)",
                )
            except Exception:
                pass

        return all_posts, failures

    def _run_search(self, strategy, test_mode):
        """Uses CORRECT Apify field names: searchQueries, maxPosts."""
        max_items = 5 if test_mode else strategy["max_items"]
        results = []

        for query in strategy["queries"]:
            run_input = {
                "searchQueries": [query],
                "maxPosts": max_items,
            }
            try:
                run = self._client.actor(strategy["actor"]).call(
                    run_input=run_input, timeout_secs=120,
                )
                if not run or "defaultDatasetId" not in run:
                    continue

                items = list(self._client.dataset(
                    run["defaultDatasetId"],
                ).iterate_items())

                logger.info(
                    "Apify returned %d items for: %s",
                    len(items), query,
                )

                for item in items:
                    norm = self._normalize(
                        item, source_strategy=strategy["label"],
                    )
                    if norm:
                        results.append(norm)
            except Exception:
                logger.exception("Apify query failed: %s", query)
                continue

        return results

    def _scrape_watchlist(self, profile_urls):
        results = []
        run_input = {
            "profileUrls": profile_urls,
            "maxPosts": 5,
        }
        try:
            run = self._client.actor(
                "harvestapi/linkedin-profile-posts",
            ).call(run_input=run_input, timeout_secs=180)
            if not run or "defaultDatasetId" not in run:
                return []

            items = list(self._client.dataset(
                run["defaultDatasetId"],
            ).iterate_items())

            for item in items:
                norm = self._normalize(
                    item, source_strategy="curated_watchlist",
                )
                if norm:
                    results.append(norm)
        except Exception:
            logger.exception("Watchlist scrape failed")
        return results

    def _normalize(self, item, source_strategy):
        """Convert harvestapi response to standard lead dict."""
        post_url = (
            item.get("linkedinUrl")
            or item.get("url")
            or item.get("postUrl")
            or ""
        )
        if not post_url:
            return None

        actor = item.get("actor") or item.get("author") or {}
        author_name = actor.get("name") or item.get("authorName") or "unknown"
        author_title = (
            actor.get("position")
            or actor.get("headline")
            or item.get("authorHeadline")
            or ""
        )
        author_profile_url = (
            actor.get("linkedinUrl")
            or actor.get("profileUrl")
            or item.get("authorProfileUrl")
            or ""
        )
        author_company = (
            actor.get("company")
            or item.get("authorCompany")
            or ""
        )
        author_location = (
            actor.get("location")
            or item.get("authorLocation")
            or ""
        )

        text = item.get("content") or item.get("text") or ""
        if len(text) < 30:
            return None

        hashtags = list(item.get("hashtags") or [])
        post_id = item.get("id") or item.get("postId") or post_url

        date_field = (
            item.get("createdAt")
            or item.get("postedAt")
            or item.get("date")
            or ""
        )
        ts = item.get("createdAtTimestamp")
        if isinstance(ts, (int, float)) and ts > 0:
            date_field = datetime.fromtimestamp(
                ts / 1000 if ts > 1e10 else ts,
                tz=timezone.utc,
            ).isoformat()

        likes = 0
        rcs = item.get("reactionTypeCounts") or []
        if isinstance(rcs, list):
            for rc in rcs:
                likes += rc.get("count", 0)
        likes = likes or item.get("likesCount", 0)

        text_lower = text.lower()
        tier1 = ["apollo", "zoominfo", "lusha", "cognism"]
        tier2 = ["outbound", "sdr", "bdr", "reply rate",
                 "data quality", "cold email"]

        return {
            "platform": "LinkedIn",
            "source_url": post_url,
            "username": author_name,
            "user_profile_url": author_profile_url,
            "user_title": author_title,
            "user_company": author_company,
            "user_location": author_location,
            "date": str(date_field),
            "content": text,
            "post_id": f"li_{post_id}",
            "hashtags": hashtags,
            "raw_score": likes,
            "comments_count": item.get("numComments", 0),
            "source_strategy": source_strategy,
            "has_tier1_keyword": any(kw in text_lower for kw in tier1),
            "has_tier2_keyword": any(kw in text_lower for kw in tier2),
        }
