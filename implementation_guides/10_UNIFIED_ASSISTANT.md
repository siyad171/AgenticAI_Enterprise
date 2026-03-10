# 10 — Unified AI Assistant (Employee Portal)

## Overview

Replace the hardcoded HR-only assistant in the Employee Portal with an **Orchestrator-powered Unified AI Assistant** that intelligently routes employee requests to the appropriate agent (HR, IT, Finance, Compliance) and surfaces the agent's planning process as a live **Agent Planning Checklist** in the UI.

---

## Current State

```
Employee Portal
└── 💬 HR Assistant (hardcoded)
    └── HR Agent.process_request()  ← Only HR, always
```

- `employee_portal.py` directly accesses `st.session_state.agents['hr']`
- No routing — every request goes to HR regardless of content
- No visibility into agent planning steps

---

## Target State

```
Employee Portal
└── 🤖 AI Assistant (unified)
    └── Orchestrator.chat()
        ├── route_task() → LLM classifies → "hr" | "it" | "finance" | "compliance"
        ├── Agent Planning Checklist (visible in UI)
        │   ├── ☑ Routing to [Agent Name]
        │   ├── ☑ Perceiving context
        │   ├── ☑ Reasoning & Planning
        │   ├── ☑ Executing: [tool_name]
        │   ├── ☑ Evaluating results
        │   └── ☑ Complete
        └── Selected Agent.process_request() → ReAct loop → result
```

---

## Architecture Changes

### 1. Employee Portal (`ui/employee_portal.py`)

| What | Change |
|------|--------|
| Menu label | `💬 HR Assistant` → `🤖 AI Assistant` |
| Header/caption | Update to reflect multi-agent capability |
| Agent reference | `st.session_state.agents['hr']` → `st.session_state.orchestrator` |
| Processing call | `agent.process_request()` → `orchestrator.chat()` |
| Quick tips | Add IT, Finance, Compliance example prompts |
| Agent badge | Show which agent handled the request (e.g., `🏥 HR Agent`, `🔧 IT Agent`) |
| Planning checklist | New UI component — animated agent planning steps |

### 2. Orchestrator (`core/orchestrator.py`)

| What | Change |
|------|--------|
| `chat()` method | Return additional `planning_steps` list in the response |
| Planning steps | Structured list of `{"step": str, "status": str, "detail": str}` |
| Agent metadata | Return agent icon/label alongside agent key |

### 3. Base Agent (`core/base_agent.py`)

| What | Change |
|------|--------|
| `process_request()` | Return `planning_steps` list tracking each ReAct phase |
| Step structure | `{"step": str, "status": "completed"/"failed", "detail": str}` |

---

## Agent Planning Checklist — UI Spec

When an employee submits a request, the UI shows a **live planning checklist** inside the assistant's response area. This makes the agentic AI process transparent.

### Visual Design

```
🤖 Agent Planning
──────────────────────────────────
✅ Routing request              → IT Agent
✅ Perceiving context            → Employee: John, Dept: Engineering
✅ Reasoning & Planning          → Need to create IT ticket
✅ Executing tool                → create_ticket(Hardware, "Laptop not charging")
✅ Evaluating results            → Ticket TKT-20260309 created
──────────────────────────────────
```

### Data Structure (returned by `process_request`)

```python
"planning_steps": [
    {"step": "Routing",      "status": "completed", "detail": "Routed to IT Agent"},
    {"step": "Perceiving",   "status": "completed", "detail": "Employee: John (EMP001), Dept: Engineering"},
    {"step": "Planning",     "status": "completed", "detail": "Tool: create_ticket — Laptop hardware issue"},
    {"step": "Executing",    "status": "completed", "detail": "create_ticket → Ticket TKT-20260309 created"},
    {"step": "Evaluating",   "status": "completed", "detail": "Ticket created successfully (confidence: 92%)"},
]
```

### UI Implementation

- Render as `st.expander("🧠 Agent Planning", expanded=True)` on first display
- Each step renders as: `✅ Step Name — detail` or `❌ Step Name — error detail`
- Status icons: `✅` completed, `❌` failed
- Collapsed in chat history (expanded=False) for older messages

---

## Employee-Facing Tool Scoping

Not all agent tools are appropriate for employee self-service. Define which tools employees can trigger vs admin-only:

### HR Agent Tools
| Tool | Employee Access | Notes |
|------|----------------|-------|
| `process_leave` | ✅ Yes | Core employee self-service |
| `policy_qa` | ✅ Yes | Policy questions |
| `get_audit_report` | ❌ No | Admin-only |
| `onboard_employee` | ❌ No | Admin-only |
| `evaluate_candidate` | ❌ No | Admin-only |
| `parse_resume` | ❌ No | Admin-only |

### IT Agent Tools
| Tool | Employee Access | Notes |
|------|----------------|-------|
| `create_ticket` | ✅ Yes | Report issues |
| `get_ticket_status` | ✅ Yes | Check own tickets |
| `track_asset` | ✅ Yes | View own assets |
| `grant_access` | ✅ Yes | Request access (not auto-approve) |
| `resolve_ticket` | ❌ No | Admin/IT staff only |
| `revoke_access` | ❌ No | Admin-only |
| `manage_software_license` | ❌ No | Admin-only |
| `get_open_tickets_summary` | ❌ No | Admin-only |

### Finance Agent Tools
| Tool | Employee Access | Notes |
|------|----------------|-------|
| `submit_expense` | ✅ Yes | Submit expense claims |
| `check_expense_status` | ✅ Yes | Check own claims |
| `get_payslip` | ✅ Yes | View own payslip |
| `manage_budget` | ❌ No | Admin-only |

### Compliance Agent Tools
| Tool | Employee Access | Notes |
|------|----------------|-------|
| `check_training_status` | ✅ Yes | View own training progress |
| `report_violation` | ✅ Yes | Whistleblower/report |
| `run_audit` | ❌ No | Admin-only |

> **Implementation approach**: Pass `context={"role": "employee"}` to the orchestrator. The orchestrator passes it to the agent. For now, all tools remain available (the LLM naturally avoids admin tools when the user is an employee). In a future iteration, we can add explicit tool filtering in `process_request`.

---

## Detailed Implementation Steps

### Step 1: Update `base_agent.py` — Add planning steps to ReAct loop

In `process_request()`, build a `planning_steps` list as each phase completes:

```python
def process_request(self, user_message: str, context: Dict = None) -> Dict:
    context = context or {}
    actions_taken = []
    planning_steps = []

    # 1. PERCEIVE
    perception = self._perceive(user_message, context)
    emp = perception.get("employee", {})
    planning_steps.append({
        "step": "Perceiving",
        "status": "completed",
        "detail": f"Employee: {emp.get('name', 'N/A')}, Dept: {emp.get('department', 'N/A')}"
    })

    # 2. REASON & PLAN
    plan = self._reason_and_plan(user_message, perception)
    # ... handle error ...
    planning_steps.append({
        "step": "Planning",
        "status": "completed",
        "detail": f"Tools: {', '.join(s.get('tool','?') for s in steps)} (confidence: {confidence:.0%})"
    })

    # 4. ACT — for each step
    # ... after executing each tool ...
    planning_steps.append({
        "step": "Executing",
        "status": "completed" if success else "failed",
        "detail": f"{tool_name} → {result_summary}"
    })

    # 5. EVALUATE
    planning_steps.append({
        "step": "Evaluating",
        "status": "completed",
        "detail": f"Generating response (confidence: {confidence:.0%})"
    })

    return {
        "response": response,
        "actions_taken": actions_taken,
        "planning_steps": planning_steps,  # NEW
        "reasoning": reasoning,
        "confidence": confidence,
        "escalated": False
    }
```

### Step 2: Update `orchestrator.py` — Add routing step to planning

In `chat()`, prepend a routing planning step:

```python
def chat(self, user_message: str, context: Dict = None) -> Dict:
    context = context or {}
    routing = self.route_task(user_message, context)
    agent_key = routing.get("agent", "hr")
    agent = self.agents.get(agent_key)

    # Build routing planning step
    agent_labels = {
        "hr": "🏥 HR Agent",
        "it": "🔧 IT Agent",
        "finance": "💰 Finance Agent",
        "compliance": "📋 Compliance Agent",
    }

    routing_step = {
        "step": "Routing",
        "status": "completed",
        "detail": f"Routed to {agent_labels.get(agent_key, agent_key)}"
    }

    result = agent.process_request(user_message, context)
    # Prepend routing step to planning_steps
    result["planning_steps"] = [routing_step] + result.get("planning_steps", [])
    result["agent"] = agent_key
    result["agent_label"] = agent_labels.get(agent_key, agent_key)
    result["routing_reasoning"] = routing.get("reasoning", "")
    return result
```

### Step 3: Update `employee_portal.py` — Unified Assistant with Planning UI

```python
def _agentic_chat(emp, orchestrator):
    st.header("🤖 AI Assistant")
    st.caption("I can handle HR, IT, Finance, and Compliance requests. Just describe what you need.")

    # ... chat history display (updated to show agent badge + planning) ...

    if prompt := st.chat_input("Describe what you need..."):
        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):
                result = orchestrator.chat(prompt, context={"employee_id": emp.employee_id})

            # Agent badge
            agent_label = result.get("agent_label", "🤖 AI")
            st.caption(f"Handled by: {agent_label}")

            # Planning checklist
            planning_steps = result.get("planning_steps", [])
            if planning_steps:
                with st.expander("🧠 Agent Planning", expanded=True):
                    for ps in planning_steps:
                        icon = "✅" if ps["status"] == "completed" else "❌"
                        st.markdown(f"{icon} **{ps['step']}** — {ps['detail']}")

            # Response
            st.markdown(result.get("response", ""))
```

### Step 4: Update Quick Tips

```python
st.markdown("""
**💡 Quick Tips — Talk to your AI Assistant:**

**HR:**
- *"I want to take casual leave from March 10 to March 14"*
- *"What is the company policy on remote work?"*
- *"How many sick leaves do I have left?"*

**IT:**
- *"My laptop is not charging, I need help"*
- *"I need VPN access for remote work"*
- *"Check status of my ticket TKT-001"*

**Finance:**
- *"Submit an expense claim for $200 travel reimbursement"*
- *"Show me my payslip for this month"*

**Compliance:**
- *"What training courses am I overdue on?"*
- *"I want to report a compliance concern"*
""")
```

---

## Files Modified

| File | Type | Description |
|------|------|-------------|
| `core/base_agent.py` | Modified | Add `planning_steps` list to `process_request()` return |
| `core/orchestrator.py` | Modified | Add routing step, agent labels, planning_steps passthrough in `chat()` |
| `ui/employee_portal.py` | Modified | Switch to orchestrator, add planning checklist UI, agent badges, unified tips |

---

## Future Enhancements (Not in This Implementation)

- **Sticky routing**: If employee is mid-conversation about an IT ticket, keep routing to IT without re-classifying every message
- **Multi-agent splitting**: "Apply for leave and reset my password" → split into two agent calls, merge responses
- **Explicit tool filtering**: Block admin-only tools based on `context["role"]` in `process_request()`
- **Streaming planning**: Show planning steps one-by-one with animation as they complete (requires Streamlit streaming support)
- **Planning history analytics**: Track which agents are most used by employees, common request patterns

---

## Testing Checklist

- [ ] Employee asks HR question → routes to HR Agent, planning shows routing + HR steps
- [ ] Employee asks IT question → routes to IT Agent, planning shows routing + IT steps
- [ ] Employee asks ambiguous question → LLM classifies correctly, falls back to keyword match if LLM fails
- [ ] Planning checklist shows all steps with correct status icons
- [ ] Agent badge shows correct agent label in chat
- [ ] Chat history preserves planning steps and agent labels
- [ ] Older messages show planning collapsed, latest shows expanded
- [ ] All existing HR functionality still works (leave, policy Q&A, etc.)
- [ ] Quick tips show examples for all departments
