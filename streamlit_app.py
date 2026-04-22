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
    page_title="UserScope Enterprise | Clean Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Professional Enterprise Light Theme CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --primary: #4f46e5;
    --primary-hover: #4338ca;
    --bg: #f8fafc;
    --card-bg: #ffffff;
    --border: #e2e8f0;
    --text: #0f172a;
    --text-muted: #64748b;
    --accent-bg: #f1f5f9;
}

/* Global Styles */
.main { background-color: var(--bg); color: var(--text); }
* { font-family: 'Plus Jakarta Sans', sans-serif; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }

/* Hide default elements */
header { visibility: hidden !important; }
footer { visibility: hidden !important; }
[data-testid="stSidebar"] { display: none !important; }

/* Professional Top Nav */
.top-nav {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 64px;
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 40px;
    z-index: 999;
}
.logo { font-weight: 800; font-size: 20px; color: var(--primary); display:flex; align-items:center; gap:10px; }
.nav-status { display: flex; align-items: center; gap: 8px; font-size: 11px; font-weight: 700; color: #059669; border: 1px solid #bbf7d0; padding: 4px 12px; border-radius: 99px; background: #f0fdf4; }
.pulse-dot { width: 6px; height: 6px; background: #059669; border-radius: 50%; animation: pulse 2s infinite; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }

/* Content Layout */
.content-wrapper { padding-top: 80px; max-width: 1300px; margin: 0 auto; }

/* Enterprise White Cards */
.saas-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    transition: all 0.2s ease-in-out;
    margin-bottom: 20px;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
}
.saas-card:hover { border-color: var(--primary); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); transform: translateY(-2px); }

/* Inputs and Buttons */
.stTextInput input, .stTextArea textarea {
    background-color: #ffffff !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}

.stButton > button {
    background: var(--primary) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s !important;
}
.stButton > button:hover { background: var(--primary-hover) !important; transform: scale(1.02); box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3); }

/* Metric Styling */
.metric-box { text-align: center; border-right: 1px solid var(--border); }
.metric-box:last-child { border-right: none; }
.m-val { font-size: 36px; font-weight: 800; color: var(--text); }
.m-label { font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }

/* Historical Logs */
.intel-log { background: #f8fafc; border: 1px solid var(--border); border-radius: 10px; padding: 16px; font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #334155; line-height: 1.6; }

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

# --- TOP NAV ---
is_online = is_port_in_use(8000)
st.markdown(f"""
<div class="top-nav">
    <div class="logo">🏢 UserScope <span style='font-weight:400; color:var(--text-muted); font-size:14px'>/ Enterprise Console</span></div>
    <div class="nav-status">
        <div class="pulse-dot"></div> {'Network Live' if is_online else 'Network Down'}
    </div>
</div>
""", unsafe_allow_html=True)

# --- MAIN CONTENT ---
st.markdown("<div class='content-wrapper'>", unsafe_allow_html=True)

# Header Section
st.markdown("<div style='margin-bottom: 30px'>", unsafe_allow_html=True)
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("<h1 style='margin:0'>User Management System</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:var(--text-muted); font-size:16px'>Manage employee directory and perform real-time text intelligence analysis.</p>", unsafe_allow_html=True)
with c2:
    with st.popover("➕ Add New Profile", use_container_width=True):
        st.markdown("### Profile Creation")
        n = st.text_input("Full Name", placeholder="Employee Name")
        e = st.text_input("Email Index", placeholder="email@company.com")
        if st.button("Commit to Database", use_container_width=True):
            if n and e:
                if api_request("POST", "/users", {"name": n, "email": e}):
                    st.toast("Profile Created")
                    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

col_dir, col_dash = st.columns([1, 2], gap="large")

# 🏛️ Employee Directory
with col_dir:
    st.markdown("<h5 style='color:var(--text-muted); margin-bottom: 15px'>DIRECTORY LISTING</h5>", unsafe_allow_html=True)
    users = api_request("GET", "/users")
    if users:
        for u in users:
            is_sel = st.session_state.selected_user and st.session_state.selected_user['id'] == u['id']
            card_border = f"border: 2px solid var(--primary); background: #f5f3ff;" if is_sel else ""
            st.markdown(f"""
            <div class="saas-card" style='padding: 15px; {card_border}'>
                <div style='display:flex; align-items:center; gap:12px'>
                    <div style='min-width:40px; height:40px; border-radius:10px; background:var(--accent-bg); color:var(--primary); display:flex; align-items:center; justify-content:center; font-weight:800; border:1px solid var(--border)'>{u['name'][0].upper()}</div>
                    <div style='overflow:hidden'>
                        <div style='font-weight:700; font-size:15px; color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis'>{u['name']}</div>
                        <div style='color:var(--text-muted); font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis'>{u['email']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            c_m, c_d = st.columns([4, 1])
            with c_m:
                if st.button("Open Dashboard", key=f"v_{u['id']}", use_container_width=True):
                    st.session_state.selected_user = u
                    st.rerun()
            with c_d:
                if st.button("🗑️", key=f"d_{u['id']}", use_container_width=True):
                    api_request("DELETE", f"/users/{u['id']}")
                    if is_sel: st.session_state.selected_user = None
                    st.rerun()
    else:
        st.markdown("<div class='saas-card' style='text-align:center; padding: 40px; color:var(--text-muted)'>No users found</div>", unsafe_allow_html=True)

# 📊 Intelligence Dashboard
with col_dash:
    sel = st.session_state.selected_user
    if sel:
        st.markdown(f"<h5 style='color:var(--text-muted); margin-bottom: 15px'>ANALYTICS: {sel['name'].upper()}</h5>", unsafe_allow_html=True)
        
        # Stats Hub
        st.markdown("<div class='saas-card' style='padding: 15px'>", unsafe_allow_html=True)
        analyses = api_request("GET", f"/users/{sel['id']}/analyses")
        m1, m2, m3 = st.columns(3)
        with m1: st.markdown(f"<div class='metric-box'><div class='m-val'>{len(analyses) if analyses else 0}</div><div class='m-label'>Total Analyses</div></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='metric-box'><div class='m-val' style='color:#059669'>ACTIVE</div><div class='m-label'>Node Status</div></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='metric-box'><div class='m-val' style='font-family:monospace; font-size:24px'>{sel['id'][:6].upper()}</div><div class='m-label'>Access Key</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Algorithm Input
        st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0'>New Intelligence Feed</h4>", unsafe_allow_html=True)
        t_input = st.text_area("", placeholder="Enter text narrative for real-time analysis...", height=100, label_visibility="collapsed")
        if st.button("Process Analytics", use_container_width=True):
            if t_input.strip():
                if api_request("POST", f"/users/{sel['id']}/analyze", {"text": t_input}):
                    st.toast("Success")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Operational Logs
        if analyses:
            st.markdown("<h5 style='color:var(--text-muted); margin: 30px 0 15px'>HISTORICAL RECORDS</h5>", unsafe_allow_html=True)
            for a in reversed(analyses):
                with st.expander(f"Record: {a['analysis_id'][:8].upper()} — {a['analyzed_at'][:16].replace('T', ' ')}"):
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("Words", a['word_count'])
                    mc2.metric("Captials", a['uppercase_count'])
                    mc3.metric("Specials", a['special_character_count'])
                    st.markdown(f"<div class='intel-log'>{a['text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="saas-card" style="text-align:center; padding: 100px 20px;">
            <div style='font-size: 50px; margin-bottom: 20px'>📁</div>
            <h3>No Profile Selected</h3>
            <p style='color:var(--text-muted)'>Select an employee from the directory to view historical data and analytics.</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
