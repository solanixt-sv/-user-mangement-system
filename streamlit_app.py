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
    page_title="UserScope Dark | Intelligence Platform",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium Midnight Dark Theme CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;700&display=swap');

:root {
    --primary: #818cf8;
    --primary-glow: rgba(129, 140, 248, 0.2);
    --bg-dark: #0f172a;
    --card-dark: #1e293b;
    --border-dark: #334155;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
}

/* Base Styles */
.stApp {
    background-color: var(--bg-dark);
    color: var(--text-primary);
}

* { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4 { color: var(--text-primary); font-family: 'Outfit', sans-serif; }

/* Custom Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-dark); }
::-webkit-scrollbar-thumb { background: var(--border-dark); border-radius: 10px; }

/* Dashboard Cards */
.card {
    background: var(--card-dark);
    border: 1px solid var(--border-dark);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.card:hover {
    border-color: var(--primary);
    box-shadow: 0 0 20px var(--primary-glow);
    transform: translateY(-2px);
}

/* Header Banner */
.header-banner {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
    border: 1px solid var(--border-dark);
    padding: 2.5rem;
    border-radius: 20px;
    margin-bottom: 2rem;
    text-align: center;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #020617 !important;
    border-right: 1px solid var(--border-dark);
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }

/* Inputs & Forms */
.stTextInput input, .stTextArea textarea {
    background-color: #0f172a !important;
    color: white !important;
    border: 1px solid var(--border-dark) !important;
    border-radius: 10px !important;
}

/* Buttons */
.stButton > button {
    background-color: var(--primary) !important;
    color: #0f172a !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    filter: brightness(1.1);
    transform: scale(1.02);
    box-shadow: 0 0 15px var(--primary-glow);
}

/* Status Pill */
.status-pill {
    display: inline-flex;
    align-items: center;
    padding: 6px 14px;
    border-radius: 99px;
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
}
.dot { width: 6px; height: 6px; background: #10b981; border-radius: 50%; margin-right: 8px; animation: pulse 2s infinite; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }

/* Fix Sidebar Toggle visibility in dark mode */
header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stHeader"] svg { fill: var(--text-primary) !important; }

footer { visibility: hidden; }
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

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='letter-spacing:-1px'>🌌 UserScope</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b; font-size:13px'>Midnight Intelligence Edition</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.expander("✨ Add New Profile", expanded=True):
        with st.form("dark_form", clear_on_submit=True):
            n = st.text_input("Full Name")
            e = st.text_input("Email")
            if st.form_submit_button("Register Account", use_container_width=True):
                if n and e:
                    if api_request("POST", "/users", {"name": n, "email": e}):
                        st.success("Synchronized")
                        st.rerun()

    st.markdown("---")
    is_online = is_port_in_use(8000)
    if is_online:
        st.markdown('<div class="status-pill"><div class="dot"></div> Engine Live</div>', unsafe_allow_html=True)
    else:
        st.error("Engine Offline")

# --- MAIN DASHBOARD ---
st.markdown("""
<div class="header-banner">
    <h1 style='color:white; margin:0; font-size: 2.5rem'>Intelligence Control</h1>
    <p style='color: var(--text-secondary); margin-top: 10px'>Sophisticated user analytics and narrative ingestion.</p>
</div>
""", unsafe_allow_html=True)

l, r = st.columns([1, 2], gap="large")

with l:
    st.markdown("### 💠 Identities")
    users = api_request("GET", "/users")
    if users:
        for u in users:
            is_sel = st.session_state.selected_user and st.session_state.selected_user['id'] == u['id']
            card_border = "border: 1.5px solid var(--primary);" if is_sel else ""
            st.markdown(f"""
            <div class="card" style="{card_border} padding: 1rem">
                <h4 style='margin:0'>{u['name']}</h4>
                <p style='color:var(--text-secondary); font-size:12px; margin:0'>{u['email']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns([2, 1])
            with c1:
                if st.button("Initialize", key=f"v_{u['id']}", use_container_width=True):
                    st.session_state.selected_user = u
                    st.rerun()
            with c2:
                if st.button("Purge", key=f"d_{u['id']}", use_container_width=True):
                    api_request("DELETE", f"/users/{u['id']}")
                    if is_sel: st.session_state.selected_user = None
                    st.rerun()
    else:
        st.info("System memory is empty.")

with r:
    sel = st.session_state.selected_user
    if sel:
        st.markdown(f"### 🧪 Subject: {sel['name']}")
        
        analyses = api_request("GET", f"/users/{sel['id']}/analyses")
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"<div class='card' style='text-align:center'><p style='font-size:10px; color:var(--text-secondary)'>ANALYSES</p><h1 style='margin:0'>{len(analyses) if analyses else 0}</h1></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='card' style='text-align:center'><p style='font-size:10px; color:var(--text-secondary)'>HASH</p><h1 style='margin:0; font-family:monospace; font-size:1.5rem'>{sel['id'][:8].upper()}</h1></div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        t_input = st.text_area("Narrative Ingestion", placeholder="Enter raw data for processing...", height=150)
        if st.button("Process Intelligence", use_container_width=True):
            if t_input.strip():
                if api_request("POST", f"/users/{sel['id']}/analyze", {"text": t_input}):
                    st.toast("Data Processed ✨")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        if analyses:
            for a in reversed(analyses):
                with st.expander(f"Data Log | {a['analyzed_at'][:16].replace('T', ' ')}"):
                    sc1, sc2, sc3 = st.columns(3)
                    sc1.metric("Words", a['word_count'])
                    sc2.metric("Caps", a['uppercase_count'])
                    sc3.metric("Symbols", a['special_character_count'])
                    st.markdown(f"<div style='background:#111827; padding:15px; border-radius:10px; border:1px solid #334155; font-family:monospace; font-size:13px'>{a['text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:center; padding: 4rem; opacity: 0.4'><h2>◈ NO SELECTION</h2><p>Select a subject to retrieve intelligence logs.</p></div>", unsafe_allow_html=True)
