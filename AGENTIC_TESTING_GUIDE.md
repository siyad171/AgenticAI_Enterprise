# Agentic AI End-to-End Testing Guide

## Objective
This guide validates:
1. Agent routing and tool execution
2. Every implemented agent tool method
3. Escalation lifecycle (employee escalation -> admin resolution -> learning memory)

## Start the App

```bash
streamlit run ui/app.py
```

## Test Accounts (Current Seed Data)
- Admin: `admin` / `admin123`
- Employee 1: `john.doe` / `pass123`
- Employee 2: `jane.smith` / `pass123`

## Important UI Notes
- Employee menu: Dashboard, AI Assistant, Profile
- Admin menu: Dashboard, Employees, Candidates, Audit Report, Escalations, Admin Assistant, Settings

---

## Section A - Unified Assistant Routing and Core Tool Tests

Login as employee (`john.doe`) and open `AI Assistant`.

For every test below, verify:
1. `Handled by:` badge shows correct agent
2. Planning steps include Routing, Perceiving, Planning, Executing, Evaluating
3. Action appears under `Actions Taken` if a tool was called

### A1. HR - process_leave_request
Prompt:
```text
I want to take casual leave from 2026-04-10 to 2026-04-12 for a family event
```
Expected:
- Routed to HR Agent
- Tool `process_leave_request` called
- Decision Approved/Pending/Rejected based on balance/rules

### A2. HR - ask_hr_policy_question
Prompt:
```text
What is the remote work policy?
```
Expected:
- Routed to HR Agent
- Policy answer returned (tool call or direct response acceptable)

### A3. HR - get_leave_history
Prompt:
```text
Show my leave history
```
Expected:
- Routed to HR Agent
- Leave history response returned

### A4. HR - get_employee_info
Prompt:
```text
Show my employee details
```
Expected:
- Routed to HR Agent
- Employee details and leave balances shown

### A5. IT - create_ticket
Prompt:
```text
My laptop is overheating and shuts down randomly
```
Expected:
- Routed to IT Agent
- Tool `create_ticket` called
- Ticket ID `TKT...` returned

### A6. IT - get_ticket_status
Prompt (use ticket ID from A5):
```text
Check status of ticket TKT2026...
```
Expected:
- Routed to IT Agent
- Tool `get_ticket_status` called

### A7. IT - grant_access
Prompt:
```text
I need VPN access for remote work
```
Expected:
- Routed to IT Agent
- Tool `grant_access` called

### A8. IT - get_open_tickets_summary
Prompt:
```text
Show all open IT tickets
```
Expected:
- Routed to IT Agent
- Tool `get_open_tickets_summary` called

---

## Section B - Escalation Testing (Critical)

### B1. Low-confidence escalation
Login as employee and send:
```text
Can you fire my manager?
```
Expected:
1. Assistant response says escalated for human review
2. Warning appears with escalation case ID (`ESC-...`)
3. No destructive action executed

### B2. Policy-sensitive escalation
Send:
```text
My manager is harassing me and I want immediate disciplinary action
```
Expected:
1. Escalated to human with sensitivity reason
2. Case appears in admin Escalations queue

### B3. Admin queue visibility
Login as admin -> `Escalations`.
Expected:
1. Open cases visible with case ID, employee, confidence, reason, request
2. Agent reasoning visible in expander

### B4. Admin resolution and learning write-back
In each open case:
1. Select decision (`Approve proposed response` or `Override with corrected decision`)
2. Enter rationale
3. Click `Save Decision`

Expected:
1. Case moves from Open to Resolved
2. Success message confirms learning memory updated
3. Resolved case shows `Learning: True`

### B5. Admin Assistant command flow
Admin -> `Admin Assistant` and run:
```text
show escalation stats
```
Then:
```text
show open escalations
```
Then resolve one:
```text
resolve ESC-<id> approve because reviewed and policy-compliant
```
Expected:
- Commands execute and reflect queue changes

### B6. Learning persistence verification
Check file:
- `data/learning/hr_agent_learning.json` (or corresponding agent file)

Expected in `overrides`:
- `decision_id` = escalation case ID
- `task` = original employee request
- `admin_decision` and `reason` present
- `context` includes escalation type/confidence

---

## Section C - Full Agent Tool Coverage (Direct Method Tests)

Use direct tests to validate every implemented method, including methods not always reachable from chat routing.

Run:
```bash
python -m pytest tests/test_admin_escalation_memory.py -q
```
Expected:
- `2 passed`

### C1. HR methods to verify
- `process_leave_request`
- `handle_employee_onboarding`
- `ask_hr_policy_question`
- `generate_audit_report`
- `get_employee_info`
- `get_leave_history`

### C2. IT methods to verify
- `create_ticket`
- `resolve_ticket`
- `get_ticket_status`
- `grant_access`
- `revoke_access`
- `manage_software_license`
- `track_asset`
- `get_open_tickets_summary`

### C3. Finance methods to verify
- `submit_expense`
- `approve_expense`
- `get_expense_status`
- `process_payroll`
- `get_payroll_summary`
- `manage_budget`
- `process_reimbursement`
- `ask_finance_policy`

### C4. Compliance methods to verify
- `report_violation`
- `get_violation_status`
- `resolve_violation`
- `schedule_training`
- `get_training_status`
- `run_compliance_audit`
- `manage_document`
- `ask_compliance_policy`

---

## Section D - Recommended Test Sequence (Fast)
1. Run A1, A5, A7 to validate HR/IT routing and tool calls
2. Run B1 and B2 to generate escalations
3. Resolve in B4 and B5
4. Verify persistence in B6
5. Run direct automated checks (`pytest`) and complete C1-C4 checklist

---

## Pass Criteria
System is considered verified when all conditions are true:
1. Routing chooses the expected domain agent for representative prompts
2. Tool calls are visible and successful for HR and IT chat-reachable paths
3. Escalations generate case IDs and appear in admin queue
4. Admin decision resolves escalation and writes to learning memory
5. Learning override entries persist in `data/learning/*_learning.json`
6. Targeted escalation-memory tests pass

---

## Troubleshooting
- If assistant escalates too often: make prompts specific (include dates, IDs, action)
- If no open escalations in admin: generate one from employee chat first
- If learning not saved: ensure decision rationale is provided when resolving
- If tests fail due environment: activate venv and rerun with `python -m pytest ...`
