"""Compliance Portal — Violations, training, documents"""
import streamlit as st
import datetime


def show_compliance_portal():
    comp = st.session_state.agents['compliance']
    db = st.session_state.db
    st.header("📜 Compliance Management")
    tab1, tab2, tab3 = st.tabs(["⚠️ Violations", "📚 Training", "🔍 Audit"])

    with tab1:
        _violation_management(comp, db)
    with tab2:
        _training_management(comp, db)
    with tab3:
        _compliance_audit(comp, db)


def _violation_management(comp, db):
    st.subheader("Report Violation")
    with st.form("report_violation"):
        reported_by = st.text_input("Reported By")
        category = st.selectbox("Category",
                                ["Security", "Data Privacy", "Harassment",
                                 "Ethics", "Safety", "Financial", "Other"])
        severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
        emp_id = st.selectbox("Employee (optional)",
                              ["N/A"] + list(db.employees.keys()))
        description = st.text_area("Description")
        if st.form_submit_button("Report", type="primary"):
            eid = emp_id if emp_id != "N/A" else None
            result = comp.report_violation(reported_by, category, description, severity, eid)
            st.success(f"✅ Violation {result['violation_id']} reported")

    st.subheader("Open Violations")
    violations = db.get_all_violations() if hasattr(db, 'get_all_violations') else []
    for v in violations:
        if v.status == "Open":
            sev_icon = "🔴" if v.severity in ("High","Critical") else "🟡"
            with st.expander(f"{sev_icon} {v.violation_id} — {v.category} ({v.severity})"):
                st.write(f"**Description:** {v.description}")
                st.write(f"**Reported by:** {v.reported_by}")
                resolution = st.text_input("Resolution", key=f"vres_{v.violation_id}")
                if st.button("Resolve", key=f"vresolve_{v.violation_id}"):
                    comp.resolve_violation(v.violation_id, resolution)
                    st.success("✅ Resolved")
                    st.rerun()


def _training_management(comp, db):
    st.subheader("Schedule Training")
    with st.form("schedule_training"):
        emp_id = st.selectbox("Employee", list(db.employees.keys()))
        training_type = st.selectbox("Training Type",
                                     ["Code of Conduct", "Data Privacy", "Anti-Harassment",
                                      "Security Awareness", "Workplace Safety", "Ethics"])
        due_date = st.date_input("Due Date",
                                 datetime.date.today() + datetime.timedelta(days=30))
        mandatory = st.checkbox("Mandatory", value=True)
        if st.form_submit_button("Schedule", type="primary"):
            result = comp.schedule_training(emp_id, training_type,
                                            due_date.strftime("%Y-%m-%d"), mandatory)
            st.success(f"✅ Training {result['training_id']} scheduled")

    st.subheader("Training Status")
    for emp_id in db.employees:
        result = comp.get_training_status(employee_id=emp_id)
        if result['status'] == 'success' and result.get('trainings'):
            with st.expander(f"{db.employees[emp_id].name} ({emp_id})"):
                for t in result['trainings']:
                    status_icon = "✅" if t['status'] == "Completed" else "⏳"
                    st.write(f"{status_icon} {t['type']} — {t['status']} (due: {t['due']})")


def _compliance_audit(comp, db):
    st.subheader("Run Compliance Audit")
    scope = st.selectbox("Audit Scope", ["full", "training", "violations"])
    if st.button("Run Audit", type="primary"):
        result = comp.run_compliance_audit(scope)
        if result['compliance_status'] == "COMPLIANT":
            st.success("✅ All compliant!")
        else:
            st.warning(f"⚠️ {result['findings_count']} issue(s) found")
        for f in result.get('findings', []):
            st.write(f"• {f}")
        st.json(result)

    st.subheader("Ask Compliance Question")
    question = st.text_input("Ask about compliance policies...")
    if st.button("Ask") and question:
        result = comp.ask_compliance_policy(question)
        st.write(result.get('answer', 'No answer available'))
