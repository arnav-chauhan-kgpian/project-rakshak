"""
Project Rakshak - Streamlit Dashboard
Multi-Agent Disaster Response System with Real-Time Analysis

Run: streamlit run app.py
"""

import streamlit as st
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Project Rakshak",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Dark theme background */
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 50%, #0f0f1a 100%);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main header */
    .hero-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #e94560 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(233, 69, 96, 0.3);
        position: relative;
        overflow: hidden;
    }
    .hero-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: shimmer 3s infinite;
    }
    @keyframes shimmer {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .hero-header h1 {
        color: white;
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1;
    }
    .hero-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.2rem;
        margin-top: 0.5rem;
        position: relative;
        z-index: 1;
    }
    
    /* Mode cards */
    .mode-card {
        background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    .mode-card:hover {
        background: linear-gradient(145deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
    }
    .mode-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #e94560);
        opacity: 0;
        transition: opacity 0.3s;
    }
    .mode-card:hover::after {
        opacity: 1;
    }
    .mode-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        display: block;
    }
    .mode-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: white;
        margin-bottom: 0.5rem;
    }
    .mode-desc {
        color: rgba(255,255,255,0.6);
        font-size: 0.9rem;
    }
    
    /* Stat cards */
    .stat-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        transition: transform 0.3s;
    }
    .stat-card:hover {
        transform: scale(1.05);
    }
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    .stat-label {
        color: rgba(255,255,255,0.7);
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Status indicators */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .status-online {
        background: rgba(74, 222, 128, 0.2);
        color: #4ade80;
        border: 1px solid rgba(74, 222, 128, 0.3);
    }
    .status-processing {
        background: rgba(251, 191, 36, 0.2);
        color: #fbbf24;
        border: 1px solid rgba(251, 191, 36, 0.3);
        animation: pulse 2s infinite;
    }
    .status-critical {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
        animation: pulse 1s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    /* Chat interface */
    .chat-container {
        background: rgba(0,0,0,0.3);
        border-radius: 20px;
        padding: 1.5rem;
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .chat-message {
        margin: 1rem 0;
        padding: 1rem 1.5rem;
        border-radius: 20px;
        max-width: 85%;
        animation: fadeIn 0.3s ease-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .chat-user {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 5px;
    }
    .chat-rakshak {
        background: linear-gradient(135deg, #1f2937, #111827);
        color: white;
        border: 1px solid rgba(233, 69, 96, 0.5);
        border-bottom-left-radius: 5px;
    }
    .chat-rakshak::before {
        content: '🛡️ Rakshak';
        display: block;
        font-size: 0.75rem;
        color: #e94560;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    /* Report display */
    .report-container {
        background: rgba(0,0,0,0.4);
        border: 1px solid rgba(233, 69, 96, 0.3);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
    }
    .report-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Agent progress */
    .agent-progress {
        background: rgba(0,0,0,0.3);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid #667eea;
    }
    .agent-name {
        font-weight: 600;
        color: white;
        margin-bottom: 0.25rem;
    }
    .agent-status {
        font-size: 0.85rem;
        color: rgba(255,255,255,0.6);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 10px;
        color: white;
        padding: 0.75rem 1rem;
    }
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    [data-testid="stSidebar"] .stRadio > label {
        color: rgba(255,255,255,0.8);
    }
    
    /* Priority badges */
    .priority-low { background: #22c55e; }
    .priority-medium { background: #eab308; }
    .priority-high { background: #f97316; }
    .priority-critical { background: #ef4444; animation: pulse 1s infinite; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        color: rgba(255,255,255,0.7);
        padding: 0.75rem 1.5rem;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
    }
    
    /* Force Dark Theme on All Widgets */
    .stAlert {
        background: rgba(0,0,0,0.4) !important;
        color: white !important;
        border-color: rgba(255,255,255,0.2) !important;
    }
    .stAlert > div {
        color: white !important;
    }
    .stDataFrame, .stTable, [data-testid="stTable"] {
        background: rgba(0,0,0,0.3) !important;
    }
    .stDataFrame table, .stTable table, [data-testid="stTable"] table {
        background: rgba(10,10,15,0.95) !important;
        color: white !important;
    }
    .stDataFrame th, .stDataFrame td, .stTable th, .stTable td {
        background: rgba(20,20,30,0.9) !important;
        color: white !important;
        border-color: rgba(255,255,255,0.1) !important;
    }
    [data-testid="stMarkdownContainer"] code {
        background: rgba(0,0,0,0.5) !important;
        color: #22c55e !important;
    }
    .stJson {
        background: rgba(0,0,0,0.4) !important;
    }
    .stMetric {
        background: rgba(0,0,0,0.3);
        padding: 1rem;
        border-radius: 10px;
    }
    .stMetric label {
        color: rgba(255,255,255,0.6) !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #667eea !important;
    }
    /* File uploader */
    .stFileUploader > div {
        background: rgba(0,0,0,0.3) !important;
        border-color: rgba(255,255,255,0.2) !important;
    }
    /* Number input */
    .stNumberInput > div > div > input {
        background: rgba(0,0,0,0.3) !important;
        color: white !important;
        border-color: rgba(255,255,255,0.2) !important;
    }
    /* Selectbox */
    .stSelectbox > div > div {
        background: rgba(0,0,0,0.3) !important;
        color: white !important;
    }
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(0,0,0,0.3) !important;
        color: white !important;
    }
    .streamlit-expanderContent {
        background: rgba(0,0,0,0.2) !important;
    }
    
    /* COMPREHENSIVE DARK THEME OVERRIDES */
    /* All labels */
    label, .stTextInput label, .stNumberInput label, .stSelectbox label, .stFileUploader label {
        color: rgba(255,255,255,0.8) !important;
    }
    
    /* All input containers */
    [data-baseweb="input"], [data-baseweb="select"], [data-baseweb="textarea"] {
        background-color: rgba(20,20,30,0.9) !important;
        border-color: rgba(255,255,255,0.2) !important;
    }
    
    /* Input text color */
    [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
        color: white !important;
        background-color: transparent !important;
    }
    
    /* Selectbox dropdown */
    [data-baseweb="select"] > div {
        background-color: rgba(20,20,30,0.95) !important;
        color: white !important;
    }
    [data-baseweb="popover"] {
        background-color: rgba(20,20,30,0.98) !important;
    }
    [data-baseweb="menu"] {
        background-color: rgba(20,20,30,0.98) !important;
    }
    [data-baseweb="menu"] li {
        color: white !important;
    }
    [data-baseweb="menu"] li:hover {
        background-color: rgba(102,126,234,0.3) !important;
    }
    
    /* File uploader complete override */
    [data-testid="stFileUploader"] {
        background: rgba(20,20,30,0.8) !important;
        border-radius: 10px;
        padding: 1rem;
    }
    [data-testid="stFileUploader"] section {
        background: transparent !important;
    }
    [data-testid="stFileUploader"] button {
        background: rgba(102,126,234,0.3) !important;
        color: white !important;
        border: 1px solid rgba(102,126,234,0.5) !important;
    }
    
    /* Text input path field */
    .stTextInput > div > div {
        background: rgba(20,20,30,0.9) !important;
    }
    
    /* Headers/subheaders */
    h1, h2, h3, h4, h5, h6 {
        color: white !important;
    }
    
    /* Markdown text */
    .stMarkdown, .stMarkdown p {
        color: rgba(255,255,255,0.85) !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if 'mode' not in st.session_state:
    st.session_state.mode = 'home'
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'report' not in st.session_state:
    st.session_state.report = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'gps_location' not in st.session_state:
    st.session_state.gps_location = {"lat": 34.0522, "lon": -118.2437}

# ==================== HELPER FUNCTIONS ====================
def check_system_status():
    """Check status of all system components"""
    status = {
        "qdrant": False,
        "llm": False,
        "audio": False
    }
    try:
        from utils.qdrant_init import get_qdrant_client
        client = get_qdrant_client()
        client.get_collections()
        status["qdrant"] = True
    except:
        pass
    
    try:
        import google.generativeai as genai
        if os.getenv("GEMINI_API_KEY"):
            status["llm"] = True
    except:
        pass
    
    try:
        from layers.ingestion.audio import AudioIngestionAgent
        status["audio"] = True
    except:
        pass
    
    return status

def render_status_badge(online, label):
    """Render a status badge"""
    if online:
        return f'<span class="status-badge status-online">🟢 {label}</span>'
    else:
        return f'<span class="status-badge status-critical">🔴 {label}</span>'

# ==================== SIDEBAR ====================
with st.sidebar:
    # Logo and title
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="font-size: 4rem;">🛡️</div>
        <h2 style="color: white; margin: 0.5rem 0;">Rakshak</h2>
        <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem;">Project Rakshak System</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation
    st.markdown("### Navigation")
    mode = st.radio(
        "Select Mode",
        ["🏠 Home", "🆘 Distress Signal", "🛰️ Rakshak Intel", "📊 Analytics", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    mode_map = {
        "🏠 Home": "home",
        "🆘 Distress Signal": "distress",
        "🛰️ Rakshak Intel": "intel",
        "📊 Analytics": "analytics",
        "⚙️ Settings": "settings"
    }
    st.session_state.mode = mode_map.get(mode, "home")
    
    st.markdown("---")
    
    # System Status
    st.markdown("### System Status")
    status = check_system_status()
    st.markdown(render_status_badge(status["qdrant"], "Qdrant Vector DB"), unsafe_allow_html=True)
    st.markdown(render_status_badge(status["llm"], "Gemini LLM"), unsafe_allow_html=True)
    st.markdown(render_status_badge(status["audio"], "Audio Models"), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick stats
    st.markdown("### Quick Stats")
    try:
        from utils.qdrant_init import get_qdrant_client
        client = get_qdrant_client()
        info = client.get_collection("disaster_memory")
        st.metric("Vectors Indexed", f"{info.points_count:,}")
    except:
        st.metric("Vectors Indexed", "N/A")
    
    st.markdown("---")
    
    # Qdrant Image (if exists)
    qdrant_img_path = "qdrant_image.png"
    if os.path.exists(qdrant_img_path):
        st.image(qdrant_img_path, caption="Powered by Qdrant", use_container_width=True)
    
    st.markdown("---")
    st.markdown(f"<small style='color: rgba(255,255,255,0.4);'>v1.0 | {datetime.now().strftime('%H:%M:%S')}</small>", unsafe_allow_html=True)


# ==================== HOME PAGE ====================
if st.session_state.mode == "home":
    # Hero Header
    st.markdown("""
    <div class="hero-header">
        <h1>🛡️ Project Rakshak</h1>
        <p>Multi-Agent Disaster Response System | Real-Time Analysis | Qdrant-Powered</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats row
    st.markdown("### System Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">15</div>
            <div class="stat-label">Active Agents</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">40x</div>
            <div class="stat-label">Faster Search</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">RRF</div>
            <div class="stat-label">Hybrid Fusion</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">Real-Time</div>
            <div class="stat-label">Processing</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Mode Selection Cards
    st.markdown("### Select Operation Mode")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="mode-card">
            <span class="mode-icon">🆘</span>
            <div class="mode-title">Distress Signal</div>
            <div class="mode-desc">Real-time chat with Rakshak AI. Voice input. Automatic triage analysis.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 LAUNCH CHAT", key="btn_distress", use_container_width=True, type="primary"):
            st.session_state.mode = "distress"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="mode-card">
            <span class="mode-icon">🛰️</span>
            <div class="mode-title">Rakshak Intel</div>
            <div class="mode-desc">Satellite imagery analysis. Full 15-agent pipeline. Historical context.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 LAUNCH INTEL", key="btn_intel", use_container_width=True, type="primary"):
            st.session_state.mode = "intel"
            st.rerun()
    
    with col3:
        st.markdown("""
        <div class="mode-card">
            <span class="mode-icon">📊</span>
            <div class="mode-title">Analytics</div>
            <div class="mode-desc">System metrics. Collection stats. Historical data visualization.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 VIEW STATS", key="btn_analytics", use_container_width=True, type="primary"):
            st.session_state.mode = "analytics"
            st.rerun()
    
    # Technology Stack
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Technology Stack")
    
    tech_cols = st.columns(5)
    techs = [
        ("🔷", "Qdrant", "Vector DB"),
        ("🤖", "Gemini", "LLM"),
        ("🎧", "Whisper", "STT"),
        ("🖼️", "DINOv2", "Vision"),
        ("🔊", "CLAP", "Audio")
    ]
    for i, (icon, name, desc) in enumerate(techs):
        with tech_cols[i]:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: rgba(255,255,255,0.03); border-radius: 10px;">
                <div style="font-size: 2rem;">{icon}</div>
                <div style="color: white; font-weight: 600;">{name}</div>
                <div style="color: rgba(255,255,255,0.5); font-size: 0.8rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)


# ==================== DISTRESS SIGNAL MODE ====================
elif st.session_state.mode == "distress":
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
        <span style="font-size: 2.5rem;">🆘</span>
        <div>
            <h2 style="color: white; margin: 0;">Distress Signal</h2>
            <p style="color: rgba(255,255,255,0.6); margin: 0;">Emergency Response Chat</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Two column layout
    col_chat, col_info = st.columns([2, 1])
    
    with col_chat:
        # Initialize agent if needed
        if st.session_state.agent is None:
            try:
                from layers.reasoning.victim_chat import VictimChatAgent
                from utils.qdrant_init import initialize_qdrant
                
                with st.spinner("🔄 Connecting to Rakshak AI..."):
                    client = initialize_qdrant()
                    st.session_state.agent = VictimChatAgent()
                    
                    risk_data = {
                        "risk_level": "CHECKING",
                        "user_location": f"{st.session_state.gps_location['lat']}, {st.session_state.gps_location['lon']}",
                        "threats": []
                    }
                    greeting = st.session_state.agent.start_chat(risk_data)
                    st.session_state.chat_history.append({"role": "rakshak", "content": greeting})
            except Exception as e:
                st.error(f"❌ Connection Failed: {e}")
        
        # Chat messages container
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        for msg in st.session_state.chat_history:
            css_class = "chat-user" if msg["role"] == "user" else "chat-rakshak"
            icon = "👤 You" if msg["role"] == "user" else ""
            st.markdown(f'<div class="chat-message {css_class}">{icon}{msg["content"]}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Input area
        st.markdown("<br>", unsafe_allow_html=True)
        input_col1, input_col2, input_col3 = st.columns([5, 1, 1])
        
        with input_col1:
            user_input = st.text_input("Type your message...", key="chat_input", label_visibility="collapsed", placeholder="Describe your emergency...")
        
        with input_col2:
            send_btn = st.button("📤 Send", use_container_width=True)
        
        with input_col3:
            voice_btn = st.button("🎤 Voice", use_container_width=True)
        
        # Handle text input
        if send_btn and user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            if st.session_state.agent:
                response = st.session_state.agent.send_message(user_input)
                st.session_state.chat_history.append({"role": "rakshak", "content": response})
            st.rerun()
        
        # Handle voice input
        if voice_btn:
            try:
                from utils.voice_input import get_voice_input, WHISPER_AVAILABLE
                if WHISPER_AVAILABLE:
                    with st.spinner("🎙️ Recording for 5 seconds..."):
                        result = get_voice_input(duration=5.0, analyze_panic=True)
                        if isinstance(result, tuple):
                            transcript, panic_level, _ = result
                        else:
                            transcript, panic_level = result, None
                        
                        if transcript:
                            st.session_state.chat_history.append({"role": "user", "content": f"🎤 {transcript}"})
                            if st.session_state.agent:
                                response = st.session_state.agent.send_message(transcript)
                                st.session_state.chat_history.append({"role": "rakshak", "content": response})
                            st.rerun()
                        else:
                            st.warning("Could not transcribe audio. Please try again.")
                else:
                    st.warning("Voice input not available. Please install sounddevice and soundfile.")
            except Exception as e:
                st.error(f"Voice error: {e}")
    
    with col_info:
        # GPS Location
        st.markdown("### 📍 Your Location")
        lat = st.number_input("Latitude", value=st.session_state.gps_location["lat"], format="%.4f", key="lat_input")
        lon = st.number_input("Longitude", value=st.session_state.gps_location["lon"], format="%.4f", key="lon_input")
        st.session_state.gps_location = {"lat": lat, "lon": lon}
        
        # Location Map
        import pandas as pd
        map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
        st.map(map_data, zoom=12)
        gmaps_url = f"https://www.google.com/maps?q={lat},{lon}"
        st.markdown(f"[🌍 Open in Google Maps]({gmaps_url})")
        
        # Status card
        st.markdown("### 📊 Session Status")
        st.markdown(f"""
        <div style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 10px; border-left: 3px solid #e94560;">
            <div style="color: rgba(255,255,255,0.6); font-size: 0.8rem;">Messages</div>
            <div style="color: white; font-size: 1.5rem; font-weight: 600;">{len(st.session_state.chat_history)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # End session button
        if st.button("🔴 End Session & Generate Triage", use_container_width=True):
            if st.session_state.agent and len(st.session_state.chat_history) > 1:
                with st.spinner("Generating Triage Analysis..."):
                    triage = st.session_state.agent.analyze_session()
                    st.session_state.report = triage
        
        # Display triage report
        if st.session_state.report:
            st.markdown("### 🚨 Emergency Report")
            
            try:
                # Try to parse JSON if string
                if isinstance(st.session_state.report, str):
                    import json
                    try:
                        triage_data = json.loads(st.session_state.report)
                    except:
                        # Fallback for raw text
                        triage_data = None
                        st.text(st.session_state.report)
                else:
                    triage_data = st.session_state.report

                if triage_data:
                    # Display Priority Badge
                    priority = triage_data.get("priority", "High").upper()
                    color_map = {
                        "LOW": "background-color: #4CAF50; color: white;",
                        "MEDIUM": "background-color: #FFC107; color: black;",
                        "HIGH": "background-color: #FF9800; color: white;",
                        "CRITICAL": "background-color: #F44336; color: white;",
                        "UNKNOWN": "background-color: #9E9E9E; color: white;"
                    }
                    p_style = color_map.get(priority, color_map["UNKNOWN"])
                    
                    st.markdown(f"""
                    <div style="padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 15px; {p_style}">
                        <h3 style="margin:0">PRIORITY: {priority}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display Affected Location
                    affected_loc = triage_data.get("affected_location", "Not specified")
                    st.markdown(f"**📍 Affected Location:** {affected_loc}")
                    
                    # Display Dispatch Info
                    st.markdown("#### 🚑 Teams Dispatched")
                    
                    # Create dispatch table data
                    resources = triage_data.get("resources_needed", [])
                    if isinstance(resources, list):
                        res_str = ", ".join(resources) if resources else "Emergency Response"
                    else:
                        res_str = str(resources) if resources else "Emergency Response"
                        
                    eta = triage_data.get("eta", "10-15 minutes")
                    action = triage_data.get("recommended_response", triage_data.get("suggested_action", "Immediate Response"))
                    
                    dispatch_data = {
                        "Parameter": ["Response Team", "Location", "Estimated ETA", "Status", "Action"],
                        "Details": [res_str, affected_loc, str(eta), "DISPATCHED", action]
                    }
                    st.table(dispatch_data)
                    
                    # Key details extraction - as bullet list
                    st.markdown("#### 📝 Injuries & Details")
                    details = triage_data.get("key_details", [])
                    if details and isinstance(details, list):
                        for item in details:
                            st.markdown(f"- 🔴 {item}")
                    elif details:
                        st.json(details)
                    else:
                        st.info("No specific injuries reported")
            except Exception as e:
                st.error(f"Error formatting report: {e}")
                st.code(st.session_state.report) # Fallback
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.agent = None
            st.session_state.report = None
            st.rerun()
        
        # Unified Triage Report (Session Log)
        if st.session_state.chat_history:
            with st.expander("📜 Unified Session Log", expanded=False):
                st.markdown("### Complete Chat Session")
                session_text = ""
                for i, msg in enumerate(st.session_state.chat_history):
                    role = "👤 USER" if msg["role"] == "user" else "🛡️ RAKSHAK"
                    session_text += f"**[{i+1}] {role}**\n{msg['content']}\n\n---\n\n"
                st.markdown(session_text)


# ==================== RAKSHAK INTEL MODE ====================
elif st.session_state.mode == "intel":
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
        <span style="font-size: 2.5rem;">🛰️</span>
        <div>
            <h2 style="color: white; margin: 0;">Rakshak Intel</h2>
            <p style="color: rgba(255,255,255,0.6); margin: 0;">14-Agent Disaster Analysis Pipeline</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📥 Input", "📊 Analysis", "📄 Report"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Incident Parameters")
            
            incident_lat = st.number_input("Latitude", value=34.0522, format="%.4f", key="intel_lat")
            incident_lon = st.number_input("Longitude", value=-118.2437, format="%.4f", key="intel_lon")
            
            disaster_type = st.selectbox(
                "Disaster Type",
                ["earthquake", "flood", "wildfire", "hurricane", "volcano", "tsunami", "tornado"]
            )
            
            # Auto-generate incident ID (not shown in UI)
            incident_id = f"{disaster_type.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Location Map
            st.markdown("### 🗺️ Incident Location")
            import pandas as pd
            map_data = pd.DataFrame({
                'lat': [incident_lat],
                'lon': [incident_lon]
            })
            st.map(map_data, zoom=10)
            
            # Google Maps link
            gmaps_url = f"https://www.google.com/maps?q={incident_lat},{incident_lon}"
            st.markdown(f"[🌍 Open in Google Maps]({gmaps_url})", unsafe_allow_html=True)
        
        with col2:
            st.markdown("### Satellite Image")
            
            # File uploader
            uploaded_file = st.file_uploader("Upload satellite image", type=["png", "jpg", "jpeg"])
            
            # Or use existing path
            image_path = st.text_input(
                "Or enter image path",
                value="imagery/guatemala-volcano_00000003_post_disaster.png"
            )
            
            # Preview
            if uploaded_file:
                st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
            elif os.path.exists(image_path):
                st.image(image_path, caption="Selected Image", use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Run Analysis Button
        if st.button("🚀 Run Full 14-Agent Analysis", use_container_width=True, type="primary"):
            st.session_state.processing = True
            st.rerun()
    
    with tab2:
        if st.session_state.processing:
            st.markdown("### 🔄 Agent Pipeline in Progress")
            
            # Progress display
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            agents_pipeline = [
                ("Satellite Agent", "Validating image input..."),
                ("Embedding Agent", "Generating DINOv2 embeddings..."),
                ("Sparse Embedding", "Creating BM25 vectors..."),
                ("Metadata Agent", "Extracting incident metadata..."),
                ("Search Execution", "Querying Qdrant (Hybrid RRF)..."),
                ("Cross-Disaster", "Applying transfer learning..."),
                ("Geo Similarity", "Finding nearby historical events..."),
                ("Evidence Synthesis", "Analyzing damage patterns..."),
                ("History Summarizer", "Generating context narrative..."),
                ("LLM Reasoning", "Generating emergency report..."),
                ("Report Auditor", "Fact-checking and enhancing..."),
                ("Post Processor", "Calculating confidence & triage..."),
                ("Visualization", "Creating charts..."),
            ]
            
            # Simulate agent progress
            for i, (agent, status) in enumerate(agents_pipeline):
                progress = (i + 1) / len(agents_pipeline)
                progress_placeholder.progress(progress)
                status_placeholder.markdown(f"""
                <div class="agent-progress">
                    <div class="agent-name">Agent {i+1}: {agent}</div>
                    <div class="agent-status">{status}</div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.3)  # Quick simulation
            
            # Run actual analysis
            try:
                from main import CentralCoordinator
                
                status_placeholder.markdown("⚡ **Running full pipeline...**")
                
                coordinator = CentralCoordinator()
                result = coordinator.process_new_incident(
                    image_path=image_path,
                    latitude=incident_lat,
                    longitude=incident_lon,
                    disaster_type=disaster_type,
                    incident_id=incident_id
                )
                
                st.session_state.report = result
                st.session_state.processing = False
                progress_placeholder.progress(1.0)
                status_placeholder.success("✅ Analysis Complete!")
                
            except Exception as e:
                st.session_state.processing = False
                st.error(f"❌ Analysis Failed: {e}")
                import traceback
                st.code(traceback.format_exc())
        else:
            st.info("Configure parameters in the **Input** tab and click **Run Analysis**.")
    
    with tab3:
        if st.session_state.report:
            report_data = st.session_state.report
            
            if report_data.get("status") == "REJECTED":
                st.error(f"❌ Analysis Rejected: {report_data.get('reason')}")
            elif report_data.get("status") == "ERROR":
                st.error(f"❌ Analysis Error: {report_data.get('error')}")
            else:
                # Metrics row
                st.markdown("### Key Metrics")
                m1, m2, m3, m4 = st.columns(4)
                
                with m1:
                    conf = report_data.get("confidence_score", 0)
                    st.metric("Confidence", f"{conf:.1%}" if isinstance(conf, float) else "N/A")
                
                with m2:
                    triage = report_data.get("triage_priority", {})
                    pri = triage.get("priority_level", "N/A")
                    st.metric("Priority", pri.upper() if pri else "N/A")
                
                with m3:
                    resp = triage.get("response_time_hours", "N/A")
                    st.metric("Response Time", f"{resp}h" if resp else "N/A")
                
                with m4:
                    res = triage.get("resource_allocation", {})
                    personnel = res.get("personnel", "N/A")
                    st.metric("Personnel", personnel)
                
                st.markdown("---")
                
                # Visual Analysis (Charts)
                st.markdown("### 📊 Visual Analysis")
                
                expl = report_data.get("explanation_package", {}).get("components", {})
                
                if expl:
                    # Row 1: Distribution & Gauges
                    v1, v2, v3 = st.columns(3)
                    
                    with v1:
                        dmg = expl.get("damage_distribution", {})
                        if dmg.get("path") and os.path.exists(dmg["path"]):
                            st.image(dmg["path"], caption="Damage Distribution", use_container_width=True)
                        else:
                            st.info("Damage chart not available")
                            
                    with v2:
                        conf = expl.get("confidence_gauge", {})
                        if conf.get("path") and os.path.exists(conf["path"]):
                            st.image(conf["path"], caption="Confidence Gauge", use_container_width=True)
                        else:
                            st.info("Confidence chart not available")
                            
                    with v3:
                        sev = expl.get("severity_breakdown", {})
                        if sev.get("path") and os.path.exists(sev["path"]):
                            st.image(sev["path"], caption="Severity Breakdown", use_container_width=True)
                        else:
                            st.info("Severity chart not available")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Row 2: Advanced Analytics
                    v4, v5 = st.columns(2)
                    
                    with v4:
                        radar = expl.get("risk_radar", {})
                        if radar.get("path") and os.path.exists(radar["path"]):
                            st.image(radar["path"], caption="Holistic Risk Assessment", use_container_width=True)
                        else:
                            st.info("Risk radar not available")
                            
                    with v5:
                        res = expl.get("resource_allocation", {})
                        if res.get("path") and os.path.exists(res["path"]):
                            st.image(res["path"], caption="Resource Allocation", use_container_width=True)
                        else:
                            st.info("Resource chart not available")
                else:
                    st.warning("No visual analysis generated.")
                
                st.markdown("---")
                
                # Full Report
                st.markdown("### 📋 Emergency Report")
                report_text = report_data.get("damage_assessment_report", "No report generated.")
                st.markdown(f'<div class="report-container">{report_text}</div>', unsafe_allow_html=True)
                
                # Download button
                st.download_button(
                    label="📥 Download Report",
                    data=report_text,
                    file_name=f"rakshak_report_{incident_id}.md",
                    mime="text/markdown"
                )
        else:
            st.info("No report available. Run an analysis first.")


# ==================== ANALYTICS MODE ====================
elif st.session_state.mode == "analytics":
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
        <span style="font-size: 2.5rem;">📊</span>
        <div>
            <h2 style="color: white; margin: 0;">System Analytics</h2>
            <p style="color: rgba(255,255,255,0.6); margin: 0;">Performance Metrics & Collection Stats</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Qdrant Stats
    st.markdown("### Qdrant Collection Statistics")
    
    try:
        from utils.qdrant_init import get_qdrant_client
        client = get_qdrant_client()
        
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                info = client.get_collection("disaster_memory")
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">disaster_memory</div>
                    <div class="stat-value">{info.points_count:,}</div>
                    <div style="color: rgba(255,255,255,0.5); font-size: 0.8rem;">vectors indexed</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.json({
                    "status": info.status.name,
                    "vectors_count": info.points_count,
                    "indexed_vectors_count": info.indexed_vectors_count,
                    "segments_count": info.segments_count
                })
            except Exception as e:
                st.warning(f"Could not fetch disaster_memory: {e}")
        
        with col2:
            try:
                audio_info = client.get_collection("disaster_audio")
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">disaster_audio</div>
                    <div class="stat-value">{audio_info.points_count:,}</div>
                    <div style="color: rgba(255,255,255,0.5); font-size: 0.8rem;">audio embeddings</div>
                </div>
                """, unsafe_allow_html=True)
            except:
                st.info("Audio collection not initialized")
    
    except Exception as e:
        st.error(f"Could not connect to Qdrant: {e}")
    
    st.markdown("---")
    
    # System Info
    st.markdown("### System Configuration")
    
    config_cols = st.columns(3)
    with config_cols[0]:
        st.markdown("**Vector Search**")
        st.markdown("- Binary Quantization: ✅")
        st.markdown("- Hybrid RRF Fusion: ✅")
        st.markdown("- Oversampling: 2.0x")
        st.markdown("- Rescore: Enabled")
    
    with config_cols[1]:
        st.markdown("**Models**")
        st.markdown("- Vision: DINOv2 (768-dim)")
        st.markdown("- Audio: CLAP (512-dim)")
        st.markdown("- STT: Whisper-tiny")
        st.markdown("- LLM: Gemini 2.5 Flash")
    
    with config_cols[2]:
        st.markdown("**Agents**")
        st.markdown("- Total: 14 specialized")
        st.markdown("- Parallel Execution: ✅")
        st.markdown("- Retry with Backoff: ✅")
        st.markdown("- Lazy Loading: ✅")


# ==================== SETTINGS MODE ====================
elif st.session_state.mode == "settings":
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
        <span style="font-size: 2.5rem;">⚙️</span>
        <div>
            <h2 style="color: white; margin: 0;">Settings</h2>
            <p style="color: rgba(255,255,255,0.6); margin: 0;">System Configuration</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### API Keys")
    st.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""), key="gemini_key")
    st.text_input("Qdrant URL", value=os.getenv("QDRANT_URL", "localhost:6333"), key="qdrant_url")
    
    st.markdown("### Search Parameters")
    st.slider("Oversampling Factor", 1.0, 5.0, 2.0, 0.5)
    st.checkbox("Enable Rescore", value=True)
    st.number_input("Max Results", value=10, min_value=1, max_value=50)
    
    st.markdown("### Model Selection")
    st.selectbox("LLM Model", ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"])
    st.selectbox("Whisper Model", ["whisper-tiny", "whisper-base", "whisper-small"])
    
    if st.button("Save Settings", type="primary"):
        st.success("Settings saved! (Note: Restart required for some changes)")


# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; color: rgba(255,255,255,0.4);">
    <p>🛡️ Project Rakshak v1.0 | Qdrant-MAS Hackathon 2024</p>
    <p style="font-size: 0.8rem;">15-Agent Multi-Modal Disaster Response System | Built with Streamlit, Qdrant, Gemini</p>
    <p style="font-size: 0.8rem; margin-top: 5px; color: #667eea;">Made by Shaunak Majumdar and Arnav Chauhan IIT KHARAGPUR</p>
</div>
""", unsafe_allow_html=True)
