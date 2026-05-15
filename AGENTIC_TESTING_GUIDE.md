# Agentic AI End-to-End Testing Guide (Updated)

## Objective
Use this guide to validate the current system behavior for:
1. Unified assistant routing and domain tool execution
2. Escalation lifecycle (Open -> Resolved)
3. Learning persistence and escalation bypass via learned overrides

## Start The App

```bash
streamlit run ui/app.py
```

## Test Accounts (Seed Data)
- Admin: `admin` / `admin123`
- Employee 1: `john.doe` / `pass123`
- Employee 2: `jane.smith` / `pass123`

## Current UI Menus
- Employee menu: `🏠 Dashboard`, `🤖 AI Assistant`, `👤 Profile`
- Admin menu: `🏠 Dashboard`, `👥 Employees`, `📋 Candidates`, `📊 Audit Report`, `🚨 Escalations`, `🤖 Admin Assistant`, `⚙️ Settings`

---

## Section A - Unified Assistant Routing + Tool Visibility

Login as employee (`john.doe`) and open `🤖 AI Assistant`.

For each prompt below, verify:
1. `Handled by:` badge shows expected domain agent
2. Planning includes Routing + Perceiving + Planning + Executing + Evaluating (for non-escalated flows)
3. Tool calls appear under `⚡ Actions Taken`

### A1. HR leave processing
Prompt:
```text
I want to take casual leave from 2026-04-10 to 2026-04-12 for a family event
```
Expected:
- Routed to `🏥 HR Agent`
- `process_leave_request` appears in actions
- Response includes decision path (Approved/Pending/Rejected based on policy + balance)

### A2. HR policy answer
Prompt:
```text
What is the remote work policy?
```
Expected:
- Routed to `🏥 HR Agent`
- Policy response returned (may call `ask_hr_policy_question`)

### A3. HR leave history
Prompt:
```text
Show my leave history
```
Expected:
- Routed to `🏥 HR Agent`
- `get_leave_history` behavior reflected in response content

### A4. HR employee info
Prompt:
```text
Show my employee details and leave balance
```
Expected:
- Routed to `🏥 HR Agent`
- `get_employee_info` behavior reflected in response content

### A5. IT ticket creation
Prompt:
```text
My laptop is overheating and shuts down randomly
```
Expected:
- Routed to `🔧 IT Agent`
- `create_ticket` appears in actions
- Ticket ID format `TKT...` returned

### A6. IT ticket status
Prompt (use ticket from A5):
```text
Check status of ticket TKT2026...
```
Expected:
- Routed to `🔧 IT Agent`
- `get_ticket_status` appears in actions

### A7. IT access grant
Prompt:
```text
I need VPN access for remote work
```
Expected:
- Routed to `🔧 IT Agent`
- `grant_access` appears in actions

### A8. IT open ticket summary
Prompt:
```text
Show all open IT tickets
```
Expected:
- Routed to `🔧 IT Agent`
- `get_open_tickets_summary` appears in actions

---

## Section B - Escalation + Learning (Critical)

### B1. Generate escalation from employee chat
As employee, send:
```text
Can you fire my manager?
```
Expected:
1. Assistant indicates human review is required
2. Warning contains case ID in format `ESC-...`
3. No destructive action executed

### B2. Generate policy-sensitive escalation
Send:
```text
My manager is harassing me and I want immediate disciplinary action
```
Expected:
1. Escalation created with sensitivity reason
2. Case appears in admin escalation queue

### B3. Admin queue visibility
Login as admin -> `🚨 Escalations`.
Expected for each open case:
1. Shows case ID, employee, confidence, escalation reason, employee request
2. Shows proposed response (if captured)
3. `Agent Reasoning` expander available when reasoning exists

### B4. Resolve escalation and persist learning
In each open case:
1. Choose one decision type:
	 - `Approve agent proposed response`
	 - `Override with corrected decision`
	 - `Escalate to specialist team`
2. Provide natural-language final response
3. Provide `Decision rationale`
4. Click `Save Decision`

Expected:
1. Case moves from Open to Resolved
2. Success message: `Decision saved and learning memory updated.`
3. Resolved list shows `Learning: True`

### B5. Admin Assistant escalation commands
Admin -> `🤖 Admin Assistant` and run:

```text
show escalation stats
```

```text
show open escalations
```

```text
resolve ESC-<id> approve because reviewed and policy-compliant
```

Also verify these variants:

```text
resolve ESC-<id> override because requires corrected response wording
```

```text
resolve ESC-<id> escalate because requires specialist team follow-up
```

Expected:
- Commands execute successfully
- Queue + stats reflect updates
- Resolve response confirms decision saved to learning memory

### B6. Learning persistence file checks
Check these files after at least one admin resolution:
- `data/learning/hr_agent_learning.json` (or the resolved agent's learning file)
- `data/learning/<agent>_agent_decisions_audit.json`

Expected in `*_learning.json`:
- `overrides` array exists
- New entry includes:
	- `decision_id` = escalation case ID
	- `task` = original employee request
	- `admin_decision`
	- `reason`
	- optional `employee_response`
	- `context.escalation_type`, `context.escalation_reason`, `context.agent_confidence`, `context.admin_decision_type`

Expected in `*_decisions_audit.json`:
- `decisions` array exists
- no `overrides` array (policy memory and decision audit are intentionally split)

### B7. Learning replay (escalation bypass) validation
After resolving a case in B4/B5, login again as employee and send a very similar prompt.

Expected:
1. If override match is strong, request can be handled without new escalation
2. Planning includes `Learning Match` step
3. Planning shows escalation bypass detail (policy-sensitive or low-confidence bypass)
4. Response style follows the learned admin response pattern

---

## Section C - Automated Escalation/Learning Regression

Run:

```bash
python -m pytest tests/test_admin_escalation_memory.py -q
```

Current expected result:
- `7 passed`

Coverage in this suite includes:
- Escalation resolution writes override learning
- Open/Resolved queue filtering
- Learned override prevents re-escalation (low-confidence and policy-sensitive paths)
- Policy-memory and decisions-audit file separation
- Override persistence across runtime sessions
- Preference for stored `employee_response` when present

---

## Section D - Full Tool-Level Validation (IT, Finance, Compliance)

Use this section to validate every tool method with expected outcomes.

### D0. Test setup and ID tracking
Before starting D1-D3, keep these IDs as you generate them:
- `ticket_id` from IT `create_ticket`
- `expense_id` from Finance `submit_expense`
- `violation_id` from Compliance `report_violation`
- `training_id` from Compliance `schedule_training`
- `document_id` from Compliance `manage_document` upload

Recommended employee IDs from seed data:
- `EMP001` (john.doe)
- `EMP002` (jane.smith)

### D1. IT tools (all methods)

1. `create_ticket`
Input example:
- employee: `EMP001`
- category: `Hardware`
- description: `Laptop fan noise and random shutdown`
- priority: `High`
Expected:
- `status = success`
- `ticket_id` starts with `TKT`
- ticket saved with status `Open`

2. `get_ticket_status`
Input:
- use `ticket_id` from step 1
Expected:
- `status = success`
- `ticket.ticket_id` matches input
- `ticket.status` initially `Open`

3. `resolve_ticket`
Input:
- same `ticket_id`
- resolution: `Thermal cleanup and BIOS update completed`
Expected:
- `status = success`
- response includes same `ticket_id`
- follow-up `get_ticket_status` shows `status = Resolved`

4. `grant_access`
Input example:
- employee: `EMP001`
- system: `VPN`
- access_level: `Standard`
Expected:
- `status = success`
- `record_id` starts with `ACC`
- response contains `system = VPN`

5. `revoke_access`
Input:
- employee: `EMP001`
- system: `VPN`
Expected:
- `status = success`
- `revoked` array returned
- previously active VPN access record moved to `Revoked`

6. `manage_software_license` (assign)
Input example:
- action: `assign`
- software: choose one with available licenses in DB
- employee: `EMP001`
Expected:
- if license available: `status = success` and `license_id` returned
- if not available: `status = error` with `No available license ...`

7. `manage_software_license` (release)
Input example:
- action: `release`
- software: same as above
Expected:
- `status = success`
- message confirms release

8. `track_asset` by employee
Input:
- employee: `EMP001`
Expected:
- `status = success`
- `assets` array returned (can be empty)

9. `track_asset` by asset id (optional if known asset exists)
Input:
- asset_id: any valid asset from DB
Expected:
- valid ID: `status = success` + `asset` object
- invalid ID: `status = error` + `Asset not found`

10. `get_open_tickets_summary`
Input:
- no parameters
Expected:
- `status = success`
- response contains `total_open`, `by_priority`, `by_category`, `tickets`

### D2. Finance tools (all methods)

1. `submit_expense`
Input example:
- employee: `EMP001`
- category: `Travel`
- amount: `120.0`
- description: `Client meeting travel`
Expected:
- `status = success`
- `expense_id` starts with `EXP`
- `approval_status` is either:
	- `Approved` (if amount <= auto-approve limit)
	- `Pending` (if amount above limit)

2. `get_expense_status`
Input:
- use `expense_id` from step 1
Expected:
- `status = success`
- returned `expense_id` matches input
- `approval_status` matches latest decision

3. `approve_expense`
Input:
- use `expense_id` from step 1
- approved_by: `Finance Admin`
- decision: `Approved`
Expected:
- `status = success`
- response includes same `expense_id`
- follow-up `get_expense_status` shows approved state

4. `process_reimbursement`
Input:
- approved `expense_id`
Expected:
- if approved expense: `status = success`, `reimbursement_id` starts with `RMB`, `amount` returned
- if not approved: `status = error`, `Expense not approved`

5. `process_payroll`
Input example:
- month: `03`
- year: `2026`
Expected:
- `status = success`
- response includes `total_employees` and `records`
- each record has `employee_id` and `net_salary`

6. `get_payroll_summary`
Input:
- same month/year as step 5
Expected:
- `status = success`
- includes `total_employees` and `total_payroll`

7. `manage_budget` allocate
Input example:
- department: `Engineering`
- action: `allocate`
- amount: `150000`
Expected:
- `status = success`
- response includes `department` and `allocated`

8. `manage_budget` view
Input:
- department: same as step 7
- action: `view`
Expected:
- `status = success`
- response includes `allocated`, `spent`, `remaining`
- if no budget exists for chosen dept: `status = error`, `No budget for ...`

9. `ask_finance_policy`
Input example:
- `What is reimbursement policy for travel expenses?`
Expected:
- `status = success`
- non-empty `answer` string

### D3. Compliance tools (all methods)

1. `report_violation`
Input example:
- reported_by: `EMP001`
- category: `Policy Breach`
- description: `Possible data handling policy breach`
- severity: `High`
Expected:
- `status = success`
- `violation_id` starts with `VIO`
- severity returned in response

2. `get_violation_status`
Input:
- use `violation_id` from step 1
Expected:
- `status = success`
- includes same `violation_id`
- `current_status` initially `Open`

3. `resolve_violation`
Input:
- same `violation_id`
- resolution: `Investigated and corrective action documented`
Expected:
- `status = success`
- follow-up `get_violation_status` shows resolved status

4. `schedule_training`
Input example:
- employee: `EMP001`
- training_type: `Data Privacy`
- due_date: future date (e.g. `2026-05-15`)
- mandatory: `True`
Expected:
- `status = success`
- `training_id` starts with `TRN`

5. `get_training_status` by training ID
Input:
- use `training_id` from step 4
Expected:
- `status = success`
- response includes same `training_id` and `status`

6. `get_training_status` by employee ID
Input:
- employee: `EMP001`
Expected:
- `status = success`
- `trainings` array returned (may include mandatory scheduled items)

7. `run_compliance_audit`
Input:
- scope: `full`
Expected:
- `status = success`
- `audit_id` starts with `AUD`
- `compliance_status` is `COMPLIANT` or `ISSUES_FOUND`
- includes `findings_count` and `findings`

8. `manage_document` upload
Input example:
- action: `upload`
- doc_type: `Policy`
- title: `Remote Work Policy v2`
- version: `2.0`
Expected:
- `status = success`
- `document_id` starts with `DOC`

9. `manage_document` list
Input:
- action: `list`
- doc_type: `Policy`
Expected:
- `status = success`
- `documents` array returned
- uploaded document appears in list (same title/version)

10. `ask_compliance_policy`
Input example:
- `What is the incident reporting SLA?`
Expected:
- `status = success`
- non-empty `answer` string

### D4. Completion criteria for Section D
Mark Section D complete only if all are true:
1. Every IT/Finance/Compliance method listed above was executed at least once
2. Each method returned expected success/error structure
3. Linked retrieval checks succeeded (status after create/resolve flows)
4. Generated IDs follow prefixes (`TKT`, `ACC`, `EXP`, `RMB`, `VIO`, `TRN`, `AUD`, `DOC`)

---

## Section E - Fast Recommended Sequence

1. Run A1, A5, A7, A8 for routing + HR/IT chat tool visibility
2. Run B1 and B2 to generate at least 2 escalations
3. Resolve one via `🚨 Escalations` (B4) and one via `🤖 Admin Assistant` (B5)
4. Validate persistence in B6 and replay in B7
5. Execute all tool-level checks in Section D (IT, Finance, Compliance)
6. Run automated regression (Section C)

---

## Pass Criteria
System is considered verified when all are true:
1. Representative prompts route to expected domain agent
2. Tool calls are visible and successful for chat-reachable HR/IT flows
3. Escalations produce `ESC-...` case IDs and appear in admin queue
4. Admin resolution stores decision and marks learning recorded
5. Learning override entries persist in `data/learning/*_learning.json`
6. Similar future requests can use learned override and avoid re-escalation when appropriate
7. `tests/test_admin_escalation_memory.py` passes

---

## Troubleshooting
- If a request does not escalate: use more sensitive wording or ambiguous phrasing
- If escalations are not visible in admin: ensure request came from employee assistant and included employee context
- If save fails in admin escalation: ensure both final response and rationale are filled
- If learning replay does not trigger: use a closer prompt match (shared key terms with resolved escalation)
- If tests are flaky due existing learning data: use unique task strings in test prompts or isolate temporary storage
