# Zintlr Intent Radar — Codex Edition (Full Deployment)

> **How to use this file:** Copy everything below "PART 3 — Bootstrap prompt" and paste it into Codex CLI in an empty folder. Codex will create the whole project, install dependencies, run the tests, and tell you what to do next. Then you push to GitHub, click two buttons on Hugging Face, and you're deployed.

---

## TABLE OF CONTENTS

1. [Codex setup](#part-1--codex-setup)
2. [Project structure](#part-2--project-structure)
3. [Bootstrap prompt for Codex](#part-3--bootstrap-prompt-for-codex)
4. [All file contents](#part-4--all-file-contents)
5. [Run locally](#part-5--run-locally)
6. [Push to GitHub](#part-6--push-to-github)
7. [Deploy UI to Hugging Face Spaces](#part-7--deploy-ui-to-hugging-face-spaces)
8. [Schedule daily runs with GitHub Actions](#part-8--schedule-daily-runs)
9. [Optional: VPS with Docker](#part-9--optional-vps-with-docker)
10. [Operating it day-to-day](#part-10--operating-it)

---

## PART 1 — CODEX SETUP

### Install Node.js 22+
Codex CLI needs Node. Get it from nodejs.org (LTS version) or:
```bash
# macOS
brew install node

# Windows (use winget or download from nodejs.org)
winget install OpenJS.NodeJS.LTS
```

### Install Codex CLI
```bash
npm install -g @openai/codex
```

### Authenticate
First run will prompt you. Either:
- Sign in with your ChatGPT account (Plus/Pro/Business plans include Codex), OR
- Use an OpenAI API key from platform.openai.com/api-keys

```bash
codex
# Follow auth prompts
```

### Verify
```bash
codex --version
```

You should see a version number. If yes, you're ready.

---

## PART 2 — PROJECT STRUCTURE

```
zintlr-intent-radar/
├── AGENTS.md                       ← Codex reads this first, every session
├── README.md                       ← HF Spaces config + project overview
├── requirements.txt                ← Python dependencies
├── .env.example                    ← Template for secrets
├── .gitignore
├── app.py                          ← Streamlit entry point (HF Spaces convention)
├── prompts/
│   └── qualifier.md                ← The LLM system prompt
├── src/
│   ├── __init__.py
│   ├── llm.py                      ← Groq + Ollama swappable client
│   ├── qualifier.py                ← Analysis logic
│   ├── exporter.py                 ← MD + CSV writers
│   └── pipeline.py                 ← Orchestration
├── scripts/
│   ├── test_llm.py                 ← Connection sanity check
│   └── run_pipeline.py             ← CLI entry point
├── tests/
│   ├── __init__.py
│   ├── test_qualifier.py
│   └── test_exporter.py
├── data/
│   ├── raw/posts.csv               ← Sample input
│   └── qualified/.gitkeep          ← Output dir (gitignored)
├── .github/workflows/
│   ├── test.yml                    ← Run pytest on every push
│   └── daily.yml                   ← Scheduled daily pipeline
└── Dockerfile                      ← Optional VPS deploy
```

---

## PART 3 — BOOTSTRAP PROMPT FOR CODEX

Open a terminal in your empty project folder. Run `codex`. When it loads, paste this single message:

````
I want to build a project called "Zintlr Intent Radar". It's a Python tool that uses an open-source LLM (Groq's free tier with Llama 3.3 70B, with Ollama as a local fallback) to score public social media posts as outbound sales prospects. It outputs a markdown report and CSV daily.

Build the entire project according to the file specifications below. After creating all files:

1. Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
2. Run: pytest tests/ -v
3. Confirm all tests pass
4. Tell me the next step

Create these files exactly. Do not add extra files. Do not change file paths. Do not skip any file.

[Then paste everything from PART 4 below]
````

Codex will read AGENTS.md after creation and use it for all future work in this project. Every subsequent task you give Codex (e.g. "add a Slack notifier") will inherit those rules.

---

## PART 4 — ALL FILE CONTENTS

### File: `AGENTS.md`

````markdown
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
````

---

### File: `README.md`

````markdown
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
````

---

### File: `requirements.txt`

```
groq>=0.11.0
ollama>=0.3.3
python-dotenv>=1.0.0
pandas>=2.0.0
streamlit>=1.30.0
pytest>=7.4.0
```

---

### File: `.env.example`

```
# Copy this file to .env (no extension change), fill in your key

# Choose: groq or ollama
LLM_PROVIDER=groq

# Groq settings — free key at console.groq.com
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Ollama settings — only used if LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b
OLLAMA_HOST=http://localhost:11434
```

---

### File: `.gitignore`

```
# Secrets — never commit
.env

# Output reports
data/qualified/*
!data/qualified/.gitkeep

# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
.pytest_cache/

# OS
.DS_Store
Thumbs.db

# Editors
.vscode/
.idea/

# Codex local files
.codex/
```

---

### File: `prompts/qualifier.md`

````markdown
You are a senior B2B sales strategist analyzing public internet posts to find high-quality outbound prospects for Zintlr.

# About Zintlr
Zintlr is a B2B contact data platform. Differentiators:
- 98%+ verified accuracy on Indian/APAC contacts (vs Apollo's ~73% APAC accuracy)
- Director/founder/CIN-level data on every GoI-registered Indian company (MCA, GST, IDS)
- Integrated AI Insights + DISC personality scoring
- Used by ICICI, Motilal Oswal, HubSpot India

# Your task
Analyze the post and return ONLY a valid JSON object — no markdown, no preamble, no commentary.

# JSON schema (return EXACTLY this structure)

```json
{
  "disqualified": false,
  "disqualifier_reason": null,
  "intent_score": 5,
  "specificity": "SPECIFIC",
  "pain_category": "Bounce Rate / Deliverability",
  "pain_in_words": "This person is frustrated because...",
  "buyer_type": "SDR/BDR",
  "identity": {
    "name": null,
    "company": "PaySync",
    "role": "SDR",
    "location": "Bangalore",
    "industry": "Fintech",
    "linkedin_url": null,
    "twitter_handle": null,
    "email": null,
    "username": "u/sdr_burnedout",
    "platform": "Reddit"
  },
  "company_context": {
    "size": "Startup",
    "geography": "India",
    "stage": "Hiring/scaling"
  },
  "why_matters": "Active comparison shopper, named our two strongest wedges in one post...",
  "recommended_action": "AE WHITE GLOVE",
  "opening_line": "saw your note about 40% bouncing on india contacts — apollo's APAC accuracy is a documented hole, you're not imagining it",
  "confidence": "HIGH"
}
```

# Disqualifier check (FIRST)
If ANY apply, set `disqualified: true`, fill `disqualifier_reason`, set `intent_score: 0`, and set all other analysis fields to `null` or empty:

- Apollo / ZoomInfo / Lusha / Cognism employee or founder
- Sponsored / promotional / affiliate content
- Older than 60 days
- Job listing or recruiter post
- Journalist or researcher seeking quotes
- Student, intern, or non-buying role
- Bot / spam / karma farming
- Pure technical "how do I" question
- Positive about Apollo / ZoomInfo / Lusha / Cognism

When in doubt → disqualify.

# Field rules

**intent_score** (1–5):
- 1 = no buying intent
- 2 = low (mild discussion)
- 3 = moderate (problem mentioned, not urgent)
- 4 = high (clear frustration, named tool)
- 5 = very high (actively asking for alternatives or naming Zintlr's exact wedge)

**specificity**: `"VAGUE"` or `"SPECIFIC"`. SPECIFIC if numbers, dates, named accounts, regions, or use cases.

**pain_category** (pick ONE): `"Bounce Rate / Deliverability"` | `"Inaccurate Data / Wrong Contacts"` | `"Poor India / APAC Coverage"` | `"Pricing / Cost"` | `"Bad UX / Workflow Friction"` | `"Comparison Shopping"` | `"General Frustration"` | `"Other"`

**buyer_type** (pick ONE): `"SDR/BDR"` | `"Sales Manager"` | `"Head of Sales / VP Sales"` | `"CRO"` | `"Founder"` | `"RevOps"` | `"Marketing / Growth"` | `"Unknown"`

**identity fields**: ONLY fill if explicitly stated/visible. Use `null` when not 95% certain. NEVER hallucinate.

**company_context.size**: `"Startup"` | `"SMB"` | `"Mid-market"` | `"Enterprise"` | `"Unknown"`
**company_context.geography**: `"India"` | `"APAC"` | `"US/EU"` | `"Global"` | `"Unknown"`
**company_context.stage**: `"Hiring/scaling"` | `"Stable"` | `"Struggling"` | `"Unknown"`

**recommended_action** (DETERMINISTIC):
| score | identity has company OR email OR linkedin? | action |
|-------|---|---|
| 5 | Yes | `"BOTH"` |
| 5 | No | `"AE WHITE GLOVE"` |
| 4 | Yes | `"BULK EMAIL"` |
| 4 | No | `"AE WHITE GLOVE (lower priority)"` |
| 3 | Yes | `"BULK EMAIL"` |
| 3 | No | `"DROP"` |
| 1–2 | Any | `"IGNORE"` |

**opening_line** rules (only if score ≥ 3, else `null`):
- Max 25 words
- Reference a specific detail from the post
- No "Hi", no "Hello", no exclamation marks
- No pitch, no product mention
- Lowercase, peer tone

**confidence**: `"HIGH"` | `"MEDIUM"` | `"LOW"`

# Examples

## Strong signal

Input:
```
Source: Reddit — r/sales
Author: u/sdr_burnedout_blr
Date: 2026-04-26

Post:
Anyone else getting destroyed by Apollo's India data lately? Sent 200 emails this week to fintech contacts in Mumbai/Bangalore — got 84 hard bounces. That's 42 percent. We're a Series A SaaS in HSR Layout, looking at alternatives that actually have working APAC data.
```

Output:
```json
{
  "disqualified": false,
  "disqualifier_reason": null,
  "intent_score": 5,
  "specificity": "SPECIFIC",
  "pain_category": "Bounce Rate / Deliverability",
  "pain_in_words": "This person is frustrated because 42% of their Apollo emails to India bounced this week, and they're now actively looking for an APAC-capable alternative.",
  "buyer_type": "SDR/BDR",
  "identity": {
    "name": null,
    "company": null,
    "role": "SDR",
    "location": "HSR Layout, Bangalore",
    "industry": "SaaS (Series A)",
    "linkedin_url": null,
    "twitter_handle": null,
    "email": null,
    "username": "u/sdr_burnedout_blr",
    "platform": "Reddit"
  },
  "company_context": {
    "size": "Startup",
    "geography": "India",
    "stage": "Hiring/scaling"
  },
  "why_matters": "Active comparison shopper who named both our strongest wedges (Apollo + India APAC accuracy). Specific bounce numbers prove they track ROI. Likely 2 weeks from buying something.",
  "recommended_action": "AE WHITE GLOVE",
  "opening_line": "saw your note about 42% bouncing in mumbai/bangalore — apollo's APAC accuracy sits around 73% which is exactly the gap you're seeing",
  "confidence": "HIGH"
}
```

## Disqualified

Input:
```
Source: Reddit — r/sales
Author: u/saas_sales_2015
Date: 2026-04-12

Post:
Apollo has its issues but honestly any data tool is going to have some bounce. Just clean your lists better lol.
```

Output:
```json
{
  "disqualified": true,
  "disqualifier_reason": "Defensive of Apollo with no buying intent",
  "intent_score": 0,
  "specificity": null,
  "pain_category": null,
  "pain_in_words": null,
  "buyer_type": null,
  "identity": {
    "name": null, "company": null, "role": null, "location": null,
    "industry": null, "linkedin_url": null, "twitter_handle": null,
    "email": null, "username": "u/saas_sales_2015", "platform": "Reddit"
  },
  "company_context": {"size": "Unknown", "geography": "Unknown", "stage": "Unknown"},
  "why_matters": null,
  "recommended_action": "IGNORE",
  "opening_line": null,
  "confidence": "HIGH"
}
```

# Now analyze this post and return ONLY the JSON object:

{INSERT POST HERE}
````

---

### File: `data/raw/posts.csv`

```csv
platform,source_url,username,date,content
Reddit,https://reddit.com/r/sales,u/sdr_burnedout_blr,2026-04-26,"Anyone else getting destroyed by Apollo's India data lately? Sent 200 emails this week to fintech contacts in Mumbai/Bangalore — got 84 hard bounces. That's 42 percent. Wasted half my month's credits. We're a Series A SaaS in HSR Layout, looking at alternatives that actually have working APAC data. Tried Lusha briefly — same problem. Suggestions?"
Reddit,https://reddit.com/r/SalesOperations,u/revops_priya,2026-04-24,"Update on switching off ZoomInfo: we cancelled last week. 18-month contract was 52k. Replacing with [evaluating 3 options]. Breaking point was 60%+ bounce rate on our enterprise India accounts. If anyone in r/sales has built a reliable APAC outbound stack would love a 15min call. - Priya, RevOps @ ScaleHQ"
Reddit,https://reddit.com/r/sales,u/coldemail_dropout,2026-04-22,"Curious what everyone's using for outbound data these days. We've been on ZoomInfo for 2 years and contract is up in 8 weeks. Honestly the data quality has gotten worse and the price hike is brutal. Open to hearing about alternatives, especially anything that handles non-US markets well."
Reddit,https://reddit.com/r/sales,u/wfh_skeptic,2026-04-25,"yeah cold outreach is dead lol. nobody opens emails anymore. we should all just do linkedin"
LinkedIn,https://linkedin.com/posts/marcus-k-apollo,Marcus K (Apollo Sales),2026-04-23,"Hey everyone — I work at Apollo and we've been investing heavily in our APAC data team this year. If anyone's having issues with bounce rates DM me directly and I can take a look at your account specifically."
G2,https://g2.com/products/apollo-io/reviews,Verified User in Computer Software,2026-04-19,"Rating: 2/5. Apollo was great when we were US-only. Started selling into India and Singapore last quarter and the data quality fell off a cliff. 1 in 3 mobile numbers wrong, emails bouncing constantly. Support told us they're 'working on APAC coverage'. Looking at alternatives now."
```

---

### File: `data/qualified/.gitkeep`

```
```

(Empty file. Just keeps the directory in git.)

---

### File: `src/__init__.py`

```python
"""Zintlr Intent Radar."""
__version__ = "0.1.0"
```

---

### File: `src/llm.py`

```python
"""
Swappable LLM client. Supports Groq (cloud, free tier) and Ollama (local).
Selection is driven by the LLM_PROVIDER env var.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract base for any LLM provider."""

    @abstractmethod
    def complete_json(self, prompt: str) -> str:
        """Send a prompt and return the raw JSON string response."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the provider + model."""


class GroqClient(LLMClient):
    """
    Groq with Llama 3.3 70B (default).
    Free tier: ~30 requests/minute, ~14,400 requests/day. No credit card required.
    Get a key at https://console.groq.com
    """

    def __init__(self, model: str = "llama-3.3-70b-versatile") -> None:
        from groq import Groq

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not set. Get a free key at console.groq.com "
                "and put it in .env"
            )
        self._client = Groq(api_key=api_key)
        self._model = model

    def complete_json(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""

    @property
    def name(self) -> str:
        return f"Groq({self._model})"


class OllamaClient(LLMClient):
    """
    Ollama runs locally; fully free, fully offline.
    Install from https://ollama.com, then: `ollama pull llama3.1:8b`
    """

    def __init__(
        self,
        model: str = "llama3.1:8b",
        host: str = "http://localhost:11434",
    ) -> None:
        import ollama

        self._client = ollama.Client(host=host)
        self._model = model

    def complete_json(self, prompt: str) -> str:
        response = self._client.chat(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            format="json",
            options={"temperature": 0.2},
        )
        return response["message"]["content"]

    @property
    def name(self) -> str:
        return f"Ollama({self._model})"


def get_llm() -> LLMClient:
    """Factory — reads LLM_PROVIDER env var, returns the right client."""
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()

    if provider == "groq":
        model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        return GroqClient(model=model)

    if provider == "ollama":
        model = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        return OllamaClient(model=model, host=host)

    raise ValueError(
        f"Unknown LLM_PROVIDER: {provider!r}. Use 'groq' or 'ollama'."
    )
```

---

### File: `src/qualifier.py`

```python
"""Sends each post to the LLM and parses the JSON response."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .llm import LLMClient


class Qualifier:
    """Wraps the LLM with the qualifier prompt and JSON parsing."""

    def __init__(self, prompt_path: Path, llm: LLMClient) -> None:
        self._template = prompt_path.read_text(encoding="utf-8")
        self._llm = llm

    @staticmethod
    def format_post(post: dict[str, str]) -> str:
        return (
            f"Source: {post.get('platform', 'Unknown')} — "
            f"{post.get('source_url', 'Unknown')}\n"
            f"Author: {post.get('username', 'Unknown')}\n"
            f"Date: {post.get('date', 'Unknown')}\n\n"
            f"Post:\n{(post.get('content') or '').strip()}"
        )

    def analyze(self, post: dict[str, str]) -> dict[str, Any]:
        post_text = self.format_post(post)
        full_prompt = self._template.replace("{INSERT POST HERE}", post_text)

        try:
            raw = self._llm.complete_json(full_prompt)
        except Exception as exc:  # noqa: BLE001
            return {"error": f"LLM call failed: {exc}", "_post": post}

        parsed = self._extract_json(raw)
        if parsed is None:
            return {
                "error": "Could not parse JSON from LLM response",
                "raw": raw[:500],
                "_post": post,
            }

        parsed["_post"] = post
        return parsed

    @staticmethod
    def _extract_json(raw: str) -> dict[str, Any] | None:
        """Try strict parse; fall back to extracting the first {...} block."""
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                return None
        return None
```

---

### File: `src/exporter.py`

```python
"""Converts qualifier output into a markdown report and a flat CSV."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

SCORE_EMOJI = {5: "🔥", 4: "✅", 3: "🟡", 2: "⚪", 1: "⚪", 0: "🚫"}


def _sort_key(r: dict[str, Any]) -> int:
    """Higher rank = appears first. Errors and DQ at the bottom."""
    if r.get("error"):
        return -2
    if r.get("disqualified"):
        return -1
    return r.get("intent_score") or 0


def export_markdown(results: list[dict[str, Any]], output_path: Path) -> None:
    """Write a human-readable markdown report sorted by score desc."""
    sorted_results = sorted(results, key=_sort_key, reverse=True)

    with output_path.open("w", encoding="utf-8") as f:
        f.write("# Zintlr Intent Radar — Daily Report\n\n")
        f.write(f"_Generated: {datetime.now().isoformat()}_  \n")
        f.write(f"_Posts processed: {len(results)}_\n\n")

        # Summary
        score_counts = {i: 0 for i in range(0, 6)}
        dq = err = 0
        for r in results:
            if r.get("error"):
                err += 1
            elif r.get("disqualified"):
                dq += 1
            else:
                score_counts[r.get("intent_score") or 0] += 1

        f.write("## Summary\n\n")
        f.write(f"- 🔥 Score 5: **{score_counts[5]}**\n")
        f.write(f"- ✅ Score 4: **{score_counts[4]}**\n")
        f.write(f"- 🟡 Score 3: **{score_counts[3]}**\n")
        f.write(f"- ⚪ Score 1–2: **{score_counts[1] + score_counts[2]}**\n")
        f.write(f"- 🚫 Disqualified: **{dq}**\n")
        if err:
            f.write(f"- ⚠️ Errors: **{err}**\n")
        f.write("\n---\n\n")

        for i, r in enumerate(sorted_results, 1):
            post = r.get("_post", {})
            label = f"{post.get('platform', '?')} — {post.get('username', '?')}"

            if r.get("error"):
                f.write(f"## {i}. ⚠️ ERROR — {label}\n\n")
                f.write(f"**Error:** {r['error']}\n\n")
                if "raw" in r:
                    f.write(f"```\n{r['raw'][:500]}\n```\n\n")
                f.write("---\n\n")
                continue

            if r.get("disqualified"):
                f.write(f"## {i}. 🚫 DISQUALIFIED — {label}\n\n")
                f.write(f"**Reason:** {r.get('disqualifier_reason', '—')}\n\n")
                f.write("---\n\n")
                continue

            score = r.get("intent_score", 0)
            emoji = SCORE_EMOJI.get(score, "⚪")
            f.write(f"## {i}. {emoji} Score {score} — {label}\n\n")
            f.write(f"**Action:** `{r.get('recommended_action', '—')}`  \n")
            f.write(
                f"**Pain:** {r.get('pain_category', '—')} "
                f"({r.get('specificity', '—')})  \n"
            )
            f.write(f"**Buyer type:** {r.get('buyer_type', '—')}  \n")
            f.write(f"**Confidence:** {r.get('confidence', '—')}\n\n")
            f.write(
                f"**Pain in their words:**\n> {r.get('pain_in_words', '—')}\n\n"
            )
            f.write(f"**Why it matters:** {r.get('why_matters', '—')}\n\n")

            opener = r.get("opening_line")
            if opener:
                f.write(f"**Suggested opener:**\n```\n{opener}\n```\n\n")

            ident = r.get("identity") or {}
            f.write("**Identity signals:**\n")
            for key in [
                "name", "company", "role", "location", "industry",
                "linkedin_url", "twitter_handle", "email",
            ]:
                val = ident.get(key)
                if val:
                    f.write(f"- {key}: {val}\n")
            f.write(
                f"- username: {ident.get('username', '—')} "
                f"on {ident.get('platform', '—')}\n\n"
            )

            ctx = r.get("company_context") or {}
            f.write(
                f"**Company context:** {ctx.get('size', '?')} | "
                f"{ctx.get('geography', '?')} | {ctx.get('stage', '?')}\n\n"
            )
            f.write(
                f"**Original:**\n```\n{(post.get('content') or '').strip()}\n```\n\n"
            )
            f.write(f"**Source:** {post.get('source_url', '—')}\n\n---\n\n")


def export_csv(results: list[dict[str, Any]], output_path: Path) -> None:
    """Flat CSV — sortable/filterable in Google Sheets."""
    sorted_results = sorted(results, key=_sort_key, reverse=True)

    headers = [
        "score", "action", "specificity", "pain_category", "buyer_type",
        "platform", "username", "name", "company", "role", "location",
        "industry", "linkedin_url", "email", "company_size", "geography",
        "stage", "pain_in_words", "why_matters", "opening_line",
        "confidence", "source_url", "original_content", "disqualified",
        "disqualifier_reason", "error",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()

        for r in sorted_results:
            post = r.get("_post", {})
            ident = r.get("identity") or {}
            ctx = r.get("company_context") or {}
            writer.writerow({
                "score": (
                    0 if r.get("disqualified") or r.get("error")
                    else (r.get("intent_score") or 0)
                ),
                "action": r.get("recommended_action", ""),
                "specificity": r.get("specificity", ""),
                "pain_category": r.get("pain_category", ""),
                "buyer_type": r.get("buyer_type", ""),
                "platform": post.get("platform", ""),
                "username": ident.get("username") or post.get("username", ""),
                "name": ident.get("name", ""),
                "company": ident.get("company", ""),
                "role": ident.get("role", ""),
                "location": ident.get("location", ""),
                "industry": ident.get("industry", ""),
                "linkedin_url": ident.get("linkedin_url", ""),
                "email": ident.get("email", ""),
                "company_size": ctx.get("size", ""),
                "geography": ctx.get("geography", ""),
                "stage": ctx.get("stage", ""),
                "pain_in_words": r.get("pain_in_words", ""),
                "why_matters": r.get("why_matters", ""),
                "opening_line": r.get("opening_line", ""),
                "confidence": r.get("confidence", ""),
                "source_url": post.get("source_url", ""),
                "original_content": (post.get("content") or "").strip(),
                "disqualified": r.get("disqualified", False),
                "disqualifier_reason": r.get("disqualifier_reason", ""),
                "error": r.get("error", ""),
            })
```

---

### File: `src/pipeline.py`

```python
"""Orchestrates the full flow: load posts → analyze → write reports."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .exporter import export_csv, export_markdown
from .llm import get_llm
from .qualifier import Qualifier


def load_posts(input_csv: Path) -> list[dict[str, str]]:
    if not input_csv.exists():
        raise FileNotFoundError(
            f"Input CSV not found at {input_csv}. "
            f"Required columns: platform, source_url, username, date, content"
        )
    with input_csv.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run_pipeline(
    input_csv: Path,
    output_dir: Path,
    prompt_path: Path,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> tuple[Path, Path, list[dict[str, Any]]]:
    """Run full pipeline. Returns (md_path, csv_path, results)."""
    llm = get_llm()
    qualifier = Qualifier(prompt_path, llm)
    posts = load_posts(input_csv)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"LLM:    {llm.name}")
    print(f"Posts:  {len(posts)}")
    print(f"Output: {output_dir}")
    print()

    results: list[dict[str, Any]] = []
    for i, post in enumerate(posts, 1):
        label = (
            f"{post.get('platform', '?')} — "
            f"{(post.get('username', '?') or '?')[:40]}"
        )
        if progress_callback:
            progress_callback(i, len(posts), label)
        else:
            print(f"[{i}/{len(posts)}] {label}")

        results.append(qualifier.analyze(post))

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    md_path = output_dir / f"report_{timestamp}.md"
    csv_path = output_dir / f"report_{timestamp}.csv"

    export_markdown(results, md_path)
    export_csv(results, csv_path)

    print()
    print(f"✓ Markdown: {md_path}")
    print(f"✓ CSV:      {csv_path}")

    return md_path, csv_path, results
```

---

### File: `scripts/test_llm.py`

```python
"""Quick sanity check on the LLM connection. Run this first."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from src.llm import get_llm

load_dotenv()

print("Testing LLM connection...")
print()

try:
    llm = get_llm()
    print(f"Provider: {llm.name}")
    response = llm.complete_json(
        'Return a JSON object with one key "status" set to "ok". '
        "Return only JSON, no other text."
    )
    print(f"Response: {response}")
    print()
    print("✓ LLM works. Run: python scripts/run_pipeline.py")
except Exception as exc:  # noqa: BLE001
    print(f"✗ ERROR: {exc}")
    print()
    print("Common fixes:")
    print("  - Make sure .env exists with GROQ_API_KEY filled in")
    print("  - For Ollama: run `ollama serve` and `ollama pull llama3.1:8b`")
    sys.exit(1)
```

---

### File: `scripts/run_pipeline.py`

```python
"""CLI entry point for running the pipeline on data/raw/posts.csv."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from src.pipeline import run_pipeline

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    print("Zintlr Intent Radar — Pipeline Run")
    print("=" * 50)
    try:
        run_pipeline(
            input_csv=PROJECT_ROOT / "data" / "raw" / "posts.csv",
            output_dir=PROJECT_ROOT / "data" / "qualified",
            prompt_path=PROJECT_ROOT / "prompts" / "qualifier.md",
        )
    except Exception as exc:  # noqa: BLE001
        print(f"\n✗ Pipeline failed: {exc}")
        sys.exit(1)
```

---

### File: `app.py`

```python
"""
Streamlit UI — root-level for Hugging Face Spaces compatibility.

Local: streamlit run app.py
HF Spaces: deployed automatically via the README.md frontmatter.
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.llm import get_llm  # noqa: E402
from src.qualifier import Qualifier  # noqa: E402

load_dotenv()
PROMPT_PATH = PROJECT_ROOT / "prompts" / "qualifier.md"

st.set_page_config(
    page_title="Zintlr Intent Radar",
    page_icon="🎯",
    layout="wide",
)
st.title("🎯 Zintlr Intent Radar")
st.caption("Upload posts → score → daily list of leads to work")

with st.sidebar:
    st.subheader("Settings")
    st.write("LLM provider is read from `.env` or HF Spaces secrets.")
    if st.button("Test LLM connection"):
        try:
            llm = get_llm()
            llm.complete_json('Return JSON: {"status": "ok"}')
            st.success(f"✓ Connected to {llm.name}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"✗ {exc}")

uploaded = st.file_uploader(
    "Upload posts CSV (columns: platform, source_url, username, date, content)",
    type="csv",
)

if uploaded:
    df_input = pd.read_csv(uploaded)
    st.write(f"Loaded **{len(df_input)}** posts")
    st.dataframe(df_input.head(), use_container_width=True)

    if st.button("🚀 Analyze posts", type="primary"):
        try:
            qualifier = Qualifier(PROMPT_PATH, get_llm())
        except Exception as exc:  # noqa: BLE001
            st.error(f"LLM setup failed: {exc}")
            st.stop()

        results = []
        progress = st.progress(0.0)
        status = st.empty()
        for i, row in enumerate(df_input.to_dict("records"), 1):
            status.text(
                f"[{i}/{len(df_input)}] "
                f"{row.get('platform', '?')} — {row.get('username', '?')}"
            )
            results.append(qualifier.analyze(row))
            progress.progress(i / len(df_input))
        status.text("Done.")
        progress.empty()
        st.session_state["results"] = results

if "results" in st.session_state:
    results = st.session_state["results"]
    rows = []
    for r in results:
        post = r.get("_post", {})
        ident = r.get("identity") or {}
        rows.append({
            "score": (
                0 if r.get("disqualified") or r.get("error")
                else (r.get("intent_score") or 0)
            ),
            "action": r.get("recommended_action", ""),
            "platform": post.get("platform", ""),
            "username": ident.get("username") or post.get("username", ""),
            "company": ident.get("company", ""),
            "location": ident.get("location", ""),
            "pain": r.get("pain_category", ""),
            "specificity": r.get("specificity", ""),
            "opener": r.get("opening_line", ""),
            "why": r.get("why_matters", ""),
            "disqualified": bool(r.get("disqualified")),
            "url": post.get("source_url", ""),
        })
    df = pd.DataFrame(rows).sort_values("score", ascending=False)

    st.markdown("---")
    st.subheader("Results")

    col1, col2, col3 = st.columns(3)
    with col1:
        score_filter = st.multiselect(
            "Score", [5, 4, 3, 2, 1, 0], default=[5, 4, 3]
        )
    with col2:
        action_options = df["action"].dropna().unique().tolist()
        action_filter = st.multiselect(
            "Action", action_options, default=action_options
        )
    with col3:
        show_dq = st.checkbox("Show disqualified", value=False)

    filtered = df[df["score"].isin(score_filter)]
    if action_filter:
        filtered = filtered[filtered["action"].isin(action_filter)]
    if not show_dq:
        filtered = filtered[~filtered["disqualified"]]

    st.write(f"Showing **{len(filtered)}** of {len(df)} leads")
    st.dataframe(
        filtered[
            ["score", "action", "platform", "username", "company",
             "location", "pain", "specificity", "opener"]
        ],
        use_container_width=True,
        height=400,
    )

    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    today = datetime.now().strftime("%Y-%m-%d_%H%M")
    st.download_button(
        "⬇️ Download filtered CSV",
        csv_bytes,
        file_name=f"zintlr_radar_{today}.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.subheader("Lead detail")
    if len(filtered) > 0:
        idx = st.selectbox(
            "Pick a lead",
            options=filtered.index.tolist(),
            format_func=lambda i: (
                f"Score {filtered.loc[i, 'score']} — "
                f"{filtered.loc[i, 'username']} "
                f"({filtered.loc[i, 'company'] or '?'})"
            ),
        )
        st.json(results[idx])
```

---

### File: `tests/__init__.py`

```python
```

(Empty — just makes it a package.)

---

### File: `tests/test_qualifier.py`

```python
"""Unit tests for the Qualifier — uses a fake LLM client (no network)."""

import json
from pathlib import Path

import pytest

from src.llm import LLMClient
from src.qualifier import Qualifier


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "qualifier.md"


class FakeLLM(LLMClient):
    """Returns a canned response for testing — no network calls."""

    def __init__(self, response: str) -> None:
        self._response = response

    def complete_json(self, prompt: str) -> str:
        return self._response

    @property
    def name(self) -> str:
        return "FakeLLM"


def test_qualifier_parses_clean_json() -> None:
    canned = json.dumps({
        "disqualified": False,
        "intent_score": 5,
        "pain_category": "Bounce Rate / Deliverability",
        "recommended_action": "BOTH",
        "confidence": "HIGH",
    })
    q = Qualifier(PROMPT_PATH, FakeLLM(canned))
    result = q.analyze({"platform": "Reddit", "content": "test"})
    assert result["intent_score"] == 5
    assert result["recommended_action"] == "BOTH"
    assert result["_post"]["platform"] == "Reddit"


def test_qualifier_handles_messy_json_with_prose() -> None:
    canned = (
        "Sure, here's the JSON: "
        '{"disqualified": false, "intent_score": 4, '
        '"recommended_action": "BULK EMAIL"} '
        "Hope that helps!"
    )
    q = Qualifier(PROMPT_PATH, FakeLLM(canned))
    result = q.analyze({"platform": "G2", "content": "x"})
    assert result["intent_score"] == 4


def test_qualifier_handles_unparseable_response() -> None:
    q = Qualifier(PROMPT_PATH, FakeLLM("definitely not json"))
    result = q.analyze({"platform": "Reddit", "content": "x"})
    assert "error" in result
    assert "raw" in result


def test_qualifier_handles_llm_exception() -> None:
    class BrokenLLM(LLMClient):
        def complete_json(self, prompt: str) -> str:
            raise ConnectionError("network down")

        @property
        def name(self) -> str:
            return "Broken"

    q = Qualifier(PROMPT_PATH, BrokenLLM())
    result = q.analyze({"platform": "Reddit", "content": "x"})
    assert "error" in result
    assert "network down" in result["error"]


def test_format_post_includes_all_fields() -> None:
    formatted = Qualifier.format_post({
        "platform": "Reddit",
        "source_url": "https://reddit.com/r/sales",
        "username": "u/test",
        "date": "2026-04-26",
        "content": "Apollo is broken",
    })
    assert "Reddit" in formatted
    assert "u/test" in formatted
    assert "Apollo is broken" in formatted
```

---

### File: `tests/test_exporter.py`

```python
"""Unit tests for the exporter — verifies markdown and CSV output."""

import csv
from pathlib import Path

import pytest

from src.exporter import export_csv, export_markdown


@pytest.fixture
def sample_results() -> list[dict]:
    return [
        {
            "disqualified": False,
            "intent_score": 5,
            "specificity": "SPECIFIC",
            "pain_category": "Bounce Rate / Deliverability",
            "pain_in_words": "Apollo bouncing",
            "buyer_type": "SDR/BDR",
            "identity": {
                "name": None, "company": "Acme",
                "role": "SDR", "location": "Bangalore",
                "industry": "SaaS", "linkedin_url": None,
                "twitter_handle": None, "email": None,
                "username": "u/test", "platform": "Reddit",
            },
            "company_context": {
                "size": "Startup", "geography": "India", "stage": "Hiring/scaling"
            },
            "why_matters": "High intent",
            "recommended_action": "BOTH",
            "opening_line": "saw your note about apollo",
            "confidence": "HIGH",
            "_post": {
                "platform": "Reddit",
                "username": "u/test",
                "content": "Apollo is broken",
                "source_url": "https://reddit.com",
            },
        },
        {
            "disqualified": True,
            "disqualifier_reason": "Apollo employee",
            "_post": {
                "platform": "LinkedIn",
                "username": "marcus",
                "content": "I work at Apollo",
                "source_url": "https://linkedin.com",
            },
        },
    ]


def test_export_markdown(tmp_path: Path, sample_results: list[dict]) -> None:
    out = tmp_path / "report.md"
    export_markdown(sample_results, out)
    content = out.read_text(encoding="utf-8")
    assert "Zintlr Intent Radar" in content
    assert "Score 5" in content
    assert "DISQUALIFIED" in content
    assert "Apollo employee" in content
    assert "Acme" in content


def test_export_csv(tmp_path: Path, sample_results: list[dict]) -> None:
    out = tmp_path / "report.csv"
    export_csv(sample_results, out)

    with out.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    # Highest score first
    assert rows[0]["score"] == "5"
    assert rows[0]["action"] == "BOTH"
    assert rows[0]["company"] == "Acme"
    # Disqualified at the end
    assert rows[1]["disqualified"] == "True"
    assert rows[1]["disqualifier_reason"] == "Apollo employee"


def test_csv_has_all_required_columns(tmp_path: Path, sample_results: list[dict]) -> None:
    out = tmp_path / "report.csv"
    export_csv(sample_results, out)

    with out.open(encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

    expected = {"score", "action", "company", "opening_line",
                "source_url", "disqualified"}
    assert expected.issubset(set(headers))
```

---

### File: `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install deps first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest
COPY . .

EXPOSE 8501

# Default command runs Streamlit. Override for cron-style runs:
# docker run ... python scripts/run_pipeline.py
CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true"]
```

---

### File: `.github/workflows/test.yml`

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run pytest
        run: pytest tests/ -v
```

---

### File: `.github/workflows/daily.yml`

```yaml
name: Daily Intent Radar Run

on:
  schedule:
    # 03:00 UTC = 08:30 IST
    - cron: "0 3 * * *"
  workflow_dispatch:  # allows manual run from GitHub Actions UI

permissions:
  contents: write    # needed to commit reports back

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run pipeline
        env:
          LLM_PROVIDER: groq
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          GROQ_MODEL: llama-3.3-70b-versatile
        run: python scripts/run_pipeline.py

      - name: Commit reports back to repo
        run: |
          git config user.name "intent-radar-bot"
          git config user.email "bot@zintlr.local"
          git add data/qualified/ || true
          git diff --staged --quiet || \
            git commit -m "Daily report $(date -u +%Y-%m-%d)"
          git push
```

---

## PART 5 — RUN LOCALLY

After Codex finishes building, in your terminal:

```bash
# 1. Activate the virtualenv Codex created
source .venv/bin/activate           # macOS/Linux
.venv\Scripts\activate              # Windows

# 2. Get a free Groq API key — console.groq.com → API Keys → create
# 3. Edit .env, paste your key after GROQ_API_KEY=

# 4. Verify connection
python scripts/test_llm.py

# 5. Run pipeline on the 6 sample posts
python scripts/run_pipeline.py

# 6. Open the markdown report in any viewer
open data/qualified/report_*.md     # macOS
xdg-open data/qualified/report_*.md # Linux
start data\qualified\report_*.md    # Windows

# 7. Try the UI
streamlit run app.py
# Browser opens at http://localhost:8501
```

If `scripts/test_llm.py` succeeds and `scripts/run_pipeline.py` produces a report where post #1 scores 5 and the Apollo employee is DISQUALIFIED, **the system works**.

---

## PART 6 — PUSH TO GITHUB

Tell Codex:

> Initialize a git repo, commit everything, and create a new GitHub repository called `zintlr-intent-radar`. Push the code there.

Or do it manually:
```bash
git init
git add .
git commit -m "Initial commit — Zintlr Intent Radar V1"

# Create repo on GitHub (https://github.com/new), then:
git remote add origin https://github.com/YOUR_USERNAME/zintlr-intent-radar.git
git branch -M main
git push -u origin main
```

**Add the GROQ_API_KEY as a GitHub secret:**
- Repo → Settings → Secrets and variables → Actions → New repository secret
- Name: `GROQ_API_KEY`
- Value: your Groq key
- This unlocks the daily scheduled run.

---

## PART 7 — DEPLOY UI TO HUGGING FACE SPACES

This is the AE-facing web UI, free, public URL.

1. Go to **huggingface.co/new-space**
2. Settings:
   - Owner: your account
   - Space name: `zintlr-intent-radar`
   - License: MIT
   - **Select the Streamlit SDK**
   - Hardware: CPU basic (free)
   - Visibility: Private (recommended for internal)
3. Create the Space.
4. In the Space's Settings → Variables and secrets → **New secret**:
   - Name: `GROQ_API_KEY`
   - Value: your Groq key
5. Connect your GitHub repo:
   - Space Settings → Linked Repositories → connect to `YOUR_USERNAME/zintlr-intent-radar`
   - Or, push directly to the Space's git remote:
     ```bash
     git remote add hf https://huggingface.co/spaces/YOUR_USER/zintlr-intent-radar
     git push hf main
     ```

The README.md frontmatter (`sdk: streamlit`, `app_file: app.py`) auto-configures the Space. After ~2 minutes you have a live URL like `https://huggingface.co/spaces/YOUR_USER/zintlr-intent-radar`.

Share that URL with your AEs. They upload posts CSVs, click Analyze, filter, download.

---

## PART 8 — SCHEDULE DAILY RUNS

Already wired. After you push to GitHub and add the `GROQ_API_KEY` secret:

- `.github/workflows/daily.yml` runs every day at 03:00 UTC (08:30 IST)
- It generates a report and commits it back to `data/qualified/` in the repo
- Click "Actions" tab on GitHub → "Daily Intent Radar Run" → "Run workflow" to trigger manually anytime

To change the schedule, edit the cron in `daily.yml`:
- `"0 3 * * *"` = 03:00 UTC daily
- `"0 9 * * 1-5"` = 09:00 UTC weekdays only
- See crontab.guru if you need help

---

## PART 9 — OPTIONAL: VPS WITH DOCKER

Only if you want it always-on with your own domain. Otherwise skip.

Get a $5/mo VPS at Hetzner / DigitalOcean. Install Docker. Then:

```bash
git clone https://github.com/YOUR_USERNAME/zintlr-intent-radar.git
cd zintlr-intent-radar
cp .env.example .env
nano .env   # paste your Groq key

docker build -t intent-radar .
docker run -d \
  --name intent-radar \
  -p 8501:8501 \
  --env-file .env \
  --restart unless-stopped \
  -v $(pwd)/data:/app/data \
  intent-radar
```

UI lives at `http://YOUR_VPS_IP:8501`. Add a domain + Caddy or Nginx for HTTPS later.

---

## PART 10 — OPERATING IT

### Daily AE workflow (via HF Spaces UI)
1. Scrape posts manually via Apify → download CSV
2. Open the HF Spaces URL
3. Upload CSV → click Analyze → wait 1-2 min
4. Filter by Score 4-5, Action `AE WHITE GLOVE` or `BOTH`
5. Download filtered CSV → import to Google Sheets → assign to AEs
6. AEs work the leads from their personal accounts

### Daily AE workflow (via GitHub Actions)
1. Apify scraper outputs to `data/raw/posts.csv` in the repo (set this up later)
2. Daily.yml runs at 03:00 UTC, scores everything, commits report back
3. AEs check the latest `data/qualified/report_*.md` in GitHub each morning
4. Sort the matching `.csv` in Sheets, work the high-score signals

### When the prompt needs tuning
The qualifier sometimes scores wrong on edge cases. To fix:
1. Open Codex in the project: `codex`
2. Tell it: *"The qualifier scored this post 5 but it should be 3. Update prompts/qualifier.md to handle this case. Add a test case for this scenario in tests/test_qualifier.py."*
3. Codex reads AGENTS.md, makes the change, runs tests, updates docs.

### When you outgrow the Groq free tier
Two options:
- Upgrade to Groq paid ($0.59 per million input tokens — still cheap)
- Switch to Ollama by changing `LLM_PROVIDER=ollama` in `.env` (zero cost, runs locally)

### What we build NEXT (each is its own Codex task)
- Apify scraper integration → no more manual CSV pasting
- Zintlr API enrichment → every signal hits Lookup + IDS for verified contacts
- SmartLead integration → bulk email track auto-sends
- HubSpot sync → leads flow into your CRM
- Slack notifier → AEs ping'd when score-5 leads arrive

For each, just tell Codex what you want. AGENTS.md gives it the context to do it correctly.

---

**End of build spec.**
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               