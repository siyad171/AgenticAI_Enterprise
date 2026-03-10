# Agentic AI Testing Guide

## What Makes This System "Agentic"

Your agents now follow the **ReAct (Reasoning + Acting)** loop:

```
User Message → PERCEIVE → REASON & PLAN → ACT (call tools) → EVALUATE → LEARN → RESPOND
```

Instead of clicking buttons and filling forms, users **describe what they need in natural language**, and the agent **thinks, decides, and acts autonomously**.

---

## How to Start the App

```bash
streamlit run ui/app.py
```

---

## Testing the Unified AI Assistant (Employee Portal)

The Employee Portal now has a **Unified AI Assistant** powered by the Orchestrator.
Instead of only handling HR queries, it **intelligently routes** requests to the correct agent
(HR, IT, Finance, Compliance) and shows a **live Agent Planning checklist** so you can see
exactly how the agent thinks, plans, and acts.

### Login
- **Username:** `john` | **Password:** `john123` (Employee role)

### Where to Test
- Sidebar → **🤖 AI Assistant**

---

### Test 1: HR Routing — Leave Request

**Type this in the chat:**
```
I want to take casual leave from 2026-03-10 to 2026-03-12 for a family function
```

**What to Expect:**
- 🤖 Agent shows "Thinking..." spinner
- **Agent badge** appears: `Handled by: 🏥 HR Agent`
- **🧠 Agent Planning** checklist (expanded) shows:
  - ✅ **Routing** — Routed to 🏥 HR Agent
  - ✅ **Perceiving** — Employee: John, Dept: Engineering
  - ✅ **Planning** — Tools: process_leave_request (confidence: 90%)
  - ✅ **Executing** — process_leave_request → Approved
  - ✅ **Evaluating** — Generating response (confidence: 90%)
- Agent **responds**: tells you the leave is approved (3 days ≤ 10 day auto-approve limit)
- You can expand **💭 Reasoning** to see the full reasoning chain
- You can expand **⚡ Actions Taken** to see which tools were called

**Expected Result:**
- Leave status: **Approved** (3 days, auto-approved)
- Confidence: ~0.90–0.95
- Routing: HR Agent
- Planning checklist: all ✅

---

### Test 2: IT Routing — Laptop Issue

**Type:**
```
My laptop is not charging and the screen flickers sometimes
```

**What to Expect:**
- **Agent badge**: `Handled by: 🔧 IT Agent`
- **🧠 Agent Planning** shows:
  - ✅ **Routing** — Routed to 🔧 IT Agent
  - ✅ **Perceiving** — Employee: John, Dept: Engineering
  - ✅ **Planning** — Tools: create_ticket (confidence: ~85%)
  - ✅ **Executing** — create_ticket → Ticket TKT... created
  - ✅ **Evaluating** — Generating response
- Agent creates an IT support ticket and gives you a ticket ID
- Resolution suggestions from the LLM (e.g., check charger, run diagnostics)

**Expected Result:**
- Ticket created with category **Hardware**, priority **Medium** or **High**
- Routing: IT Agent
- Planning checklist: all ✅

---

### Test 3: IT Routing — Access Request

**Type:**
```
I need VPN access for remote work
```

**What to Expect:**
- **Agent badge**: `Handled by: 🔧 IT Agent`
- Agent calls `grant_access` tool with system=VPN
- Planning checklist shows routing to IT, then grant_access execution

---

### Test 4: IT Routing — Ticket Status Check

**Type (use a ticket ID from Test 2):**
```
Check the status of my ticket TKT20260309...
```

**What to Expect:**
- Routes to IT Agent
- Calls `get_ticket_status` tool
- Returns ticket details (status, category, priority, description)

---

### Test 5: HR Routing — Policy Question

**Type:**
```
What is the company's remote work policy?
```

**What to Expect:**
- **Agent badge**: `Handled by: 🏥 HR Agent`
- Routes to HR (policy-related keyword)
- Agent may call `ask_hr_policy_question` tool OR answer directly
- Planning shows: Routing → HR, Perceiving, Planning (possibly no_tool_needed), Evaluating

---

### Test 6: HR Routing — Leave Balance

**Type:**
```
Show me my leave balance
```

**What to Expect:**
- Routes to HR Agent
- Returns your current leave balances
- If you took leave in Test 1, casual balance will be reduced

---

### Test 7: Leave Request That Needs Approval

**Type:**
```
I need annual leave from 2026-03-05 to 2026-03-25 for international travel
```

**What to Expect:**
- Routes to HR Agent
- Agent reasons that 21 days > 10 day auto-approve limit → requires manager approval
- Leave status: **Pending** (requires manager approval)
- Planning checklist shows all steps completed

---

### Test 8: Ambiguous Request (Tests Reasoning)

**Type:**
```
I'm not feeling well, can I take tomorrow off?
```

**What to Expect:**
- Routes to HR Agent
- Agent **reasons**: "not feeling well" → sick leave, "tomorrow" → calculates tomorrow's date
- Agent calls `process_leave_request` with leave_type="Sick Leave"
- Planning shows the full reasoning chain

---

### Test 9: Escalation (Low Confidence)

**Type:**
```
Can you fire my manager?
```

**What to Expect:**
- Agent recognizes this is outside its capabilities
- Confidence drops below threshold (0.6)
- Planning checklist shows: Routing → ✅, Perceiving → ✅, Planning → ✅, **Escalation → ✅**
- Response: "I've analyzed your request but I'm not confident enough to act autonomously..."
- Shows **⚠️ This request has been escalated for human review**

---

### Test 10: Cross-Domain Routing Verification

Test these one by one to verify routing works for each agent:

| # | Message | Expected Agent |
|---|---------|----------------|
| a | *"Submit an expense claim for $150 taxi reimbursement"* | 💰 Finance Agent |
| b | *"What compliance trainings am I overdue on?"* | 📋 Compliance Agent |
| c | *"I need to report a security concern about data handling"* | 📋 Compliance Agent |
| d | *"My email is not working"* | 🔧 IT Agent |
| e | *"Show me my leave history"* | 🏥 HR Agent |

For each, verify:
- ✅ Correct agent badge appears
- ✅ Planning checklist starts with correct Routing step
- ✅ Agent responds appropriately

---

### Test 11: Planning Checklist in Chat History

1. Send any request (e.g., *"How many sick leaves do I have?"*)
2. Verify the **🧠 Agent Planning** expander is **expanded** on the latest message
3. Send a second request (e.g., *"I need VPN access"*)
4. Scroll up — the first message's planning should now be **collapsed**
5. The latest message's planning should be **expanded**

---

## Testing the IT Agent (Admin Portal)

### Login
- **Username:** `admin` | **Password:** `admin123` (Admin role)

### Where to Test
- Sidebar → **🖥️ IT** → **💬 IT Assistant** tab

---

### Test 8: Create IT Ticket via Natural Language

**Type:**
```
EMP002's laptop screen is flickering badly, this is urgent
```

**What to Expect:**
- Agent **reasons**: hardware issue, urgent → High priority
- Agent **acts**: calls `create_ticket` with category=Hardware, priority=High
- Agent **responds**: ticket ID, plus troubleshooting suggestions from LLM
- Expand reasoning to see: "This indicates a hardware issue that needs immediate attention"

**Expected Result:**
- Ticket created with status **Open**, priority **High**
- Actions: `create_ticket ✅`

---

### Test 9: Grant System Access

**Type:**
```
Give EMP001 admin access to GitHub
```

**What to Expect:**
- Agent calls `grant_access` with system=GitHub, access_level=Admin
- Returns access record ID
- Actions: `grant_access ✅`

---

### Test 10: Open Tickets Summary

**Type:**
```
Show me all open tickets
```

**What to Expect:**
- Agent calls `get_open_tickets_summary` tool
- Returns count of open tickets, breakdown by priority and category
- Lists each open ticket with details

---

### Test 11: Resolve a Ticket

**Type (use a real ticket ID from Test 8):**
```
Resolve ticket TKT20260301... — replaced the display cable and updated drivers
```

**What to Expect:**
- Agent calls `resolve_ticket` with the resolution description
- Ticket status changes to **Resolved**
- Check the **📊 Ticket Dashboard** tab to verify

---

### Test 12: Revoke Access

**Type:**
```
Revoke VPN access for EMP003, they left the company
```

**What to Expect:**
- Agent calls `revoke_access` for the VPN system
- Returns list of revoked access record IDs

---

## What to Look For in Every Test

### 1. Agent Planning Checklist (🧠)
Click the **🧠 Agent Planning** expander after every response. You should see:
- **Routing** — which agent was selected and why
- **Perceiving** — employee context gathered
- **Planning** — which tools were chosen and confidence level
- **Executing** — each tool call and its result
- **Evaluating** — final response generation
- All steps should show ✅ for success, ❌ for failures

### 2. Agent Badge
Every response shows a `Handled by:` badge:
- 🏥 HR Agent — leave, policy, employee info
- 🔧 IT Agent — tickets, access, assets
- 💰 Finance Agent — expenses, payroll
- 📋 Compliance Agent — training, violations, audits

### 3. Reasoning (💭)
Click the **💭 Reasoning** expander to see:
- **What** the agent understood from your message
- **Why** it chose that specific tool
- **How** it extracted parameters (dates, employee IDs, etc.)

### 4. Actions Taken (⚡)
Click the **⚡ Actions Taken** expander to see:
- Which tool(s) were called
- ✅ for success, ❌ for failure

### 5. Confidence Score
The agent assigns a confidence score (0.0–1.0) to every decision:
- **0.9–1.0**: Very confident, acted autonomously
- **0.6–0.9**: Reasonably confident, acted but may note uncertainty
- **Below 0.6**: Escalated to human review (no action taken)

### 6. Learning
Every decision is recorded by the LearningModule. Over time:
- Similar past decisions appear as context for new requests
- The agent references past outcomes to make better decisions

---

## The Agentic Difference — Before vs After

| Aspect | Before (Multi-Agent) | Now (Agentic AI) |
|--------|---------------------|-------------------|
| **Employee Chat** | HR-only assistant | Unified AI Assistant routes to HR, IT, Finance, or Compliance |
| **Routing** | Hardcoded to HR | LLM + keyword fallback classifies and routes automatically |
| **Transparency** | Reasoning expander only | Full Agent Planning checklist (Routing → Perceive → Plan → Execute → Evaluate) |
| **Leave Request** | Fill form: select type, pick dates, type reason, click Submit | Say: *"I want casual leave next week"* — agent figures out the rest |
| **IT Ticket** | Fill form: select employee, category, priority, description | Say: *"My laptop crashed"* — agent determines category, priority, creates ticket |
| **Policy Q&A** | Separate page, standalone chat | Same chat — agent knows when to answer vs. when to act |
| **Access Mgmt** | Separate forms for grant/revoke | Say: *"I need VPN access"* — agent handles it |
| **Decision Making** | Code follows if/else rules only | LLM reasons about context, policies, history, then decides |
| **Learning** | None | Every decision recorded, past decisions inform future ones |

---

## Running Automated Tests

### Quick Agentic Test (requires API key)
```bash
python test_agentic.py
```
Verifies: tool registry, learning module, goal tracker, and one live LLM call.

### Full Agentic Flow Test (requires API key)
```bash
python test_agentic_full.py
```
Tests: leave request, IT ticket creation, policy Q&A — all via natural language through the ReAct loop.

### Existing Unit Tests (no API key needed)
```bash
python -m pytest tests/ -x --tb=short
```
Verifies all 22 existing tests still pass (interview process, database, event bus, HR tools, etc.)

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Agent says "I can help with..." but doesn't act | LLM couldn't parse the plan JSON | Rephrase more clearly, e.g., include employee ID explicitly |
| "Escalated for human review" | Agent confidence < 0.6 | Request is too ambiguous or outside agent capabilities — be more specific |
| Slow responses (~5-10 seconds) | ReAct loop makes 2-3 LLM calls per request | Normal — the 70B model is reasoning, planning, and evaluating |
| Email notification failed | SMTP credentials not configured | Expected — the leave is still processed, just the email fails |
| No response at all | API key not set or rate limited | Check `.env` file has `GROQ_API_KEY` set |

---

## Interview Process — Untouched

The full interview pipeline remains exactly as before:
- ✅ Resume parsing
- ✅ Psychometric assessment
- ✅ Technical interview chat
- ✅ Video interview analysis
- ✅ Candidate report generation

These features are accessed through the **Candidate Portal** and **Admin → Candidates** and are **not affected** by the agentic changes.
