"""Hacker News scraper via Algolia for Zintlr Pulse.

Uses the free Algolia HN Search API (no authentication required).
Searches for stories and comments mentioning competitor tools.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Callable, Optional

import requests


logger = logging.getLogger(__name__)

TIER1_KEYWORDS = [
    "apollo.io",
    "zoominfo",
    "lusha.com",
    "cognism",
    "rocketreach",
]


class HackerNewsScraper:
    """Scrapes Hacker News via Algolia API."""

    def __init__(self, timeout: int = 30) -> None:
        """Initialize scraper.
        
        Args:
            timeout: HTTP request timeout in seconds.
        """
        self.timeout = timeout
        self.base_url = "https://hn.algolia.com/api/v1/search"

    def _scrape_keyword(
        self,
        keyword: str,
        freshness_days: int
    ) -> tuple[list[dict], Optional[str]]:
        """Scrape HN for mentions of a keyword.
        
        Args:
            keyword: Search keyword (e.g., "apollo").
            freshness_days: Include posts from last N days.
            
        Returns:
            Tuple of (leads_list, error_message).
        """
        leads = []
        cutoff_epoch = int((
            datetime.utcnow() - timedelta(days=freshness_days)
        ).timestamp())
        
        data = None
        hits = []

        for tags in ("story", "comment"):
            params = {
                "query": keyword,
                "tags": tags,
                "numericFilters": f"created_at_i>{cutoff_epoch}",
            }
            logger.info("HN searching for: %s, tags=%s", keyword, tags)
            try:
                resp = requests.get(self.base_url, params=params, timeout=(5, 10))
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.Timeout:
                return [], f"HN: HTTP timeout after 15s on keyword '{keyword}'"
            except requests.exceptions.ConnectionError as e:
                return [], f"HN: connection error - {str(e)[:100]}"
            except requests.exceptions.RequestException as e:
                return [], f"HN: request failed - {str(e)[:100]}"
            except ValueError as e:
                return [], f"HN: invalid JSON response - {str(e)[:100]}"

            if not isinstance(data, dict) or "hits" not in data:
                return [], f"HN: unexpected response format - missing 'hits' key"

            hits = data.get("hits", []) or []
            logger.info("HN: %d results for %s with tags=%s", len(hits), keyword, tags)
            if hits:
                break

        seen_ids = set()
        
        for hit in data["hits"]:
            obj_id = hit.get("objectID")
            
            # Dedupe by object_id
            if obj_id in seen_ids:
                continue
            seen_ids.add(obj_id)
            
            # Extract content
            title = hit.get("title", "")
            comment_text = hit.get("comment_text", "")
            content = (title or comment_text).strip()
            
            if not content:
                continue
            
            # Determine type
            story_id = hit.get("story_id")
            is_story = story_id is None or story_id == hit.get("id")
            
            # Build URL
            if is_story:
                url = f"https://news.ycombinator.com/item?id={hit.get('id')}"
            else:
                url = f"https://news.ycombinator.com/item?id={story_id}"
            
            author = hit.get("author", "anonymous")
            created_epoch = hit.get("created_at_i", 0)
            created_date = datetime.utcfromtimestamp(created_epoch).isoformat() + "Z"
            
            lead = {
                "platform": "Hacker News",
                "source_url": url,
                "username": author,
                "date": created_date,
                "content": content,
                "post_id": f"hn_{obj_id}",
                "has_tier1_keyword": True,  # We searched for the keyword
                "has_tier2_keyword": False,
                "raw_score": hit.get("points", 0),
            }
            leads.append(lead)
        
        return leads, None

    def scrape(
        self,
        freshness_days: int,
        progress_callback: Optional[Callable[[int, int, str, str], None]] = None,
    ) -> tuple[list[dict], list[str]]:
        """Scrape HN for all tier1 keywords.
        
        Args:
            freshness_days: Include posts from last N days.
            progress_callback: Called as (current_idx, total, source_name, status).
            
        Returns:
            Tuple of (all_posts, failures_list).
        """
        all_leads = []
        failures = []
        seen_post_ids = set()
        
        for idx, keyword in enumerate(TIER1_KEYWORDS):
            if progress_callback:
                progress_callback(
                    idx,
                    len(TIER1_KEYWORDS),
                    "Hacker News",
                    keyword,
                )

            logger.info("HN loop keyword %s (%d/%d)", keyword, idx + 1, len(TIER1_KEYWORDS))
            time.sleep(0.5)
            leads, error = self._scrape_keyword(keyword, freshness_days)

            logger.info("HN: keyword %s returned %d leads", keyword, len(leads))

            # Dedupe by post_id
            for lead in leads:
                if lead["post_id"] not in seen_post_ids:
                    all_leads.append(lead)
                    seen_post_ids.add(lead["post_id"])

            if error:
                failures.append(error)
        
        return all_leads, failures
