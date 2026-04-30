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