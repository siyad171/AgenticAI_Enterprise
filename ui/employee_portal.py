"""Employee Portal — Dashboard, leave requests, policy Q&A"""
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
        "🏠 Dashboard", "📝 Leave Request", "❓ Policy Q&A", "👤 Profile"])
    if st.sidebar.button("🚪 Logout"):
        logout()

    if page == "🏠 Dashboard":
        _dashboard(emp)
    elif page == "📝 Leave Request":
        _leave_request(emp, agent)
    elif page == "❓ Policy Q&A":
        _policy_qa(emp, agent)
    elif page == "👤 Profile":
        _profile(emp)


def _dashboard(emp):
    st.header(f"Welcome, {emp.name}!")
    c1, c2, c3 = st.columns(3)
    c1.metric("Casual Leave", emp.leave_balance.get("Casual Leave", 0))
    c2.metric("Sick Leave", emp.leave_balance.get("Sick Leave", 0))
    c3.metric("Annual Leave", emp.leave_balance.get("Annual Leave", 0))


def _leave_request(emp, agent):
    st.header("📝 Request Leave")
    with st.form("leave_form"):
        leave_type = st.selectbox("Leave Type",
                                  ["Casual Leave", "Sick Leave", "Annual Leave", "Unpaid Leave"])
        c1, c2 = st.columns(2)
        start = c1.date_input("Start Date")
        end = c2.date_input("End Date")
        reason = st.text_area("Reason")
        submit = st.form_submit_button("Submit", type="primary")
        if submit:
            result = agent.process_leave_request(
                emp.employee_id, leave_type,
                start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), reason)
            if result.get("decision") == "Approved":
                st.success(f"✅ {result['message']}")
            elif result.get("decision") == "Pending":
                st.warning(f"⏳ {result['message']}")
            else:
                st.error(f"❌ {result['message']}")


def _policy_qa(emp, agent):
    st.header("❓ Ask HR Policy Question")
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg['role']):
            st.write(msg['content'])

    if prompt := st.chat_input("Ask a question about company policies..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        result = agent.ask_hr_policy_question(prompt, emp.employee_id)
        answer = result.get("answer", "Sorry, I couldn't process your question.")
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()


def _profile(emp):
    st.header("👤 My Profile")
    st.write(f"**Employee ID:** {emp.employee_id}")
    st.write(f"**Name:** {emp.name}")
    st.write(f"**Email:** {emp.email}")
    st.write(f"**Department:** {emp.department}")
    st.write(f"**Position:** {emp.position}")
    st.write(f"**Join Date:** {emp.join_date}")
