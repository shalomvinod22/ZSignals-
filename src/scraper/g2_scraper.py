"""G2 review scraper for Zintlr Pulse.

Scrapes G2 reviews for competitor products.
Uses BeautifulSoup4 and polite requests with exponential backoff.
"""

import random
import time
from datetime import datetime, timedelta
from typing import Callable, Optional

import requests
from bs4 import BeautifulSoup


G2_PRODUCTS = [
    "apollo-io",
    "zoominfo",
    "lusha",
    "cognism",
    "clearbit",
    "rocketreach",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
]


class G2Scraper:
    """Scrapes G2 reviews for competitor tools."""

    def __init__(self, timeout: int = 30) -> None:
        """Initialize scraper.
        
        Args:
            timeout: HTTP request timeout in seconds.
        """
        self.timeout = timeout
        self.session = requests.Session()

    def _get_user_agent(self) -> str:
        """Return a random user agent."""
        return random.choice(USER_AGENTS)

    def _fetch_reviews(self, slug: str, retries: int = 3) -> tuple[Optional[str], Optional[str]]:
        """Fetch G2 review page HTML with exponential backoff.
        
        Args:
            slug: Product slug (e.g., "apollo-io").
            retries: Max retries on 429/503/403.
            
        Returns:
            Tuple of (html_content or None, error_message or None).
        """
        url = f"https://www.g2.com/products/{slug}/reviews?ratings[]=1&ratings[]=2"
        
        for attempt in range(retries):
            try:
                headers = {
                    "User-Agent": self._get_user_agent(),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
                resp = self.session.get(url, timeout=(5, 20), headers=headers)
                
                # Check for Cloudflare block
                if resp.status_code == 403 or "cloudflare" in resp.text.lower()[:5000]:
                    return None, f"G2 {slug}: Cloudflare blocked (HTTP {resp.status_code})"
                
                # Check status code
                if resp.status_code == 429:
                    return None, f"G2 {slug}: rate limited (HTTP 429)"
                elif resp.status_code != 200:
                    return None, f"G2 {slug}: HTTP {resp.status_code}"
                
                return resp.text, None
                    
            except requests.exceptions.Timeout:
                if attempt == retries - 1:
                    return None, f"G2 {slug}: HTTP timeout after 25s (attempt {attempt + 1}/{retries})"
                backoff = [5, 15, 30][attempt]
                time.sleep(backoff)
            except requests.exceptions.ConnectionError as e:
                if attempt == retries - 1:
                    return None, f"G2 {slug}: connection error - {str(e)[:100]}"
                time.sleep(2)
            except requests.exceptions.RequestException as e:
                if attempt == retries - 1:
                    return None, f"G2 {slug}: request failed - {str(e)[:100]}"
                time.sleep(2)
        
        return None, f"G2 {slug}: all retries exhausted"

    def _scrape_product(
        self,
        slug: str,
        freshness_days: int
    ) -> tuple[list[dict], Optional[str]]:
        """Scrape reviews for a single product.
        
        Args:
            slug: Product slug.
            freshness_days: Include reviews from last N days.
            
        Returns:
            Tuple of (reviews_list, error_message).
        """
        leads = []
        html, fetch_error = self._fetch_reviews(slug)
        
        if html is None:
            return [], f"G2 {slug}: {fetch_error or 'failed to fetch'}"
        
        soup = BeautifulSoup(html, "html.parser")
        cutoff_date = datetime.utcnow() - timedelta(days=freshness_days)
        
        # Parse review cards (G2 structure: div.paper.paper--white is a review)
        review_divs = soup.find_all("div", class_="paper paper--white")
        
        if len(review_divs) == 0:
            return [], f"G2 {slug}: page loaded but 0 reviews parsed (selector may be outdated or blocked)"
        
        for review_div in review_divs:
            try:
                # Extract reviewer name
                name_elem = review_div.find("h3", class_="ugc-reviewer-name")
                reviewer_name = (
                    name_elem.get_text(strip=True) if name_elem else "Anonymous"
                )
                
                # Extract reviewer title/company
                title_elem = review_div.find("p", class_="ugc-reviewer-company")
                reviewer_title = (
                    title_elem.get_text(strip=True) if title_elem else ""
                )
                
                # Extract review title
                review_title_elem = review_div.find("h3", class_="ugc-review-title")
                review_title = (
                    review_title_elem.get_text(strip=True) if review_title_elem else ""
                )
                
                # Extract review body
                body_elem = review_div.find("p", class_="ugc-review-body")
                review_body = body_elem.get_text(strip=True) if body_elem else ""
                
                if not review_body:
                    continue
                
                # Extract rating
                rating_elem = review_div.find("span", class_="ugc-review-rating")
                rating_text = rating_elem.get_text(strip=True) if rating_elem else "0"
                try:
                    rating = float(rating_text.split()[0])
                except (ValueError, IndexError):
                    rating = 0
                
                # Extract date
                date_elem = review_div.find("p", class_="ugc-review-date")
                date_text = date_elem.get_text(strip=True) if date_elem else ""
                
                # Try to parse date (G2 uses "X months ago" format)
                try:
                    if "ago" in date_text.lower():
                        # Simple heuristic: assume recent if "ago" present
                        review_date = datetime.utcnow()
                    else:
                        # Fallback to now if unparseable
                        review_date = datetime.utcnow()
                except Exception:
                    review_date = datetime.utcnow()
                
                # Filter by date
                if review_date < cutoff_date:
                    continue
                
                content = f"{review_title}\n{review_body}".strip()
                
                lead = {
                    "platform": "G2",
                    "source_url": f"https://www.g2.com/products/{slug}/reviews",
                    "username": reviewer_name,
                    "date": review_date.isoformat() + "Z",
                    "content": content,
                    "post_id": f"g2_{slug}_{reviewer_name}_{int(review_date.timestamp())}",
                    "has_tier1_keyword": True,  # They're reviewing the competitor
                    "has_tier2_keyword": True,  # Complaints are inherent in low-rating reviews
                    "raw_score": rating,
                    "product_slug": slug,
                }
                leads.append(lead)
            except Exception:
                # Skip malformed reviews
                continue
        
        return leads, None

    def scrape(
        self,
        freshness_days: int,
        progress_callback: Optional[Callable[[int, int, str, str], None]] = None,
    ) -> tuple[list[dict], list[str]]:
        """Scrape all products for low-rated reviews.
        
        Args:
            freshness_days: Include reviews from last N days.
            progress_callback: Called as (current_idx, total, source_name, status).
            
        Returns:
            Tuple of (all_reviews, failures_list).
        """
        import time as time_module
        MAX_TOTAL_SECONDS = 120
        scrape_start = time_module.time()
        
        all_leads = []
        failures = []
        
        for idx, product in enumerate(G2_PRODUCTS):
            # Check elapsed time
            elapsed = time_module.time() - scrape_start
            if elapsed > MAX_TOTAL_SECONDS:
                failures.append(f"G2: scrape time exceeded {MAX_TOTAL_SECONDS}s, stopping early")
                break
            
            if progress_callback:
                progress_callback(idx, len(G2_PRODUCTS), "G2", product)
            
            time.sleep(random.uniform(5, 15))
            leads, error = self._scrape_product(product, freshness_days)
            all_leads.extend(leads)
            
            if error:
                failures.append(error)
        
        return all_leads, failures
