"""Orchestrator Dashboard — Workflows, agent status, goals"""
import streamlit as st


def show_orchestrator_dashboard():
    orch = st.session_state.orchestrator
    st.header("🔄 Orchestrator Dashboard")

    # Agent statuses
    st.subheader("Agent Status")
    agents = st.session_state.agents
    for name, agent in agents.items():
        caps = agent.get_capabilities()
        st.write(f"**{agent.agent_name}:** {', '.join(caps)}")

    st.divider()

    # Active workflows
    st.subheader("Available Workflows")
    workflows = ["New Hire Onboarding", "Employee Exit", "Expense Claim", "Security Incident"]
    for wf in workflows:
        st.write(f"• {wf}")

    st.divider()

    # Route a task
    st.subheader("Route a Task")
    task = st.text_input("Describe the task")
    if st.button("Route", type="primary") and task:
        with st.spinner("Routing task..."):
            result = orch.route_task(task)
            st.json(result)

    st.divider()

    # Execute workflow
    st.subheader("Execute Workflow")
    wf_type = st.selectbox("Workflow", ["new_hire", "employee_exit",
                                         "expense_claim", "security_incident"])
    context_str = st.text_area("Context (JSON)", '{"employee_id": "EMP001"}')
    if st.button("Execute Workflow"):
        import json
        try:
            context = json.loads(context_str)
            result = orch.execute_workflow(wf_type, context)
            st.json(result)
        except json.JSONDecodeError:
            st.error("Invalid JSON context")

    st.divider()

    # Dashboard metrics
    st.subheader("System Metrics")
    dashboard = orch.get_dashboard()
    st.json(dashboard)
