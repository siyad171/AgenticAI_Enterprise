"""IT Portal — Agentic chat interface for IT support"""
import streamlit as st
import datetime


def show_it_portal():
    it = st.session_state.agents['it']
    db = st.session_state.db
    st.header("🖥️ IT Management")
    tab1, tab2 = st.tabs(["💬 IT Assistant", "📊 Ticket Dashboard"])

    with tab1:
        _agentic_chat(it, db)
    with tab2:
        _ticket_dashboard(it, db)


def _agentic_chat(it, db):
    st.subheader("💬 IT Assistant")
    st.caption("🤖 Agentic AI — I can create tickets, manage access, track assets, resolve issues, and more. Just describe what you need.")

    chat_key = "it_chat_admin"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # Quick action suggestions
    with st.expander("💡 Example requests", expanded=False):
        st.markdown("""
        - *"Create a high priority ticket for John — his laptop won't boot"*
        - *"Grant EMP001 admin access to GitHub"*
        - *"Show me all open tickets"*
        - *"Revoke VPN access for EMP003, they left the company"*
        - *"What assets are assigned to EMP002?"*
        - *"Resolve ticket TKT... — replaced the hard drive"*
        """)

    # Display chat history
    for msg in st.session_state[chat_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("reasoning"):
                with st.expander("🧠 Agent Reasoning", expanded=False):
                    st.caption(msg["reasoning"])
                if msg.get("actions"):
                    with st.expander("⚡ Actions Taken", expanded=False):
                        for a in msg["actions"]:
                            status_icon = "✅" if a.get("success") else "❌"
                            st.caption(f"{status_icon} {a['tool']}")

    # Chat input
    if prompt := st.chat_input("Describe the IT issue or request..."):
        st.session_state[chat_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🤖 Analyzing..."):
                result = it.process_request(prompt, context={})

            response = result.get("response", "I couldn't process that. Please try again.")
            reasoning = result.get("reasoning", "")
            actions = result.get("actions_taken", [])
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

        st.session_state[chat_key].append({
            "role": "assistant", "content": response,
            "reasoning": reasoning, "actions": actions
        })

    if st.session_state[chat_key]:
        if st.button("🗑️ Clear Chat"):
            st.session_state[chat_key] = []
            st.rerun()


def _ticket_dashboard(it, db):
    """Read-only dashboard showing ticket status."""
    st.subheader("📊 Ticket Overview")
    tickets = getattr(db, 'it_tickets', {})

    if not tickets:
        st.info("No tickets yet. Use the IT Assistant to create one.")
        return

    # Metrics
    open_t = [t for t in tickets.values() if t.status == "Open"]
    resolved_t = [t for t in tickets.values() if t.status == "Resolved"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Open", len(open_t))
    c2.metric("Resolved", len(resolved_t))
    c3.metric("Total", len(tickets))

    # Ticket list
    for tid, ticket in tickets.items():
        status_color = "🟢" if ticket.status == "Resolved" else "🔴" if ticket.priority == "Critical" else "🟡"
        with st.expander(f"{status_color} {tid} — {ticket.category} ({ticket.status})"):
            st.write(f"**Priority:** {ticket.priority} | **Employee:** {ticket.employee_id}")
            st.write(f"**Description:** {ticket.description}")
            if hasattr(ticket, 'resolution') and ticket.resolution:
                st.write(f"**Resolution:** {ticket.resolution}")
            st.write(f"**Created:** {ticket.created_date}")
