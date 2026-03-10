"""Employee Portal — Agentic chat interface + profile"""
import streamlit as st
import datetime
from ui.utils import logout


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

    # Chat input
    if prompt := st.chat_input("Describe what you need... (e.g., 'I want to take leave next week' or 'My laptop is not working')"):
        # Append user message
        st.session_state[chat_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process through orchestrator → routes to correct agent
        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):
                result = orchestrator.chat(
                    prompt,
                    context={"employee_id": emp.employee_id}
                )

            response = result.get("response", "I couldn't process that. Please try again.")
            reasoning = result.get("reasoning", "")
            actions = result.get("actions_taken", [])
            confidence = result.get("confidence", 0)
            escalated = result.get("escalated", False)
            agent_label = result.get("agent_label", "🤖 AI")
            planning_steps = result.get("planning_steps", [])

            # Agent badge
            st.caption(f"Handled by: {agent_label}")

            # Planning checklist (expanded for latest message)
            if planning_steps:
                with st.expander("🧠 Agent Planning", expanded=True):
                    for ps in planning_steps:
                        icon = "✅" if ps["status"] == "completed" else "❌"
                        st.markdown(f"{icon} **{ps['step']}** — {ps['detail']}")

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
                st.warning("⚠️ This request has been escalated for human review.")

        # Save to history
        st.session_state[chat_key].append({
            "role": "assistant",
            "content": response,
            "reasoning": reasoning,
            "actions": actions,
            "planning_steps": planning_steps,
            "agent_label": agent_label,
            "confidence": confidence
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
