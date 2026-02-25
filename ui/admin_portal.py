"""Admin Portal — Employee mgmt, candidates, audit, config"""
import streamlit as st
import datetime
from ui.utils import logout


def _count_new_candidates(db) -> int:
    """Count candidates in 'Pending' or 'Test_Scheduled' status."""
    return sum(1 for c in db.candidates.values()
               if getattr(c, 'status', '') in ('Pending', 'Test_Scheduled', 'Accepted'))


def show_admin_portal():
    db = st.session_state.db
    new_count = _count_new_candidates(db)
    badge = f" ({new_count})" if new_count else ""

    st.sidebar.title("⚙️ Admin Portal")
    page = st.sidebar.radio("Menu", [
        "🏠 Dashboard", "👥 Employees", f"📋 Candidates{badge}",
        "📊 Audit Report", "⚙️ Settings",
        "🖥️ IT", "💰 Finance", "📜 Compliance",
        "🔄 Orchestrator"])
    if st.sidebar.button("🚪 Logout"):
        logout()

    if page == "🏠 Dashboard":
        _admin_dashboard()
    elif page == "👥 Employees":
        _employee_management()
    elif page.startswith("📋 Candidates"):
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

    # Notification banner
    new_count = _count_new_candidates(db)
    if new_count:
        st.warning(f"🔔 **{new_count} candidate(s)** awaiting review — "
                   "go to **📋 Candidates** to view full reports.")

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

    # Candidate selector
    cand_options = {f"{c.name} — {c.status} ({cid})": cid
                    for cid, c in db.candidates.items()}
    selected_label = st.selectbox("Select Candidate", list(cand_options.keys()))
    cid = cand_options[selected_label]
    candidate = db.get_candidate(cid)

    # Quick info row
    c1, c2, c3, c4 = st.columns(4)
    c1.write(f"**Position:** {candidate.applied_position}")
    c2.write(f"**Experience:** {candidate.experience_years} yrs")
    c3.write(f"**Status:** {candidate.status}")
    c4.write(f"**Skills:** {len(candidate.extracted_skills or [])}")

    st.divider()

    # Show full report
    from ui.candidate_report_ui import show_candidate_report
    llm_service = st.session_state.get("llm")
    compare = st.checkbox("Compare with benchmark", value=True)
    show_candidate_report(candidate, llm_service=llm_service, compare=compare)


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
