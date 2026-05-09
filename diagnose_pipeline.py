"""Discover actual DB schema before querying."""
from dotenv import load_dotenv
load_dotenv()

import sqlite3
from src.db import PulseDB

db = PulseDB()
conn = sqlite3.connect(db.db_path)
cur = conn.cursor()

print("=" * 70)
print("DB SCHEMA DISCOVERY")
print("=" * 70)

# 1. List all tables
print("\n[1] ALL TABLES")
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
for t in tables:
    print(f"  - {t}")

# 2. Show schema of each relevant table
for table in ["seen_posts", "qualifier_cache", "scrape_history"]:
    if table not in tables:
        print(f"\n[!] Table '{table}' DOES NOT EXIST")
        continue
    print(f"\n[2] SCHEMA of '{table}'")
    cur.execute(f"PRAGMA table_info({table})")
    cols = cur.fetchall()
    for col in cols:
        # col is (cid, name, type, notnull, default, pk)
        print(f"  {col[1]:30} {col[2]:15} (pk={col[5]})")

    # Count rows
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    print(f"  ROW COUNT: {count}")

    # Sample 3 rows
    if count > 0:
        cur.execute(f"SELECT * FROM {table} LIMIT 3")
        rows = cur.fetchall()
        col_names = [d[0] for d in cur.description]
        print(f"  SAMPLE ROWS (showing {min(3, count)}):")
        for row in rows:
            print(f"    {dict(zip(col_names, row))}")

# 3. Look for any LinkedIn-related rows by searching common columns
print("\n[3] SEARCH FOR LINKEDIN POSTS (try common column names)")
li_columns_to_try = ["source", "platform", "source_strategy", "type"]
for col in li_columns_to_try:
    try:
        cur.execute(
            f"SELECT COUNT(*) FROM seen_posts WHERE {col} LIKE '%linkedin%' "
            f"OR {col} LIKE '%LinkedIn%'"
        )
        count = cur.fetchone()[0]
        print(f"  Column '{col}' has {count} LinkedIn rows")
    except Exception as e:
        print(f"  Column '{col}' doesn't exist or query failed")

# 4. Search by post_id prefix (LinkedIn posts have li_ prefix in our scraper)
print("\n[4] SEARCH BY post_id PREFIX 'li_'")
try:
    cur.execute("SELECT COUNT(*) FROM seen_posts WHERE post_id LIKE 'li_%'")
    count = cur.fetchone()[0]
    print(f"  Posts with id starting with 'li_': {count}")
    if count > 0:
        cur.execute(
            "SELECT post_id FROM seen_posts WHERE post_id LIKE 'li_%' LIMIT 5"
        )
        print(f"  Sample IDs:")
        for (pid,) in cur.fetchall():
            print(f"    {pid[:80]}")
except Exception as e:
    print(f"  Error: {e}")

conn.close()
print("\n" + "=" * 70)
print("SCHEMA DISCOVERY COMPLETE")
print("=" * 70)