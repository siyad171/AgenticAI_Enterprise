"""Employee Portal — Agentic chat interface + profile"""
import streamlit as st
import datetime
from ui.utils import logout


def show_employee_portal():
    user = st.session_state.current_user
    emp_id = user.employee_id
    emp = st.session_state.db.get_employee(emp_id)
    agent = st.session_state.agents['hr']

    st.sidebar.title(f"👋 {emp.name}")
    page = st.sidebar.radio("Menu", [
        "🏠 Dashboard", "💬 HR Assistant", "👤 Profile"])
    if st.sidebar.button("🚪 Logout"):
        logout()

    if page == "🏠 Dashboard":
        _dashboard(emp)
    elif page == "💬 HR Assistant":
        _agentic_chat(emp, agent)
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
    **💡 Quick Tips — Talk to your HR Assistant:**
    - *"I want to take casual leave from March 10 to March 14"*
    - *"What is the company policy on remote work?"*
    - *"How many sick leaves do I have left?"*
    - *"Show me my leave history"*
    """)


def _agentic_chat(emp, agent):
    st.header("💬 HR Assistant")
    st.caption(f"🤖 Agentic AI — I can process leave requests, answer policy questions, look up your info, and more. Just describe what you need.")

    # Initialize chat history key per employee
    chat_key = f"hr_chat_{emp.employee_id}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # Display chat history
    for msg in st.session_state[chat_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # Show reasoning in an expander for transparency
            if msg["role"] == "assistant" and msg.get("reasoning"):
                with st.expander("🧠 Agent Reasoning", expanded=False):
                    st.caption(msg["reasoning"])
                if msg.get("actions"):
                    with st.expander("⚡ Actions Taken", expanded=False):
                        for a in msg["actions"]:
                            status_icon = "✅" if a.get("success") else "❌"
                            st.caption(f"{status_icon} {a['tool']}")

    # Chat input
    if prompt := st.chat_input("Describe what you need... (e.g., 'I want to take leave next week')"):
        # Append user message
        st.session_state[chat_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process through agentic ReAct loop
        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):
                result = agent.process_request(
                    prompt,
                    context={"employee_id": emp.employee_id}
                )

            response = result.get("response", "I couldn't process that. Please try again.")
            reasoning = result.get("reasoning", "")
            actions = result.get("actions_taken", [])
            confidence = result.get("confidence", 0)
            escalated = result.get("escalated", False)

            st.markdown(response)

            if reasoning:
                with st.expander("🧠 Agent Reasoning", expanded=False):
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
