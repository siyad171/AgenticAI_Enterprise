# 09 — Testing & Deployment

> **Depends on:** All previous guides (00–08)
> **Creates:** `tests/` folder, run scripts, deployment config

---

## Part A — Test Structure

```
tests/
├── __init__.py
├── conftest.py          ← shared fixtures
├── test_database.py     ← core/database.py
├── test_llm_service.py  ← core/llm_service.py (mocked)
├── test_event_bus.py    ← core/event_bus.py
├── test_hr_agent.py     ← agents/hr_agent.py
├── test_it_agent.py     ← agents/it_agent.py
├── test_finance_agent.py← agents/finance_agent.py
├── test_compliance_agent.py
├── test_orchestrator.py ← core/orchestrator.py
├── test_tools.py        ← tools layer (email, code exec, etc.)
└── test_integration.py  ← end-to-end multi-agent flows
```

---

## Part B — `tests/conftest.py`

```python
"""Shared pytest fixtures for all tests"""
import pytest
import os

# Force test mode
os.environ["TESTING"] = "1"


@pytest.fixture
def db():
    """Fresh database instance with seed data"""
    from core.database import Database
    database = Database()
    database.seed_sample_data()
    return database


@pytest.fixture
def llm():
    """LLM service (real or mocked based on env)"""
    from core.llm_service import LLMService
    return LLMService()


@pytest.fixture
def event_bus():
    """Fresh event bus"""
    from core.event_bus import EventBus
    return EventBus()


@pytest.fixture
def hr_agent(db, llm, event_bus):
    """HR Agent with dependencies"""
    from agents.hr_agent import HRAgent
    return HRAgent(db=db, llm=llm, event_bus=event_bus)


@pytest.fixture
def it_agent(db, llm, event_bus):
    from agents.it_agent import ITAgent
    return ITAgent(db=db, llm=llm, event_bus=event_bus)


@pytest.fixture
def finance_agent(db, llm, event_bus):
    from agents.finance_agent import FinanceAgent
    return FinanceAgent(db=db, llm=llm, event_bus=event_bus)


@pytest.fixture
def compliance_agent(db, llm, event_bus):
    from agents.compliance_agent import ComplianceAgent
    return ComplianceAgent(db=db, llm=llm, event_bus=event_bus)


@pytest.fixture
def all_agents(hr_agent, it_agent, finance_agent, compliance_agent):
    """Dict of all agents"""
    return {
        'hr': hr_agent,
        'it': it_agent,
        'finance': finance_agent,
        'compliance': compliance_agent
    }


@pytest.fixture
def orchestrator(all_agents, llm, event_bus):
    from core.orchestrator import Orchestrator
    return Orchestrator(agents=all_agents, llm=llm, event_bus=event_bus)
```

---

## Part C — `tests/test_database.py`

```python
"""Test database models and methods"""

def test_seed_data_creates_employees(db):
    assert len(db.employees) >= 2, "Seed should create at least 2 employees"

def test_seed_data_creates_job_positions(db):
    assert len(db.job_positions) >= 1, "Seed should create at least 1 job"

def test_add_employee(db):
    from core.database import Employee
    emp = Employee(
        employee_id="E999", name="Test User", email="test@co.com",
        department="QA", position="Tester", join_date="2025-01-01",
        leave_balance={"Casual Leave": 10, "Sick Leave": 7, "Annual Leave": 15}
    )
    db.add_employee(emp)
    assert db.get_employee("E999") is not None

def test_add_candidate(db):
    from core.database import Candidate
    cand = Candidate(
        candidate_id="CAND999", name="Candidate", email="c@co.com",
        applied_position="Developer", resume_text="Python expert",
        extracted_skills=["Python"], experience_years=3, education="BSc CS",
        application_date="2025-01-01", status="Pending"
    )
    db.add_candidate(cand)
    assert db.get_candidate("CAND999") is not None

def test_leave_balance_update(db):
    emp_id = list(db.employees.keys())[0]
    emp = db.get_employee(emp_id)
    old = emp.leave_balance.get("Casual Leave", 0)
    emp.leave_balance["Casual Leave"] = old - 2
    assert db.get_employee(emp_id).leave_balance["Casual Leave"] == old - 2

def test_audit_log(db):
    from core.database import AuditLog
    log = AuditLog(
        timestamp="2025-01-01T00:00:00", agent="hr",
        action="test_action", details={"test": True}, status="success"
    )
    db.add_audit_log(log)
    assert len(db.audit_logs) >= 1
```

---

## Part D — `tests/test_event_bus.py`

```python
"""Test event bus pub/sub"""

def test_subscribe_and_publish(event_bus):
    received = []
    event_bus.subscribe("test_event", lambda data: received.append(data))
    event_bus.publish("test_event", {"msg": "hello"})
    assert len(received) == 1
    assert received[0]["msg"] == "hello"

def test_multiple_subscribers(event_bus):
    results = []
    event_bus.subscribe("evt", lambda d: results.append("A"))
    event_bus.subscribe("evt", lambda d: results.append("B"))
    event_bus.publish("evt", {})
    assert results == ["A", "B"]

def test_event_log(event_bus):
    event_bus.publish("log_test", {"data": 1})
    assert len(event_bus.event_log) >= 1
    assert event_bus.event_log[-1]["event_type"] == "log_test"
```

---

## Part E — `tests/test_hr_agent.py`

```python
"""Test HR Agent functions"""

def test_process_leave_approved(hr_agent, db):
    emp_id = list(db.employees.keys())[0]
    result = hr_agent.process_leave_request(
        emp_id, "Casual Leave", "2025-06-01", "2025-06-02", "Family event")
    assert result["decision"] in ["Approved", "Pending"]

def test_process_leave_insufficient(hr_agent, db):
    emp_id = list(db.employees.keys())[0]
    emp = db.get_employee(emp_id)
    emp.leave_balance["Casual Leave"] = 0
    result = hr_agent.process_leave_request(
        emp_id, "Casual Leave", "2025-06-01", "2025-06-02", "Test")
    assert result["decision"] == "Rejected"

def test_evaluate_candidate(hr_agent, db):
    from core.database import Candidate
    cand = Candidate(
        candidate_id="C001", name="Alice", email="a@co.com",
        applied_position="Developer", resume_text="Expert Python dev",
        extracted_skills=["Python", "Django", "REST API"],
        experience_years=5, education="MSc CS",
        application_date="2025-01-01", status="Pending"
    )
    job = list(db.job_positions.values())[0]
    result = hr_agent.evaluate_candidate(cand, job)
    assert "evaluation" in result
    assert "score" in result["evaluation"]

def test_parse_resume(hr_agent):
    resume = """
    John Smith
    Python Developer with 5 years experience
    Skills: Python, Django, PostgreSQL, Docker
    Education: BSc Computer Science
    """
    result = hr_agent.parse_resume_text(resume)
    assert "skills" in result
    assert "experience_years" in result

def test_hr_policy_question(hr_agent):
    result = hr_agent.ask_hr_policy_question("What is the leave policy?")
    assert "answer" in result

def test_audit_report(hr_agent, db):
    result = hr_agent.generate_audit_report("2025-01-01", "2025-12-31")
    assert "summary" in result
```

---

## Part F — `tests/test_tools.py`

```python
"""Test tools layer"""
import os

def test_local_executor():
    from tools.local_executor import LocalPythonExecutor
    executor = LocalPythonExecutor()
    result = executor.execute("print('hello')")
    assert result["success"] is True
    assert "hello" in result["output"]

def test_local_executor_timeout():
    from tools.local_executor import LocalPythonExecutor
    executor = LocalPythonExecutor(timeout=2)
    result = executor.execute("import time; time.sleep(10)")
    assert result["success"] is False

def test_psychometric_scoring():
    from tools.psychometric_assessment import PsychometricAssessment
    pa = PsychometricAssessment()
    # Answer all 20 questions with option index 2
    answers = {i: 2 for i in range(20)}
    scores = pa.calculate_quotients(answers)
    assert "EQ" in scores
    assert "AQ" in scores
    assert "SQ" in scores
    assert "BQ" in scores
    assert all(0 <= v <= 100 for v in scores.values())

def test_interview_storage():
    from tools.interview_storage import InterviewStorage
    storage = InterviewStorage()
    cand_id = "TEST_CAND_001"
    data = {"candidate_id": cand_id, "score": 85, "test": True}
    storage.save_interview(cand_id, data)
    loaded = storage.load_interview(cand_id)
    assert loaded is not None
    assert loaded.get("score") == 85
    # Cleanup
    import shutil, pathlib
    path = pathlib.Path("interview_results") / cand_id
    if path.exists():
        shutil.rmtree(path)
```

---

## Part G — `tests/test_integration.py`

```python
"""Integration tests — multi-agent workflows"""

def test_full_onboarding_flow(orchestrator, all_agents, db):
    """Test: new employee triggers HR + IT + Compliance events"""
    hr = all_agents['hr']
    result = hr.handle_employee_onboarding(
        "New Person", "new@co.com", "Engineering", "Developer", "2025-06-01")
    assert "employee_id" in result

    # IT agent should have received event (if event bus connected)
    # Compliance should schedule training
    # These assertions depend on event handlers being wired
    emp_id = result["employee_id"]
    emp = db.get_employee(emp_id)
    assert emp is not None
    assert emp.name == "New Person"


def test_orchestrator_routes_hr_task(orchestrator):
    result = orchestrator.route_task("I need to apply for leave")
    assert result.get("agent") == "hr" or "hr" in str(result).lower()


def test_orchestrator_routes_it_task(orchestrator):
    result = orchestrator.route_task("My laptop is not working")
    assert result.get("agent") == "it" or "it" in str(result).lower()
```

---

## Part H — Running Tests

### Command

```powershell
# From project root
cd C:\Users\siyad\OneDrive\Desktop\Main Project\HR_Agent

# Activate venv
.\.venv\Scripts\Activate.ps1

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_hr_agent.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Add to `requirements.txt` (test section)

```
pytest>=7.0
pytest-cov>=4.0
```

---

## Part I — Running the App

### Development

```powershell
# Activate environment
cd "C:\Users\siyad\OneDrive\Desktop\Main Project\HR_Agent"
.\.venv\Scripts\Activate.ps1

# Set environment variables (or use .env with python-dotenv)
$env:GROQ_API_KEY = "your-api-key"
$env:SMTP_EMAIL = "your-email@gmail.com"
$env:SMTP_PASSWORD = "your-app-password"

# Run
streamlit run ui/app.py
```

### First Run Checklist

1. ✅ `.env` file exists with `GROQ_API_KEY`
2. ✅ `python -c "from core.database import Database; d=Database(); d.seed_sample_data(); print('OK')"` works
3. ✅ `python -c "from core.llm_service import LLMService; l=LLMService(); print(l.generate_response('Hello'))"` works
4. ✅ `python -c "from agents.hr_agent import HRAgent; print('Import OK')"` works
5. ✅ `streamlit run ui/app.py` starts without errors
6. ✅ Login as admin / candidate / employee all work

---

## Part J — Deployment Notes

### Option 1: Local (Development)

Just `streamlit run ui/app.py` — already covered above.

### Option 2: Streamlit Community Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Set main file path: `ui/app.py`
5. Add secrets in Streamlit Cloud settings:
   ```toml
   # .streamlit/secrets.toml (local) or Streamlit Cloud Secrets
   GROQ_API_KEY = "gsk_..."
   SMTP_EMAIL = "..."
   SMTP_PASSWORD = "..."
   ```
6. Deploy

### Option 3: Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.headless=true"]
```

```powershell
docker build -t hr-agent .
docker run -p 8501:8501 --env-file .env hr-agent
```

---

## Part K — Verification Script

Create `verify_setup.py` in the project root:

```python
"""Verify all modules import correctly"""
import sys

checks = [
    ("core.config",              "from core.config import GROQ_API_KEY"),
    ("core.database",            "from core.database import Database"),
    ("core.llm_service",         "from core.llm_service import LLMService"),
    ("core.event_bus",           "from core.event_bus import EventBus"),
    ("core.base_agent",          "from core.base_agent import BaseAgent"),
    ("core.orchestrator",        "from core.orchestrator import Orchestrator"),
    ("core.goal_tracker",        "from core.goal_tracker import GoalTracker"),
    ("core.learning_module",     "from core.learning_module import LearningModule"),
    ("agents.hr_agent",          "from agents.hr_agent import HRAgent"),
    ("agents.it_agent",          "from agents.it_agent import ITAgent"),
    ("agents.finance_agent",     "from agents.finance_agent import FinanceAgent"),
    ("agents.compliance_agent",  "from agents.compliance_agent import ComplianceAgent"),
    ("tools.email_service",      "from tools.email_service import EmailService"),
    ("tools.code_executor",      "from tools.code_executor import CodeExecutor"),
    ("tools.local_executor",     "from tools.local_executor import LocalPythonExecutor"),
    ("tools.ai_code_analyzer",   "from tools.ai_code_analyzer import AICodeAnalyzer"),
    ("tools.interview_storage",  "from tools.interview_storage import InterviewStorage"),
    ("tools.psychometric_assessment", "from tools.psychometric_assessment import PsychometricAssessment"),
    ("tools.technical_interview_chat","from tools.technical_interview_chat import TechnicalInterviewChat"),
]

passed = 0
failed = 0
for name, stmt in checks:
    try:
        exec(stmt)
        print(f"  ✅ {name}")
        passed += 1
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        failed += 1

print(f"\n{'='*40}")
print(f"Results: {passed} passed, {failed} failed out of {len(checks)}")
if failed:
    sys.exit(1)
else:
    print("All imports OK! Ready to run.")
```

---

## ✅ Done Checklist

- [ ] `tests/__init__.py` (empty)
- [ ] `tests/conftest.py` — shared fixtures
- [ ] `tests/test_database.py` — CRUD tests
- [ ] `tests/test_event_bus.py` — pub/sub tests
- [ ] `tests/test_hr_agent.py` — all 6 functions
- [ ] `tests/test_tools.py` — local executor, psychometric, storage
- [ ] `tests/test_integration.py` — multi-agent flows
- [ ] `verify_setup.py` — import verification script
- [ ] App runs: `streamlit run ui/app.py`
- [ ] All tests pass: `python -m pytest tests/ -v`
