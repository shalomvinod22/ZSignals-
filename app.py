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