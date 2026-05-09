# AGENTS.md — Zintlr Intent Radar

## What this project does
Internal Zintlr tool that ingests public social posts (Reddit, YouTube comments, G2 reviews, LinkedIn, etc.) and scores them as outbound prospects for Zintlr's BDR/AE team.

The thesis: people publicly complaining about Apollo, ZoomInfo, Lusha, or Cognism are high-intent buyers for Zintlr (which has 98%+ accuracy on Indian/APAC contacts). This system finds them, scores 1–5, drafts an opener, and produces a daily list.

## Tech stack
- **Python 3.11+**
- **Groq API** (free tier, Llama 3.3 70B) — primary LLM
- **Ollama** (Llama 3.1 8B) — local fallback LLM
- **Streamlit** — web UI for AEs
- **pandas** — tabular data handling
- **pytest** — tests
- **Hugging Face Spaces** — hosted Streamlit UI (free)
- **GitHub Actions** — daily scheduled runs

## Repository layout
- `src/` — business logic (LLM client, qualifier, exporter, pipeline)
- `prompts/qualifier.md` — the LLM system prompt
- `scripts/` — CLI entry points
- `app.py` — Streamlit app at root (HF Spaces convention)
- `tests/` — pytest tests
- `data/raw/posts.csv` — input
- `data/qualified/` — outputs (gitignored except `.gitkeep`)
- `.github/workflows/` — CI and scheduled runs
- `Dockerfile` — optional VPS deploy

## Setup (run once after cloning)
```bash
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env, paste GROQ_API_KEY (get free at console.groq.com)
```

## Common commands
| Task | Command |
|------|---------|
| Run tests | `pytest tests/ -v` |
| Test LLM connection | `python scripts/test_llm.py` |
| Run pipeline on sample posts | `python scripts/run_pipeline.py` |
| Run Streamlit UI | `streamlit run app.py` |
| Syntax check | `python -m py_compile src/*.py scripts/*.py app.py` |

## Code style
- Type hints on all public functions
- Docstrings on classes and module-level functions
- Pure functions where possible; I/O lives at the edges (pipeline.py, exporter.py)
- No global mutable state
- `pathlib.Path` everywhere — no `os.path.join`
- `python-dotenv` for env vars; never hardcode secrets

## Before completing any task
1. Run `pytest tests/ -v` — all tests must pass
2. Run `python scripts/test_llm.py` — LLM connection must work (skip if no key in env)
3. Update `AGENTS.md` if structure or commands changed
4. Update `tests/` if behavior changed

## Hard rules — never violate
- **Never commit `.env`** or any file containing real API keys
- **Never put secrets in code or tests** — always read from env
- **Never hardcode the LLM provider** — must respect `LLM_PROVIDER` env var
- **Never log full prompts or LLM responses** in production code paths (only counts and IDs)
- **Never break the JSON contract** the qualifier prompt expects from the LLM

## Deployment surfaces (priority order)
1. **Local CLI** — `python scripts/run_pipeline.py` on a dev laptop
2. **Local Streamlit** — `streamlit run app.py` for in-office AE use
3. **Hugging Face Spaces** — git push, AEs use the public URL
4. **GitHub Actions daily** — `.github/workflows/daily.yml`, commits reports back
5. **Docker on VPS** — `docker compose up -d`, only if 1–4 don't fit

## What this is NOT
- Not customer-facing — internal Zintlr tool only
- Not an outreach sender — produces lists, humans send messages
- Not a CRM — outputs CSV; humans import to HubSpot/Sheets

---

## V1.2 — Zintlr Pulse

**What's new**: Production-grade auto-scraping with modern dark-mode UI for BDR/AE team.

### New modules

#### Scraper layer (`src/scraper/`)
- `reddit_scraper.py` — public JSON endpoint scraper (no API key required)
- `g2_scraper.py` — G2 reviews via BeautifulSoup4
- `hackernews_scraper.py` — Algolia HN Search API
- `orchestrator.py` — combines all scrapers with graceful failure handling

#### Database layer (`src/db.py`)
- SQLite-based state tracking: seen posts, lead status, qualifier cache, scrape history
- `PulseDB` class with transactional writes
- Connection uses `check_same_thread=False` for Streamlit safety
- Tables: `seen_posts`, `lead_status`, `qualifier_cache`, `scrape_history`, `user_config`

#### Classification & pipeline
- `src/signal_classifier.py` — lightweight regex-based signal detection (complaint, hiring, comparison_shopping, etc.)
- `src/demo_data.py` — 12 curated example posts for testing/demos
- `src/pulse_pipeline.py` — orchestrates scraping + classification + qualification + caching

#### UI (`app.py`)
- Replaced entirely with dark-mode Streamlit UI (Linear/Vercel aesthetic)
- Primary/accent colors: indigo + cyan from Zintlr logo
- Hero stat bar, scrape control panel, results tabs, lead cards with actions
- Settings & diagnostics tab

### New env vars
- `APIFY_API_TOKEN` — fallback scraper (optional)
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` — PRAW config (optional)

### Database file
- Location: `data/seen_posts.db` (gitignored)
- Auto-created on first run via `PulseDB()`

### New tests
- `tests/test_db.py` — PulseDB table creation, dedup, cache, status tracking
- `tests/test_signal_classifier.py` — signal detection patterns
- `tests/test_orchestrator.py` — multi-source scraping, partial failures, dedup
- `tests/test_pulse_pipeline.py` — caching, bucketing, demo mode
- `tests/test_demo_data.py` — demo post schema validation

### Common commands (V1.2)
| Task | Command |
|------|---------|
| Run UI | `streamlit run app.py` |
| Run tests | `pytest tests/ -v` |
| Reset dedup | `python -c "from src.db import PulseDB; PulseDB().reset_seen_posts()"` |
| Test scrapers | `pytest tests/test_orchestrator.py -v` |

### Hard rules — V1.2 specific
- **Scrapers must isolate failures** — one source down ≠ entire scrape fails
- **Tests must never make real network calls** — all mocked/patched
- **Database writes wrapped in transactions** — no corrupted half-writes
- **Qualifier prompt locked** — don't modify `prompts/qualifier.md` (V1 compatibility)
- **UI respects dark aesthetic** — no light mode, no contrast violations
- **Logo optional** — if `data/assets/zintlr_logo_main.png` missing, UI still works

### What changed from V1
- V1: CSV upload → analyze → export
- V1.2: Auto-scrape daily → deduplicate → cache → qualify → live dashboard
- V1 CSV upload mode still available in app.py as fallback (not yet removed)
- Database tracks lead status and scrape history