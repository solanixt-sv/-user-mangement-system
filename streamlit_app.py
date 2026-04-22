import streamlit as st
import requests
import subprocess
import time
import socket
import os
import threading
import uvicorn
from datetime import datetime

# --- Configuration ---
API_BASE_URL = "http://localhost:8000"

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# --- Background Backend Runner ---
def run_backend():
    if not is_port_in_use(8000):
        from main import app as fastapi_app
        uvicorn.run(fastapi_app, host="0.0.0.0", port=8000, log_level="error")

if "backend_started" not in st.session_state:
    thread = threading.Thread(target=run_backend, daemon=True)
    thread.start()
    st.session_state.backend_started = True
    time.sleep(2)

# --- UI Setup ---
st.set_page_config(
    page_title="UserScope SaaS | Intelligence Control",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed", # Professional SaaS usually hides sidebar initially
)

# Professional SaaS Dark Theme CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --primary: #6366f1;
    --primary-hover: #4f46e5;
    --bg: #0b0e14;
    --card-bg: #151921;
    --card-hover: #1c222d;
    --border: #262c36;
    --text: #f1f5f9;
    --text-muted: #94a3b8;
}

/* Zero Margin & Global Styles */
.main { background-color: var(--bg); color: var(--text); }
* { font-family: 'Plus Jakarta Sans', sans-serif; }

/* Custom Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }

/* Remove default headers */
header { visibility: hidden !important; }
footer { visibility: hidden !important; }
[data-testid="stSidebar"] { display: none !important; }

/* Custom Top Navigation Bar */
.top-nav {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 64px;
    background: rgba(11, 14, 20, 0.8);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 40px;
    z-index: 999;
}
.logo { font-weight: 800; font-size: 20px; color: var(--primary); display:flex; align-items:center; gap:10px; }
.nav-status { display: flex; align-items: center; gap: 8px; font-size: 11px; font-weight: 600; color: #10b981; border: 1px solid rgba(16,185,129,0.2); padding: 4px 12px; border-radius: 99px; background: rgba(16,185,129,0.05); }
.pulse-dot { width: 6px; height: 6px; background: #10b981; border-radius: 50%; animation: pulse 2s infinite; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }

/* Main Content Area */
.content-wrapper { padding-top: 80px; max-width: 1400px; margin: 0 auto; }

/* SaaS Card Grid */
.saas-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    transition: all 0.3s ease;
    margin-bottom: 20px;
}
.saas-card:hover { border-color: var(--primary); transform: translateY(-3px); box-shadow: 0 10px 40px -10px rgba(0,0,0,0.5); }

/* Buttons & Interactive Elements */
.stButton > button {
    background: var(--primary) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 8px 24px !important;
    font-weight: 600 !important;
    height: 44px !important;
}
.stButton > button:hover { background: var(--primary-hover) !important; transform: scale(1.02); }

.secondary-btn > .stButton > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text-muted) !important;
}
.secondary-btn > .stButton > button:hover { border-color: #ef4444 !important; color: #ef4444 !important; }

/* Metrics */
.metric-box { text-align: center; border-right: 1px solid var(--border); }
.metric-box:last-child { border-right: none; }
.m-val { font-size: 32px; font-weight: 800; color: var(--text); }
.m-label { font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; }

/* Modern Expander */
.stExpander { background: var(--card-bg) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; border:none !important; }
.stExpander summary { background: var(--card-bg) !important; padding: 12px !important; border-radius: 12px !important; }

/* Intelligence Block */
.intel-log { background: #0b0e14; border: 1px solid var(--border); border-radius: 8px; padding: 12px; font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #a5b4fc; }

</style>
""", unsafe_allow_html=True)

# --- Logic ---
def api_request(method, endpoint, data=None):
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET": r = requests.get(url, timeout=5)
        elif method == "POST": r = requests.post(url, json=data, timeout=5)
        elif method == "DELETE": r = requests.delete(url, timeout=5)
        if r.status_code in [200, 201]: return r.json()
    except: pass
    return None

if 'selected_user' not in st.session_state:
    st.session_state.selected_user = None

# --- TOP NAVIGATION ---
is_online = is_port_in_use(8000)
st.markdown(f"""
<div class="top-nav">
    <div class="logo">⚡ UserScope <span style='font-weight:400; color:var(--text-muted); font-size:14px; opacity:0.5'>/ SaaS Intelligence</span></div>
    <div class="nav-status">
        <div class="pulse-dot"></div> {'Instance: Running' if is_online else 'Instance: Offline'}
    </div>
</div>
""", unsafe_allow_html=True)

# --- CONTENT WRAPPER ---
st.markdown("<div class='content-wrapper'>", unsafe_allow_html=True)

# Hero Section
st.markdown("<div style='margin-bottom: 40px'>", unsafe_allow_html=True)
c1, c2 = st.columns([2, 1])
with c1:
    st.markdown("<h1 style='margin:0'>Identity Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:var(--text-muted); font-size:16px'>Manage real-time user metrics and execute narrative intelligence algorithms.</p>", unsafe_allow_html=True)
with c2:
    with st.popover("➕ Add New Identity", use_container_width=True):
        st.markdown("### Register Account")
        n = st.text_input("Display Name", placeholder="e.g. John Doe")
        e = st.text_input("Account Email", placeholder="john@example.com")
        if st.button("Authorize & Sync", use_container_width=True):
            if n and e:
                if api_request("POST", "/users", {"name": n, "email": e}):
                    st.toast("Sync Success")
                    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

col_dir, col_intel = st.columns([1, 2], gap="large")

# 👥 Identity Directory
with col_dir:
    st.markdown("<h4 style='color:var(--text-muted); margin-bottom: 20px'>ACTIVE DIRECTORY</h4>", unsafe_allow_html=True)
    users = api_request("GET", "/users")
    if users:
        for u in users:
            is_sel = st.session_state.selected_user and st.session_state.selected_user['id'] == u['id']
            card_border = f"border-color: {st.get_option('theme.primaryColor') if is_sel else 'var(--primary)'}" if is_sel else ""
            st.markdown(f"""
            <div class="saas-card" style='padding: 18px; {card_border}'>
                <div style='display:flex; align-items:center; gap:15px'>
                    <div style='width:36px; height:36px; border-radius:50%; background:var(--primary); display:flex; align-items:center; justify-content:center; font-weight:800; font-size:14px'>{u['name'][0].upper()}</div>
                    <div style='flex:1'>
                        <div style='font-weight:700; font-size:15px'>{u['name']}</div>
                        <div style='color:var(--text-muted); font-size:12px'>{u['email']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns([3, 1])
            with c1:
                if st.button("Manage Intelligence", key=f"v_{u['id']}", use_container_width=True):
                    st.session_state.selected_user = u
                    st.rerun()
            with c2:
                st.markdown("<div class='secondary-btn'>", unsafe_allow_html=True)
                if st.button("×", key=f"d_{u['id']}", use_container_width=True):
                    api_request("DELETE", f"/users/{u['id']}")
                    if is_sel: st.session_state.selected_user = None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='saas-card' style='text-align:center; opacity:0.5'>Directory is empty</div>", unsafe_allow_html=True)

# 🔬 Intelligence Board
with col_intel:
    sel = st.session_state.selected_user
    if sel:
        st.markdown(f"<h4 style='color:var(--text-muted); margin-bottom: 20px'>OPERATIONAL HUB: {sel['name'].upper()}</h4>", unsafe_allow_html=True)
        
        # Performance Hub Card
        st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
        analyses = api_request("GET", f"/users/{sel['id']}/analyses")
        m1, m2, m3 = st.columns(3)
        with m1: st.markdown(f"<div class='metric-box'><div class='m-val'>{len(analyses) if analyses else 0}</div><div class='m-label'>Analyses</div></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='metric-box'><div class='m-val'>ACTIVE</div><div class='m-label'>Status</div></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='metric-box'><div class='m-val'>{sel['id'][:6].upper()}</div><div class='m-label'>Auth HASH</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Algorithm Input
        st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0'>Data Ingestion</h4>", unsafe_allow_html=True)
        t_input = st.text_area("", placeholder="Paste raw narrative text here for quantitative intelligence analysis...", height=120, label_visibility="collapsed")
        if st.button("Execute Algorithm", use_container_width=True):
            if t_input.strip():
                if api_request("POST", f"/users/{sel['id']}/analyze", {"text": t_input}):
                    st.toast("Intelligence Generated")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Operational History
        if analyses:
            st.markdown("<h4 style='margin: 40px 0 20px'>LOG HISTORY</h4>", unsafe_allow_html=True)
            for a in reversed(analyses):
                with st.expander(f"Operation ID: {a['analysis_id'][:8].upper()} — {a['analyzed_at'][:16].replace('T', ' ')}"):
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("W-Count", a['word_count'])
                    mc2.metric("U-Count", a['uppercase_count'])
                    mc3.metric("S-Count", a['special_character_count'])
                    st.markdown(f"<div class='intel-log'>{a['text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="saas-card" style="text-align:center; padding: 120px 20px;">
            <div style='font-size: 48px; margin-bottom: 20px'>📡</div>
            <h3 style='margin:0'>Awaiting Selection</h3>
            <p style='color:var(--text-muted)'>Please select an identity from the directory to initialize the intelligence pipeline.</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True) # Close content-wrapper
