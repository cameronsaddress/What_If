"""
Quantum Life Fork Simulator - Main Streamlit App
A web app that simulates alternate life paths based on key decisions
"""

import streamlit as st
import asyncio
from datetime import datetime
import os
from typing import Optional
import stripe
from dotenv import load_dotenv

# Import our modules
from backend import SimulationEngine, SimulationResult, LifeBranch
from visualization import RiverOfDestiny, MobileRiverAdapter
from rate_limiter import rate_limiter, response_cache, api_monitor
from security import input_validator, api_key_manager, security_monitor

# Load environment variables
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_API_KEY", "")

# Page config
st.set_page_config(
    page_title="Quantum Life Fork Simulator",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for gaming aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600;700&family=Poppins:wght@400;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        background-attachment: fixed;
        min-height: 100vh;
    }
    
    .main {
        padding-top: 1rem;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 30px;
        margin: 20px;
        padding: 30px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    }
    
    /* Headers with Game Style */
    h1, h2, h3 {
        font-family: 'Fredoka', cursive !important;
        text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.2);
    }
    
    h1 {
        background: linear-gradient(45deg, #FFD700, #FFA500, #FF6B6B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem !important;
        text-align: center;
        margin-bottom: 0 !important;
        animation: float 3s ease-in-out infinite;
    }
    
    /* Animated Buttons */
    .stButton>button {
        font-family: 'Fredoka', cursive !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 15px 40px;
        font-size: 1.2rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        position: relative;
        overflow: hidden;
    }
    
    .stButton>button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        transition: left 0.5s;
    }
    
    .stButton>button:hover::before {
        left: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-5px) scale(1.05);
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.6);
    }
    
    /* Input Fields with Game Style */
    .stTextArea textarea, .stTextInput input, .stSelectbox select {
        font-family: 'Poppins', sans-serif !important;
        background: rgba(255, 255, 255, 0.9) !important;
        border: 3px solid #FFD700 !important;
        border-radius: 20px !important;
        padding: 15px 20px !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 5px 20px rgba(255, 215, 0, 0.2) !important;
    }
    
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #FF6B6B !important;
        box-shadow: 0 5px 30px rgba(255, 107, 107, 0.4) !important;
        transform: scale(1.02);
    }
    
    /* Card Styles */
    .timeline-item {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.2rem;
        margin: 0.8rem 0;
        border-left: 5px solid transparent;
        border-image: linear-gradient(45deg, #FFD700, #FF6B6B) 1;
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
        font-family: 'Poppins', sans-serif;
    }
    
    .timeline-item:hover {
        transform: translateX(10px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
    
    .branch-story {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 25px;
        margin: 1.5rem 0;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        border: 2px solid transparent;
        background-clip: padding-box;
        position: relative;
        font-family: 'Poppins', sans-serif;
    }
    
    .branch-story::before {
        content: '';
        position: absolute;
        top: -2px; left: -2px; right: -2px; bottom: -2px;
        background: linear-gradient(45deg, #FFD700, #FF6B6B, #667eea);
        border-radius: 25px;
        z-index: -1;
    }
    
    /* Premium Banner */
    .premium-banner {
        background: linear-gradient(45deg, #FFD700, #FFA500);
        color: #333;
        padding: 1.5rem;
        border-radius: 20px;
        text-align: center;
        margin: 1.5rem 0;
        box-shadow: 0 10px 30px rgba(255, 215, 0, 0.3);
        font-family: 'Fredoka', cursive;
        font-size: 1.1rem;
        animation: pulse 2s infinite;
        position: relative;
        overflow: hidden;
    }
    
    .premium-banner::before {
        content: '⭐';
        position: absolute;
        font-size: 100px;
        opacity: 0.1;
        top: -20px;
        right: -20px;
        animation: rotate 10s linear infinite;
    }
    
    /* Disclaimer with Fun Style */
    .disclaimer {
        background: linear-gradient(135deg, #FFE5B4, #FFDAB9);
        border: 2px dashed #FFA500;
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
        font-size: 0.9rem;
        font-family: 'Poppins', sans-serif;
        position: relative;
        padding-left: 3rem;
    }
    
    .disclaimer::before {
        content: '⚠️';
        position: absolute;
        left: 1rem;
        font-size: 1.5rem;
    }
    
    /* Share Buttons */
    .share-button {
        padding: 0.8rem 1.5rem;
        background: linear-gradient(135deg, #1DA1F2, #0e71c8);
        color: white;
        text-decoration: none;
        border-radius: 30px;
        font-size: 1rem;
        font-family: 'Fredoka', cursive;
        transition: all 0.3s ease;
        display: inline-block;
        box-shadow: 0 5px 15px rgba(29, 161, 242, 0.3);
    }
    
    .share-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(29, 161, 242, 0.5);
    }
    
    /* API Status Box */
    .api-status {
        background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
        border: 2px solid #4CAF50;
        padding: 1rem;
        border-radius: 20px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        font-family: 'Poppins', sans-serif;
        box-shadow: 0 5px 15px rgba(76, 175, 80, 0.2);
    }
    
    /* Confirmation Dialog */
    .confirmation-dialog {
        background: linear-gradient(135deg, #ffffff, #f5f5f5);
        border: 3px solid #FFD700;
        padding: 2rem;
        border-radius: 25px;
        box-shadow: 0 15px 50px rgba(0, 0, 0, 0.2);
        margin: 1rem 0;
        text-align: center;
        position: relative;
        font-family: 'Fredoka', cursive;
    }
    
    .confirmation-dialog h3 {
        color: #667eea;
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    
    /* Tabs with Game Style */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.8);
        border-radius: 20px;
        padding: 5px;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        font-family: 'Fredoka', cursive !important;
        font-weight: 600;
        border-radius: 15px;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white !important;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #FFD700, #FFA500, #FF6B6B);
        border-radius: 10px;
    }
    
    /* Animations */
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    /* Expander with Game Style */
    .streamlit-expanderHeader {
        font-family: 'Fredoka', cursive !important;
        background: linear-gradient(135deg, #FFD700, #FFA500);
        border-radius: 15px;
        font-weight: 600;
    }
    
    /* Success/Error Messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 15px;
        font-family: 'Poppins', sans-serif;
        padding: 1rem;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Mobile Responsive */
    @media (max-width: 768px) {
        .main {
            margin: 10px;
            padding: 20px;
        }
        h1 {
            font-size: 2.5rem !important;
        }
        .stButton>button {
            padding: 12px 30px;
            font-size: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'simulation_result' not in st.session_state:
    st.session_state.simulation_result = None
if 'is_premium' not in st.session_state:
    st.session_state.is_premium = False
if 'simulation_engine' not in st.session_state:
    st.session_state.simulation_engine = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'api_type' not in st.session_state:
    st.session_state.api_type = "grok"
if 'show_confirmation' not in st.session_state:
    st.session_state.show_confirmation = False
if 'pending_simulation' not in st.session_state:
    st.session_state.pending_simulation = None

def main():
    # Header
    st.markdown("# 🌊 Quantum Life Fork Simulator")
    st.markdown("### Explore the multiverse of your life decisions")
    
    # Check if loading shared simulation
    query_params = st.query_params
    if 'sim' in query_params:
        load_shared_simulation(query_params['sim'])
        return
    
    # API Configuration Section
    with st.expander("🔧 API Configuration", expanded=not bool(st.session_state.api_key)):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            api_key = st.text_input(
                "API Key",
                value=st.session_state.api_key,
                type="password",
                placeholder="Enter your API key here...",
                help="Enter your Grok, Anthropic, or OpenAI API key"
            )
            if api_key != st.session_state.api_key:
                # Validate API key format
                if api_key and not input_validator.validate_api_key(api_key, st.session_state.api_type):
                    st.error(f"Invalid {st.session_state.api_type} API key format")
                else:
                    st.session_state.api_key = api_key
                    st.session_state.simulation_engine = None
        
        with col2:
            api_type = st.selectbox(
                "API Type",
                options=["grok", "anthropic", "openai"],
                index=["grok", "anthropic", "openai"].index(st.session_state.api_type),
                format_func=lambda x: {
                    "grok": "🤖 Grok (xAI)",
                    "anthropic": "🧠 Claude",
                    "openai": "🌟 GPT-4"
                }[x]
            )
            if api_type != st.session_state.api_type:
                st.session_state.api_type = api_type
                st.session_state.simulation_engine = None
        
        # API Status Display
        if st.session_state.api_key:
            status = rate_limiter.get_status()
            cache_stats = response_cache.get_stats()
            api_stats = api_monitor.get_stats()
            
            masked_key = api_key_manager.mask_key(st.session_state.api_key)
            st.markdown(f"""
            <div class="api-status">
                <strong>API Status:</strong> ✅ Configured ({st.session_state.api_type.upper()})<br>
                <strong>API Key:</strong> {masked_key}<br>
                <strong>Rate Limit:</strong> {status['available_tokens']}/{status['max_tokens']} requests available<br>
                <strong>Cache:</strong> {cache_stats['hits']} hits, {cache_stats['misses']} misses ({cache_stats['hit_rate']})<br>
                <strong>Total API Calls:</strong> {api_stats['total_calls']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Please enter an API key to use the simulator")
    
    # Disclaimer with game style
    st.markdown("""
    <div class="disclaimer">
        <strong>Fun Reminder:</strong> This is a game of "what ifs" - not a crystal ball! 
        Enjoy the wild possibilities, but make real decisions with your brain, not our RNG! 🎲
    </div>
    """, unsafe_allow_html=True)
    
    # Main input section
    col1, col2 = st.columns([3, 1])
    
    with col1:
        raw_decision = st.text_area(
            "What life decision are you contemplating?",
            placeholder="Example: What if I moved to Paris instead of staying in my hometown?",
            height=80,
            key="decision_input",
            help="Enter a major life decision you're thinking about or curious to explore",
            max_chars=500
        )
        # Sanitize input in real-time
        decision = input_validator.sanitize_decision(raw_decision) if raw_decision else ""
    
    with col2:
        mode = st.selectbox(
            "Simulation Mode",
            ["realistic", "50/50", "random"],
            format_func=lambda x: {
                "realistic": "🎯 Realistic",
                "50/50": "⚖️ Balanced",
                "random": "🎲 Wild Card"
            }[x],
            help="Realistic: Based on real probabilities | 50/50: Equal chances | Random: Anything goes!"
        )
    
    # Premium features notice
    if not st.session_state.is_premium:
        st.markdown("""
        <div class="premium-banner">
            🌟 <strong>Upgrade to Premium</strong> for 4 branches, detailed reports, and no ads! 
            <br>Only $2.99 per simulation
        </div>
        """, unsafe_allow_html=True)
    
    # Generate button with game style
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        if st.button("🎮 START SIMULATION 🌌", type="primary", use_container_width=True):
            if not decision.strip():
                st.error("🚨 Whoa there! You need to enter a decision first!")
            elif not st.session_state.api_key:
                st.error("🔒 Oops! You need to enter your API key in Game Settings first!")
            else:
                # Store pending simulation and show confirmation
                st.session_state.pending_simulation = {"decision": decision, "mode": mode}
                st.session_state.show_confirmation = True
                st.rerun()
    
    # Confirmation Dialog
    if st.session_state.show_confirmation and st.session_state.pending_simulation:
        show_confirmation_dialog()
    
    # Display results
    if st.session_state.simulation_result:
        display_simulation_results()
    
    # Footer with ads for free users
    if not st.session_state.is_premium:
        display_ads()

async def confirmation_callback(title: str, message: str) -> bool:
    """Callback for manual API confirmation"""
    # This is handled through Streamlit's UI, not async
    return True  # Will be controlled by UI

async def generate_simulation(decision: str, mode: str):
    """Generate the simulation and store in session state"""
    # Initialize engine with API key and confirmation callback
    if not st.session_state.simulation_engine:
        st.session_state.simulation_engine = SimulationEngine(
            api_key=st.session_state.api_key,
            api_type=st.session_state.api_type,
            confirm_callback=confirmation_callback
        )
    
    engine = st.session_state.simulation_engine
    
    # Determine number of branches based on premium status
    num_branches = 4 if st.session_state.is_premium else 3
    
    try:
        # Generate branches
        branches = await engine.generate_branches(decision, mode, num_branches)
        
        # Create simulation result
        sim_id = engine.generate_simulation_id(decision, mode)
        result = SimulationResult(
            simulation_id=sim_id,
            user_decision=decision,
            mode=mode,
            branches=branches,
            created_at=datetime.utcnow(),
            share_url=f"?sim={sim_id}"
        )
        
        # Save to database
        await engine.save_simulation(result)
        
        # Store in session
        st.session_state.simulation_result = result
        
    except Exception as e:
        st.error(f"Error generating simulation: {str(e)}")
        # Fallback to basic simulation
        st.warning("Using simplified simulation mode...")

def display_simulation_results():
    """Display the simulation results with visualizations"""
    result = st.session_state.simulation_result
    
    # Title
    st.markdown(f"## 🎭 Your Quantum Lives: *\"{result.user_decision}\"*")
    
    # River of Destiny Visualization
    st.markdown("### 🌊 Your River of Destiny")
    
    # Generate SVG visualization
    river = RiverOfDestiny(width=800, height=600)
    branches_data = [branch.dict() for branch in result.branches]
    svg_content = river.generate_river_svg(branches_data, result.user_decision)
    
    # Adapt for mobile if needed
    if st.session_state.get('is_mobile', False):
        svg_content = MobileRiverAdapter.adapt_for_mobile(svg_content, 400)
    
    # Display SVG with interactivity hint
    st.markdown("*Hover over the branches to explore your alternate timelines*")
    st.markdown(f'<div style="text-align: center">{svg_content}</div>', unsafe_allow_html=True)
    
    # Detailed branch information
    st.markdown("### 📖 Your Alternate Timeline Stories")
    
    tabs = st.tabs([f"Path {i+1}: {branch.title}" for i, branch in enumerate(result.branches)])
    
    for i, (tab, branch) in enumerate(zip(tabs, result.branches)):
        with tab:
            # Game-style fate score badge
            if branch.fate_score > 70:
                fate_emoji = "🏆"
                fate_text = "LEGENDARY"
                fate_gradient = "linear-gradient(135deg, #FFD700, #FFA500)"
            elif branch.fate_score > 40:
                fate_emoji = "⭐"
                fate_text = "EPIC"
                fate_gradient = "linear-gradient(135deg, #9C27B0, #E91E63)"
            else:
                fate_emoji = "🔥"
                fate_text = "CHALLENGING"
                fate_gradient = "linear-gradient(135deg, #F44336, #FF5722)"
            
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 1rem;">
                <div style="display: inline-block; background: {fate_gradient}; color: white; 
                           padding: 0.8rem 2rem; border-radius: 50px; font-size: 1.2rem;
                           font-family: 'Fredoka', cursive; font-weight: 700;
                           box-shadow: 0 5px 20px rgba(0,0,0,0.2);
                           animation: pulse 2s infinite;">
                    {fate_emoji} {fate_text} FATE: {branch.fate_score}/100 {fate_emoji}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Story
            st.markdown(f'<div class="branch-story">{branch.story}</div>', unsafe_allow_html=True)
            
            # Timeline with game style
            st.markdown("""
            <h4 style="font-family: 'Fredoka', cursive; color: #667eea; text-align: center;">
                📅 Your Quest Timeline 📅
            </h4>
            """, unsafe_allow_html=True)
            for event in branch.timeline:
                st.markdown(f"""
                <div class="timeline-item">
                    <strong>{event['year']}:</strong> {event['event']}
                </div>
                """, unsafe_allow_html=True)
            
            # Key events with game style
            st.markdown("""
            <h4 style="font-family: 'Fredoka', cursive; color: #FF6B6B; text-align: center; margin-top: 2rem;">
                🔑 Power-Up Moments 🔑
            </h4>
            """, unsafe_allow_html=True)
            for event in branch.key_events:
                st.markdown(f"• {event}")
            
            # Game-style probability meter
            prob_percent = int(branch.probability_score * 100)
            st.markdown("""
            <div style="margin-top: 2rem; text-align: center;">
                <p style="font-family: 'Fredoka', cursive; font-size: 1.1rem; color: #764ba2; margin-bottom: 0.5rem;">
                    🎲 Reality Chance Meter 🎲
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.progress(branch.probability_score)
            st.markdown(f"""
            <p style="text-align: center; font-family: 'Poppins', sans-serif; color: #667eea; font-weight: 600;">
                {prob_percent}% Probability Level
            </p>
            """, unsafe_allow_html=True)
    
    # Sharing section with game style
    st.markdown("""
    <h3 style="text-align: center; font-family: 'Fredoka', cursive; color: #FFD700; margin-top: 3rem;">
        🎆 Share Your Epic Adventure! 🎆
    </h3>
    """, unsafe_allow_html=True)
    
    share_url = f"https://quantumlife.app{result.share_url}"
    share_text = f"I just explored my quantum lives! What if I {result.user_decision}? 🌊 See my alternate timelines:"
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <a href="https://twitter.com/intent/tweet?text={share_text}&url={share_url}" 
           target="_blank" class="share-button" style="background: #1DA1F2">
           🐦 Twitter
        </a>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <a href="https://www.facebook.com/sharer/sharer.php?u={share_url}" 
           target="_blank" class="share-button" style="background: #4267B2">
           📘 Facebook
        </a>
        """, unsafe_allow_html=True)
    
    with col3:
        # TikTok share (simplified)
        st.markdown(f"""
        <a href="#" onclick="alert('Screenshot and share on TikTok with #QuantumLifeChallenge!')" 
           class="share-button" style="background: #000">
           🎵 TikTok
        </a>
        """, unsafe_allow_html=True)
    
    with col4:
        if st.button("📋 Copy Link"):
            st.write(f"Share link: {share_url}")
            st.success("Link copied! (Copy manually)")
    
    # Premium section with game style
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.is_premium:
            if st.button("📥 DOWNLOAD QUEST LOG (PDF) 📥", use_container_width=True):
                st.info("🎮 PDF Quest Log generation coming soon! 🎮")
        else:
            if st.button("👑 UNLOCK PREMIUM POWERS - $2.99 👑", use_container_width=True):
                process_premium_upgrade()

def load_shared_simulation(sim_id: str):
    """Load a shared simulation"""
    engine = st.session_state.simulation_engine
    
    with st.spinner("Loading shared simulation..."):
        result = asyncio.run(engine.load_simulation(sim_id))
        
    if result:
        st.session_state.simulation_result = result
        display_simulation_results()
    else:
        st.error("Simulation not found! It may have expired or the link is incorrect.")
        if st.button("Create New Simulation"):
            st.query_params.clear()
            st.rerun()

def process_premium_upgrade():
    """Handle premium upgrade via Stripe"""
    if not stripe.api_key:
        st.error("Payment processing not configured. Contact support.")
        return
    
    try:
        # Create Stripe checkout session
        # (Simplified for demo - would need full implementation)
        st.info("Redirecting to secure payment...")
        # checkout_session = stripe.checkout.Session.create(...)
        st.session_state.is_premium = True  # Demo mode
        st.success("Welcome to Premium! Enjoy all features.")
        st.rerun()
    except Exception as e:
        st.error(f"Payment error: {str(e)}")

def display_ads():
    """Display contextual ads for free users"""
    st.markdown("---")
    st.markdown("### 💼 Sponsored")
    
    # Simple text ads based on decision theme
    decision = st.session_state.simulation_result.user_decision if st.session_state.simulation_result else ""
    
    ads = {
        "career": "🎯 **CareerCoach Pro** - Make confident career decisions with expert guidance",
        "relationship": "💕 **LoveLife Counseling** - Navigate relationships with professional support",
        "education": "🎓 **EduPath Advisor** - Find your perfect educational journey",
        "default": "🌟 **LifeCoach AI** - Transform your decisions into success stories"
    }
    
    ad_type = "default"
    if any(word in decision.lower() for word in ["job", "career", "work"]):
        ad_type = "career"
    elif any(word in decision.lower() for word in ["marry", "relationship", "love"]):
        ad_type = "relationship"
    elif any(word in decision.lower() for word in ["study", "college", "degree"]):
        ad_type = "education"
    
    st.info(ads[ad_type])

def show_confirmation_dialog():
    """Show game-style confirmation dialog for API calls"""
    decision = st.session_state.pending_simulation["decision"]
    mode = st.session_state.pending_simulation["mode"]
    
    st.markdown("""
    <div class="confirmation-dialog">
        <h3>🎮 Ready to Launch Simulation? 🎮</h3>
    </div>
    """, unsafe_allow_html=True)
    
    status = rate_limiter.get_status()
    
    st.info(f"""
    🎆 **Your Quest:** {decision}
    🎮 **Game Mode:** {mode}
    🤖 **AI Engine:** {st.session_state.api_type.upper()}
    ⚡ **Power Level:** {status['available_tokens']}/{status['max_tokens']} charges
    
    🚀 Ready to explore the multiverse? Let's GO!
    """)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🚀 LAUNCH! 🚀", type="primary"):
            st.session_state.show_confirmation = False
            with st.spinner("🌀 Calculating quantum probabilities..."):
                asyncio.run(generate_simulation(decision, mode))
    
    with col2:
        if st.button("🚫 Not Yet"):
            st.session_state.show_confirmation = False
            st.session_state.pending_simulation = None
            st.rerun()
    
    with col3:
        if st.button("🧿 Reset Memory"):
            response_cache.clear()
            st.success("🎆 Memory crystals cleared! Fresh start! 🎆")
            st.rerun()

if __name__ == "__main__":
    main()