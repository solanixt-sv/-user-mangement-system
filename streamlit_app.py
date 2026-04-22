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

# Clean Professional Look
st.markdown("""
<style>
.stApp { background-color: #ffffff; }
.main { color: #1e293b; }
.section-card {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}
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
                res = client.post("/token", data={"username": le, "password": lp})
                if res.status_code == 200:
                    st.session_state.access_token = res.json()["access_token"]
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
            st.markdown(f"""
            <div class="section-card">
                <div style="font-weight:600; font-size:1.1rem;">{u['name']}</div>
                <div style="font-size:0.9rem; color:#64748b; margin-bottom:12px;">{u['email']}</div>
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
        st.markdown(f"### Analysis: {sel['name']}")
        
        st.info("Historical data and metrics are displayed below.")
        
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
        m1.metric("Analyses", len(analyses) if analyses else 0)
        m2.metric("Status", "Active")
        m3.metric("User ID", sel['id'][:5])

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
            st.markdown("<h5 style='color:var(--text-muted); margin: 30px 0 15px'>HISTORICAL RECORDS</h5>", unsafe_allow_html=True)
            for a in analyses:
                with st.expander(f"Record: {a['analysis_id'][:8].upper()} — {a['analyzed_at'][:16].replace('T', ' ')}"):
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("Words", a['word_count'])
                    mc2.metric("Captials", a['uppercase_count'])
                    mc3.metric("Specials", a['special_character_count'])
                    st.code(a['text'])
            
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
