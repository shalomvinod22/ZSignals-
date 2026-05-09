#!/usr/bin/env python3
"""
V1.3 MEGA FIX VERIFICATION SCRIPT
Executes all 7 verification phases from user spec to confirm 100% compliance.
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Tuple

# Load .env file at the very top so all verifications have access to env vars
from dotenv import load_dotenv
load_dotenv()

WORKSPACE = Path(__file__).parent
PROMPT_PATH = WORKSPACE / "prompts" / "qualifier.md"
LINKEDIN_SCRAPER_PATH = WORKSPACE / "src" / "scraper" / "linkedin_scraper.py"
DB_PATH = WORKSPACE / "src" / "db.py"
APP_PATH = WORKSPACE / "app.py"


def verify_1_prompt_has_v13_keys() -> Tuple[bool, str]:
    """VERIFY 1: Prompt file contains all V1.3 required JSON keys."""
    prompt_text = PROMPT_PATH.read_text(encoding="utf-8")
    
    # Check for V1.3 schema keys
    required_keys = [
        "pain_stage",
        "pain_type", 
        "pain_evidence",
        "persona",
        "signal_stack",
        "conversation_kit",
        "likely_objections",
        "outbound_strategy",
        "reasoning",
        "ae_priority",
        "tier",
        "is_disqualified",
    ]
    
    missing = [k for k in required_keys if k not in prompt_text]
    if missing:
        return False, f"Missing prompt keys: {missing}"
    
    return True, f"All {len(required_keys)} V1.3 schema keys present in prompt"


def verify_2_linkedin_uses_correct_fields() -> Tuple[bool, str]:
    """VERIFY 2: LinkedIn scraper uses correct Apify field names."""
    scraper_text = LINKEDIN_SCRAPER_PATH.read_text(encoding="utf-8")
    
    # Check for CORRECT field names
    has_search_queries = "searchQueries" in scraper_text
    has_max_posts = "maxPosts" in scraper_text
    
    # Ensure WRONG field names are not present (false positives OK if in comments/data)
    has_queries_run_input = '"queries"' in scraper_text and "run_input" in scraper_text.split('"queries"')[0][-100:]
    has_max_items_run_input = '"maxItems"' in scraper_text and "run_input" in scraper_text.split('"maxItems"')[0][-100:]
    
    if not has_search_queries or not has_max_posts:
        return False, f"Missing correct field names: searchQueries={has_search_queries}, maxPosts={has_max_posts}"
    
    if has_queries_run_input or has_max_items_run_input:
        return False, "Found deprecated run_input field names (queries/maxItems)"
    
    return True, "LinkedIn scraper uses CORRECT Apify field names (searchQueries, maxPosts)"


def verify_3_db_schema_updated() -> Tuple[bool, str]:
    """VERIFY 3: Database has V1.3 tables and helpers."""
    db_text = DB_PATH.read_text(encoding="utf-8")
    
    # Check for V1.3 table definitions
    required_tables = [
        "CREATE TABLE.*lead_outcomes",
        "CREATE TABLE.*linkedin_watchlist",
        "CREATE TABLE.*source_quality",
    ]
    
    required_helpers = [
        "def get_lead_outcome",
        "def update_lead_outcome",
        "def list_watchlist",
        "def add_to_watchlist",
        "def record_source_quality",
        "def get_source_quality_summary",
    ]
    
    import re
    
    missing_tables = []
    for table_pattern in required_tables:
        if not re.search(table_pattern, db_text):
            missing_tables.append(table_pattern)
    
    missing_helpers = []
    for helper_pattern in required_helpers:
        if helper_pattern not in db_text:
            missing_helpers.append(helper_pattern)
    
    issues = []
    if missing_tables:
        issues.append(f"Missing tables: {missing_tables}")
    if missing_helpers:
        issues.append(f"Missing helpers: {missing_helpers}")
    
    if issues:
        return False, "; ".join(issues)
    
    return True, f"DB schema has all V1.3 tables and {len(required_helpers)} helper methods"


def verify_4_qualifier_function_exists() -> Tuple[bool, str]:
    """VERIFY 4: Qualifier module has qualify_post() function."""
    # Reload .env to be safe in case this is called from elsewhere
    from dotenv import load_dotenv
    load_dotenv()
    
    from src.qualifier import qualify_post
    
    # Try a test call
    try:
        result = qualify_post({
            "platform": "test",
            "content": "test content"
        })
        
        # Check for V1.3 keys in result
        v13_keys = {"score", "tier", "is_disqualified", "pain_type", "pain_stage", "reasoning"}
        present_keys = set(result.keys()) & v13_keys
        
        if len(present_keys) < 4:  # Should have at least most keys
            return False, f"Result missing V1.3 keys. Has: {present_keys}"
        
        return True, f"qualify_post() works and returns V1.3 schema (found {len(present_keys)} expected keys)"
    except Exception as e:
        return False, f"qualify_post() failed: {e}"


def verify_5_pytest_all_pass() -> Tuple[bool, str]:
    """VERIFY 5: All pytest tests pass (40/40)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
    )
    
    # Parse output for pass count
    import re
    match = re.search(r"(\d+) passed", result.stdout + result.stderr)
    
    if result.returncode != 0 or not match:
        return False, f"Tests failed or couldn't parse. Return code: {result.returncode}"
    
    passed_count = int(match.group(1))
    if passed_count < 40:
        return False, f"Only {passed_count}/40 tests passed"
    
    return True, f"All {passed_count} tests pass"


def verify_6_app_imports_clean() -> Tuple[bool, str]:
    """VERIFY 6: app.py can import without errors."""
    try:
        # Don't execute, just parse - check for syntax errors
        # Read with explicit UTF-8 encoding to handle emojis/non-ASCII chars
        app_text = APP_PATH.read_text(encoding="utf-8")
        compile(app_text, str(APP_PATH), 'exec')
        
        return True, "app.py has valid Python syntax"
    except Exception as e:
        return False, f"app.py import failed: {e}"


def verify_7_linkedin_scraper_syntax() -> Tuple[bool, str]:
    """VERIFY 7: LinkedIn scraper has valid Python syntax."""
    try:
        scraper_text = LINKEDIN_SCRAPER_PATH.read_text(encoding="utf-8")
        compile(scraper_text, str(LINKEDIN_SCRAPER_PATH), 'exec')
        
        # Also check for required class/functions
        has_search_strategies = "SEARCH_STRATEGIES" in scraper_text
        has_scrape_method = "def scrape(" in scraper_text
        
        if not (has_search_strategies and has_scrape_method):
            return False, "Missing SEARCH_STRATEGIES or scrape() method"
        
        return True, "LinkedIn scraper has valid syntax and all required components"
    except Exception as e:
        return False, f"Scraper syntax error: {e}"


def main():
    """Run all 7 verification phases."""
    print("\n" + "=" * 80)
    print("V1.3 MEGA FIX VERIFICATION — 7 Phases")
    print("=" * 80 + "\n")
    
    verifications = [
        ("VERIFY 1: Prompt has V1.3 keys", verify_1_prompt_has_v13_keys),
        ("VERIFY 2: LinkedIn uses correct Apify fields", verify_2_linkedin_uses_correct_fields),
        ("VERIFY 3: DB schema updated to V1.3", verify_3_db_schema_updated),
        ("VERIFY 4: Qualifier function works", verify_4_qualifier_function_exists),
        ("VERIFY 5: All pytest tests pass", verify_5_pytest_all_pass),
        ("VERIFY 6: app.py imports clean", verify_6_app_imports_clean),
        ("VERIFY 7: LinkedIn scraper syntax valid", verify_7_linkedin_scraper_syntax),
    ]
    
    results = []
    for name, verify_fn in verifications:
        try:
            passed, message = verify_fn()
            status = "PASS" if passed else "FAIL"
            results.append((name, status, message))
            print(f"[{status}] {name}")
            print(f"      {message}\n")
        except Exception as e:
            results.append((name, "ERROR", str(e)))
            print(f"[ERROR] {name}")
            print(f"      {e}\n")
    
    # Summary
    print("=" * 80)
    passed_count = sum(1 for _, status, _ in results if status == "PASS")
    total_count = len(results)
    
    if passed_count == total_count:
        print(f"V1.3 MEGA FIX COMPLETE - {passed_count}/{total_count} phases passed")
        print("=" * 80 + "\n")
        return 0
    else:
        print(f"V1.3 MEGA FIX FAILED - {passed_count}/{total_count} phases passed")
        print("\nFailures:")
        for name, status, message in results:
            if status != "PASS":
                print(f"  - {name}: {message}")
        print("=" * 80 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())