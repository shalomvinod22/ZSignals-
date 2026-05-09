"""Clear V1.2 cache so the next scrape re-qualifies posts with V1.3 brain."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from src.db import PulseDB  # noqa: E402


def main() -> None:
    db = PulseDB()
    conn = sqlite3.connect(db.db_path)
    cur = conn.cursor()

    cur.execute("DELETE FROM qualifier_cache")
    conn.commit()
    print("Cleared qualifier_cache")

    cur.execute("""
        SELECT post_id, source, first_seen_at
        FROM seen_posts
    """)
    posts_meta = cur.fetchall()
    print(f"Found {len(posts_meta)} posts in seen_posts")
    print("Cache cleared. Next scrape will qualify all scraped posts with V1.3.")
    conn.close()


if __name__ == "__main__":
    main()
