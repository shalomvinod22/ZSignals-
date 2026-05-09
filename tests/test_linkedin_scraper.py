import pytest

from src.scraper.linkedin_scraper import LinkedInScraper


def test_linkedin_scraper_requires_apify_token(monkeypatch) -> None:
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="APIFY_API_TOKEN"):
        LinkedInScraper()
