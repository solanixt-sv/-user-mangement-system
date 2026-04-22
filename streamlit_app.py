import streamlit as st
import requests
import subprocess
import time
import socket
import os
import threading
import uvicorn
from datetime import datetime
from fastapi.testclient import TestClient
from main import app as fastapi_app

# --- Configuration ---
API_BASE_URL = "http://localhost:8000"

# Integrated Mode: Backend runs within the Streamlit process via TestClient

# --- UI Setup ---
st.set_page_config(
    page_title="UserScope Enterprise | Clean Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Premium Enterprise Design System
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

:root {
    --primary: #6366f1;
    --primary-glow: rgba(99, 102, 241, 0.2);
    --secondary: #ec4899;
    --bg: #0f172a;
    --card-bg: #1e293b;
    --border: #334155;
    --text: #f8fafc;
    --text-muted: #94a3b8;
    --success: #10b981;
}

/* Base Styles */
.main { background: var(--bg); color: var(--text); }
* { font-family: 'Inter', sans-serif; }
h1, h2, h3, .logo { font-family: 'Space Grotesk', sans-serif; }

/* Custom Scrollbar */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }

/* Remove default padding */
.block-container { padding-top: 2rem !important; }

/* Navbar */
.nav-bar {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 70px;
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 5%;
    z-index: 1000;
}
.logo-box { display: flex; align-items: center; gap: 12px; }
.logo-icon { width: 40px; height: 40px; background: linear-gradient(135deg, var(--primary), var(--secondary)); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 800; color: white; }

/* Premium Cards */
.glass-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 24px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    margin-bottom: 20px;
}
.glass-card:hover {
    border-color: var(--primary);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.1);
    transform: translateY(-5px);
}

/* Auth Center */
.auth-container {
    max-width: 450px;
    margin: 100px auto;
    animation: fadeIn 0.8s ease-out;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: #0f172a !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
}
.stTextInput input:focus { border-color: var(--primary) !important; box-shadow: 0 0 0 2px var(--primary-glow) !important; }

/* Buttons */
.stButton button {
    background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
    border: none !important;
    border-radius: 12px !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 12px 24px !important;
    transition: all 0.2s !important;
    width: 100%;
}
.stButton button:hover { transform: scale(1.02); box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.4) !important; }

/* Status Badge */
.status-badge {
    background: var(--primary-glow);
    color: var(--primary);
    padding: 6px 12px;
    border-radius: 100px;
    font-size: 12px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 6px;
    border: 1px solid var(--primary);
}
.pulse { width: 8px; height: 8px; background: var(--primary); border-radius: 50%; animation: pulse-anim 2s infinite; }
@keyframes pulse-anim { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(99, 102, 241, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); } }

/* Sidebar */
[data-testid="stSidebar"] { background-color: #0f172a !important; border-right: 1px solid var(--border) !important; }
[data-testid="stSidebar"] * { color: var(--text) !important; }

</style>
""", unsafe_allow_html=True)

# --- Logic ---
# --- Integrated API Bridge ---
# This allows Streamlit to call FastAPI logic directly without a separate server process.
# Perfect for deployment on streamlit.io
client = TestClient(fastapi_app)

def api_request(method, endpoint, data=None, params=None):
    headers = {}
    if "access_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    
    try:
        # Use TestClient to bridge Streamlit and FastAPI
        if method == "GET": r = client.get(endpoint, params=params, headers=headers)
        elif method == "POST": r = client.post(endpoint, json=data, headers=headers)
        elif method == "DELETE": r = client.delete(endpoint, headers=headers)
        
        if r.status_code in [200, 201]: 
            return r.json()
        elif r.status_code == 401:
            st.session_state.clear()
            st.toast("Session expired. Please login again.", icon="🔒")
            st.rerun()
        elif r.status_code == 400:
            st.toast(f"Error: {r.json().get('detail')}", icon="❌")
    except Exception as e: 
        st.toast(f"Bridge Error: {str(e)}", icon="⚠️")
    return None

# Initialize Session States
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = None
if 'user_offset' not in st.session_state:
    st.session_state.user_offset = 0
if 'analysis_offset' not in st.session_state:
    st.session_state.analysis_offset = 0
if 'access_token' not in st.session_state:
    st.session_state.access_token = None

# --- TOP NAV ---
st.markdown(f"""
<div class="nav-bar">
    <div class="logo-box">
        <div class="logo-icon">U</div>
        <div style="font-weight:700; font-size:22px;">UserScope <span style="color:var(--primary)">Elite</span></div>
    </div>
    <div class="status-badge">
        <div class="pulse"></div> System Operational (Integrated)
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Branding
with st.sidebar:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### 🛠️ Elite Console")
    st.divider()
    if st.session_state.access_token:
        st.info("Authenticated Session Active")
        if st.button("🚪 Terminate Session", use_container_width=True):
            st.session_state.access_token = None
            st.session_state.selected_user = None
            st.rerun()
    else:
        st.warning("Please sign in")

# --- AUTHENTICATION GATE ---
if not st.session_state.access_token:
    st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
    
    auth_tab1, auth_tab2 = st.tabs(["🔐 Secure Login", "📝 System Registration"])
    
    with auth_tab1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center; margin-bottom:30px;'>Welcome Back</h2>", unsafe_allow_html=True)
        le = st.text_input("Corporate Email", placeholder="email@company.com", key="login_email")
        lp = st.text_input("Secure Password", type="password", placeholder="••••••••", key="login_pass")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Access Secure Node", use_container_width=True):
            if le and lp:
                with st.spinner("Authenticating..."):
                    try:
                        # Use internal bridge for login
                        res = client.post("/token", data={"username": le, "password": lp})
                        if res.status_code == 200:
                            st.session_state.access_token = res.json()["access_token"]
                            st.toast("Access Granted", icon="🟢")
                            st.rerun()
                        else:
                            st.error("Authentication failed: Invalid credentials")
                    except Exception as e:
                        st.error(f"Bridge connection error: {e}")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with auth_tab2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center; margin-bottom:30px;'>Create Identity</h2>", unsafe_allow_html=True)
        sn = st.text_input("Official Name", placeholder="John Doe", key="signup_name")
        se = st.text_input("Assigned Email", placeholder="name@company.com", key="signup_email")
        sp = st.text_input("New Security Key", type="password", placeholder="••••••••", key="signup_pass")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Register & Initialize", use_container_width=True):
            if sn and se and sp:
                with st.spinner("Creating profile..."):
                    try:
                        # Use internal bridge for signup
                        res = client.post("/users", json={"name": sn, "email": se, "password": sp})
                        if res.status_code == 201:
                            l_res = client.post("/token", data={"username": se, "password": sp})
                            if l_res.status_code == 200:
                                st.session_state.access_token = l_res.json()["access_token"]
                                st.toast("Identity Established", icon="✨")
                                st.rerun()
                        else:
                            st.error(f"Registration failed: {res.json().get('detail')}")
                    except Exception as e:
                        st.error(f"Bridge connection error: {e}")
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- MAIN CONTENT ---
st.markdown("<div style='padding-top:100px; max-width:1400px; margin:0 auto; padding-left:20px; padding-right:20px;'>", unsafe_allow_html=True)

# Header Section
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("<h1 style='font-size:3rem; margin:0;'>Intelligence Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:var(--text-muted); font-size:1.1rem;'>Global employee management and real-time behavioral analysis.</p>", unsafe_allow_html=True)
with c2:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.popover("➕ Provision User", use_container_width=True):
        st.markdown("### Profile Deployment")
        n = st.text_input("Full Name", placeholder="Employee Name")
        e = st.text_input("Email", placeholder="email@company.com")
        p = st.text_input("Initial Password", type="password", placeholder="Secure Password")
        if st.button("Deploy to Network", use_container_width=True):
            if n and e and p:
                if api_request("POST", "/users", {"name": n, "email": e, "password": p}):
                    st.toast("Profile Deployed", icon="🚀")
                    st.rerun()

st.markdown("<br><br>", unsafe_allow_html=True)

col_dir, col_dash = st.columns([1, 2], gap="large")

# 🏛️ Employee Directory
with col_dir:
    st.markdown("<h5 style='color:var(--text-muted); margin-bottom: 15px'>DIRECTORY LISTING</h5>", unsafe_allow_html=True)
    
    # Directory Controls
    with st.container():
        dc1, dc2 = st.columns([1, 1])
        with dc1:
            u_sort = st.selectbox("Order", ["asc", "desc"], label_visibility="collapsed", key="u_sort_sel")
        with dc2:
            page_num = (st.session_state.user_offset // 10) + 1
            st.markdown(f"<div style='text-align:right; font-size:12px; font-weight:700; color:var(--primary); padding-top:10px'>PAGE {page_num}</div>", unsafe_allow_html=True)

    users = api_request("GET", "/users", params={
        "limit": 10, 
        "offset": st.session_state.user_offset, 
        "sort": u_sort
    })
    if users:
        for u in users:
            is_sel = st.session_state.selected_user and st.session_state.selected_user['id'] == u['id']
            card_border = f"border: 2px solid var(--primary); background: #f5f3ff;" if is_sel else ""
            st.markdown(f"""
            <div class="glass-card" style='padding: 20px; {card_border}'>
                <div style='display:flex; align-items:center; gap:15px'>
                    <div style='min-width:50px; height:50px; border-radius:12px; background:linear-gradient(135deg, var(--primary), var(--secondary)); color:white; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:20px;'>{u['name'][0].upper()}</div>
                    <div style='overflow:hidden'>
                        <div style='font-weight:700; font-size:18px; color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis'>{u['name']}</div>
                        <div style='color:var(--text-muted); font-size:13px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis'>{u['email']}</div>
                    </div>
                </div>
                <div style='margin-top:20px; display:flex; gap:10px;'>
            """, unsafe_allow_html=True)
            
            c_m, c_d = st.columns([4, 1])
            with c_m:
                if st.button("View Analysis", key=f"v_{u['id']}", use_container_width=True):
                    st.session_state.selected_user = u
                    st.rerun()
            with c_d:
                if st.button("🗑️", key=f"d_{u['id']}", use_container_width=True):
                    api_request("DELETE", f"/users/{u['id']}")
                    if is_sel: st.session_state.selected_user = None
                    st.rerun()
            st.markdown("</div></div>", unsafe_allow_html=True)
        
        # Pagination Buttons
        pb1, pb2 = st.columns(2)
        with pb1:
            if st.button("⬅️ Previous", disabled=st.session_state.user_offset == 0, use_container_width=True):
                st.session_state.user_offset = max(0, st.session_state.user_offset - 10)
                st.rerun()
        with pb2:
            if st.button("Next ➡️", disabled=not users or len(users) < 10, use_container_width=True):
                st.session_state.user_offset += 10
                st.rerun()
    else:
        st.markdown("<div class='glass-card' style='text-align:center; padding: 60px; color:var(--text-muted)'>No neural links found</div>", unsafe_allow_html=True)
        if st.session_state.user_offset > 0:
            if st.button("🔄 Reset Pagination"):
                st.session_state.user_offset = 0
                st.rerun()

# 📊 Intelligence Dashboard
with col_dash:
    sel = st.session_state.selected_user
    if sel:
        st.markdown(f"<h5 style='color:var(--text-muted); margin-bottom: 20px'>OPERATIONAL INTELLIGENCE: {sel['name'].upper()}</h5>", unsafe_allow_html=True)
        
        # Stats Hub
        st.markdown("<div class='glass-card' style='padding: 25px'>", unsafe_allow_html=True)
        
        # Analytics Controls (Filtering & Sorting)
        ac1, ac2, ac3 = st.columns([2, 1, 1])
        with ac1:
            min_w = st.slider("Min Words", 0, 50, 0, help="Filter results by minimum word count")
        with ac2:
            a_sort = st.selectbox("Sort", ["asc", "desc"], index=1, key="a_sort_sel")
        with ac3:
            if st.button("🔄", help="Reset Filters"):
                st.session_state.analysis_offset = 0
                st.rerun()

        analyses = api_request("GET", f"/users/{sel['id']}/analyses", params={
            "limit": 5,
            "offset": st.session_state.analysis_offset,
            "sort": a_sort,
            "min_words": min_w
        })

        m1, m2, m3 = st.columns(3)
        with m1: st.markdown(f"<div style='text-align:center;'><div style='font-size:40px; font-weight:800;'>{len(analyses) if analyses else 0}</div><div style='font-size:12px; color:var(--text-muted); text-transform:uppercase;'>Records</div></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div style='text-align:center;'><div style='font-size:40px; font-weight:800; color:var(--success)'>LIVE</div><div style='font-size:12px; color:var(--text-muted); text-transform:uppercase;'>Status</div></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div style='text-align:center;'><div style='font-size:40px; font-weight:800; color:var(--primary)'>{sel['id'][:4].upper()}</div><div style='font-size:12px; color:var(--text-muted); text-transform:uppercase;'>Link ID</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Algorithm Input
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0'>New Behavioral Input</h4>", unsafe_allow_html=True)
        t_input = st.text_area("", placeholder="Enter text narrative for real-time analysis...", height=120, label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Execute Core Analysis", use_container_width=True):
            if t_input.strip():
                with st.spinner("Analyzing text..."):
                    if api_request("POST", f"/users/{sel['id']}/analyze", {"text": t_input}):
                        st.toast("Analysis Captured", icon="🧠")
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Operational Logs
        if analyses:
            st.markdown("<h5 style='color:var(--text-muted); margin: 30px 0 15px'>HISTORICAL RECORDS</h5>", unsafe_allow_html=True)
            for a in analyses:
                with st.expander(f"Record: {a['analysis_id'][:8].upper()} — {a['analyzed_at'][:16].replace('T', ' ')}"):
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("Words", a['word_count'])
                    mc2.metric("Captials", a['uppercase_count'])
                    mc3.metric("Specials", a['special_character_count'])
                    st.markdown(f"<div style='background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; border-left:4px solid var(--primary); font-family:monospace;'>{a['text']}</div>", unsafe_allow_html=True)
            
            # Analysis Pagination
            ap1, ap2 = st.columns(2)
            with ap1:
                if st.button("⬅️ Earlier", key="a_prev", disabled=st.session_state.analysis_offset == 0, use_container_width=True):
                    st.session_state.analysis_offset = max(0, st.session_state.analysis_offset - 5)
                    st.rerun()
            with ap2:
                if st.button("Later ➡️", key="a_next", disabled=not analyses or len(analyses) < 5, use_container_width=True):
                    st.session_state.analysis_offset += 5
                    st.rerun()
    else:
        st.markdown("""
        <div class="glass-card" style="text-align:center; padding: 120px 20px; border-style: dashed;">
            <div style='font-size: 70px; margin-bottom: 20px'>🛰️</div>
            <h2>No Active Link</h2>
            <p style='color:var(--text-muted)'>Select a profile from the directory to establish a synchronization link and view analytics.</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
