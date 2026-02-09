# 07 — UI Foundation

> **Depends on:** `01_CORE_CONFIG_DB.md`, `02_CORE_SERVICES.md`, `05_HR_AGENT.md`, `06_NEW_AGENTS.md`
> **Creates:** `ui/app.py`, `ui/styles.py`, `ui/login_ui.py`, `ui/utils.py`

---

## Overview

The current `app.py` is a **2239-line monolith**. We split it into:

| File | Purpose | Approx Lines |
|------|---------|-------------|
| `ui/app.py` | Entry point, session init, router | ~120 |
| `ui/styles.py` | All CSS (`st.markdown`) | ~350 |
| `ui/login_ui.py` | Login page (Candidate / Employee / Admin tabs) | ~120 |
| `ui/utils.py` | Shared helpers (`parse_pdf_resume`, `logout`) | ~30 |
| Portal UIs | See guide 08 | — |

---

## `ui/styles.py`

Extract the entire `<style>` block from current `app.py` lines 460–784.

```python
"""
Global Streamlit CSS — Poppins font, cards, gradients, sidebar
Copy the FULL <style>...</style> block from current app.py (lines 460-784).
"""
import streamlit as st


def inject_css():
    """Inject global CSS into Streamlit page"""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

        /* ─── COPY THE ENTIRE CSS BLOCK FROM CURRENT app.py lines 460-784 ─── */
        /* The CSS covers:
           - Font family (Poppins)
           - Main container styling
           - Sidebar gradient and menu items
           - Card components (.card, .metric-card)
           - Status badges (.status-badge)
           - Form styling
           - Button overrides (primary, secondary)
           - Tab styling
           - Chat message containers
           - Code editor styling
           - Metric displays
           - Responsive design
        */

        /* IMPORTANT: Copy verbatim — do not modify the CSS */
    </style>
    """, unsafe_allow_html=True)
```

> **Instruction to implementing agent:** Copy lines 460–784 of the current `app.py` into the `st.markdown(...)` call above.

---

## `ui/utils.py`

```python
"""Shared UI utilities"""
import streamlit as st
import PyPDF2
import io


def parse_pdf_resume(uploaded_file) -> str:
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        st.error(f"Error parsing PDF: {str(e)}")
        return ""


def logout():
    """Clear session and rerun"""
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()
```

---

## `ui/login_ui.py`

```python
"""Login page — 3 tabs: Candidate, Employee, Admin"""
import streamlit as st
import datetime


def show_login_page():
    """Render the login page with role tabs"""
    st.markdown("""
    <div style="text-align:center; padding:2rem 0;">
        <h1>🤖 Agentic AI Enterprise Platform</h1>
        <p style="color:#888;">Multi-Agent HR · IT · Finance · Compliance</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2, tab3 = st.tabs(["👤 Candidate", "💼 Employee", "⚙️ Admin"])

        # ── Candidate Tab ─────────────────────────────────────
        with tab1:
            st.markdown("### New Applicant?")
            if st.button("📝 Apply for a Position", use_container_width=True, type="primary"):
                st.session_state.show_application_form = True
                st.rerun()

        # ── Employee Tab ──────────────────────────────────────
        with tab2:
            st.markdown("### Employee Login")
            with st.form("employee_login"):
                e_user = st.text_input("Username", key="emp_user")
                e_pass = st.text_input("Password", type="password", key="emp_pass")
                login_btn = st.form_submit_button("Login", use_container_width=True)
                if login_btn:
                    user = st.session_state.db.authenticate_user(e_user, e_pass)
                    if user and user.role == "Employee":
                        st.session_state.logged_in = True
                        st.session_state.current_user = user
                        st.session_state.user_role = "Employee"
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

        # ── Admin Tab ─────────────────────────────────────────
        with tab3:
            st.markdown("### Admin Login")
            with st.form("admin_login"):
                a_user = st.text_input("Username", key="admin_user")
                a_pass = st.text_input("Password", type="password", key="admin_pass")
                login_btn = st.form_submit_button("Login", use_container_width=True)
                if login_btn:
                    user = st.session_state.db.authenticate_user(a_user, a_pass)
                    if user and user.role == "Admin":
                        st.session_state.logged_in = True
                        st.session_state.current_user = user
                        st.session_state.user_role = "Admin"
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
```

---

## `ui/app.py` — Entry Point

```python
"""
Agentic AI Enterprise Platform — Streamlit Entry Point
Run: streamlit run ui/app.py
"""
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Agentic AI Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Inject CSS ────────────────────────────────────────────────
from ui.styles import inject_css
inject_css()

# ── Initialize Session State ─────────────────────────────────
from core.database import Database
from core.llm_service import LLMInterface
from core.event_bus import EventBus
from core.orchestrator import Orchestrator
from agents.hr_agent import HRAgent
from agents.it_agent import ITAgent
from agents.finance_agent import FinanceAgent
from agents.compliance_agent import ComplianceAgent

if 'db' not in st.session_state:
    st.session_state.db = Database()

if 'llm' not in st.session_state:
    api_key = os.getenv("GROQ_API_KEY")
    st.session_state.llm = LLMInterface(api_key, st.session_state.db)

if 'event_bus' not in st.session_state:
    st.session_state.event_bus = EventBus()

if 'agents' not in st.session_state:
    db = st.session_state.db
    llm = st.session_state.llm
    bus = st.session_state.event_bus
    st.session_state.agents = {
        'hr': HRAgent(db, llm, bus),
        'it': ITAgent(db, llm, bus),
        'finance': FinanceAgent(db, llm, bus),
        'compliance': ComplianceAgent(db, llm, bus),
    }

if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = Orchestrator(
        st.session_state.agents, st.session_state.llm, st.session_state.event_bus
    )

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# ── Router ────────────────────────────────────────────────────
from ui.login_ui import show_login_page

def main():
    if not st.session_state.logged_in:
        # Check for candidate application flow
        if st.session_state.get('show_application_form'):
            from ui.candidate_portal import show_candidate_portal
            show_candidate_portal()
        else:
            show_login_page()
    else:
        role = st.session_state.get('user_role', 'Employee')
        if role == "Admin":
            from ui.admin_portal import show_admin_portal
            show_admin_portal()
        elif role == "Employee":
            from ui.employee_portal import show_employee_portal
            show_employee_portal()
        # IT / Finance / Compliance portals can be added here

main()
```

---

## ✅ Done Checklist

- [ ] `ui/app.py` — entry point with session initialization for all 4 agents + orchestrator
- [ ] `ui/styles.py` — CSS extracted from current app.py (lines 460–784)
- [ ] `ui/login_ui.py` — login page with 3 role tabs
- [ ] `ui/utils.py` — `parse_pdf_resume()`, `logout()`
- [ ] All session state keys initialized (db, llm, event_bus, agents, orchestrator, logged_in, current_user)
- [ ] Router dispatches to correct portal based on role
