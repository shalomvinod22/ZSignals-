import os
import time
import logging
from datetime import datetime, timezone
from typing import Optional, Callable

from apify_client import ApifyClient


logger = logging.getLogger(__name__)

SUBREDDITS = [
    "sales",
    "SalesOperations",
    "LeadGeneration",
    "coldemail",
    "SaaS",
    "IndianStartups",
    "StartupsIndia",
    "developersIndia",
]

TIER1_KEYWORDS = [
    "apollo",
    "zoominfo",
    "lusha",
    "cognism",
    "clearbit",
    "rocketreach",
    "apollo.io",
]

TIER2_KEYWORDS = [
    "bouncing",
    "bounce rate",
    "wrong numbers",
    "bad data",
    "inaccurate",
    "alternative",
    "switching",
    "leaving",
    "cancelled",
    "outbound stack",
    "data quality",
    "apac",
    "india data",
    "verified emails",
    "direct dials",
]

ACTOR_ID = "harshmaur/reddit-scraper"
ACTOR_TIMEOUT_SEC = 120
TOTAL_TIMEOUT_SEC = 240


class RedditScraper:
    """Scrapes Reddit via Apify (harshmaur/reddit-scraper actor)."""

    def __init__(self) -> None:
        token = os.environ.get("APIFY_API_TOKEN")
        if not token:
            raise RuntimeError(
                "APIFY_API_TOKEN not set in environment. "
                "Get a free token at console.apify.com -> Settings -> "
                "Integrations and add it to your .env file."
            )
        self._client = ApifyClient(token)

    def scrape(
        self,
        freshness_days: int,
        progress_callback: Optional[Callable] = None,
        test_mode: bool = False,
    ) -> tuple[list[dict], list[str]]:
        """Run the scrape. Returns (posts, failures)."""
        subs = ["sales"] if test_mode else list(SUBREDDITS)
        days = 1 if test_mode else freshness_days
        max_per_sub = 10 if test_mode else 50

        all_posts: list[dict] = []
        failures: list[str] = []
        start = time.time()
        cutoff_epoch = (
            datetime.now(timezone.utc).timestamp() - days * 86400
        )

        for idx, sub in enumerate(subs, 1):
            if progress_callback:
                progress_callback(idx, len(subs), f"Reddit r/{sub}", "scraping")

            elapsed = time.time() - start
            if elapsed > TOTAL_TIMEOUT_SEC:
                failures.append(
                    f"Reddit: total scrape budget {TOTAL_TIMEOUT_SEC}s "
                    f"exceeded, stopping early after r/{sub}"
                )
                break

            try:
                sub_posts = self._scrape_subreddit(sub, max_per_sub, cutoff_epoch)
                all_posts.extend(sub_posts)
                logger.info(
                    "r/%s: %d posts within %d days",
                    sub,
                    len(sub_posts),
                    days,
                )
            except Exception as e:
                failures.append(
                    f"r/{sub}: {type(e).__name__}: {str(e)[:150]}"
                )
                logger.exception("Apify scrape failed for r/%s", sub)
                continue

        if progress_callback:
            progress_callback(len(subs), len(subs), "Reddit", f"done ({len(all_posts)} posts)")

        return all_posts, failures

    def _scrape_subreddit(
        self,
        sub: str,
        max_posts: int,
        cutoff_epoch: float,
    ) -> list[dict]:
        """Run one Apify actor call for one subreddit."""
        run_input = {
            "startUrls": [{"url": f"https://www.reddit.com/r/{sub}/new/"}],
            "maxItems": max_posts,
            "type": "posts",
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            },
        }

        run = self._client.actor(ACTOR_ID).call(
            run_input=run_input,
            timeout_secs=ACTOR_TIMEOUT_SEC,
        )
        if not run or "defaultDatasetId" not in run:
            return []

        dataset = self._client.dataset(run["defaultDatasetId"])
        items = list(dataset.iterate_items())

        return [
            self._normalize_item(item, sub)
            for item in items
            if self._is_within_window(item, cutoff_epoch)
        ]

    @staticmethod
    def _is_within_window(item: dict, cutoff_epoch: float) -> bool:
        ts = item.get("createdAt") or item.get("created_utc") or 0
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
            except (ValueError, TypeError):
                return True
        try:
            return float(ts) >= cutoff_epoch
        except (TypeError, ValueError):
            return True

    def _normalize_item(self, item: dict, sub: str) -> dict:
        title = item.get("title") or ""
        body = (
            item.get("text") or item.get("selftext") or item.get("body") or ""
        )
        content = f"{title}\n\n{body}".strip()

        text_lower = content.lower()
        has_t1 = any(kw in text_lower for kw in TIER1_KEYWORDS)
        has_t2 = any(kw in text_lower for kw in TIER2_KEYWORDS)

        date_field = item.get("createdAt") or item.get("created_utc") or item.get("date") or ""
        if isinstance(date_field, (int, float)):
            date_field = datetime.fromtimestamp(date_field, tz=timezone.utc).isoformat()

        raw_id = item.get("id") or item.get("postId") or item.get("name") or item.get("parsedId") or ""
        post_id = raw_id if str(raw_id).startswith("t3_") else f"t3_{raw_id}"

        return {
            "platform": "Reddit",
            "source_url": (
                item.get("contentUrl")
                or item.get("postUrl")
                or item.get("url")
                or item.get("permalink")
                or ""
            ),
            "username": (
                item.get("username")
                or item.get("author")
                or item.get("authorName")
                or "unknown"
            ),
            "date": str(date_field),
            "content": content,
            "post_id": post_id,
            "has_tier1_keyword": has_t1,
            "has_tier2_keyword": has_t2,
            "raw_score": item.get("score") or item.get("ups") or item.get("upVotes") or 0,
            "subreddit": sub,
        }
