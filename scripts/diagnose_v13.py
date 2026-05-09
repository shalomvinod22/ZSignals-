"""Comprehensive diagnostic of V1.3 state."""

import sys
import os
import sqlite3
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("ZINTLR PULSE V1.3 DIAGNOSTIC")
print("=" * 70)

# === Check 1: Qualifier prompt ===
print("\n[1] QUALIFIER PROMPT (prompts/qualifier.md)")
prompt_path = Path("prompts/qualifier.md")
if prompt_path.exists():
    content = prompt_path.read_text(encoding="utf-8")
    print(f"  Length: {len(content)} chars")
    checks = {
        "pain_stage": "pain_stage" in content,
        "conversation_kit": "conversation_kit" in content,
        "likely_objections": "likely_objections" in content,
        "outbound_strategy": "outbound_strategy" in content,
        "APAC/India context": "APAC" in content or "India" in content,
        "Persona detection": "persona" in content.lower(),
    }
    for k, v in checks.items():
        print(f"  {k}: {'YES' if v else 'NO'}")
else:
    print("  MISSING - prompts/qualifier.md does not exist")

# === Check 2: Qualifier module exports ===
print("\n[2] QUALIFIER MODULE (src/qualifier.py)")
try:
    import src.qualifier as q
    callables = [n for n in dir(q) if not n.startswith('_')
                 and callable(getattr(q, n))]
    print(f"  Exports: {callables}")
    print(f"  Has qualify_post function: {'qualify_post' in callables}")
    print(f"  Has Qualifier class: {'Qualifier' in callables}")
except Exception as e:
    print(f"  IMPORT ERROR: {e}")

# === Check 3: LinkedIn scraper architecture ===
print("\n[3] LINKEDIN SCRAPER (src/scraper/linkedin_scraper.py)")
ls_path = Path("src/scraper/linkedin_scraper.py")
if ls_path.exists():
    ls_content = ls_path.read_text(encoding="utf-8")
    print(f"  Length: {len(ls_content)} chars")
    print(f"  ApifyClient: {'ApifyClient' in ls_content}")
    print(f"  harvestapi: {'harvestapi' in ls_content}")
    print(f"  SEARCH_STRATEGIES: {'SEARCH_STRATEGIES' in ls_content}")
    print(f"  INDIAN_B2B_SEED_PROFILES: {'INDIAN_B2B_SEED_PROFILES' in ls_content}")
    print(f"  Uses 'searchQueries' (CORRECT): {chr(34) + 'searchQueries' + chr(34) in ls_content}")
    print(f"  Uses 'maxPosts' (CORRECT): {chr(34) + 'maxPosts' + chr(34) in ls_content}")
    print(f"  Uses 'queries' (BAD): {chr(34) + 'queries' + chr(34) + ': [' in ls_content}")
    print(f"  Uses 'maxItems' (BAD): {chr(34) + 'maxItems' + chr(34) in ls_content}")
    print(f"  Has LINKEDIN_AUTH_TOKEN (BAD): {'LINKEDIN_AUTH_TOKEN' in ls_content}")
    print(f"  Has BeautifulSoup import (BAD): {'BeautifulSoup' in ls_content}")
    print(f"  Has proxy.apify (BAD): {'proxy.apify' in ls_content}")
else:
    print("  MISSING")

# === Check 4: DB tables ===
print("\n[4] DATABASE SCHEMA")
try:
    from src.db import PulseDB
    db = PulseDB()
    conn = sqlite3.connect(db.db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"  All tables: {tables}")
    required = ["lead_outcomes", "linkedin_watchlist", "source_quality"]
    for t in required:
        present = t in tables
        print(f"  Required table '{t}': {'YES' if present else 'MISSING'}")
        if present:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            count = cur.fetchone()[0]
            print(f"    Rows: {count}")

    db_methods = [m for m in dir(db) if not m.startswith('_')]
    helper_checks = [
        "get_lead_outcome", "update_lead_outcome",
        "list_watchlist", "add_to_watchlist",
        "record_source_quality", "get_source_quality_summary",
    ]
    for m in helper_checks:
        print(f"  Method db.{m}: {'YES' if m in db_methods else 'MISSING'}")
    conn.close()
except Exception as e:
    print(f"  DB ERROR: {e}")

# === Check 5: Settings tab content ===
print("\n[5] SETTINGS TAB (app.py)")
app_path = Path("app.py")
if app_path.exists():
    app_content = app_path.read_text(encoding="utf-8")
    checks = {
        "LinkedIn Connection section": "LinkedIn Connection" in app_content,
        "Search Strategies section": "Search Strateg" in app_content,
        "Watchlist section": "Watchlist" in app_content,
        "Source Quality section": "Source Quality" in app_content,
    }
    for k, v in checks.items():
        print(f"  {k}: {'YES' if v else 'MISSING'}")

# === Check 6: Lead card UI elements ===
print("\n[6] LEAD CARD UI (app.py V1.3 layout)")
if app_path.exists():
    app_content = app_path.read_text(encoding="utf-8")
    checks = {
        "Renders pain_stage": "pain_stage" in app_content,
        "Renders conversation_kit": "conversation_kit" in app_content,
        "Renders likely_objections": "likely_objections" in app_content,
        "Renders outbound_strategy": "outbound_strategy" in app_content,
        "Status update wiring": "update_lead_outcome" in app_content,
    }
    for k, v in checks.items():
        print(f"  {k}: {'YES' if v else 'MISSING'}")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)