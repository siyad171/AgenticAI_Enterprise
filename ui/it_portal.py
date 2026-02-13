"""IT Portal — Ticket management, access control, assets"""
import streamlit as st
import datetime


def show_it_portal():
    it = st.session_state.agents['it']
    db = st.session_state.db
    st.header("🖥️ IT Management")
    tab1, tab2, tab3 = st.tabs(["🎫 Tickets", "🔐 Access", "💻 Assets"])

    with tab1:
        _ticket_management(it, db)
    with tab2:
        _access_management(it, db)
    with tab3:
        _asset_tracking(it, db)


def _ticket_management(it, db):
    st.subheader("Create IT Ticket")
    with st.form("create_ticket"):
        emp_id = st.selectbox("Employee", list(db.employees.keys()))
        category = st.selectbox("Category",
                                ["Hardware", "Software", "Network", "Security", "Other"])
        priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
        description = st.text_area("Description")
        if st.form_submit_button("Create Ticket", type="primary"):
            result = it.create_ticket(emp_id, category, description, priority)
            if result['status'] == 'success':
                st.success(f"✅ Ticket {result['ticket_id']} created")
                if result.get('suggestion'):
                    st.info(f"💡 Suggestion: {result['suggestion']}")

    st.subheader("Open Tickets")
    tickets = getattr(db, 'it_tickets', {})
    for tid, ticket in tickets.items():
        status_color = "🟢" if ticket.status == "Resolved" else "🔴" if ticket.priority == "Critical" else "🟡"
        with st.expander(f"{status_color} {tid} — {ticket.category} ({ticket.status})"):
            st.write(f"**Priority:** {ticket.priority} | **Employee:** {ticket.employee_id}")
            st.write(f"**Description:** {ticket.description}")
            if ticket.status == "Open":
                resolution = st.text_input("Resolution", key=f"res_{tid}")
                if st.button("Resolve", key=f"resolve_{tid}"):
                    it.resolve_ticket(tid, resolution)
                    st.success("✅ Resolved")
                    st.rerun()


def _access_management(it, db):
    st.subheader("Grant Access")
    with st.form("grant_access"):
        emp_id = st.selectbox("Employee", list(db.employees.keys()), key="access_emp")
        system = st.selectbox("System", ["Email", "VPN", "JIRA", "Slack", "GitHub", "AWS Console"])
        level = st.selectbox("Access Level", ["Standard", "Admin", "Read-Only"])
        if st.form_submit_button("Grant Access", type="primary"):
            result = it.grant_access(emp_id, system, level)
            st.success(f"✅ Access granted: {result['record_id']}")

    st.subheader("Revoke Access")
    with st.form("revoke_access"):
        emp_id = st.selectbox("Employee", list(db.employees.keys()), key="revoke_emp")
        system = st.text_input("System to revoke")
        reason = st.text_input("Reason")
        if st.form_submit_button("Revoke Access"):
            result = it.revoke_access(emp_id, system, reason)
            st.success(f"✅ Revoked: {result['revoked']}")


def _asset_tracking(it, db):
    st.subheader("Track Assets")
    search_by = st.radio("Search by", ["Employee ID", "Asset ID"])
    if search_by == "Employee ID":
        emp_id = st.selectbox("Employee", list(db.employees.keys()), key="asset_emp")
        if st.button("Search"):
            result = it.track_asset(employee_id=emp_id)
            if result['status'] == 'success':
                for a in result.get('assets', []):
                    st.write(f"• {a['asset_id']} — {a['type']} ({a['status']})")
            else:
                st.info("No assets found")
    else:
        asset_id = st.text_input("Asset ID")
        if st.button("Search", key="asset_search"):
            result = it.track_asset(asset_id=asset_id)
            if result['status'] == 'success':
                st.json(result['asset'])
            else:
                st.error(result.get('message', 'Not found'))
