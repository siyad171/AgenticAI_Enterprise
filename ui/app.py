"""
Agentic AI Enterprise Platform — Streamlit Entry Point
Run: streamlit run ui/app.py
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)

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
from core.llm_service import LLMService
from core.event_bus import EventBus
from core.orchestrator import Orchestrator
from agents.hr_agent import HRAgent
from agents.it_agent import ITAgent
from agents.finance_agent import FinanceAgent
from agents.compliance_agent import ComplianceAgent

if 'db' not in st.session_state:
    st.session_state.db = Database()

if 'llm' not in st.session_state:
    st.session_state.llm = LLMService()

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

main()
