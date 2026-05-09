"""PulseDB: SQLite-backed state management for Zintlr Pulse.

Manages seen posts, lead status, qualifier cache, scrape history, and user config.
All writes use transactions. Connection uses check_same_thread=False for Streamlit safety.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


class PulseDB:
    """SQLite database for Zintlr Pulse scraper and qualifier state."""

    def __init__(self, db_path: str = "data/seen_posts.db") -> None:
        """Initialize database connection and create tables if needed.
        
        Args:
            db_path: Path to SQLite database file. Will be created if missing.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=10.0
        )
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        """Create all required tables if they do not exist."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seen_posts (
                post_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_scrape_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_status (
                post_id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'Pending',
                note TEXT DEFAULT '',
                updated_at TEXT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES seen_posts(post_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qualifier_cache (
                post_id TEXT PRIMARY KEY,
                qualifier_json TEXT NOT NULL,
                qualified_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scrape_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                sources_used TEXT NOT NULL,
                freshness_days INTEGER NOT NULL,
                posts_scraped INTEGER DEFAULT 0,
                posts_qualified INTEGER DEFAULT 0,
                high_count INTEGER DEFAULT 0,
                medium_count INTEGER DEFAULT 0,
                low_count INTEGER DEFAULT 0,
                dq_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                failures TEXT DEFAULT '[]',
                runtime_seconds REAL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_outcomes (
                post_id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending',
                ae_notes TEXT,
                wrong_correction TEXT,
                contacted_at TIMESTAMP,
                replied_at TIMESTAMP,
                won_at TIMESTAMP,
                lost_at TIMESTAMP,
                marked_wrong_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS linkedin_watchlist (
                profile_url TEXT PRIMARY KEY,
                display_name TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT,
                last_scraped TIMESTAMP,
                posts_scraped_count INTEGER DEFAULT 0,
                qualified_leads_count INTEGER DEFAULT 0,
                active BOOLEAN DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_quality (
                source TEXT,
                source_subkey TEXT,
                date DATE DEFAULT (DATE('now')),
                posts_scraped INTEGER DEFAULT 0,
                posts_qualified INTEGER DEFAULT 0,
                high_count INTEGER DEFAULT 0,
                medium_count INTEGER DEFAULT 0,
                low_count INTEGER DEFAULT 0,
                dq_count INTEGER DEFAULT 0,
                PRIMARY KEY (source, source_subkey, date)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        self.conn.commit()
        
        # Auto-seed linkedin_watchlist if empty
        self._seed_watchlist()

    def _seed_watchlist(self) -> None:
        """Seed linkedin_watchlist with curated Indian B2B profiles if empty."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM linkedin_watchlist")
        if cursor.fetchone()[0] > 0:
            return  # Already seeded
        
        seed_profiles = [
            "https://www.linkedin.com/in/aneeshreddy/",
            "https://www.linkedin.com/in/avinashraghava/",
            "https://www.linkedin.com/in/girishmathrubootham/",
            "https://www.linkedin.com/in/sridharvembu/",
            "https://www.linkedin.com/in/krishsubramanian/",
            "https://www.linkedin.com/in/abhinavasthana/",
        ]
        
        for url in seed_profiles:
            cursor.execute(
                "INSERT OR IGNORE INTO linkedin_watchlist (profile_url, source) VALUES (?, ?)",
                (url, "auto_seed")
            )
        self.conn.commit()

    def is_seen(self, post_id: str) -> bool:
        """Check if a post has been seen before.
        
        Args:
            post_id: Unique post identifier.
            
        Returns:
            True if post exists in seen_posts table.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM seen_posts WHERE post_id = ?", (post_id,))
        return cursor.fetchone() is not None

    def mark_seen_batch(self, items: list[tuple[str, str]]) -> None:
        """Mark multiple posts as seen in a single transaction.
        
        Args:
            items: List of (post_id, source) tuples.
        """
        now = datetime.utcnow().isoformat() + "Z"
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("BEGIN")
            for post_id, source in items:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO seen_posts
                    (post_id, source, first_seen_at, last_scrape_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (post_id, source, now, now)
                )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_status(self, post_id: str) -> str:
        """Get the current status of a lead.
        
        Args:
            post_id: Unique post identifier.
            
        Returns:
            Status string ("Pending", "Contacted", "Replied", "Won", "Lost", "Skipped")
            or "Pending" if not found.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT status FROM lead_status WHERE post_id = ?", (post_id,))
        row = cursor.fetchone()
        return row[0] if row else "Pending"

    def set_status(self, post_id: str, status: str, note: str = "") -> None:
        """Set the status and optional note for a lead.
        
        Args:
            post_id: Unique post identifier.
            status: New status value.
            note: Optional note text.
        """
        now = datetime.utcnow().isoformat() + "Z"
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("BEGIN")
            cursor.execute(
                """
                INSERT OR REPLACE INTO lead_status
                (post_id, status, note, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (post_id, status, note, now)
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_note(self, post_id: str) -> str:
        """Get the note for a lead.
        
        Args:
            post_id: Unique post identifier.
            
        Returns:
            Note text or empty string if not found.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT note FROM lead_status WHERE post_id = ?", (post_id,))
        row = cursor.fetchone()
        return row[0] if row else ""

    def get_qualifier_cache(self, post_id: str) -> Optional[dict]:
        """Retrieve cached qualifier result for a post.
        
        Args:
            post_id: Unique post identifier.
            
        Returns:
            Parsed JSON dict or None if not cached.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT qualifier_json FROM qualifier_cache WHERE post_id = ?",
            (post_id,)
        )
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def set_qualifier_cache(self, post_id: str, qualifier_dict: dict) -> None:
        """Store a qualifier result in cache, or delete if None.
        
        Args:
            post_id: Unique post identifier.
            qualifier_dict: Parsed result dict from qualifier, or None to delete.
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("BEGIN")
            if qualifier_dict is None:
                cursor.execute("DELETE FROM qualifier_cache WHERE post_id = ?", (post_id,))
            else:
                now = datetime.utcnow().isoformat() + "Z"
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO qualifier_cache
                    (post_id, qualifier_json, qualified_at)
                    VALUES (?, ?, ?)
                    """,
                    (post_id, json.dumps(qualifier_dict), now)
                )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def clear_qualifier_cache(self) -> None:
        """Remove all cached qualifier results."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN")
            cursor.execute("DELETE FROM qualifier_cache")
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def record_lead_outcome(self, post_id: str, outcome: str, notes: str = "") -> None:
        """Store a final lead outcome for a post."""
        now = datetime.utcnow().isoformat() + "Z"
        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN")
            cursor.execute(
                """
                INSERT OR REPLACE INTO lead_outcomes
                (post_id, outcome, notes, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (post_id, outcome, notes, now),
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_lead_outcome(self, post_id: str) -> Optional[dict]:
        """Retrieve the saved lead outcome for a post."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM lead_outcomes WHERE post_id = ?",
            (post_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_lead_outcome(self, post_id: str, status: Optional[str] = None, **kwargs) -> bool:
        """Update lead outcome for a post.
        
        Args:
            post_id: Post identifier
            status: New status (pending, contacted, replied, won, lost, wrong)
            **kwargs: Other fields (ae_notes, wrong_correction, etc.)
        
        Returns:
            True if update successful
        """
        cursor = self.conn.cursor()
        try:
            updates = []
            values = []
            
            if status is not None:
                updates.append("status = ?")
                values.append(status)
            
            for key in ['ae_notes', 'wrong_correction', 'contacted_at', 'replied_at', 'won_at', 'lost_at', 'marked_wrong_at']:
                if key in kwargs:
                    updates.append(f"{key} = ?")
                    values.append(kwargs[key])
            
            if not updates:
                return True
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(post_id)
            
            query = f"UPDATE lead_outcomes SET {', '.join(updates)} WHERE post_id = ?"
            cursor.execute(query, values)
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            raise e

    def list_watchlist(self, active_only: bool = True) -> list:
        """List LinkedIn watchlist profiles.
        
        Args:
            active_only: If True, only return active=1 profiles
        
        Returns:
            List of watchlist dicts
        """
        cursor = self.conn.cursor()
        if active_only:
            cursor.execute("SELECT * FROM linkedin_watchlist WHERE active = 1")
        else:
            cursor.execute("SELECT * FROM linkedin_watchlist")
        return [dict(row) for row in cursor.fetchall()]

    def add_to_watchlist(self, profile_url: str, display_name: Optional[str] = None, source: str = "manual") -> bool:
        """Add a profile to the LinkedIn watchlist.
        
        Args:
            profile_url: LinkedIn profile URL
            display_name: Optional display name
            source: Source of the profile (manual, auto_seed, etc.)
        
        Returns:
            True if added successfully
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT OR REPLACE INTO linkedin_watchlist (profile_url, display_name, source, added_at, active) VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1)",
                (profile_url, display_name, source)
            )
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def record_source_quality(self, source: str, source_subkey: str, **counts) -> None:
        """Record source quality metrics.
        
        Args:
            source: Source name (reddit, linkedin, hackernews, etc.)
            source_subkey: Strategy/subkey (e.g., strategy name)
            **counts: Metrics dict with keys: posts_scraped, posts_qualified, high_count, medium_count, low_count, dq_count
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO source_quality 
                   (source, source_subkey, posts_scraped, posts_qualified, high_count, medium_count, low_count, dq_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source, source_subkey,
                    counts.get('posts_scraped', 0),
                    counts.get('posts_qualified', 0),
                    counts.get('high_count', 0),
                    counts.get('medium_count', 0),
                    counts.get('low_count', 0),
                    counts.get('dq_count', 0),
                )
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_source_quality_summary(self, days: int = 7) -> list:
        """Get source quality summary for the last N days.
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of summary dicts
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT source, source_subkey, date, 
                      SUM(posts_scraped) as total_scraped,
                      SUM(posts_qualified) as total_qualified,
                      SUM(high_count) as high,
                      SUM(medium_count) as medium,
                      SUM(low_count) as low,
                      SUM(dq_count) as dq
               FROM source_quality
               WHERE date >= DATE('now', ? || ' days')
               GROUP BY source, source_subkey, date
               ORDER BY date DESC
            """,
            (f"-{days}",)
        )
        return [dict(row) for row in cursor.fetchall()]

    def add_linkedin_watchlist_old(
        self,
        profile_url: str,
        name: Optional[str] = None,
        company: Optional[str] = None,
        reason: str = "",
    ) -> None:
        """Deprecated - compatibility shim."""
        # Map old schema to new
        self.add_to_watchlist(profile_url, display_name=name, source="manual")

    def get_linkedin_watchlist_old(self, limit: int = 50) -> list[dict]:
        """Deprecated - use list_watchlist instead."""
        return []

    # =============================================================================
    # Compatibility wrappers for tests and existing code
    # =============================================================================
    
    def add_linkedin_watchlist(
        self,
        profile_url: str,
        name: Optional[str] = None,
        company: Optional[str] = None,
        reason: str = "",
    ) -> None:
        """Compatibility wrapper - maps old signature to new add_to_watchlist."""
        self.add_to_watchlist(profile_url, display_name=name, source="manual")

    def get_linkedin_watchlist(self, limit: int = 50) -> list[dict]:
        """Compatibility wrapper - maps old signature to new list_watchlist."""
        return self.list_watchlist(active_only=True)

    def clear_linkedin_watchlist_old(self) -> None:
        """Clear the LinkedIn watchlist."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN")
            cursor.execute("DELETE FROM linkedin_watchlist")
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def set_source_quality(self, source: str, quality: str, notes: str = "") -> None:
        """Store quality assessment for a source."""
        now = datetime.utcnow().isoformat() + "Z"
        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN")
            cursor.execute(
                """
                INSERT OR REPLACE INTO source_quality
                (source, quality, last_checked_at, notes)
                VALUES (?, ?, ?, ?)
                """,
                (source, quality, now, notes),
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_source_quality(self, source: str) -> Optional[dict]:
        """Retrieve the latest quality assessment for a source."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT source, quality, last_checked_at, notes FROM source_quality WHERE source = ?",
            (source,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def clear_source_quality_old(self) -> None:
        """Deprecated."""
        pass

    def start_scrape_run_old(self, sources: list[str], freshness_days: int) -> int:
        """Deprecated - compatibility shim."""
        return self.start_scrape_run(sources, freshness_days)

    def start_scrape_run(self, sources: list[str], freshness_days: int) -> int:
        """Start a new scrape run and return its ID.
        
        Args:
            sources: List of source names (e.g., ["reddit", "g2"]).
            freshness_days: Window size in days for this scrape.
            
        Returns:
            Run ID (row id) for later finish_scrape_run() call.
        """
        now = datetime.utcnow().isoformat() + "Z"
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("BEGIN")
            cursor.execute(
                """
                INSERT INTO scrape_history
                (started_at, sources_used, freshness_days)
                VALUES (?, ?, ?)
                """,
                (now, json.dumps(sources), freshness_days)
            )
            run_id = cursor.lastrowid
            self.conn.commit()
            return run_id
        except Exception as e:
            self.conn.rollback()
            raise e

    def finish_scrape_run(self, run_id: int, stats: dict) -> None:
        """Mark a scrape run as complete with final statistics.
        
        Args:
            run_id: Run ID from start_scrape_run().
            stats: Dict with keys: posts_scraped, posts_qualified, high_count,
                   medium_count, low_count, dq_count, error_count, failures,
                   runtime_seconds.
        """
        now = datetime.utcnow().isoformat() + "Z"
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("BEGIN")
            cursor.execute(
                """
                UPDATE scrape_history SET
                    finished_at = ?,
                    posts_scraped = ?,
                    posts_qualified = ?,
                    high_count = ?,
                    medium_count = ?,
                    low_count = ?,
                    dq_count = ?,
                    error_count = ?,
                    failures = ?,
                    runtime_seconds = ?
                WHERE id = ?
                """,
                (
                    now,
                    stats.get("posts_scraped", 0),
                    stats.get("posts_qualified", 0),
                    stats.get("high_count", 0),
                    stats.get("medium_count", 0),
                    stats.get("low_count", 0),
                    stats.get("dq_count", 0),
                    stats.get("error_count", 0),
                    json.dumps(stats.get("failures", [])),
                    stats.get("runtime_seconds"),
                    run_id
                )
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_scrape_history(self, limit: int = 20) -> list[dict]:
        """Retrieve recent scrape runs.
        
        Args:
            limit: Maximum number of recent runs to return.
            
        Returns:
            List of dicts with run metadata. Newest first.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM scrape_history
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append(dict(row))
        return result

    def get_config(self, key: str, default: str = "") -> str:
        """Retrieve a user configuration value.
        
        Args:
            key: Configuration key.
            default: Value to return if key not found.
            
        Returns:
            Configuration value or default.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM user_config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

    def set_config(self, key: str, value: str) -> None:
        """Store a user configuration value.
        
        Args:
            key: Configuration key.
            value: Configuration value.
        """
        now = datetime.utcnow().isoformat() + "Z"
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("BEGIN")
            cursor.execute(
                """
                INSERT OR REPLACE INTO user_config
                (key, value, updated_at)
                VALUES (?, ?, ?)
                """,
                (key, value, now)
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_all_leads_with_status(self, status_filter: Optional[list[str]] = None) -> list[dict]:
        """Retrieve all leads with their current status.
        
        Args:
            status_filter: If provided, only include leads with these statuses.
            
        Returns:
            List of dicts with post_id, status, note, updated_at.
        """
        cursor = self.conn.cursor()
        
        if status_filter:
            placeholders = ",".join("?" * len(status_filter))
            query = f"""
                SELECT post_id, status, note, updated_at
                FROM lead_status
                WHERE status IN ({placeholders})
                ORDER BY updated_at DESC
            """
            cursor.execute(query, status_filter)
        else:
            cursor.execute(
                """
                SELECT post_id, status, note, updated_at
                FROM lead_status
                ORDER BY updated_at DESC
                """
            )
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def reset_seen_posts(self) -> None:
        """Clear the seen_posts table. Use with caution — allows re-scraping all posts."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN")
            cursor.execute("DELETE FROM seen_posts")
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
