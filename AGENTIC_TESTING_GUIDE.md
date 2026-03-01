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

## Testing the HR Agent (Employee Portal)

### Login
- **Username:** `john` | **Password:** `john123` (Employee role)

### Where to Test
- Sidebar → **💬 HR Assistant**

---

### Test 1: Leave Request via Natural Language

**Type this in the chat:**
```
I want to take casual leave from 2026-03-10 to 2026-03-12 for a family function
```

**What to Expect:**
- 🤖 Agent shows "Thinking..." spinner
- Agent **reasons**: identifies this as a leave request, extracts dates, leave type, and reason
- Agent **acts**: calls `process_leave_request` tool internally
- Agent **responds**: tells you the leave is approved (3 days ≤ 10 day auto-approve limit)
- You can expand **🧠 Agent Reasoning** to see the full reasoning chain
- You can expand **⚡ Actions Taken** to see which tools were called

**Expected Result:**
- Leave status: **Approved** (3 days, auto-approved)
- Confidence: ~0.90–0.95
- Actions: `process_leave_request ✅`

---

### Test 2: Leave Request That Needs Approval

**Type:**
```
I need annual leave from 2026-03-05 to 2026-03-25 for international travel
```

**What to Expect:**
- Agent reasons that 21 days > 10 day limit → requires manager approval
- Leave status: **Pending** (requires manager approval)
- Agent explains the policy in its response

---

### Test 3: Policy Question (No Tool Needed)

**Type:**
```
What is the company's remote work policy?
```

**What to Expect:**
- Agent may call `ask_hr_policy_question` tool, OR answer directly from context
- Responds with policy details about remote work (up to 3 days/week)
- No leave processing happens — agent is smart enough to know this is just a question

---

### Test 4: Employee Info Lookup

**Type:**
```
Show me my leave balance
```

**What to Expect:**
- Agent calls `get_employee_info` tool
- Returns your current leave balances (Casual: 12, Sick: 15, Annual: 20 initially)
- If you already took leave in Test 1, casual balance will be reduced

---

### Test 5: Leave History

**Type:**
```
Show me all my past leave requests
```

**What to Expect:**
- Agent calls `get_leave_history` tool
- Lists all leave requests you've made with dates, types, and statuses

---

### Test 6: Ambiguous Request (Tests Reasoning)

**Type:**
```
I'm not feeling well, can I take tomorrow off?
```

**What to Expect:**
- Agent **reasons**: "not feeling well" → sick leave, "tomorrow" → calculates tomorrow's date
- Agent calls `process_leave_request` with leave_type="Sick Leave"
- May show slightly lower confidence since "tomorrow" is relative
- If confidence is too low (<0.6), agent **escalates** instead of acting

---

### Test 7: Escalation (Low Confidence)

**Type:**
```
Can you fire my manager?
```

**What to Expect:**
- Agent recognizes this is outside its capabilities
- Confidence drops below threshold (0.6)
- Response: "I've analyzed your request but I'm not confident enough to act autonomously..."
- Shows **⚠️ This request has been escalated for human review**

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

### 1. Agent Reasoning (🧠)
Click the **🧠 Agent Reasoning** expander after every response. You should see:
- **What** the agent understood from your message
- **Why** it chose that specific tool
- **How** it extracted parameters (dates, employee IDs, etc.)

### 2. Actions Taken (⚡)
Click the **⚡ Actions Taken** expander to see:
- Which tool(s) were called
- ✅ for success, ❌ for failure

### 3. Confidence Score
The agent assigns a confidence score (0.0–1.0) to every decision:
- **0.9–1.0**: Very confident, acted autonomously
- **0.6–0.9**: Reasonably confident, acted but may note uncertainty
- **Below 0.6**: Escalated to human review (no action taken)

### 4. Learning
Every decision is recorded by the LearningModule. Over time:
- Similar past decisions appear as context for new requests
- The agent references past outcomes to make better decisions

---

## The Agentic Difference — Before vs After

| Aspect | Before (Multi-Agent) | Now (Agentic AI) |
|--------|---------------------|-------------------|
| **Leave Request** | Fill form: select type, pick dates, type reason, click Submit | Say: *"I want casual leave next week"* — agent figures out the rest |
| **IT Ticket** | Fill form: select employee, category, priority, description | Say: *"John's laptop crashed"* — agent determines category, priority, creates ticket |
| **Policy Q&A** | Separate page, standalone chat | Same chat — agent knows when to answer vs. when to act |
| **Access Mgmt** | Separate forms for grant/revoke | Say: *"Give John GitHub access"* — agent handles it |
| **Decision Making** | Code follows if/else rules only | LLM reasons about context, policies, history, then decides |
| **Learning** | None | Every decision recorded, past decisions inform future ones |
| **Transparency** | Black box | Full reasoning chain visible in every response |

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
