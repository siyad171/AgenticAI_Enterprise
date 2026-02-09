# 08 — UI Portals

> **Depends on:** `07_UI_FOUNDATION.md`, all agents, all tools
> **Creates:** `ui/candidate_portal.py`, `ui/employee_portal.py`, `ui/admin_portal.py`, `ui/it_portal.py`, `ui/finance_portal.py`, `ui/compliance_portal.py`, `ui/orchestrator_dashboard.py`, `ui/chat_interview_ui.py`, `ui/technical_interview_ui.py`, `ui/psychometric_ui.py`, `ui/video_interview_ui.py`, `ui/results_viewer_ui.py`

---

## Portal Map

| File | Lines (est.) | Role | Key Features |
|------|-------------|------|-------------|
| `candidate_portal.py` | ~200 | Candidate | Application form, resume upload, MCQ test, technical interview, psychometric, video |
| `employee_portal.py` | ~250 | Employee | Dashboard, leave request, policy Q&A chat, profile view |
| `admin_portal.py` | ~350 | Admin | Employee management, candidate review, audit report, eligibility config |
| `it_portal.py` | ~150 | Admin/IT | Ticket dashboard, access management, asset tracking |
| `finance_portal.py` | ~150 | Admin/Finance | Expense management, payroll, budget |
| `compliance_portal.py` | ~150 | Admin/Compliance | Violations, training, audit, documents |
| `orchestrator_dashboard.py` | ~100 | Admin | Cross-agent workflows, agent statuses, goal tracker |
| `chat_interview_ui.py` | ~200 | Candidate | 6-stage AI interviewer chat interface |
| `technical_interview_ui.py` | ~300 | Candidate | Code editor (streamlit-ace), test cases, AI review |
| `psychometric_ui.py` | ~150 | Candidate | 20-question assessment with results visualization |
| `video_interview_ui.py` | ~120 | Candidate | Video upload + hybrid analysis display |
| `results_viewer_ui.py` | ~150 | Admin | Browse all interview results (JSON viewer) |

---

## General Pattern

Every portal file follows this structure:

```python
"""Portal Name — Role description"""
import streamlit as st

def show_portal_name():
    # Sidebar navigation
    st.sidebar.title("Portal Title")
    page = st.sidebar.radio("Navigation", ["Page A", "Page B", ...])
    
    if st.sidebar.button("🚪 Logout"):
        from ui.utils import logout
        logout()
    
    if page == "Page A":
        _render_page_a()
    elif page == "Page B":
        _render_page_b()

def _render_page_a():
    st.header("Page A")
    # ... streamlit widgets ...
```

---

## `ui/candidate_portal.py`

```python
"""Candidate Portal — Application, tests, interviews"""
import streamlit as st
import datetime
from ui.utils import parse_pdf_resume


def show_candidate_portal():
    st.title("📝 Candidate Application Portal")
    agent = st.session_state.agents['hr']
    db = st.session_state.db

    # Step tracking
    if 'candidate_step' not in st.session_state:
        st.session_state.candidate_step = "application"

    step = st.session_state.candidate_step

    if step == "application":
        _show_application_form(agent, db)
    elif step == "mcq_test":
        _show_mcq_test(agent, db)
    elif step == "technical_interview":
        _show_technical_choice(agent, db)
    elif step == "psychometric":
        from ui.psychometric_ui import show_psychometric_assessment
        show_psychometric_assessment()
    elif step == "video_interview":
        from ui.video_interview_ui import show_video_interview
        show_video_interview()
    elif step == "complete":
        st.success("🎉 Application complete! You will be notified by email.")
        if st.button("← Back to Login"):
            st.session_state.show_application_form = False
            st.session_state.candidate_step = "application"
            st.rerun()


def _show_application_form(agent, db):
    """Application form with resume upload and position selection"""
    st.subheader("Step 1: Personal Information")

    with st.form("application_form"):
        name = st.text_input("Full Name *")
        email = st.text_input("Email *")
        phone = st.text_input("Phone Number")

        # Position selection
        active_jobs = {jid: j for jid, j in db.job_positions.items()
                       if j.status == "Active"}
        position = st.selectbox("Position *",
                                [j.title for j in active_jobs.values()])

        # Resume upload
        st.subheader("Resume")
        resume_file = st.file_uploader("Upload PDF Resume", type=["pdf"])
        resume_text = st.text_area("Or paste resume text", height=150)

        submitted = st.form_submit_button("Submit Application", type="primary")

        if submitted and name and email and position:
            # Parse resume
            if resume_file:
                resume_text = parse_pdf_resume(resume_file)
            if not resume_text:
                st.error("Please provide a resume")
                return

            # Extract skills via LLM
            parsed = agent.parse_resume_text(resume_text)

            # Generate candidate ID
            cand_id = f"CAND{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

            from core.database import Candidate
            candidate = Candidate(
                candidate_id=cand_id, name=name, email=email, phone=phone,
                applied_position=position, resume_text=resume_text,
                extracted_skills=parsed['skills'],
                experience_years=parsed['experience_years'],
                education=parsed['education'],
                application_date=datetime.datetime.now().isoformat(),
                status="Pending"
            )
            db.add_candidate(candidate)

            # Evaluate
            job_id = db.get_job_id_by_title(position)
            job = db.get_job_position(job_id)
            result = agent.evaluate_candidate(candidate, job)

            st.session_state.current_candidate_id = cand_id

            if result['evaluation']['decision'] == "Accepted":
                st.success(f"✅ Application accepted! Score: {result['evaluation']['score']}%")
                st.session_state.candidate_step = "mcq_test"
                st.rerun()
            elif result['evaluation']['decision'] == "Pending Review":
                st.warning("⏳ Application under review")
            else:
                st.error(f"❌ {result['evaluation']['message']}")


def _show_mcq_test(agent, db):
    """MCQ test for accepted candidates"""
    st.subheader("Step 2: Knowledge Assessment")
    cand_id = st.session_state.get('current_candidate_id')
    candidate = db.get_candidate(cand_id)
    if not candidate:
        st.error("Candidate not found"); return

    job_id = db.get_job_id_by_title(candidate.applied_position)
    job = db.get_job_position(job_id)
    if not job or not job.test_questions:
        st.error("No test available"); return

    questions = job.test_questions
    with st.form("mcq_test"):
        answers = {}
        for i, q in enumerate(questions):
            answers[i] = st.radio(f"Q{i+1}: {q['question']}",
                                  q['options'], key=f"mcq_{i}")
        submit = st.form_submit_button("Submit Answers", type="primary")

        if submit:
            correct = sum(1 for i, q in enumerate(questions)
                          if answers[i] == q['correct_answer'])
            score = (correct / len(questions)) * 100
            passing = score >= 60

            if passing:
                st.success(f"✅ Passed! Score: {score:.0f}%")
                st.session_state.candidate_step = "technical_interview"
                st.rerun()
            else:
                st.error(f"❌ Score: {score:.0f}% (need 60%)")


def _show_technical_choice(agent, db):
    """Let candidate choose technical interview mode"""
    st.subheader("Step 3: Technical Interview")
    mode = st.radio("Choose interview mode:",
                    ["💬 Chat Interview (AI Interviewer)",
                     "⚡ Quick Code Test"])
    if st.button("Start", type="primary"):
        if "Chat" in mode:
            st.session_state.candidate_step = "chat_interview"
            st.rerun()
        else:
            st.session_state.candidate_step = "quick_code_test"
            st.rerun()
```

> **Note:** The `chat_interview_ui.py`, `technical_interview_ui.py`, `psychometric_ui.py`, and `video_interview_ui.py` are separate files — see below.

---

## `ui/employee_portal.py`

```python
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
        leave_type = st.selectbox("Leave Type", ["Casual Leave","Sick Leave","Annual Leave","Unpaid Leave"])
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
```

---

## `ui/admin_portal.py`

```python
"""Admin Portal — Employee mgmt, candidates, audit, config"""
import streamlit as st
import datetime
from ui.utils import logout


def show_admin_portal():
    st.sidebar.title("⚙️ Admin Portal")
    page = st.sidebar.radio("Menu", [
        "🏠 Dashboard", "👥 Employees", "📋 Candidates",
        "📊 Audit Report", "⚙️ Settings",
        "🖥️ IT", "💰 Finance", "📜 Compliance",
        "🔄 Orchestrator"])
    if st.sidebar.button("🚪 Logout"):
        logout()

    if page == "🏠 Dashboard":
        _admin_dashboard()
    elif page == "👥 Employees":
        _employee_management()
    elif page == "📋 Candidates":
        _candidate_review()
    elif page == "📊 Audit Report":
        _audit_report()
    elif page == "⚙️ Settings":
        _settings()
    elif page == "🖥️ IT":
        from ui.it_portal import show_it_portal
        show_it_portal()
    elif page == "💰 Finance":
        from ui.finance_portal import show_finance_portal
        show_finance_portal()
    elif page == "📜 Compliance":
        from ui.compliance_portal import show_compliance_portal
        show_compliance_portal()
    elif page == "🔄 Orchestrator":
        from ui.orchestrator_dashboard import show_orchestrator_dashboard
        show_orchestrator_dashboard()


def _admin_dashboard():
    db = st.session_state.db
    st.header("🏠 Admin Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Employees", len(db.employees))
    c2.metric("Candidates", len(db.candidates))
    c3.metric("Open Tickets", len([t for t in getattr(db, 'it_tickets', {}).values()
                                    if getattr(t, 'status', '') == 'Open']))
    c4.metric("Audit Logs", len(db.audit_logs))


def _employee_management():
    db = st.session_state.db
    agent = st.session_state.agents['hr']
    st.header("👥 Employee Management")

    # Onboarding form
    with st.expander("➕ Add New Employee"):
        with st.form("onboard_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            dept = st.text_input("Department")
            pos = st.text_input("Position")
            jdate = st.date_input("Join Date")
            if st.form_submit_button("Create", type="primary"):
                result = agent.handle_employee_onboarding(
                    name, email, dept, pos, jdate.strftime("%Y-%m-%d"))
                st.success(f"✅ Employee {result['employee_id']} created")

    # Employee list
    st.subheader("Current Employees")
    for eid, emp in db.employees.items():
        with st.expander(f"{emp.name} ({eid})"):
            st.write(f"**Dept:** {emp.department} | **Position:** {emp.position}")
            st.write(f"**Email:** {emp.email} | **Joined:** {emp.join_date}")
            st.write(f"**Leave:** Casual={emp.leave_balance.get('Casual Leave',0)}, "
                     f"Sick={emp.leave_balance.get('Sick Leave',0)}, "
                     f"Annual={emp.leave_balance.get('Annual Leave',0)}")


def _candidate_review():
    db = st.session_state.db
    st.header("📋 Candidate Review")
    if not db.candidates:
        st.info("No candidates yet")
        return
    for cid, cand in db.candidates.items():
        with st.expander(f"{cand.name} — {cand.status}"):
            st.write(f"**Position:** {cand.applied_position}")
            st.write(f"**Skills:** {', '.join(cand.extracted_skills)}")
            st.write(f"**Experience:** {cand.experience_years} years")
            if cand.evaluation_result:
                st.write(f"**Score:** {cand.evaluation_result.get('score', 'N/A')}%")
            # View interview results
            from ui.results_viewer_ui import show_candidate_results
            show_candidate_results(cid)


def _audit_report():
    agent = st.session_state.agents['hr']
    st.header("📊 Audit Report")
    c1, c2 = st.columns(2)
    start = c1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
    end = c2.date_input("End Date")
    if st.button("Generate Report", type="primary"):
        report = agent.generate_audit_report(
            start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        summary = report.get('summary', {})
        st.metric("Total Activities", summary.get('total_activities', 0))
        st.json(report)


def _settings():
    db = st.session_state.db
    st.header("⚙️ Eligibility Criteria")
    criteria = db.eligibility_criteria
    with st.form("criteria_form"):
        skill = st.slider("Skill Match Threshold %", 0, 100,
                           criteria.get('skill_match_threshold', 50))
        auto = st.slider("Auto-Accept Threshold %", 0, 100,
                          criteria.get('auto_accept_threshold', 50))
        exp = st.checkbox("Require Experience", criteria.get('experience_required', True))
        edu = st.checkbox("Require Education", criteria.get('education_required', True))
        if st.form_submit_button("Save"):
            db.update_eligibility_criteria({
                'skill_match_threshold': skill, 'auto_accept_threshold': auto,
                'experience_required': exp, 'education_required': edu})
            st.success("✅ Settings saved")
```

---

## Remaining Portal Stubs

Create these files with the **same pattern** — a `show_*()` function that reads from the appropriate agent in `st.session_state.agents`:

### `ui/it_portal.py` — Tickets, access, assets

```python
"""IT Portal — Ticket management, access control, assets"""
import streamlit as st

def show_it_portal():
    it = st.session_state.agents['it']
    st.header("🖥️ IT Management")
    tab1, tab2, tab3 = st.tabs(["🎫 Tickets", "🔐 Access", "💻 Assets"])
    with tab1:
        # Create ticket form + list open tickets
        pass
    with tab2:
        # Grant/revoke access forms
        pass
    with tab3:
        # Asset tracking
        pass
```

### `ui/finance_portal.py` — Expenses, payroll, budget

```python
"""Finance Portal — Expenses, payroll, budget"""
import streamlit as st

def show_finance_portal():
    fin = st.session_state.agents['finance']
    st.header("💰 Finance Management")
    tab1, tab2, tab3 = st.tabs(["📑 Expenses", "💵 Payroll", "📊 Budget"])
    with tab1:
        # Submit/review expenses
        pass
    with tab2:
        # Process payroll + view summary
        pass
    with tab3:
        # Department budget management
        pass
```

### `ui/compliance_portal.py` — Violations, training, audit

```python
"""Compliance Portal — Violations, training, documents"""
import streamlit as st

def show_compliance_portal():
    comp = st.session_state.agents['compliance']
    st.header("📜 Compliance Management")
    tab1, tab2, tab3 = st.tabs(["⚠️ Violations", "📚 Training", "🔍 Audit"])
    with tab1:
        # Report/resolve violations
        pass
    with tab2:
        # Schedule/track training
        pass
    with tab3:
        # Run compliance audit
        pass
```

### `ui/orchestrator_dashboard.py` — Cross-agent view

```python
"""Orchestrator Dashboard — Workflows, agent status, goals"""
import streamlit as st

def show_orchestrator_dashboard():
    orch = st.session_state.orchestrator
    st.header("🔄 Orchestrator Dashboard")

    # Agent statuses
    st.subheader("Agent Status")
    statuses = orch.get_all_agent_statuses()
    for name, caps in statuses.items():
        st.write(f"**{name}:** {', '.join(caps)}")

    # Active workflows
    st.subheader("Active Workflows")
    workflows = orch.get_active_workflows()
    if workflows:
        for wf in workflows:
            st.write(f"• {wf}")
    else:
        st.info("No active workflows")

    # Route a task
    st.subheader("Route a Task")
    task = st.text_input("Describe the task")
    if st.button("Route") and task:
        result = orch.route_task(task)
        st.json(result)
```

---

## Interview UIs (Brief Specs)

### `ui/chat_interview_ui.py`
- Uses `tools.technical_interview_chat.TechnicalInterviewChat`
- Chat-style interface with `st.chat_message`
- Stages: introduction → clarification → approach → coding → review
- Hint button (max 3), submit code button
- Shows final report with scores

### `ui/technical_interview_ui.py`
- Uses `streamlit_ace` for code editor
- Uses `tools.code_executor.CodeExecutor` for running test cases
- Uses `tools.ai_code_analyzer.AICodeAnalyzer` for code review
- Problem selector, language dropdown, run/submit buttons
- Test case results display

### `ui/psychometric_ui.py`
- Uses `tools.psychometric_assessment.PsychometricAssessment`
- Renders 20 questions as `st.radio` widgets
- Shows radar chart of EQ/AQ/SQ/BQ scores
- Shows recommendations

### `ui/video_interview_ui.py`
- Uses `tools.video_analyzer_hybrid.HybridVideoAnalyzer` (optional)
- `st.file_uploader` for video
- Shows confidence score breakdown

### `ui/results_viewer_ui.py`
- Uses `tools.interview_storage.InterviewStorage`
- Browse all candidates and their interview JSONs
- Display scores, conversation transcripts, psychometric results

> **Instruction:** These interview UI files should be ported from the current `chat_interview_ui.py`, `technical_interview_ui.py`, `psychometric_ui.py`, and `results_viewer_ui.py` — updating imports to use `tools.*` and `agents.*` paths.

---

## ✅ Done Checklist

- [ ] `ui/candidate_portal.py` — application form, MCQ, interview mode selection
- [ ] `ui/employee_portal.py` — dashboard, leave, policy Q&A, profile
- [ ] `ui/admin_portal.py` — employees, candidates, audit, settings, links to IT/Finance/Compliance
- [ ] `ui/it_portal.py` — tickets, access, assets (using IT Agent)
- [ ] `ui/finance_portal.py` — expenses, payroll, budget (using Finance Agent)
- [ ] `ui/compliance_portal.py` — violations, training, audit (using Compliance Agent)
- [ ] `ui/orchestrator_dashboard.py` — agent status, workflows, task routing
- [ ] `ui/chat_interview_ui.py` — ported from existing, updated imports
- [ ] `ui/technical_interview_ui.py` — ported from existing, updated imports
- [ ] `ui/psychometric_ui.py` — ported from existing, updated imports
- [ ] `ui/video_interview_ui.py` — ported from existing, updated imports
- [ ] `ui/results_viewer_ui.py` — ported from existing, updated imports
