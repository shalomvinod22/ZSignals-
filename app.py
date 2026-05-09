# -*- coding: utf-8 -*-
"""Zintlr Pulse: Dark-mode Streamlit UI for internal BDR/AE team."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from src.db import PulseDB
from src.llm import get_llm
from src.qualifier import Qualifier
from src.pulse_pipeline import run_pulse_scrape


# ============================================================
# DESIGN SYSTEM
# ============================================================

PRIMARY = "#5B5FE9"
PRIMARY_LIGHT = "#7B7FFF"
ACCENT = "#3FE9DA"
ACCENT_HOVER = "#5FF5E8"
BG = "#0A0B0F"
BG_CARD = "#13141A"
BG_CARD_HOVER = "#1A1B23"
BORDER = "#22242E"
TEXT_PRIMARY = "#F4F4F8"
TEXT_SECONDARY = "#9EA3B0"
TEXT_MUTED = "#5C6170"
SUCCESS = "#22C55E"
WARNING = "#F59E0B"
DANGER = "#EF4444"
HIGH_TIER = "#FF4D4D"
MEDIUM_TIER = "#3FE9DA"
LOW_TIER = "#9EA3B0"


def inject_custom_css() -> None:
    """Inject dark mode styling."""
    css = f"""
    <style>
        :root {{
            --primary: {PRIMARY};
            --accent: {ACCENT};
            --bg: {BG};
            --bg-card: {BG_CARD};
        }}
        
        * {{
            font-family: 'Inter', 'SF Pro Display', system-ui, -apple-system, sans-serif;
        }}
        
        code {{
            font-family: 'JetBrains Mono', 'Menlo', monospace;
        }}
        
        body {{
            background-color: {BG};
            color: {TEXT_PRIMARY};
        }}
        
        .stApp {{
            background-color: {BG};
        }}
        
        .stMetric {{
            background-color: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 10px;
        }}
        
        .stButton > button {{
            background-color: {PRIMARY};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 500;
            transition: all 200ms;
        }}
        
        .stButton > button:hover {{
            background-color: {PRIMARY_LIGHT};
            transform: translateY(-1px);
        }}
        
        .stExpander {{
            background-color: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 12px;
        }}
        
        .stTabs [data-baseweb="tab-list"] {{
            border-bottom: 2px solid {BORDER};
        }}
        
        .stTabs [aria-selected="true"] {{
            border-bottom-color: {PRIMARY};
            color: {PRIMARY};
        }}
        
        .stTabs [aria-selected="false"] {{
            color: {TEXT_MUTED};
        }}
        
        /* Cards */
        [data-testid="metric-container"] {{
            background-color: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 20px;
        }}
        
        /* Smooth scroll */
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: {BG};
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {BORDER};
            border-radius: 4px;
        }}
        
        /* Text colors */
        .text-primary {{
            color: {TEXT_PRIMARY};
        }}
        
        .text-secondary {{
            color: {TEXT_SECONDARY};
        }}
        
        .text-muted {{
            color: {TEXT_MUTED};
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Zintlr Pulse",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_custom_css()

# Initialize paths and LLM
PROJECT_ROOT = Path(__file__).resolve().parent
PROMPT_PATH = PROJECT_ROOT / "prompts" / "qualifier.md"


# ============================================================
# INITIALIZE SESSION STATE
# ============================================================

if "db" not in st.session_state:
    st.session_state.db = PulseDB()

if "qualifier" not in st.session_state:
    try:
        llm = get_llm()
        st.session_state.qualifier = Qualifier(PROMPT_PATH, llm)
    except Exception:
        st.session_state.qualifier = None

if "scrape_in_progress" not in st.session_state:
    st.session_state.scrape_in_progress = False

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "progress_messages" not in st.session_state:
    st.session_state.progress_messages = []


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_relative_time(iso_str: str) -> str:
    """Convert ISO datetime to relative time string."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.utcnow()
        delta = now - dt.replace(tzinfo=None)
        
        if delta.total_seconds() < 60:
            return "now"
        elif delta.total_seconds() < 3600:
            mins = int(delta.total_seconds() / 60)
            return f"{mins}m ago"
        elif delta.total_seconds() < 86400:
            hours = int(delta.total_seconds() / 3600)
            return f"{hours}h ago"
        else:
            days = int(delta.total_seconds() / 86400)
            return f"{days}d ago"
    except Exception:
        return "unknown"


def get_score_color(score: int) -> str:
    """Get color for intent score."""
    if score >= 5:
        return HIGH_TIER
    elif score >= 3:
        return MEDIUM_TIER
    else:
        return LOW_TIER


def get_score_label(score: int) -> str:
    """Get label for intent score."""
    if score >= 5:
        return " SCORE 5"
    elif score >= 4:
        return " SCORE 4"
    elif score >= 3:
        return "WARNING SCORE 3"
    else:
        return "YELLOW SCORE 2"


def _badge(text: str, bg: str, fg: str = "#0A0B0F") -> str:
    """Build a single inline HTML badge. Always rendered with
    unsafe_allow_html=True by callers."""
    return (
        f'<span style="background:{bg};color:{fg};padding:3px 10px;'
        f'border-radius:6px;font-size:11px;font-weight:600;'
        f'letter-spacing:0.3px;margin-right:6px;">{text}</span>'
    )


def render_lead_card(post: dict, db: PulseDB) -> None:
    """Render a single lead as a Streamlit native card with updated V1.3 fields."""

    score = post.get("score", post.get("intent_score", 0))
    signal_types = post.get("signal_types", [])
    post_id = post.get("post_id")
    identity = post.get("identity") or {}
    disqualified = bool(post.get("is_disqualified", post.get("disqualified")))
    confidence = post.get("confidence") or post.get("tier") or "-"
    recommended_action = post.get("ae_priority") or post.get("recommended_action") or "-"
    company_context = post.get("company_context") or {}

    tier_color = {
        5: HIGH_TIER,
        4: MEDIUM_TIER,
        3: MEDIUM_TIER,
        2: LOW_TIER,
        1: LOW_TIER,
        0: TEXT_MUTED,
    }.get(score, TEXT_MUTED)

    with st.container(border=True):
        top_col1, top_col2 = st.columns([3, 1])

        with top_col1:
            badges_html = _badge(
                "DISQUALIFIED" if disqualified else get_score_label(score),
                DANGER if disqualified else tier_color,
                "#FFFFFF",
            )
            badges_html += _badge(f"Action: {recommended_action}", BG_CARD, ACCENT)
            badges_html += _badge(f"Confidence: {confidence}", BG_CARD, TEXT_SECONDARY)
            for sig in signal_types[:3]:
                badges_html += _badge(sig.replace("_", " ").upper(), BG_CARD, ACCENT)
            st.markdown(badges_html, unsafe_allow_html=True)

        with top_col2:
            platform = post.get("platform", "?")
            date_str = format_relative_time(post.get("date", ""))
            st.caption(f"{platform} - {date_str}")

        st.write("")

        lead_title = identity.get("name") or identity.get("username") or post.get("username", "-")
        st.markdown(f"** {lead_title}**")

        details = []
        if identity.get("company"):
            details.append(identity["company"])
        if identity.get("role"):
            details.append(identity["role"])
        if identity.get("location"):
            details.append(identity["location"])
        if identity.get("industry"):
            details.append(identity["industry"])
        if details:
            st.caption(" - ".join(details))

        if disqualified:
            reason = post.get("disqualifier_reason") or "Disqualified by policy"
            st.error(f" {reason}")

        pain = post.get("pain_evidence") or post.get("pain_in_words") or "No explicit pain extracted"
        spec = post.get("specificity") or "GENERAL"
        category = post.get("pain_type") or post.get("pain_category") or "Unknown"
        st.markdown(f"** {category} - {spec}**")
        st.caption(pain)

        original = post.get("content", "").strip()
        if original:
            display = original if len(original) <= 400 else original[:400] + "..."
            st.markdown(f"> _{display}_")

        why = post.get("why_matters")
        if why:
            st.markdown(f"**Why this matters:** {why}")

        conversation_kit = post.get("conversation_kit") or {}
        opening_line = (
            conversation_kit.get("cold_opener_email")
            if isinstance(conversation_kit, dict)
            else None
        ) or post.get("opening_line")
        if opening_line and not disqualified:
            st.markdown("**Suggested opener:**")
            st.code(opening_line, language=None)

        ctx_label = " | ".join(
            part for part in [
                company_context.get("size"),
                company_context.get("geography"),
                company_context.get("stage"),
            ]
            if part
        )
        if ctx_label:
            st.caption(f" Company context: {ctx_label}")

        action_col1, action_col2, action_col3, action_col4 = st.columns(4)
        with action_col1:
            url = post.get("source_url", "")
            if url:
                st.link_button(" Open post", url, use_container_width=True)
        with action_col2:
            if st.button(" Re-qualify", key=f"req_{post_id}", use_container_width=True):
                db.set_qualifier_cache(post_id, None)
                st.rerun()
        with action_col3:
            if st.button("WARNING Wrong", key=f"wrong_{post_id}", use_container_width=True):
                db.set_status(post_id, "Skipped", note="AE flagged as wrong")
                st.rerun()
        with action_col4:
            if not disqualified:
                st.caption(f"Recommended: {recommended_action}")
            else:
                st.caption("Disqualified")

        current_status = db.get_status(post_id) or "Pending"
        status_options = ["Pending", "Contacted", "Replied", "Won", "Lost", "Skipped"]
        new_status = st.radio(
            "Status",
            status_options,
            index=status_options.index(current_status) if current_status in status_options else 0,
            horizontal=True,
            key=f"status_{post_id}",
            label_visibility="collapsed",
        )
        if new_status != current_status:
            db.set_status(post_id, new_status)
            st.rerun()

        with st.expander(" Notes", expanded=False):
            existing_note = db.get_note(post_id) or ""
            note_input = st.text_area(
                "Notes",
                value=existing_note,
                key=f"note_{post_id}",
                label_visibility="collapsed",
                placeholder="Add a note about this lead...",
            )
            if st.button("Save note", key=f"save_note_{post_id}"):
                db.set_status(post_id, new_status, note=note_input)
                st.success("Note saved")


# ============================================================
# HEADER
# ============================================================

col_logo, col_spacer, col_status = st.columns([1, 3, 1])

with col_logo:
    logo_path = Path("data/assets/zintlr_logo_main.png")
    if logo_path.exists():
        st.image(str(logo_path), width=32)
    st.markdown(
        f'<span style="font-size: 18px; font-weight: bold; color: {TEXT_PRIMARY};">Pulse</span>',
        unsafe_allow_html=True,
    )

with col_status:
    try:
        llm = get_llm()
        st.markdown(
            f'<span style="color: {SUCCESS};">* Live</span> <span style="color: {TEXT_MUTED};">v1.3</span>',
            unsafe_allow_html=True,
        )
    except Exception:
        st.markdown(
            f'<span style="color: {DANGER};">* Offline</span>',
            unsafe_allow_html=True,
        )

st.divider()


# ============================================================
# HERO STAT BAR
# ============================================================

col1, col2, col3, col4 = st.columns(4)

high_count = 0
med_count = 0
low_count = 0
last_scrape = "Never"

if st.session_state.last_result:
    high_count = st.session_state.last_result["stats"].get("high_count", 0)
    med_count = st.session_state.last_result["stats"].get("medium_count", 0)
    low_count = st.session_state.last_result["stats"].get("low_count", 0)

history = st.session_state.db.get_scrape_history(1)
if history:
    last_scrape = format_relative_time(history[0]["started_at"])

with col1:
    st.metric(" HIGH leads", high_count)

with col2:
    st.metric(" MEDIUM leads", med_count)

with col3:
    st.metric("YELLOW LOW leads", low_count)

with col4:
    st.metric(" Last scrape", last_scrape)

st.divider()


# ============================================================
# SCRAPE CONTROL PANEL
# ============================================================

with st.expander(" Run a new scrape", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        valid_sources = ["reddit", "g2", "hackernews", "linkedin"]
        default_sources = [
            source.strip()
            for source in st.session_state.db.get_config(
                "default_sources", "reddit,hackernews"
            ).split(",")
            if source.strip() in valid_sources
        ]
        sources = st.multiselect(
            "Data sources",
            valid_sources,
            default=default_sources or ["reddit", "hackernews"],
            help="LinkedIn is new in V1.3 and uses the Apify proxy via APIFY_API_TOKEN. G2 remains optional because it may be blocked by Cloudflare.",
        )
        st.session_state.db.set_config("default_sources", ",".join(sources))

        freshness_options = {
            "Last 24 hours": 1,
            "Last 3 days": 3,
            "Last 7 days": 7,
            "Last 14 days": 14,
            "Last 30 days": 30,
        }
        default_freshness = st.session_state.db.get_config(
            "default_freshness", "Last 7 days"
        )
        freshness_label = st.selectbox(
            "Freshness window",
            list(freshness_options.keys()),
            index=list(freshness_options.keys()).index(default_freshness),
        )
        freshness_days = freshness_options[freshness_label]
        st.session_state.db.set_config("default_freshness", freshness_label)
    
    with col2:
        dedup_mode = st.radio(
            "Deduplication",
            ("Show only NEW since last scrape", "Show all leads in window"),
            index=0,
        )
        dedup_mode = "new_only" if dedup_mode.startswith("Show only") else "all"
        
        test_mode = st.checkbox(" Test scrape (limited scope)")
        demo_mode = st.checkbox(" Demo Mode (curated 12 posts)")
    
    if st.session_state.qualifier is None:
        st.error(
            "LLM not configured. Verify GROQ_API_KEY / OLLAMA settings in .env "
            "and refresh the page before scraping."
        )
    elif st.button(" Run Scrape Now", use_container_width=True):
        st.session_state.scrape_in_progress = True
        
        # Run scrape in main thread (Streamlit constraint)
        status_text = st.empty()
        progress_bar = st.empty()
        
        def progress_callback(*args, **kwargs):
            # Args may be: (current_idx, total, source_name, status)
            # Or legacy: (current_idx, total)
            current_idx = args[0] if len(args) > 0 else 0
            total = args[1] if len(args) > 1 else 0
            source_name = args[2] if len(args) > 2 else "scraping"
            status = args[3] if len(args) > 3 else ""

            if total > 0:
                progress_bar.progress(min(max(current_idx / total, 0.0), 1.0))
            status_text.text(f"[{current_idx}/{total}] {source_name}: {status}")
        
        try:
            result = run_pulse_scrape(
                sources=sources if not demo_mode else [],
                freshness_days=freshness_days,
                dedup_mode=dedup_mode,
                db=st.session_state.db,
                qualifier=st.session_state.qualifier,
                progress_callback=progress_callback,
                test_mode=test_mode,
                demo_mode=demo_mode,
            )
            st.session_state.last_result = result
            
            # Show result summary
            high = result['stats']['high_count']
            med = result['stats']['medium_count']
            low = result['stats']['low_count']
            dq = result['stats']['dq_count']
            failures = result.get('failures', [])
            
            # Success banner
            st.success(
                f"Scrape complete! {high} HIGH + {med} MEDIUM + {low} LOW = {high+med+low} total leads. "
                f"Runtime: {result['runtime_seconds']:.1f}s"
            )
            
            # Failure banner if issues found
            if failures:
                st.warning(f"WARNING {len(failures)} source(s) had issues:")
                for fail in failures[:10]:  # Show max 10
                    st.caption(f"  - {fail}")
            
            st.rerun()
        except Exception as e:
            st.error(f"Scrape failed: {str(e)}")
        finally:
            st.session_state.scrape_in_progress = False
            status_text.empty()
            progress_bar.empty()


# ============================================================
# RESULTS TABS
# ============================================================

if st.session_state.last_result:
    result = st.session_state.last_result
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        f" HIGH ({result['stats']['high_count']})",
        f" MEDIUM ({result['stats']['medium_count']})",
        f"YELLOW LOW ({result['stats']['low_count']})",
        f" DISQUALIFIED ({result['stats']['dq_count']})",
        " History",
        " Settings",
    ])
    
    # TAB 1: HIGH
    with tab1:
        posts = result["buckets"]["HIGH"]
        if posts:
            for post in posts:
                render_lead_card(post, st.session_state.db)
        else:
            # Show diagnostic if 0 leads AND failures exist
            failures = result.get("failures", [])
            if failures:
                st.warning(
                    "**No HIGH-intent leads found.** "
                    f"({len(failures)} source issues detected)\n\n"
                    f"Last scrape had failures:\n" + 
                    "\n".join(f"  - {f}" for f in failures[:5])
                )
                st.caption(" Tip: Try again in 5 min (may be rate-limited) or check Settings > Diagnostics")
            else:
                st.info("No HIGH-intent leads found in this window. Try a longer freshness window or different sources.")
    
    # TAB 2: MEDIUM
    with tab2:
        posts = result["buckets"]["MEDIUM"]
        if posts:
            for post in posts:
                render_lead_card(post, st.session_state.db)
        else:
            st.info("No MEDIUM-intent leads found in this window.")
    
    # TAB 3: LOW
    with tab3:
        posts = result["buckets"]["LOW"]
        if posts:
            for post in posts:
                render_lead_card(post, st.session_state.db)
        else:
            st.info("No LOW-intent leads found in this window.")
    
    # TAB 4: DISQUALIFIED
    with tab4:
        posts = result["buckets"]["DISQUALIFIED"]
        if posts:
            for post in posts:
                render_lead_card(post, st.session_state.db)
        else:
            st.info("No disqualified leads.")
    
    # TAB 5: HISTORY
    with tab5:
        history = st.session_state.db.get_scrape_history(20)
        if history:
            history_df = pd.DataFrame(history)
            st.dataframe(history_df, use_container_width=True)
        else:
            st.info("No scrape history yet.")
    
    # TAB 6: SETTINGS
    with tab6:
        db = st.session_state.db
        st.subheader("Diagnostics")

        if st.button("Test LLM connection"):
            try:
                llm = get_llm()
                st.success(f"PASS {llm.name} responsive")
            except Exception as e:
                st.error(f"FAIL LLM connection failed: {str(e)}")

        st.markdown("---")
        st.subheader("Source configuration")
        st.write(
            "LinkedIn scraping uses the Apify proxy via `APIFY_API_TOKEN` and optionally `LINKEDIN_SEARCH_TERMS` for a more targeted feed. "
            "If missing, LinkedIn scraping may fail or return zero results."
        )
        token_present = bool(os.environ.get("APIFY_API_TOKEN"))
        st.write(f"Apify API token present: {'' if token_present else ''}")
        search_terms = os.environ.get("LINKEDIN_SEARCH_TERMS", "(defaults to tier-1 keywords)")
        st.write(f"LinkedIn search terms: {search_terms}")

        if st.button("Re-qualify all recent leads"):
            for post in result["posts"]:
                db.set_qualifier_cache(post["post_id"], None)
            st.success("Cleared qualifier cache for recent leads. Re-run scrape to re-score.")

        st.markdown("---")
        st.subheader("Last Scrape Failures")
        failures = result.get("failures", [])
        if failures:
            st.warning(f"**{len(failures)} failure(s):**")
            for fail in failures:
                st.code(fail, language=None)
        else:
            st.success("PASS Last scrape had no failures")

        st.markdown("---")
        st.subheader("Database Health")

        db_info = {
            "seen_posts": st.session_state.db.conn.execute(
                "SELECT COUNT(*) FROM seen_posts"
            ).fetchone()[0],
            "lead_status": st.session_state.db.conn.execute(
                "SELECT COUNT(*) FROM lead_status"
            ).fetchone()[0],
            "qualifier_cache": st.session_state.db.conn.execute(
                "SELECT COUNT(*) FROM qualifier_cache"
            ).fetchone()[0],
            "lead_outcomes": st.session_state.db.conn.execute(
                "SELECT COUNT(*) FROM lead_outcomes"
            ).fetchone()[0],
            "linkedin_watchlist": st.session_state.db.conn.execute(
                "SELECT COUNT(*) FROM linkedin_watchlist"
            ).fetchone()[0],
            "source_quality": st.session_state.db.conn.execute(
                "SELECT COUNT(*) FROM source_quality"
            ).fetchone()[0],
        }

        for key, count in db_info.items():
            st.metric(key, count)

        if st.button("Reset qualifier cache"):
            st.session_state.db.clear_qualifier_cache()
            st.success("Qualifier cache cleared.")

        if st.button("Reset seen posts"):
            st.session_state.db.reset_seen_posts()
            st.success("Seen posts cleared. Re-run scrape to get all posts again.")
else:
    st.info("No scrapes yet. Run one above to see results.")
