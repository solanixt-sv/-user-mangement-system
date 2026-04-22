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

# Premium SaaS Design System
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@400;500;600&display=swap');

.stApp { 
    background: linear-gradient(135deg, #f8fafc 0%, #eff6ff 100%);
    font-family: 'Inter', sans-serif;
}

h1, h2, h3, .stSubheader { font-family: 'Outfit', sans-serif; color: #1e1b4b; }

/* Premium Floating Cards */
.saas-card {
    background: white;
    border: 1px solid rgba(226, 232, 240, 0.8);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.saas-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

/* Sidebar Customization */
[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
}

/* Indigo Button */
.stButton>button {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    padding: 10px 20px;
    transition: opacity 0.2s;
}
.stButton>button:hover { opacity: 0.9; color: white; }

/* Status Badges */
.badge-indigo { background: #eef2ff; color: #4338ca; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; }
.badge-emerald { background: #ecfdf5; color: #047857; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; }
.badge-rose { background: #fff1f2; color: #be123c; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; }
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

# --- SIDEBAR ---
with st.sidebar:
    st.title("Settings")
    if st.session_state.access_token:
        st.success("Session Active")
        if st.button("Logout", use_container_width=True):
            st.session_state.access_token = None
            st.session_state.selected_user = None
            st.rerun()
    else:
        st.warning("Please Login")

# --- AUTHENTICATION GATE ---
if not st.session_state.access_token:
    st.title("User Management System")
    st.write("Please login or create an account to proceed.")
    
    auth_tab1, auth_tab2 = st.tabs(["Login", "Create Account"])
    
    with auth_tab1:
        st.subheader("Login")
        le = st.text_input("Email", placeholder="admin@example.com")
        lp = st.text_input("Password", type="password", placeholder="••••••••")
        if st.button("Sign In", use_container_width=True):
            if le and lp:
                with st.spinner("Authenticating..."):
                    res = client.post("/token", data={"username": le, "password": lp})
                    if res.status_code == 200:
                        st.session_state.access_token = res.json()["access_token"]
                        st.toast("Welcome back!", icon="👋")
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
        
    with auth_tab2:
        st.subheader("Sign Up")
        sn = st.text_input("Name", placeholder="Your Name")
        se = st.text_input("Email Address", placeholder="name@example.com")
        sp = st.text_input("New Password", type="password", placeholder="••••••••")
        if st.button("Register", use_container_width=True):
            if sn and se and sp:
                res = client.post("/users", json={"name": sn, "email": se, "password": sp})
                if res.status_code == 201:
                    l_res = client.post("/token", data={"username": se, "password": sp})
                    if l_res.status_code == 200:
                        st.session_state.access_token = l_res.json()["access_token"]
                        st.rerun()
                else:
                    st.error(res.json().get("detail", "Error creating account"))
    st.stop()

# --- MAIN CONTENT ---
st.title("Directory & Analytics")
st.write("Manage users and analyze text data.")
st.divider()

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
            sel_style = "border-left: 4px solid #4f46e5; background: #f5f3ff;" if is_sel else ""
            st.markdown(f"""
            <div class="saas-card" style='{sel_style}'>
                <div style="font-weight:700; font-size:1.1rem; color:#1e1b4b;">{u['name']}</div>
                <div style="font-size:0.85rem; color:#64748b; margin-bottom:12px;">{u['email']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            c_m, c_d = st.columns([4, 1])
            with c_m:
                if st.button("Open Analytics", key=f"v_{u['id']}", use_container_width=True):
                    st.session_state.selected_user = u
                    st.rerun()
            with c_d:
                if st.button("🗑️", key=f"d_{u['id']}", use_container_width=True):
                    api_request("DELETE", f"/users/{u['id']}")
                    if is_sel: st.session_state.selected_user = None
                    st.rerun()
        
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
        st.info("No users found in the system.")
        if st.session_state.user_offset > 0:
            if st.button("🔄 Reset Pagination"):
                st.session_state.user_offset = 0
                st.rerun()

# 📊 Analytics Panel
with col_dash:
    sel = st.session_state.selected_user
    if sel:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, #4f46e5, #7c3aed); padding:24px; border-radius:16px; color:white; margin-bottom:24px; box-shadow: 0 10px 20px rgba(79, 70, 229, 0.2);">
            <div style="font-size:14px; opacity:0.8; font-weight:600; text-transform:uppercase; letter-spacing:1px;">Active Workspace</div>
            <div style="font-size:32px; font-weight:700; margin-top:4px;">{sel['name']}</div>
            <div style="font-size:14px; opacity:0.9; margin-top:2px;">{sel['email']} • <span style="font-weight:600">ID: {sel['id'][:5].upper()}</span></div>
        </div>
        """, unsafe_allow_html=True)
        
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
        with m1:
            st.markdown("<div class='saas-card' style='text-align:center; padding:15px; background:white;'>"
                        "<div style='font-size:11px; color:#64748b; font-weight:700;'>ANALYSES</div>"
                        f"<div style='font-size:24px; font-weight:700; color:#4f46e5;'>{len(analyses) if analyses else 0}</div></div>", unsafe_allow_html=True)
        with m2:
            st.markdown("<div class='saas-card' style='text-align:center; padding:15px; background:white;'>"
                        "<div style='font-size:11px; color:#64748b; font-weight:700;'>UPTIME</div>"
                        "<div style='font-size:24px; font-weight:700; color:#059669;'>100%</div></div>", unsafe_allow_html=True)
        with m3:
            st.markdown("<div class='saas-card' style='text-align:center; padding:15px; background:white;'>"
                        "<div style='font-size:11px; color:#64748b; font-weight:700;'>SECURITY</div>"
                        "<div style='font-size:24px; font-weight:700; color:#7c3aed;'>JWT</div></div>", unsafe_allow_html=True)

        # Input Area
        st.subheader("New Text Analysis")
        t_input = st.text_area("Enter text for analysis", placeholder="Type here...", height=100)
        if st.button("Run Intelligence Analysis", use_container_width=True):
            if t_input.strip():
                if api_request("POST", f"/users/{sel['id']}/analyze", {"text": t_input}):
                    st.success("Analysis complete")
                    st.rerun()

        # Operational Logs
        if analyses:
            st.markdown("<h5 style='color:#64748b; margin: 30px 0 15px; font-weight:700; letter-spacing:0.5px;'>HISTORICAL INTELLIGENCE</h5>", unsafe_allow_html=True)
            for a in analyses:
                st.markdown(f"""
                <div class="saas-card" style="padding:20px; background:white;">
                    <div style="display:flex; gap:8px; margin-bottom:12px;">
                        <span class="badge-indigo">Words: {a['word_count']}</span>
                        <span class="badge-emerald">Capitals: {a['uppercase_count']}</span>
                        <span class="badge-rose">Specials: {a['special_character_count']}</span>
                    </div>
                    <div style="background:#f1f5f9; padding:16px; border-radius:12px; font-size:14px; line-height:1.6; color:#334155; border-left:4px solid #4f46e5;">
                        {a['text']}
                    </div>
                    <div style="font-size:11px; color:#94a3b8; margin-top:12px; font-weight:500;">RECORD ID: {a['analysis_id'][:8].upper()} • {a['analyzed_at'][:16].replace('T', ' ')}</div>
                </div>
                """, unsafe_allow_html=True)
            
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
        st.info("Select a user from the directory to view details.")

st.markdown("</div>", unsafe_allow_html=True)
