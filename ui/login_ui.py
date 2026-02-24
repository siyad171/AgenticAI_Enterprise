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

    session_mgr = st.session_state.get('session_mgr')

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2, tab3 = st.tabs(["👤 Candidate", "💼 Employee", "⚙️ Admin"])

        # ── Candidate Tab ─────────────────────────────────────
        with tab1:
            st.markdown("### New Applicant?")
            if st.button("📝 Apply for a Position", use_container_width=True, type="primary"):
                st.session_state.show_application_form = True
                # Persist candidate session in cookie
                if session_mgr:
                    session_mgr.create_session({
                        "username": "__candidate__",
                        "role": "Candidate",
                    })
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
                        # Persist in cookie
                        if session_mgr:
                            session_mgr.create_session({
                                "username": user.username,
                                "role": "Employee",
                                "employee_id": user.employee_id,
                            })
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
                        # Persist in cookie
                        if session_mgr:
                            session_mgr.create_session({
                                "username": user.username,
                                "role": "Admin",
                            })
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
