"""Employee Portal — Agentic chat interface + profile"""
import streamlit as st
import datetime
from ui.utils import logout


def _find_escalation_case(orchestrator, case_id: str):
    if not case_id:
        return None
    for case in orchestrator.get_escalation_queue():
        if case.get("case_id") == case_id:
            return case
    return None


def _render_escalation_updates(emp, orchestrator):
    cases = [
        c for c in orchestrator.get_escalation_queue()
        if c.get("employee_id") == emp.employee_id
    ]
    if not cases:
        return

    open_cases = [c for c in cases if c.get("status") == "Open"]
    resolved_cases = [c for c in cases if c.get("status") == "Resolved"]

    st.subheader("📌 Escalation Updates")
    if open_cases:
        st.warning(f"{len(open_cases)} request(s) are currently under human review.")
    if resolved_cases:
        st.success(f"{len(resolved_cases)} escalated request(s) have admin decisions.")

    latest = sorted(cases, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
    with st.expander("View latest escalation statuses", expanded=False):
        for case in latest:
            status = case.get("status", "Open")
            case_id = case.get("case_id", "N/A")
            created = case.get("created_at", "N/A")
            if status == "Resolved":
                st.markdown(f"**{case_id}** | Resolved")
                st.caption(f"Created: {created}")
                st.caption(f"Resolution Type: {case.get('admin_decision_type') or 'N/A'}")
                final_employee_response = case.get("employee_response") or case.get("admin_decision") or "N/A"
                st.caption(f"Final Response: {final_employee_response}")
                st.caption(f"Rationale: {case.get('admin_reason') or 'N/A'}")
                st.caption(f"Resolved At: {case.get('resolved_at') or 'N/A'}")
            else:
                st.markdown(f"**{case_id}** | Open")
                st.caption(f"Created: {created}")
                st.caption(f"Reason: {case.get('escalation_reason') or case.get('human_reason') or 'N/A'}")


def show_employee_portal():
    user = st.session_state.current_user
    emp_id = user.employee_id
    emp = st.session_state.db.get_employee(emp_id)
    orchestrator = st.session_state.orchestrator

    st.sidebar.title(f"👋 {emp.name}")
    page = st.sidebar.radio("Menu", [
        "🏠 Dashboard", "🤖 AI Assistant", "👤 Profile"])
    if st.sidebar.button("🚪 Logout"):
        logout()

    if page == "🏠 Dashboard":
        _dashboard(emp)
    elif page == "🤖 AI Assistant":
        _agentic_chat(emp, orchestrator)
    elif page == "👤 Profile":
        _profile(emp)


def _dashboard(emp):
    st.header(f"Welcome, {emp.name}!")
    c1, c2, c3 = st.columns(3)
    c1.metric("Casual Leave", emp.leave_balance.get("Casual Leave", 0))
    c2.metric("Sick Leave", emp.leave_balance.get("Sick Leave", 0))
    c3.metric("Annual Leave", emp.leave_balance.get("Annual Leave", 0))

    # Quick tips
    st.divider()
    st.markdown("""
    **💡 Quick Tips — Talk to your AI Assistant:**

    **🏥 HR:**
    - *"I want to take casual leave from March 10 to March 14"*
    - *"What is the company policy on remote work?"*
    - *"How many sick leaves do I have left?"*

    **🔧 IT:**
    - *"My laptop is not charging, I need help"*
    - *"I need VPN access for remote work"*
    - *"Check status of my ticket TKT-001"*

    **💰 Finance:**
    - *"Submit an expense claim for $200 travel reimbursement"*

    **📋 Compliance:**
    - *"What training courses am I overdue on?"*
    """)


def _agentic_chat(emp, orchestrator):
    st.header("🤖 AI Assistant")
    st.caption("I can handle HR, IT, Finance, and Compliance requests. Just describe what you need.")
    _render_escalation_updates(emp, orchestrator)

    # Initialize chat history key per employee
    chat_key = f"ai_chat_{emp.employee_id}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # Display chat history
    for msg in st.session_state[chat_key]:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                # Agent badge
                agent_label = msg.get("agent_label", "")
                if agent_label:
                    st.caption(f"Handled by: {agent_label}")

                # Planning checklist (collapsed for history)
                planning = msg.get("planning_steps", [])
                if planning:
                    with st.expander("🧠 Agent Planning", expanded=False):
                        for ps in planning:
                            icon = "✅" if ps["status"] == "completed" else "❌"
                            st.markdown(f"{icon} **{ps['step']}** — {ps['detail']}")

            st.markdown(msg["content"])

            if msg["role"] == "assistant":
                if msg.get("reasoning"):
                    with st.expander("💭 Reasoning", expanded=False):
                        st.caption(msg["reasoning"])
                if msg.get("actions"):
                    with st.expander("⚡ Actions Taken", expanded=False):
                        for a in msg["actions"]:
                            status_icon = "✅" if a.get("success") else "❌"
                            st.caption(f"{status_icon} {a['tool']}")
                escalation_id = msg.get("escalation_id", "")
                if escalation_id:
                    case = _find_escalation_case(orchestrator, escalation_id)
                    if case and case.get("status") == "Resolved":
                        final_employee_response = case.get("employee_response") or case.get("admin_decision") or "N/A"
                        st.success(
                            f"Escalation {escalation_id} resolved by admin. "
                            f"Final response: {final_employee_response}"
                        )
                        if case.get("admin_reason"):
                            st.caption(f"Rationale: {case.get('admin_reason')}")
                    else:
                        st.warning(f"Escalation {escalation_id} is still under human review.")

    # Chat input
    if prompt := st.chat_input("Describe what you need... (e.g., 'I want to take leave next week' or 'My laptop is not working')"):
        # Append user message
        st.session_state[chat_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process through orchestrator → streams steps one by one as they complete
        with st.chat_message("assistant"):
            badge_placeholder = st.empty()
            planning_placeholder = st.empty()

            displayed_steps = []
            result_data = {}

            for item in orchestrator.chat_stream(
                prompt,
                context={"employee_id": emp.employee_id}
            ):
                if item["type"] == "step":
                    displayed_steps.append(item["step"])
                    # Re-render the live planning list with the new step appended
                    with planning_placeholder.container():
                        st.markdown("**🧠 Agent Planning**")
                        for ps in displayed_steps:
                            icon = "✅" if ps["status"] == "completed" else "❌"
                            st.markdown(f"{icon} **{ps['step']}** — {ps['detail']}")
                        st.caption("⏳ Processing...")
                elif item["type"] == "result":
                    result_data = item

            response = result_data.get("response", "I couldn't process that. Please try again.")
            reasoning = result_data.get("reasoning", "")
            actions = result_data.get("actions_taken", [])
            confidence = result_data.get("confidence", 0)
            escalated = result_data.get("escalated", False)
            escalation_id = result_data.get("escalation_id", "")
            agent_label = result_data.get("agent_label", "🤖 AI")
            planning_steps = displayed_steps

            # Set agent badge now that we know which agent handled it
            badge_placeholder.caption(f"Handled by: {agent_label}")

            # Collapse live planning view into a tidy expander
            if displayed_steps:
                with planning_placeholder.container():
                    with st.expander("🧠 Agent Planning", expanded=False):
                        for ps in displayed_steps:
                            icon = "✅" if ps["status"] == "completed" else "❌"
                            st.markdown(f"{icon} **{ps['step']}** — {ps['detail']}")
            else:
                planning_placeholder.empty()

            st.markdown(response)

            if reasoning:
                with st.expander("💭 Reasoning", expanded=False):
                    st.caption(reasoning)
            if actions:
                with st.expander("⚡ Actions Taken", expanded=False):
                    for a in actions:
                        status_icon = "✅" if a.get("success") else "❌"
                        st.caption(f"{status_icon} {a['tool']}")
            if escalated:
                if escalation_id:
                    st.warning(f"⚠️ This request has been escalated for human review. Case ID: {escalation_id}")
                else:
                    st.warning("⚠️ This request has been escalated for human review.")

        # Save to history
        st.session_state[chat_key].append({
            "role": "assistant",
            "content": response,
            "reasoning": reasoning,
            "actions": actions,
            "planning_steps": planning_steps,
            "agent_label": agent_label,
            "confidence": confidence,
            "escalated": escalated,
            "escalation_id": escalation_id,
        })

    # Clear chat button
    if st.session_state[chat_key]:
        if st.sidebar.button("🗑️ Clear Chat"):
            st.session_state[chat_key] = []
            st.rerun()


def _profile(emp):
    st.header("👤 My Profile")
    st.write(f"**Employee ID:** {emp.employee_id}")
    st.write(f"**Name:** {emp.name}")
    st.write(f"**Email:** {emp.email}")
    st.write(f"**Department:** {emp.department}")
    st.write(f"**Position:** {emp.position}")
    st.write(f"**Join Date:** {emp.join_date}")
