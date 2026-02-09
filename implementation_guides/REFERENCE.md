# REFERENCE — Quick Lookup Tables

> Use this file to quickly find any model, method, event, or file path without reading the full guides.

---

## 1. File Map

| File Path | Guide | Purpose |
|-----------|-------|---------|
| `core/__init__.py` | 00 | Package init |
| `core/config.py` | 01 | All constants, API keys, env vars |
| `core/database.py` | 01 | Models (dataclasses), Database class, seed data |
| `core/llm_service.py` | 02 | Groq API wrapper |
| `core/event_bus.py` | 02 | Pub/sub event system |
| `core/events.py` | 02 | Event type constants |
| `core/base_agent.py` | 02 | Abstract base for all agents |
| `core/orchestrator.py` | 03 | Task routing + workflow engine |
| `core/goal_tracker.py` | 03 | KPI goals per agent |
| `core/learning_module.py` | 03 | Decision memory + override learning |
| `agents/__init__.py` | 06 | Agent imports |
| `agents/hr_agent.py` | 05 | HR Agent (6 functions) |
| `agents/it_agent.py` | 06 | IT Agent (7 capabilities) |
| `agents/finance_agent.py` | 06 | Finance Agent (8 capabilities) |
| `agents/compliance_agent.py` | 06 | Compliance Agent (8 capabilities) |
| `tools/__init__.py` | 04 | Tool imports |
| `tools/email_service.py` | 04 | SMTP email (LLM body + fallback) |
| `tools/local_executor.py` | 04 | Python subprocess runner |
| `tools/code_executor.py` | 04 | Judge0 API + local fallback |
| `tools/ai_code_analyzer.py` | 04 | LLM code analysis |
| `tools/video_analyzer.py` | 04 | DeepFace + SpeechBrain (heavy) |
| `tools/video_analyzer_hybrid.py` | 04 | Whisper + LLM (lightweight) |
| `tools/technical_interview_chat.py` | 04 | 6-stage AI interviewer |
| `tools/psychometric_assessment.py` | 04 | 20-question EQ/AQ/SQ/BQ |
| `tools/interview_storage.py` | 04 | JSON file persistence |
| `prompts/hr/leave_email.py` | 05 | Leave email prompt |
| `prompts/hr/resume_parser.py` | 05 | Resume parsing prompt |
| `prompts/hr/policy_qa.py` | 05 | Policy Q&A prompt |
| `prompts/it/ticket.py` | 06 | IT ticket prompt |
| `prompts/finance/expense.py` | 06 | Expense review prompt |
| `prompts/compliance/violation.py` | 06 | Violation analysis prompt |
| `prompts/interview/socratic.py` | 04 | Technical interviewer system prompt |
| `prompts/shared/json_format.py` | 02 | Shared JSON formatting prompt |
| `ui/app.py` | 07 | Streamlit entry point |
| `ui/styles.py` | 07 | CSS extraction |
| `ui/login_ui.py` | 07 | Login page (3 tabs) |
| `ui/utils.py` | 07 | parse_pdf_resume, logout |
| `ui/candidate_portal.py` | 08 | Candidate application flow |
| `ui/employee_portal.py` | 08 | Employee dashboard, leave, Q&A |
| `ui/admin_portal.py` | 08 | Admin management panel |
| `ui/it_portal.py` | 08 | IT ticket/access/asset UI |
| `ui/finance_portal.py` | 08 | Finance expense/payroll/budget UI |
| `ui/compliance_portal.py` | 08 | Compliance violations/training UI |
| `ui/orchestrator_dashboard.py` | 08 | Cross-agent workflow UI |
| `ui/chat_interview_ui.py` | 08 | AI chat interview UI |
| `ui/technical_interview_ui.py` | 08 | Code editor + test runner UI |
| `ui/psychometric_ui.py` | 08 | Psychometric assessment UI |
| `ui/video_interview_ui.py` | 08 | Video upload + analysis UI |
| `ui/results_viewer_ui.py` | 08 | Interview results browser |
| `tests/conftest.py` | 09 | Test fixtures |
| `tests/test_*.py` | 09 | Unit + integration tests |
| `verify_setup.py` | 09 | Import verification script |

---

## 2. Database Models

| Model | Fields | Guide |
|-------|--------|-------|
| `Employee` | employee_id, name, email, department, position, join_date, leave_balance, status | 01-B |
| `LeaveRequest` | request_id, employee_id, leave_type, start_date, end_date, reason, status, decision_date | 01-B |
| `JobPosition` | job_id, title, department, required_skills, min_experience, education_requirement, status, test_questions | 01-B |
| `Candidate` | candidate_id, name, email, phone, applied_position, resume_text, extracted_skills, experience_years, education, application_date, status, evaluation_result | 01-B |
| `User` | username, password, role, employee_id | 01-B |
| `TechnicalProblem` | problem_id, title, description, difficulty, test_cases, language | 01-B |
| `CodeSubmission` | submission_id, candidate_id, problem_id, code, language, results, score, timestamp | 01-B |
| `AuditLog` | timestamp, agent, action, details, status | 01-B |
| `ITTicket` | ticket_id, employee_id, category, description, priority, status, assigned_to, created_date, resolved_date | 01-C |
| `AccessRecord` | record_id, employee_id, system_name, access_level, granted_by, granted_date, revoked_date, status | 01-C |
| `SoftwareLicense` | license_id, software_name, total_seats, used_seats, assigned_to, expiry_date | 01-C |
| `ITAsset` | asset_id, asset_type, serial_number, assigned_to, status, purchase_date | 01-C |
| `ExpenseClaim` | claim_id, employee_id, amount, category, description, receipt_url, status, submitted_date, reviewed_by | 01-D |
| `PayrollRecord` | record_id, employee_id, month, base_salary, deductions, bonuses, net_pay, status | 01-D |
| `Budget` | budget_id, department, fiscal_year, total_amount, spent_amount, remaining | 01-D |
| `Reimbursement` | reimbursement_id, employee_id, claim_id, amount, status, processed_date | 01-D |
| `Violation` | violation_id, reported_by, employee_id, category, description, severity, status, reported_date, resolved_date | 01-E |
| `TrainingRecord` | record_id, employee_id, training_name, category, status, scheduled_date, completed_date, score | 01-E |
| `ComplianceAudit` | audit_id, auditor, department, findings, risk_level, audit_date, status | 01-E |
| `ComplianceDocument` | document_id, title, category, version, content_summary, effective_date, status | 01-E |

---

## 3. Enums

| Enum | Values | Used By |
|------|--------|---------|
| `EmployeeStatus` | Active, Inactive, OnLeave, Terminated | Employee |
| `LeaveStatus` | Pending, Approved, Rejected, Cancelled | LeaveRequest |
| `CandidateStatus` | Pending, Screening, Interview, Accepted, Rejected | Candidate |
| `TicketStatus` | Open, InProgress, Resolved, Closed | ITTicket |
| `TicketPriority` | Low, Medium, High, Critical | ITTicket |
| `ExpenseStatus` | Pending, Approved, Rejected, Reimbursed | ExpenseClaim |
| `ViolationSeverity` | Low, Medium, High, Critical | Violation |

---

## 4. Event Types

| Constant | String Value | Published By | Consumed By |
|----------|-------------|-------------|-------------|
| `LEAVE_PROCESSED` | `"leave_processed"` | HR | — |
| `EMPLOYEE_ONBOARDED` | `"employee_onboarded"` | HR | IT, Compliance |
| `EMPLOYEE_OFFBOARDED` | `"employee_offboarded"` | HR | IT, Finance |
| `CANDIDATE_APPLIED` | `"new_candidate_applied"` | HR | — |
| `TICKET_CREATED` | `"ticket_created"` | IT | — |
| `TICKET_RESOLVED` | `"ticket_resolved"` | IT | — |
| `ACCESS_GRANTED` | `"access_granted"` | IT | Compliance |
| `ACCESS_REVOKED` | `"access_revoked"` | IT | — |
| `EXPENSE_SUBMITTED` | `"expense_submitted"` | Finance | Compliance |
| `EXPENSE_APPROVED` | `"expense_approved"` | Finance | — |
| `PAYROLL_PROCESSED` | `"payroll_processed"` | Finance | — |
| `VIOLATION_REPORTED` | `"violation_reported"` | Compliance | HR |
| `SECURITY_INCIDENT` | `"security_incident"` | Compliance | IT |

---

## 5. Agent Capabilities

### HR Agent (6)
| Method | Purpose |
|--------|---------|
| `process_leave_request(emp_id, type, start, end, reason)` | Validate + approve/reject leave |
| `handle_employee_onboarding(name, email, dept, pos, date)` | Create employee + credentials |
| `ask_hr_policy_question(question, emp_id?)` | LLM-powered policy Q&A |
| `generate_audit_report(start_date, end_date)` | Activity summary + compliance |
| `evaluate_candidate(candidate, job)` | Skill/exp/edu scoring |
| `parse_resume_text(text)` | Extract skills, exp, education |

### IT Agent (7)
| Method | Purpose |
|--------|---------|
| `create_ticket(emp_id, category, description, priority)` | New IT ticket |
| `resolve_ticket(ticket_id, resolution)` | Close ticket with notes |
| `get_ticket_status(ticket_id)` | Check ticket state |
| `grant_access(emp_id, system, level, granted_by)` | Grant system access |
| `revoke_access(emp_id, system)` | Revoke access |
| `manage_software_license(software, action, emp_id?)` | Assign/release licenses |
| `track_asset(asset_id?, action?, emp_id?)` | Asset CRUD |

### Finance Agent (8)
| Method | Purpose |
|--------|---------|
| `submit_expense(emp_id, amount, category, desc, receipt?)` | New expense claim |
| `approve_expense(claim_id, reviewer, decision)` | Approve/reject expense |
| `get_expense_status(claim_id)` | Check expense state |
| `process_payroll(emp_id, month, salary, deductions, bonuses)` | Calculate net pay |
| `get_payroll_summary(month?)` | Payroll totals |
| `manage_budget(dept, fiscal_year, total)` | Set/update budget |
| `process_reimbursement(claim_id)` | Reimburse approved expenses |
| `ask_finance_policy(question)` | LLM policy Q&A |

### Compliance Agent (8)
| Method | Purpose |
|--------|---------|
| `report_violation(reported_by, emp_id, category, desc, severity)` | New violation |
| `get_violation_status(violation_id)` | Check violation state |
| `resolve_violation(violation_id, resolution)` | Close violation |
| `schedule_training(emp_id, name, category, date)` | Schedule training |
| `get_training_status(emp_id?)` | Training records |
| `run_compliance_audit(auditor, department)` | Department audit |
| `manage_document(title, category, content, version?)` | CRUD compliance docs |
| `ask_compliance_policy(question)` | LLM policy Q&A |

---

## 6. Orchestrator Workflows

| Workflow | Steps (agents) |
|----------|---------------|
| `new_hire` | HR (onboard) → IT (setup access) → Compliance (training) |
| `employee_exit` | HR (offboard) → IT (revoke) → Finance (final pay) |
| `expense_claim` | Finance (submit) → Finance (auto/manual approve) → Finance (reimburse) |
| `security_incident` | Compliance (report) → IT (lock access) → HR (notify) |

---

## 7. LLM Models Used

| Model | Use Case | Config Key |
|-------|----------|-----------|
| `llama-3.1-8b-instant` | Chat, Q&A, email body | `GROQ_MODEL` |
| `llama-3.3-70b-versatile` | Code analysis, resume parsing, evaluation | `GROQ_MODEL_LARGE` |
| `whisper-large-v3-turbo` | Audio/video transcription | `GROQ_WHISPER_MODEL` |

---

## 8. Prompts Folder Structure

```
prompts/
├── hr/
│   ├── __init__.py
│   ├── leave_email.py      → get_leave_email_prompt(emp, request, decision)
│   ├── resume_parser.py    → get_resume_parser_prompt(text)
│   └── policy_qa.py        → get_policy_qa_prompt(question, context)
├── it/
│   ├── __init__.py
│   └── ticket.py           → get_ticket_analysis_prompt(ticket)
├── finance/
│   ├── __init__.py
│   └── expense.py          → get_expense_review_prompt(claim)
├── compliance/
│   ├── __init__.py
│   └── violation.py        → get_violation_analysis_prompt(violation)
├── interview/
│   ├── __init__.py
│   └── socratic.py         → get_interviewer_system_prompt(stage, problem)
└── shared/
    ├── __init__.py
    └── json_format.py      → get_json_format_prompt(schema)
```

---

## 9. Default Users (Seed Data)

| Username | Password | Role | Employee ID |
|----------|----------|------|-------------|
| `admin` | `admin123` | Admin | `EMP001` |
| `john` | `john123` | Employee | `EMP001` |
| `jane` | `jane123` | Employee | `EMP002` |
| `candidate` | — | Candidate | — |

> Candidates register through the application form; no pre-set credentials.

---

## 10. Key Session State Variables

| Variable | Type | Set In | Used By |
|----------|------|--------|---------|
| `st.session_state.db` | Database | app.py | All portals |
| `st.session_state.agents` | dict[str, BaseAgent] | app.py | All portals |
| `st.session_state.orchestrator` | Orchestrator | app.py | Admin portal |
| `st.session_state.event_bus` | EventBus | app.py | All agents |
| `st.session_state.logged_in` | bool | login_ui.py | app.py router |
| `st.session_state.current_user` | User | login_ui.py | All portals |
| `st.session_state.candidate_step` | str | candidate_portal.py | Candidate flow |
| `st.session_state.chat_history` | list[dict] | employee_portal.py | Policy Q&A |
| `st.session_state.current_candidate_id` | str | candidate_portal.py | Interview UIs |

---

## 11. Implementation Order Summary

```
Guide 00 → Project Setup (folders, venv, requirements, .env)
Guide 01 → Config + Database (models, methods, seed data)
Guide 02 → Core Services (LLM, EventBus, BaseAgent)
Guide 03 → Orchestration (Orchestrator, GoalTracker, LearningModule)
Guide 04 → Tools Layer (9 tools: email, code exec, AI analyzer, video, interview, psychometric, storage)
Guide 05 → HR Agent (6 functions + prompt files)
Guide 06 → New Agents (IT, Finance, Compliance + __init__)
Guide 07 → UI Foundation (app.py entry, styles, login, utils)
Guide 08 → UI Portals (12 portal/UI files)
Guide 09 → Testing & Deployment (pytest, verify, Docker)
```

**Estimated total files:** ~55 Python files + config/env files
**Estimated total lines:** ~5,000–6,000 lines of production code
