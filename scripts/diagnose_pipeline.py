from dotenv import load_dotenv
load_dotenv()
import sqlite3, json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db import PulseDB

db = PulseDB()
conn = sqlite3.connect(db.db_path)
cur = conn.cursor()

print("=" * 60)
print("PIPELINE DIAGNOSTIC")
print("=" * 60)

# How many LinkedIn posts are unqualified?
cur.execute("""
    SELECT COUNT(*) FROM seen_posts
    WHERE post_id LIKE 'li_%'
    AND post_id NOT IN (SELECT post_id FROM qualifier_cache)
""")
unqualified_li = cur.fetchone()[0]
print(f"\nLinkedIn posts NOT qualified: {unqualified_li}")

# Sample qualifier_cache entry to see schema
cur.execute("SELECT qualifier_json FROM qualifier_cache LIMIT 1")
row = cur.fetchone()
if row:
    try:
        data = json.loads(row[0])
        keys = list(data.keys())
        print(f"\nSample cache schema keys: {keys[:15]}")
        is_v12 = "intent_score" in data or "buyer_type" in data
        is_v13 = "pain_stage" in data or "conversation_kit" in data
        print(f"Has V1.2 keys (BAD): {is_v12}")
        print(f"Has V1.3 keys (GOOD): {is_v13}")
    except Exception as e:
        print(f"Parse error: {e}")

# Look at orchestrator and pipeline files
import pathlib
for f in [
    "src/scraper/orchestrator.py",
    "src/pulse_pipeline.py",
    "src/pipeline.py",
]:
    p = pathlib.Path(f)
    if p.exists():
        print(f"\nFile {f} EXISTS, length={len(p.read_text(encoding='utf-8'))}")

conn.close()
