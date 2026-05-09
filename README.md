---
title: Zintlr Intent Radar
emoji: 🎯
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: 1.30.0
app_file: app.py
pinned: false
license: mit
---

# Zintlr Intent Radar

Internal tool that scores public social posts (Reddit, YouTube, G2 reviews, etc.) as outbound prospects for Zintlr. Targets people publicly complaining about Apollo / ZoomInfo / Lusha / Cognism.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and paste your Groq API key

python scripts/test_llm.py        # verify connection
python scripts/run_pipeline.py    # run on sample posts
streamlit run app.py              # launch the UI
```

## Daily workflow

1. Paste 30–50 scraped posts into `data/raw/posts.csv` (columns: `platform, source_url, username, date, content`)
2. Run `python scripts/run_pipeline.py`
3. Open `data/qualified/report_YYYY-MM-DD_HHMM.md` for the human report, or import the matching `.csv` into Google Sheets

## LLM options

Default is **Groq** (free, fast). Switch to **Ollama** (local, fully offline) by editing `.env`:
```
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b
```

## Deployment

- **Streamlit UI** auto-deploys to Hugging Face Spaces on git push (this README's frontmatter configures it)
- **Daily scheduled runs** via `.github/workflows/daily.yml`
- See AGENTS.md for full operational guidance
