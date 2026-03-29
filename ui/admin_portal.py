"""Admin Portal — Employee mgmt, candidates, audit, config"""
import streamlit as st
import datetime
import re
from ui.utils import logout


def _count_new_candidates(db) -> int:
    """Count candidates in 'Pending' or 'Test_Scheduled' status."""
    return sum(1 for c in db.candidates.values()
               if getattr(c, 'status', '') in ('Pending', 'Test_Scheduled', 'Accepted'))


def show_admin_portal():
    db = st.session_state.db
    orch = st.session_state.orchestrator
    new_count = _count_new_candidates(db)
    badge = f" ({new_count})" if new_count else ""

    st.sidebar.title("⚙️ Admin Portal")
    page = st.sidebar.radio("Menu", [
        "🏠 Dashboard", "👥 Employees", f"📋 Candidates{badge}",
        "📊 Audit Report", "🚨 Escalations",
        "🤖 Admin Assistant", "⚙️ Settings"])
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
    elif page == "🚨 Escalations":
        _escalations()
    elif page == "🤖 Admin Assistant":
        _admin_assistant()
    elif page == "⚙️ Settings":
        _settings()


def _admin_dashboard():
    db = st.session_state.db
    orch = st.session_state.orchestrator
    metrics = orch.get_escalation_metrics()
    st.header("🏠 Admin Dashboard")

    # Notification banner
    new_count = _count_new_candidates(db)
    if new_count:
        st.warning(f"🔔 **{new_count} candidate(s)** awaiting review — "
                   "go to **📋 Candidates** to view full reports.")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Employees", len(db.employees))
    c2.metric("Candidates", len(db.candidates))
    c3.metric("Open Tickets", len([t for t in getattr(db, 'it_tickets', {}).values()
                                    if getattr(t, 'status', '') == 'Open']))
    c4.metric("Open Escalations", metrics.get("open", 0))
    c5.metric("Audit Logs", len(db.audit_logs))


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


def _escalations():
    orch = st.session_state.orchestrator
    st.header("🚨 Escalations")

    open_cases = list(reversed(orch.get_escalation_queue(status="Open")))
    resolved_cases = list(reversed(orch.get_escalation_queue(status="Resolved")))

    if not open_cases:
        st.success("No open escalations right now.")
    else:
        st.subheader(f"Open Cases ({len(open_cases)})")
        for case in open_cases:
            title = (
                f"{case.get('case_id')} | {case.get('agent_label')} | "
                f"{case.get('employee_name', 'Unknown')} ({case.get('employee_id', 'N/A')})"
            )
            with st.expander(title):
                st.write(f"**Created:** {case.get('created_at', 'N/A')}")
                st.write(f"**Confidence:** {case.get('confidence', 0.0):.0%}")
                st.write(f"**Escalation Reason:** {case.get('escalation_reason') or case.get('human_reason') or 'N/A'}")
                st.write("**Employee Request:**")
                st.info(case.get("request", ""))

                st.write("**Agent Proposed Response:**")
                proposed = (case.get("proposed_response") or "").strip()
                if proposed:
                    st.info(proposed)
                else:
                    st.warning("No proposed response was captured for this escalation.")

                if case.get("reasoning"):
                    with st.expander("Agent Reasoning", expanded=False):
                        st.caption(case.get("reasoning", ""))

                decision = st.selectbox(
                    "Admin Decision",
                    [
                        "Approve agent proposed response",
                        "Override with corrected decision",
                        "Escalate to specialist team",
                    ],
                    key=f"decision_{case.get('case_id')}"
                )

                final_response = ""
                if decision == "Approve agent proposed response":
                    final_response = st.text_area(
                        "Final response to employee (natural language)",
                        value=proposed,
                        key=f"approved_response_{case.get('case_id')}",
                        help="This exact response will be shown to the employee and reused as learning guidance."
                    )
                elif decision == "Override with corrected decision":
                    final_response = st.text_area(
                        "Corrected response for this situation (required)",
                        key=f"override_response_{case.get('case_id')}",
                        placeholder=(
                            "Write the exact natural-language response the agent should give in similar future cases. "
                            "Example: Please share details by email with HR so a human specialist can review this request."
                        ),
                        help="Use clear natural language because this is stored as reusable policy guidance."
                    )
                else:
                    final_response = st.text_area(
                        "Specialist escalation response (natural language)",
                        value=(
                            "Your request requires specialist HR review. "
                            "I have escalated it to the specialist team for manual handling."
                        ),
                        key=f"specialist_response_{case.get('case_id')}",
                        help="This response is sent to the employee and used as a learning pattern for specialist escalation."
                    )

                reason = st.text_area(
                    "Decision rationale",
                    key=f"reason_{case.get('case_id')}",
                    placeholder="Explain why this decision should be reused for similar future cases."
                )

                if st.button("Save Decision", key=f"save_{case.get('case_id')}", type="primary"):
                    if not final_response.strip():
                        st.error("Please provide a natural-language final response for the employee.")
                    elif not reason.strip():
                        st.error("Please provide rationale so the agent can learn from this decision.")
                    else:
                        decision_type = {
                            "Approve agent proposed response": "approve_proposed",
                            "Override with corrected decision": "override_corrected",
                            "Escalate to specialist team": "escalate_specialist",
                        }.get(decision, "custom")

                        result = orch.resolve_escalation(
                            case_id=case.get("case_id"),
                            admin_decision=final_response.strip(),
                            reason=reason.strip(),
                            resolved_by="Admin",
                            decision_type=decision_type,
                        )
                        if result.get("status") == "success":
                            st.success("Decision saved and learning memory updated.")
                            st.rerun()
                        else:
                            st.error(result.get("message", "Failed to resolve escalation."))

    if resolved_cases:
        with st.expander(f"Resolved Cases ({len(resolved_cases)})", expanded=False):
            for case in resolved_cases[:50]:
                st.write(
                    f"- {case.get('case_id')} | {case.get('agent_label')} | "
                    f"Type: {case.get('admin_decision_type', 'N/A')} | "
                    f"Decision: {case.get('admin_decision')} | Learning: {case.get('learning_recorded')}"
                )


def _admin_assistant():
    st.header("🤖 Admin Assistant")
    st.caption("Use this assistant to monitor escalations and apply quick admin decisions.")

    chat_key = "admin_assistant_chat"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    for msg in st.session_state[chat_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    with st.expander("Supported commands", expanded=False):
        st.markdown("- show open escalations")
        st.markdown("- show escalation stats")
        st.markdown("- resolve ESC-<id> approve because <reason> (approve agent proposed response)")
        st.markdown("- resolve ESC-<id> override because <reason>")
        st.markdown("- resolve ESC-<id> escalate because <reason>")

    if prompt := st.chat_input("Ask admin assistant..."):
        st.session_state[chat_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        response = _run_admin_assistant(prompt)
        st.session_state[chat_key].append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)


def _run_admin_assistant(prompt: str) -> str:
    orch = st.session_state.orchestrator
    text = prompt.strip()
    lower = text.lower()

    if "show open escalation" in lower or "open escalations" in lower:
        open_cases = orch.get_escalation_queue(status="Open")
        if not open_cases:
            return "No open escalations."

        top = list(reversed(open_cases))[:5]
        lines = [f"Open escalations: {len(open_cases)}"]
        for c in top:
            lines.append(
                f"- {c.get('case_id')} | {c.get('agent_label')} | "
                f"{c.get('employee_name', 'Unknown')} | reason: {c.get('escalation_reason') or c.get('human_reason') or 'N/A'}"
            )
        return "\n".join(lines)

    if "show escalation stats" in lower or "escalation stats" in lower:
        m = orch.get_escalation_metrics()
        return f"Escalations -> Open: {m['open']}, Resolved: {m['resolved']}, Total: {m['total']}"

    if lower.startswith("resolve "):
        m = re.search(r"(ESC-\d+)", text, flags=re.IGNORECASE)
        if not m:
            return "Could not find escalation ID. Use format: resolve ESC-<id> approve because <reason>"

        case_id = m.group(1).upper()
        case = next((c for c in orch.get_escalation_queue() if c.get("case_id") == case_id), None)
        if not case:
            return f"Escalation case {case_id} not found."

        if " override " in f" {lower} ":
            decision_type = "override_corrected"
            final_response = (
                "Your request has been reviewed by admin. "
                "Please share complete details with HR by email so the team can process this safely."
            )
        elif " escalate " in f" {lower} ":
            decision_type = "escalate_specialist"
            final_response = (
                "Your request requires specialist review. "
                "It has been escalated to the specialist team for manual handling."
            )
        else:
            decision_type = "approve_proposed"
            final_response = (case.get("proposed_response") or "").strip() or (
                "Your request has been reviewed and approved by admin."
            )

        reason = "Resolved by admin assistant command"
        if " because " in lower:
            reason = text.split(" because ", 1)[1].strip() or reason

        result = orch.resolve_escalation(
            case_id,
            final_response,
            reason,
            resolved_by="Admin",
            decision_type=decision_type,
        )
        if result.get("status") != "success":
            return result.get("message", "Could not resolve escalation.")
        return f"Resolved {case_id}. Natural-language decision saved to learning memory."

    return (
        "I can help with escalation operations. Try: 'show open escalations', "
        "'show escalation stats', or 'resolve ESC-<id> approve because <reason>'."
    )
