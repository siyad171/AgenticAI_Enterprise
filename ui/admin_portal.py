"""Admin Portal — Employee mgmt, candidates, audit, config"""
import streamlit as st
import datetime
from ui.utils import logout


def show_admin_portal():
    st.sidebar.title("⚙️ Admin Portal")
    page = st.sidebar.radio("Menu", [
        "🏠 Dashboard", "👥 Employees", "📋 Candidates",
        "📊 Audit Report", "⚙️ Settings",
        "🖥️ IT", "💰 Finance", "📜 Compliance",
        "🔄 Orchestrator"])
    if st.sidebar.button("🚪 Logout"):
        logout()

    if page == "🏠 Dashboard":
        _admin_dashboard()
    elif page == "👥 Employees":
        _employee_management()
    elif page == "📋 Candidates":
        _candidate_review()
    elif page == "📊 Audit Report":
        _audit_report()
    elif page == "⚙️ Settings":
        _settings()
    elif page == "🖥️ IT":
        from ui.it_portal import show_it_portal
        show_it_portal()
    elif page == "💰 Finance":
        from ui.finance_portal import show_finance_portal
        show_finance_portal()
    elif page == "📜 Compliance":
        from ui.compliance_portal import show_compliance_portal
        show_compliance_portal()
    elif page == "🔄 Orchestrator":
        from ui.orchestrator_dashboard import show_orchestrator_dashboard
        show_orchestrator_dashboard()


def _admin_dashboard():
    db = st.session_state.db
    st.header("🏠 Admin Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Employees", len(db.employees))
    c2.metric("Candidates", len(db.candidates))
    c3.metric("Open Tickets", len([t for t in getattr(db, 'it_tickets', {}).values()
                                    if getattr(t, 'status', '') == 'Open']))
    c4.metric("Audit Logs", len(db.audit_logs))


def _employee_management():
    db = st.session_state.db
    agent = st.session_state.agents['hr']
    st.header("👥 Employee Management")

    # Onboarding form
    with st.expander("➕ Add New Employee"):
        with st.form("onboard_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            dept = st.text_input("Department")
            pos = st.text_input("Position")
            jdate = st.date_input("Join Date")
            if st.form_submit_button("Create", type="primary"):
                result = agent.handle_employee_onboarding(
                    name, email, dept, pos, jdate.strftime("%Y-%m-%d"))
                st.success(f"✅ Employee {result['employee_id']} created")

    # Employee list
    st.subheader("Current Employees")
    for eid, emp in db.employees.items():
        with st.expander(f"{emp.name} ({eid})"):
            st.write(f"**Dept:** {emp.department} | **Position:** {emp.position}")
            st.write(f"**Email:** {emp.email} | **Joined:** {emp.join_date}")
            st.write(f"**Leave:** Casual={emp.leave_balance.get('Casual Leave',0)}, "
                     f"Sick={emp.leave_balance.get('Sick Leave',0)}, "
                     f"Annual={emp.leave_balance.get('Annual Leave',0)}")


def _candidate_review():
    db = st.session_state.db
    st.header("📋 Candidate Review")
    if not db.candidates:
        st.info("No candidates yet")
        return
    for cid, cand in db.candidates.items():
        with st.expander(f"{cand.name} — {cand.status}"):
            st.write(f"**Position:** {cand.applied_position}")
            st.write(f"**Skills:** {', '.join(cand.extracted_skills)}")
            st.write(f"**Experience:** {cand.experience_years} years")
            if cand.evaluation_result:
                st.write(f"**Score:** {cand.evaluation_result.get('score', 'N/A')}%")
            # View interview results
            from ui.results_viewer_ui import show_candidate_results
            show_candidate_results(cid)


def _audit_report():
    agent = st.session_state.agents['hr']
    st.header("📊 Audit Report")
    c1, c2 = st.columns(2)
    start = c1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
    end = c2.date_input("End Date")
    if st.button("Generate Report", type="primary"):
        report = agent.generate_audit_report(
            start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        summary = report.get('summary', {})
        st.metric("Total Activities", summary.get('total_activities', 0))
        st.json(report)


def _settings():
    db = st.session_state.db
    st.header("⚙️ Eligibility Criteria")
    criteria = db.eligibility_criteria
    with st.form("criteria_form"):
        skill = st.slider("Skill Match Threshold %", 0, 100,
                           criteria.get('skill_match_threshold', 50))
        auto = st.slider("Auto-Accept Threshold %", 0, 100,
                          criteria.get('auto_accept_threshold', 50))
        exp = st.checkbox("Require Experience", criteria.get('experience_required', True))
        edu = st.checkbox("Require Education", criteria.get('education_required', True))
        if st.form_submit_button("Save"):
            db.update_eligibility_criteria({
                'skill_match_threshold': skill, 'auto_accept_threshold': auto,
                'experience_required': exp, 'education_required': edu})
            st.success("✅ Settings saved")
