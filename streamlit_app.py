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
    # Only start if not already running
    if not is_port_in_use(8000):
        from main import app as fastapi_app
        uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)

# Start backend in a separate thread
if "backend_started" not in st.session_state:
    thread = threading.Thread(target=run_backend, daemon=True)
    thread.start()
    st.session_state.backend_started = True
    time.sleep(2) # Allow time for uvicorn to bind to port

# --- UI Setup ---
st.set_page_config(
    page_title="UserScope Enterprise | Management & Analytics",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Professional Enterprise CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;700&display=swap');

:root {
    --primary: #4f46e5;
    --primary-glow: rgba(79, 70, 229, 0.15);
    --secondary: #6366f1;
    --bg: #fdfdff;
    --sidebar: #0f172a;
    --dark-text: #111827;
    --muted-text: #4b5563;
    --border: #e5e7eb;
}

/* Global resets */
.main {
    background-color: var(--bg);
    color: var(--dark-text);
}

* { font-family: 'Inter', sans-serif; }

h1, h2, h3 {
    font-family: 'Outfit', sans-serif;
    letter-spacing: -0.02em;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: var(--sidebar) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: #f8fafc !important; }

/* Dashboard Cards */
.card {
    background: white;
    border-radius: 12px;
    border: 1px solid var(--border);
    padding: 1.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    margin-bottom: 1.25rem;
    transition: all 0.2s ease;
}
.card:hover {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    border-color: #d1d5db;
}

/* Status Indicators */
.status-pill {
    display: inline-flex;
    align-items: center;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 600;
    background: #ecfdf5;
    color: #059669;
}
.status-pill.offline {
    background: #fef2f2;
    color: #dc2626;
}
.pulse {
    width: 6px;
    height: 6px;
    background: currentColor;
    border-radius: 50%;
    margin-right: 8px;
    animation: blink 2s infinite;
}
@keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }

/* Professional Buttons */
.stButton > button {
    background-color: white !important;
    color: var(--dark-text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    font-weight: 600 !important;
    width: 100%;
}
.stButton > button:hover {
    border-color: var(--primary) !important;
    color: var(--primary) !important;
    background-color: var(--primary-glow) !important;
}

/* Header Banner */
.header-banner {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    padding: 2.5rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 20px 25px -5px rgba(79, 70, 229, 0.2);
}

/* Analysis Items */
.analysis-item {
    border-left: 3px solid var(--primary);
    background: #f9fafb;
    padding: 1rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: 0.75rem;
}

header { visibility: hidden; }
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
        return None
    except: return None

if 'selected_user' not in st.session_state:
    st.session_state.selected_user = None

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:white; margin-bottom:0'>💠 UserScope</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8; font-size:14px'>Enterprise Management</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.expander("➕   Register New Account", expanded=False):
        with st.form("reg_form", clear_on_submit=True):
            n = st.text_input("Full Name")
            e = st.text_input("Email")
            if st.form_submit_button("Add User to Database", use_container_width=True):
                if n and e:
                    if api_request("POST", "/users", {"name": n, "email": e}):
                        st.success("User Synchronized")
                        st.rerun()

    st.markdown("---")
    is_online = is_port_in_use(8000)
    status_cls = "" if is_online else "offline"
    st.markdown(f"""
    <div style='padding: 12px; background: rgba(255,255,255,0.05); border-radius: 8px'>
        <div class="status-pill {status_cls}">
            <div class="pulse"></div> {'System Operational' if is_online else 'Connection Lost'}
        </div>
        <p style='font-size: 11px; margin-top: 8px; color: #64748b'>v1.2.0 Stable Build</p>
    </div>
    """, unsafe_allow_html=True)

# --- MAIN PAGE ---
st.markdown("""
<div class="header-banner">
    <h1 style='color:white; margin:0'>Management Console</h1>
    <p style='color: rgba(255,255,255,0.8); margin-top: 8px'>Enterprise-grade user tracking and real-time intelligence analysis.</p>
</div>
""", unsafe_allow_html=True)

l, r = st.columns([1, 2], gap="large")

with l:
    st.markdown("### 📋 Active Directory")
    users = api_request("GET", "/users")
    if users:
        for u in users:
            is_sel = st.session_state.selected_user and st.session_state.selected_user['id'] == u['id']
            card_style = "border-left: 4px solid #4f46e5; background: #f5f3ff;" if is_sel else ""
            st.markdown(f"""
            <div class="card" style="{card_style}">
                <div style='display:flex; justify-content:space-between; align-items:start'>
                    <div>
                        <h4 style='margin:0'>{u['name']}</h4>
                        <p style='color:#6b7280; font-size:13px; margin:0'>{u['email']}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns([2, 1])
            with c1:
                if st.button("Access Dashboard", key=f"v_{u['id']}"):
                    st.session_state.selected_user = u
                    st.rerun()
            with c2:
                if st.button("Delete", key=f"d_{u['id']}"):
                    api_request("DELETE", f"/users/{u['id']}")
                    if is_sel: st.session_state.selected_user = None
                    st.rerun()
    else:
        st.info("Directory is empty. Register a user in the sidebar.")

with r:
    sel = st.session_state.selected_user
    if sel:
        st.markdown(f"### 📊 Profile: {sel['name']}")
        
        # Performance Metrics
        analyses = api_request("GET", f"/users/{sel['id']}/analyses")
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"""
            <div class="card" style="text-align:center">
                <p style='font-size:12px; color:#6b7280; text-transform:uppercase'>Analytic Operations</p>
                <h2 style='margin:0'>{len(analyses) if analyses else 0}</h2>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="card" style="text-align:center">
                <p style='font-size:12px; color:#6b7280; text-transform:uppercase'>Profile Reference</p>
                <h2 style='margin:0; font-family:monospace'>{sel['id'][:6].upper()}</h2>
            </div>
            """, unsafe_allow_html=True)

        # Intelligence Input
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        t_input = st.text_area("Intelligence Data Ingestion", placeholder="Enter narrative text for structured analysis...", height=120)
        if st.button("Execute Quantitative Analysis", use_container_width=True):
            if t_input.strip():
                if api_request("POST", f"/users/{sel['id']}/analyze", {"text": t_input}):
                    st.toast("Analysis Successful")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # History
        if analyses:
            st.markdown("#### Operational Logs")
            for a in reversed(analyses):
                with st.expander(f"Log: {a['analyzed_at'][:19].replace('T', ' ')}", expanded=False):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Words", a['word_count'])
                    c2.metric("Capitals", a['uppercase_count'])
                    c3.metric("Symbols", a['special_character_count'])
                    st.markdown(f"<div class='analysis-item'>{a['text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='text-align:center; padding: 5rem 0; color: #9ca3af'>
            <icon style='font-size: 3rem'>📁</icon>
            <h3>Awaiting Selection</h3>
            <p>Select a profile from the directory to view analytics.</p>
        </div>
        """, unsafe_allow_html=True)
