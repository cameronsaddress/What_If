"""
What If — AI-powered life-path simulator.
Streamlit UI for exploring alternate outcomes of major decisions.
"""

import streamlit as st
import asyncio
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

from backend import SimulationEngine, SimulationResult
from visualization import RiverOfDestiny, MobileRiverAdapter
from rate_limiter import rate_limiter, response_cache, api_monitor
from security import input_validator

load_dotenv()

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="What If — Life Path Simulator",
    page_icon="https://em-content.zobj.net/source/apple/391/crystal-ball_1f52e.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Styling — clean, modern glassmorphism
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        background-attachment: fixed;
    }

    .main {
        padding-top: 1rem;
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        border-radius: 24px;
        margin: 16px;
        padding: 32px;
    }

    h1, h2, h3 {
        font-family: 'Inter', sans-serif !important;
        color: #e0e0ff;
    }

    h1 {
        font-size: 2.8rem !important;
        font-weight: 700 !important;
        text-align: center;
        background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem !important;
    }

    p, label, .stMarkdown {
        font-family: 'Inter', sans-serif !important;
        color: #c8c8e0;
    }

    .stButton>button {
        font-family: 'Inter', sans-serif !important;
        background: linear-gradient(135deg, #7c3aed 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 14px 36px;
        font-size: 1rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.2s ease;
        box-shadow: 0 4px 20px rgba(124, 58, 237, 0.3);
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(124, 58, 237, 0.5);
    }

    .stTextArea textarea, .stTextInput input, .stSelectbox select {
        font-family: 'Inter', sans-serif !important;
        background: rgba(255, 255, 255, 0.07) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        color: #e0e0ff !important;
        padding: 14px 16px !important;
        font-size: 1rem !important;
    }

    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.25) !important;
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin: 12px 0;
    }

    .timeline-item {
        background: rgba(255, 255, 255, 0.04);
        padding: 16px 20px;
        margin: 8px 0;
        border-left: 3px solid #7c3aed;
        border-radius: 0 12px 12px 0;
        color: #c8c8e0;
        font-family: 'Inter', sans-serif;
    }

    .branch-story {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(8px);
        padding: 24px;
        border-radius: 16px;
        margin: 16px 0;
        border: 1px solid rgba(255, 255, 255, 0.08);
        color: #d0d0e8;
        font-family: 'Inter', sans-serif;
        line-height: 1.7;
    }

    .fate-badge {
        display: inline-block;
        padding: 8px 24px;
        border-radius: 50px;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.95rem;
        color: white;
    }

    .api-status {
        background: rgba(52, 211, 153, 0.08);
        border: 1px solid rgba(52, 211, 153, 0.2);
        padding: 16px;
        border-radius: 12px;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: #a0e0c0;
    }

    .disclaimer-box {
        background: rgba(251, 191, 36, 0.06);
        border: 1px solid rgba(251, 191, 36, 0.15);
        padding: 14px 20px;
        border-radius: 12px;
        font-size: 0.85rem;
        color: #d4c080;
        font-family: 'Inter', sans-serif;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif !important;
        font-weight: 500;
        border-radius: 8px;
        color: #a0a0c0;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(124, 58, 237, 0.3) !important;
        color: white !important;
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #7c3aed, #2563eb, #34d399);
        border-radius: 8px;
    }

    .streamlit-expanderHeader {
        font-family: 'Inter', sans-serif !important;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        font-weight: 500;
        color: #c8c8e0;
    }

    @media (max-width: 768px) {
        .main { margin: 8px; padding: 16px; }
        h1 { font-size: 2rem !important; }
        .stButton>button { padding: 12px 24px; font-size: 0.9rem; }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "simulation_result" not in st.session_state:
    st.session_state.simulation_result = None
if "simulation_engine" not in st.session_state:
    st.session_state.simulation_engine = None
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("OPENROUTER_API_KEY", "")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    st.markdown("# What If")
    st.markdown(
        '<p style="text-align:center; color:#8888aa; font-size:1.1rem; margin-top:-8px;">'
        "Explore the branching timelines of your life decisions</p>",
        unsafe_allow_html=True,
    )

    # Check for shared simulation
    query_params = st.query_params
    if "sim" in query_params:
        load_shared_simulation(query_params["sim"])
        return

    # --- API key ---
    with st.expander("Settings", expanded=not bool(st.session_state.api_key)):
        api_key = st.text_input(
            "OpenRouter API Key",
            value=st.session_state.api_key,
            type="password",
            placeholder="sk-or-v1-...",
            help="Get a free key at openrouter.ai — routes to Claude, GPT-4o, Gemini, and more",
        )
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
            st.session_state.simulation_engine = None

        if st.session_state.api_key:
            status = rate_limiter.get_status()
            cache_stats = response_cache.get_stats()
            api_stats = api_monitor.get_stats()

            masked = (
                f"{st.session_state.api_key[:7]}...{st.session_state.api_key[-4:]}"
                if len(st.session_state.api_key) > 11
                else "****"
            )
            st.markdown(
                f'<div class="api-status">'
                f"<strong>Status:</strong> Connected &nbsp; | &nbsp; "
                f"<strong>Key:</strong> {masked} &nbsp; | &nbsp; "
                f"<strong>Rate limit:</strong> {status['available_tokens']}/{status['max_tokens']} &nbsp; | &nbsp; "
                f"<strong>Cache:</strong> {cache_stats['hit_rate']} hit rate &nbsp; | &nbsp; "
                f"<strong>API calls:</strong> {api_stats['total_calls']}"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.info("Enter your OpenRouter API key to enable AI-powered simulations.")

    # --- Disclaimer ---
    st.markdown(
        '<div class="disclaimer-box">'
        "<strong>Note:</strong> This is an exploratory tool, not a prediction engine. "
        "Results are AI-generated narratives informed by real-world probability data. "
        "Use them for reflection, not decision-making."
        "</div>",
        unsafe_allow_html=True,
    )

    # --- Input ---
    col1, col2 = st.columns([3, 1])

    with col1:
        raw_decision = st.text_area(
            "What decision are you exploring?",
            placeholder="Example: What if I moved to Tokyo instead of staying in my hometown?",
            height=80,
            key="decision_input",
            max_chars=500,
        )
        decision = input_validator.sanitize_decision(raw_decision) if raw_decision else ""

    with col2:
        mode = st.selectbox(
            "Mode",
            ["realistic", "50/50", "random"],
            format_func=lambda x: {
                "realistic": "Realistic",
                "50/50": "Balanced (50/50)",
                "random": "Wildcard",
            }[x],
            help="Realistic: research-backed probabilities | Balanced: equal odds | Wildcard: anything goes",
        )

    # --- Generate ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Run Simulation", type="primary", use_container_width=True):
            if not decision.strip():
                st.error("Please enter a decision to simulate.")
            elif not st.session_state.api_key:
                st.warning("No API key — running in offline fallback mode.")
                with st.spinner("Generating timelines..."):
                    asyncio.run(generate_simulation(decision, mode))
            else:
                with st.spinner("Generating timelines..."):
                    asyncio.run(generate_simulation(decision, mode))

    # --- Results ---
    if st.session_state.simulation_result:
        display_results()


# ---------------------------------------------------------------------------
# Simulation runner
# ---------------------------------------------------------------------------

async def generate_simulation(decision: str, mode: str):
    if not st.session_state.simulation_engine:
        st.session_state.simulation_engine = SimulationEngine(
            api_key=st.session_state.api_key or None,
        )

    engine = st.session_state.simulation_engine

    try:
        branches = await engine.generate_branches(decision, mode, num_branches=4)

        sim_id = engine.generate_simulation_id(decision, mode)
        result = SimulationResult(
            simulation_id=sim_id,
            user_decision=decision,
            mode=mode,
            branches=branches,
            created_at=datetime.now(timezone.utc),
            share_url=f"?sim={sim_id}",
        )

        await engine.save_simulation(result)
        st.session_state.simulation_result = result

    except Exception as e:
        st.error(f"Simulation error: {e}")


# ---------------------------------------------------------------------------
# Results display
# ---------------------------------------------------------------------------

def display_results():
    result = st.session_state.simulation_result

    st.markdown(f'## "{result.user_decision}"')

    # SVG visualization
    st.markdown("### River of Destiny")
    river = RiverOfDestiny(width=800, height=600)
    branches_data = [b.model_dump() for b in result.branches]
    svg = river.generate_river_svg(branches_data, result.user_decision)

    st.markdown(
        '<p style="text-align:center; color:#8888aa; font-size:0.85rem;">'
        "Hover over branches to explore alternate timelines</p>",
        unsafe_allow_html=True,
    )
    st.markdown(f'<div style="text-align:center">{svg}</div>', unsafe_allow_html=True)

    # Branch details
    st.markdown("### Timeline Details")

    tabs = st.tabs([f"Path {i+1}: {b.title}" for i, b in enumerate(result.branches)])

    for tab, branch in zip(tabs, result.branches):
        with tab:
            # Fate score badge
            if branch.fate_score >= 70:
                gradient = "linear-gradient(135deg, #34d399, #059669)"
                label = "Favorable"
            elif branch.fate_score >= 40:
                gradient = "linear-gradient(135deg, #a78bfa, #7c3aed)"
                label = "Mixed"
            else:
                gradient = "linear-gradient(135deg, #f87171, #dc2626)"
                label = "Challenging"

            st.markdown(
                f'<div style="text-align:center; margin-bottom:16px;">'
                f'<span class="fate-badge" style="background:{gradient};">'
                f"{label} — Fate Score: {branch.fate_score}/100"
                f"</span></div>",
                unsafe_allow_html=True,
            )

            # Story
            st.markdown(f'<div class="branch-story">{branch.story}</div>', unsafe_allow_html=True)

            # Timeline
            st.markdown(
                '<p style="color:#a78bfa; font-weight:600; margin-top:20px;">Timeline</p>',
                unsafe_allow_html=True,
            )
            for event in branch.timeline:
                st.markdown(
                    f'<div class="timeline-item">'
                    f'<strong>{event["year"]}:</strong> {event["event"]}</div>',
                    unsafe_allow_html=True,
                )

            # Key events
            st.markdown(
                '<p style="color:#60a5fa; font-weight:600; margin-top:20px;">Key Events</p>',
                unsafe_allow_html=True,
            )
            for event in branch.key_events:
                st.markdown(f"- {event}")

            # Probability bar
            prob_pct = int(branch.probability_score * 100)
            st.markdown(
                '<p style="color:#8888aa; font-size:0.85rem; margin-top:20px;">Probability</p>',
                unsafe_allow_html=True,
            )
            st.progress(branch.probability_score)
            st.markdown(
                f'<p style="text-align:center; color:#a0a0c0; font-size:0.85rem;">{prob_pct}%</p>',
                unsafe_allow_html=True,
            )

    # Simulation metadata
    st.markdown("---")
    st.markdown(
        f'<p style="text-align:center; color:#666; font-size:0.8rem;">'
        f"Simulation {result.simulation_id} &nbsp;|&nbsp; "
        f"Mode: {result.mode} &nbsp;|&nbsp; "
        f"{len(result.branches)} branches generated"
        f"</p>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Shared simulation loader
# ---------------------------------------------------------------------------

def load_shared_simulation(sim_id: str):
    if not st.session_state.simulation_engine:
        st.session_state.simulation_engine = SimulationEngine(
            api_key=st.session_state.api_key or None,
        )

    with st.spinner("Loading simulation..."):
        result = asyncio.run(st.session_state.simulation_engine.load_simulation(sim_id))

    if result:
        st.session_state.simulation_result = result
        display_results()
    else:
        st.error("Simulation not found. It may have expired or the link is incorrect.")
        if st.button("Start New Simulation"):
            st.query_params.clear()
            st.rerun()


if __name__ == "__main__":
    main()
