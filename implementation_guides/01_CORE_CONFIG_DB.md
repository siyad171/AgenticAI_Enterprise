# 🗃️ Step 1: Core Config + Database

> **Requires**: `00_PROJECT_SETUP.md` completed  
> **Creates**: `core/config.py`, `core/database.py`  
> **Next**: → `02_CORE_SERVICES.md`

---

## File 1: `core/config.py`

Central configuration. **All magic numbers, thresholds, and settings live here.** Agents import from this — never hardcode values.

```python
"""
core/config.py — Centralized configuration
All agents and tools read from this single file.
Admin can override some values via the UI (stored in DB).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# LLM Provider (Groq — free tier)
# ──────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_CHAT_MODEL = "llama-3.1-8b-instant"       # Fast: conversation, chat
LLM_ANALYSIS_MODEL = "llama-3.3-70b-versatile" # Deep: analysis, evaluation
LLM_WHISPER_MODEL = "whisper-large-v3-turbo"   # Audio transcription
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 800

# ──────────────────────────────────────────────
# Email (SMTP)
# ──────────────────────────────────────────────
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# ──────────────────────────────────────────────
# Code Execution (Judge0)
# ──────────────────────────────────────────────
JUDGE0_API_KEY = os.getenv("JUDGE0_API_KEY", "")

# ──────────────────────────────────────────────
# HR Agent
# ──────────────────────────────────────────────
LEAVE_AUTO_APPROVE_MAX_DAYS = 10
LEAVE_BALANCE_DEFAULT = {
    "Casual Leave": 12,
    "Sick Leave": 15,
    "Annual Leave": 20
}
CANDIDATE_ACCEPT_THRESHOLD = 50
CANDIDATE_REVIEW_THRESHOLD = 40
TEST_PASS_THRESHOLD = 60
EXPERIENCE_PENALTY_FACTOR = 0.7
EDUCATION_PENALTY_FACTOR = 0.8

# ──────────────────────────────────────────────
# IT Agent
# ──────────────────────────────────────────────
IT_PROVISIONING_SLA_HOURS = 24
PASSWORD_MIN_LENGTH = 12
PASSWORD_ROTATION_DAYS = 90
APPROVED_SOFTWARE = [
    "VS Code", "Slack", "Jira", "GitHub",
    "Zoom", "Chrome", "Firefox"
]

# ──────────────────────────────────────────────
# Finance Agent
# ──────────────────────────────────────────────
EXPENSE_AUTO_APPROVE_LIMIT = 5000
EXPENSE_MANAGER_NOTIFY_LIMIT = 25000
BUDGET_ALERT_THRESHOLD_PERCENT = 90
DEFAULT_SALARIES = {
    "Engineering": 80000,
    "Marketing": 70000,
    "Sales": 60000,
    "HR": 65000,
    "Finance": 75000,
}

# ──────────────────────────────────────────────
# Compliance Agent
# ──────────────────────────────────────────────
TRAINING_OVERDUE_DAYS = 30
AUDIT_PASS_SCORE = 70
DOCUMENT_RETENTION_YEARS = 7
MANDATORY_TRAININGS = [
    {"name": "Data Privacy & Protection", "frequency": "Annual", "duration": "2 hours"},
    {"name": "Workplace Safety", "frequency": "Annual", "duration": "1 hour"},
    {"name": "Anti-Harassment Awareness", "frequency": "Annual", "duration": "1.5 hours"},
    {"name": "Security Awareness", "frequency": "Quarterly", "duration": "30 minutes"},
]

# ──────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────
ESCALATION_CONFIDENCE_THRESHOLD = 0.6

# ──────────────────────────────────────────────
# Storage Paths
# ──────────────────────────────────────────────
INTERVIEW_RESULTS_DIR = "data/interview_results"
LEARNING_DATA_DIR = "data/learning"
UPLOADS_DIR = "data/uploads"
```

---

## File 2: `core/database.py`

This is the **largest single file** in the project. It contains:
1. All Enums
2. All 20+ dataclasses (data models)
3. The `Database` class with 50+ methods
4. The `_initialize_data()` seed data

### Part A — Enums

```python
"""
core/database.py — Unified in-memory database for all agents
"""
import datetime
import random
import string
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

# ═══════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════

class LeaveType(Enum):
    CASUAL = "Casual Leave"
    SICK = "Sick Leave"
    ANNUAL = "Annual Leave"
    UNPAID = "Unpaid Leave"

class LeaveStatus(Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class TicketStatus(Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

class TicketPriority(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class ExpenseStatus(Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    REIMBURSED = "Reimbursed"

class TrainingStatus(Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    OVERDUE = "Overdue"

class ViolationSeverity(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"
```

### Part B — HR Data Models

```python
# ═══════════════════════════════════════════════════
# HR DATA MODELS
# ═══════════════════════════════════════════════════

@dataclass
class Employee:
    employee_id: str
    name: str
    email: str
    department: str
    position: str
    join_date: str                     # "YYYY-MM-DD"
    leave_balance: Dict[str, int]      # {"Casual Leave": 12, ...}

@dataclass
class LeaveRequest:
    request_id: str
    employee_id: str
    employee_name: str
    leave_type: str                    # LeaveType value strings
    start_date: str
    end_date: str
    days: int
    reason: str
    status: str                        # "Pending" | "Approved" | "Rejected"
    submitted_date: str
    processed_date: Optional[str] = None

@dataclass
class JobPosition:
    job_id: str
    title: str
    department: str
    description: str
    required_skills: List[str]
    min_experience: int                # years
    min_education: str
    status: str                        # "Active" | "Closed"
    test_questions: Optional[List[Dict]] = None
    # Each: {"question": str, "options": [str], "correct_answer": str}

@dataclass
class Candidate:
    candidate_id: str
    name: str
    email: str
    phone: str
    applied_position: str
    resume_text: str
    extracted_skills: List[str]
    experience_years: int
    education: str
    application_date: str
    status: str                        # Pending|Accepted|Rejected|Test_Scheduled|Hired
    evaluation_result: Optional[Dict] = None
    test_score: Optional[float] = None
    test_taken: bool = False

@dataclass
class User:
    username: str
    password: str
    role: str                          # Candidate|Employee|Admin|IT_Admin|Finance_Admin
    employee_id: Optional[str] = None

@dataclass
class TechnicalProblem:
    problem_id: str
    title: str
    difficulty: str                    # Easy | Medium | Hard
    description: str
    input_format: str
    output_format: str
    constraints: str
    examples: List[Dict]               # [{"input", "output", "explanation"}]
    test_cases: List[Dict]             # [{"input", "expected", "visible": bool}]
    time_limit: float                  # seconds
    memory_limit: int                  # KB
    tags: List[str]
    starter_code: Dict[str, str]       # {"python": "...", "java": "...", "cpp": "..."}

@dataclass
class CodeSubmission:
    submission_id: str
    candidate_id: str
    problem_id: str
    code: str
    language: str
    submitted_at: str
    test_results: Optional[Dict] = None
    ai_analysis: Optional[Dict] = None
    interview_qa: Optional[List[Dict]] = None
    conversation_transcript: Optional[List[Dict]] = None
    hints_used: int = 0
    approach_score: int = 0
    communication_score: int = 0
    final_interview_score: Optional[int] = None
    final_score: Optional[float] = None

@dataclass
class AuditLog:
    log_id: str
    timestamp: str
    agent: str                         # "HR Agent" | "IT Agent" | etc.
    action: str
    details: Dict
    user: str
```

### Part C — IT Data Models (New)

```python
# ═══════════════════════════════════════════════════
# IT DATA MODELS
# ═══════════════════════════════════════════════════

@dataclass
class ITTicket:
    ticket_id: str
    employee_id: str
    category: str                      # Password Reset|Software Install|VPN|Hardware|Access|Other
    subject: str
    description: str
    priority: str                      # TicketPriority values
    status: str                        # TicketStatus values
    created_date: str
    resolved_date: Optional[str] = None
    resolution: Optional[str] = None
    assigned_to: str = "IT Agent"

@dataclass
class AccessRecord:
    record_id: str
    employee_id: str
    systems: List[str]                 # ["Email", "Slack", "GitHub", ...]
    role_permissions: str              # Standard|Developer|Manager|Admin
    provisioned_date: str
    status: str                        # Active | Revoked
    revoked_date: Optional[str] = None

@dataclass
class SoftwareLicense:
    license_id: str
    software_name: str
    total_licenses: int
    used_licenses: int
    cost_per_license: float
    renewal_date: str

@dataclass
class ITAsset:
    asset_id: str
    asset_type: str                    # Laptop|Monitor|Phone|Headset
    model: str
    assigned_to: Optional[str] = None  # employee_id or None
    status: str = "Available"          # Available|Assigned|Repair|Retired
```

### Part D — Finance Data Models (New)

```python
# ═══════════════════════════════════════════════════
# FINANCE DATA MODELS
# ═══════════════════════════════════════════════════

@dataclass
class ExpenseClaim:
    claim_id: str
    employee_id: str
    category: str                      # Travel|Meals|Software|Equipment|Training|Other
    amount: float
    description: str
    receipt_uploaded: bool
    submitted_date: str
    status: str                        # ExpenseStatus values
    approved_date: Optional[str] = None
    approver: Optional[str] = None
    rejection_reason: Optional[str] = None

@dataclass
class PayrollRecord:
    record_id: str
    employee_id: str
    month: str                         # "2026-02"
    gross_salary: float
    deductions: Dict[str, float]       # {"tax": 5000, "insurance": 2000}
    net_salary: float
    payment_date: str
    status: str                        # Pending|Processed|Paid

@dataclass
class Budget:
    budget_id: str
    department: str
    fiscal_year: str                   # "2026"
    allocated_amount: float
    spent_amount: float
    category_breakdown: Dict[str, float]

@dataclass
class Reimbursement:
    reimbursement_id: str
    employee_id: str
    claim_id: str
    amount: float
    processed_date: str
    payment_method: str                # "Bank Transfer" | "Check"
    status: str                        # Pending|Processed|Completed
```

### Part E — Compliance Data Models (New)

```python
# ═══════════════════════════════════════════════════
# COMPLIANCE DATA MODELS
# ═══════════════════════════════════════════════════

@dataclass
class Violation:
    violation_id: str
    violation_type: str                # Training Overdue|Policy Breach|Data Privacy|Expense Anomaly
    employee_id: Optional[str]
    description: str
    severity: str                      # ViolationSeverity values
    detected_date: str
    detected_by: str                   # Agent name
    status: str                        # Open|Under Review|Resolved|Dismissed
    resolution: Optional[str] = None
    resolved_date: Optional[str] = None

@dataclass
class TrainingRecord:
    record_id: str
    employee_id: str
    training_name: str
    required: bool
    status: str                        # TrainingStatus values
    due_date: str
    completed_date: Optional[str] = None
    score: Optional[float] = None

@dataclass
class ComplianceAudit:
    audit_id: str
    audit_date: str
    scope: str                         # Full|HR|IT|Finance
    score: float                       # 0-100
    findings: List[Dict]               # [{"area", "issue", "severity"}]
    recommendations: List[str]
    conducted_by: str

@dataclass
class ComplianceDocument:
    doc_id: str
    employee_id: str
    document_type: str                 # ID Proof|Educational Certificate|Tax Form|NDA
    uploaded_date: str
    verified: bool
    verified_by: Optional[str] = None
```

### Part F — Database Class

```python
# ═══════════════════════════════════════════════════
# DATABASE CLASS
# ═══════════════════════════════════════════════════

class Database:
    """Unified in-memory database for all agents."""

    def __init__(self):
        # --- HR ---
        self.employees: Dict[str, Employee] = {}
        self.leave_requests: Dict[str, LeaveRequest] = {}
        self.job_positions: Dict[str, JobPosition] = {}
        self.candidates: Dict[str, Candidate] = {}
        self.users: Dict[str, User] = {}
        self.technical_problems: Dict[str, TechnicalProblem] = {}
        self.code_submissions: Dict[str, CodeSubmission] = {}
        self.hr_policies: Dict[str, str] = {}
        self.eligibility_criteria: Dict = {}

        # --- IT ---
        self.it_tickets: Dict[str, ITTicket] = {}
        self.access_records: Dict[str, AccessRecord] = {}
        self.software_licenses: Dict[str, SoftwareLicense] = {}
        self.it_assets: Dict[str, ITAsset] = {}
        self.it_policies: Dict[str, str] = {}

        # --- Finance ---
        self.expense_claims: Dict[str, ExpenseClaim] = {}
        self.payroll_records: Dict[str, PayrollRecord] = {}
        self.budgets: Dict[str, Budget] = {}
        self.reimbursements: Dict[str, Reimbursement] = {}
        self.finance_policies: Dict[str, str] = {}

        # --- Compliance ---
        self.violations: Dict[str, Violation] = {}
        self.training_records: Dict[str, TrainingRecord] = {}
        self.compliance_audits: Dict[str, ComplianceAudit] = {}
        self.compliance_documents: Dict[str, ComplianceDocument] = {}
        self.compliance_policies: Dict[str, str] = {}

        # --- Shared ---
        self.audit_logs: List[AuditLog] = []

        self._initialize_data()
```

### Part G — HR Methods (Existing — preserve exactly)

```python
    # ═══════════════════ HR METHODS ═══════════════════

    def get_employee(self, employee_id: str) -> Optional[Employee]:
        return self.employees.get(employee_id)

    def add_employee(self, employee: Employee):
        self.employees[employee.employee_id] = employee

    def search_employee_by_name(self, name: str) -> Optional[Employee]:
        name_lower = name.lower()
        for emp in self.employees.values():
            if name_lower in emp.name.lower():
                return emp
        return None

    def get_employee_summary(self) -> str:
        """Formatted text injected into LLM system prompt."""
        summary = "CURRENT EMPLOYEE DATABASE:\n\n"
        for emp_id, emp in self.employees.items():
            summary += f"""Employee ID: {emp.employee_id}
Name: {emp.name}
Email: {emp.email}
Department: {emp.department}
Position: {emp.position}
Join Date: {emp.join_date}
Leave Balance:
  - Casual Leave: {emp.leave_balance.get('Casual Leave', 0)} days
  - Sick Leave: {emp.leave_balance.get('Sick Leave', 0)} days
  - Annual Leave: {emp.leave_balance.get('Annual Leave', 0)} days
---
"""
        return summary

    def add_leave_request(self, leave_request: LeaveRequest):
        self.leave_requests[leave_request.request_id] = leave_request

    def update_leave_balance(self, employee_id: str, leave_type: str, days: int):
        if employee_id in self.employees:
            self.employees[employee_id].leave_balance[leave_type] -= days

    def check_leave_date_conflict(self, employee_id: str, start_date: str, end_date: str) -> Optional[LeaveRequest]:
        """Check overlap with any approved leave for this employee."""
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        for req in self.leave_requests.values():
            if req.employee_id == employee_id and req.status == LeaveStatus.APPROVED.value:
                ex_start = datetime.datetime.strptime(req.start_date, "%Y-%m-%d")
                ex_end = datetime.datetime.strptime(req.end_date, "%Y-%m-%d")
                if not (end < ex_start or start > ex_end):
                    return req
        return None

    def add_candidate(self, candidate: Candidate):
        self.candidates[candidate.candidate_id] = candidate

    def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        return self.candidates.get(candidate_id)

    def update_candidate_test_status(self, candidate_id: str, test_score: float, passed: bool):
        if candidate_id in self.candidates:
            self.candidates[candidate_id].test_score = test_score
            self.candidates[candidate_id].test_taken = True
            self.candidates[candidate_id].status = "Hired" if passed else "Rejected"

    def convert_candidate_to_employee(self, candidate_id: str):
        """Returns (username, password, employee_id) or (None, None, None)."""
        candidate = self.candidates.get(candidate_id)
        if not candidate or candidate.status != "Hired":
            return None, None, None

        employee_id = f"EMP{len(self.employees) + 1:03d}"
        username = candidate.email.split('@')[0].lower()
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        job_id = self.get_job_id_by_title(candidate.applied_position)
        dept = self.job_positions[job_id].department if job_id else "General"

        employee = Employee(
            employee_id=employee_id,
            name=candidate.name,
            email=candidate.email,
            department=dept,
            position=candidate.applied_position,
            join_date=datetime.datetime.now().strftime("%Y-%m-%d"),
            leave_balance={"Casual Leave": 12, "Sick Leave": 15, "Annual Leave": 20}
        )
        self.employees[employee_id] = employee
        self.users[username] = User(username=username, password=password, role="Employee", employee_id=employee_id)
        return username, password, employee_id

    def add_job_position(self, job: JobPosition):
        self.job_positions[job.job_id] = job

    def get_job_position(self, job_id: str) -> Optional[JobPosition]:
        return self.job_positions.get(job_id)

    def get_job_id_by_title(self, title: str) -> Optional[str]:
        for job_id, job in self.job_positions.items():
            if job.title == title:
                return job_id
        return None

    def update_eligibility_criteria(self, criteria: Dict):
        self.eligibility_criteria.update(criteria)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.users.get(username)
        if user and user.password == password:
            return user
        return None

    def add_user(self, user: User):
        self.users[user.username] = user

    def get_hr_policy(self, policy_type: str) -> str:
        return self.hr_policies.get(policy_type, "Policy not found")

    def get_all_policies(self) -> str:
        """Returns ALL policies (HR + IT + Finance + Compliance) formatted."""
        all_p = {}
        all_p.update(self.hr_policies)
        all_p.update(self.it_policies)
        all_p.update(self.finance_policies)
        all_p.update(self.compliance_policies)
        return "\n\n".join(f"=== {k.upper()} ===\n{v}" for k, v in all_p.items())

    def get_technical_problem(self, problem_id: str) -> Optional[TechnicalProblem]:
        return self.technical_problems.get(problem_id)

    def get_problems_by_difficulty(self, difficulty: str) -> List[TechnicalProblem]:
        return [p for p in self.technical_problems.values() if p.difficulty == difficulty]

    def add_code_submission(self, submission: CodeSubmission):
        self.code_submissions[submission.submission_id] = submission

    def get_candidate_submissions(self, candidate_id: str) -> List[CodeSubmission]:
        return [s for s in self.code_submissions.values() if s.candidate_id == candidate_id]

    def update_submission_results(self, submission_id: str, test_results: Dict, ai_analysis: Dict):
        if submission_id in self.code_submissions:
            self.code_submissions[submission_id].test_results = test_results
            self.code_submissions[submission_id].ai_analysis = ai_analysis

    def update_submission_interview_qa(self, submission_id: str, qa_entry: Dict):
        if submission_id in self.code_submissions:
            if self.code_submissions[submission_id].interview_qa is None:
                self.code_submissions[submission_id].interview_qa = []
            self.code_submissions[submission_id].interview_qa.append(qa_entry)

    def update_submission_final_score(self, submission_id: str, final_score: float):
        if submission_id in self.code_submissions:
            self.code_submissions[submission_id].final_score = final_score

    def add_audit_log(self, log: AuditLog):
        self.audit_logs.append(log)
```

### Part H — IT Methods (New)

```python
    # ═══════════════════ IT METHODS ═══════════════════

    def add_it_ticket(self, ticket: ITTicket):
        self.it_tickets[ticket.ticket_id] = ticket

    def get_it_ticket(self, ticket_id: str) -> Optional[ITTicket]:
        return self.it_tickets.get(ticket_id)

    def get_employee_tickets(self, employee_id: str) -> List[ITTicket]:
        return [t for t in self.it_tickets.values() if t.employee_id == employee_id]

    def update_ticket_status(self, ticket_id: str, status: str, resolution: str = None):
        if ticket_id in self.it_tickets:
            self.it_tickets[ticket_id].status = status
            if resolution:
                self.it_tickets[ticket_id].resolution = resolution
            if status in ("Resolved", "Closed"):
                self.it_tickets[ticket_id].resolved_date = datetime.datetime.now().isoformat()

    def add_access_record(self, record: AccessRecord):
        self.access_records[record.record_id] = record

    def get_employee_access(self, employee_id: str) -> Optional[AccessRecord]:
        for rec in self.access_records.values():
            if rec.employee_id == employee_id and rec.status == "Active":
                return rec
        return None

    def revoke_access(self, employee_id: str):
        for rec in self.access_records.values():
            if rec.employee_id == employee_id and rec.status == "Active":
                rec.status = "Revoked"
                rec.revoked_date = datetime.datetime.now().isoformat()

    def add_software_license(self, license_obj: SoftwareLicense):
        self.software_licenses[license_obj.license_id] = license_obj

    def update_license_usage(self, license_id: str, change: int):
        if license_id in self.software_licenses:
            self.software_licenses[license_id].used_licenses += change

    def add_it_asset(self, asset: ITAsset):
        self.it_assets[asset.asset_id] = asset

    def assign_asset(self, asset_id: str, employee_id: str):
        if asset_id in self.it_assets:
            self.it_assets[asset_id].assigned_to = employee_id
            self.it_assets[asset_id].status = "Assigned"

    def get_it_policy(self, policy_type: str) -> str:
        return self.it_policies.get(policy_type, "Policy not found")
```

### Part I — Finance Methods (New)

```python
    # ═══════════════════ FINANCE METHODS ═══════════════════

    def add_expense_claim(self, claim: ExpenseClaim):
        self.expense_claims[claim.claim_id] = claim

    def get_expense_claim(self, claim_id: str) -> Optional[ExpenseClaim]:
        return self.expense_claims.get(claim_id)

    def get_employee_expenses(self, employee_id: str) -> List[ExpenseClaim]:
        return [c for c in self.expense_claims.values() if c.employee_id == employee_id]

    def update_expense_status(self, claim_id: str, status: str, approver: str = None, reason: str = None):
        if claim_id in self.expense_claims:
            self.expense_claims[claim_id].status = status
            if approver:
                self.expense_claims[claim_id].approver = approver
            if reason:
                self.expense_claims[claim_id].rejection_reason = reason
            if status == "Approved":
                self.expense_claims[claim_id].approved_date = datetime.datetime.now().isoformat()

    def add_payroll_record(self, record: PayrollRecord):
        self.payroll_records[record.record_id] = record

    def get_employee_payroll(self, employee_id: str, month: str = None) -> List[PayrollRecord]:
        records = [r for r in self.payroll_records.values() if r.employee_id == employee_id]
        if month:
            records = [r for r in records if r.month == month]
        return records

    def add_budget(self, budget: Budget):
        self.budgets[budget.budget_id] = budget

    def get_department_budget(self, department: str) -> Optional[Budget]:
        for b in self.budgets.values():
            if b.department == department:
                return b
        return None

    def update_budget_spent(self, department: str, amount: float):
        for b in self.budgets.values():
            if b.department == department:
                b.spent_amount += amount
                break

    def add_reimbursement(self, reimbursement: Reimbursement):
        self.reimbursements[reimbursement.reimbursement_id] = reimbursement

    def get_finance_policy(self, policy_type: str) -> str:
        return self.finance_policies.get(policy_type, "Policy not found")
```

### Part J — Compliance Methods (New)

```python
    # ═══════════════════ COMPLIANCE METHODS ═══════════════════

    def add_violation(self, violation: Violation):
        self.violations[violation.violation_id] = violation

    def get_open_violations(self) -> List[Violation]:
        return [v for v in self.violations.values() if v.status in ("Open", "Under Review")]

    def update_violation_status(self, violation_id: str, status: str, resolution: str = None):
        if violation_id in self.violations:
            self.violations[violation_id].status = status
            if resolution:
                self.violations[violation_id].resolution = resolution
            if status in ("Resolved", "Dismissed"):
                self.violations[violation_id].resolved_date = datetime.datetime.now().isoformat()

    def add_training_record(self, record: TrainingRecord):
        self.training_records[record.record_id] = record

    def get_employee_training(self, employee_id: str) -> List[TrainingRecord]:
        return [t for t in self.training_records.values() if t.employee_id == employee_id]

    def get_overdue_training(self) -> List[TrainingRecord]:
        now = datetime.datetime.now()
        overdue = []
        for t in self.training_records.values():
            if t.status != TrainingStatus.COMPLETED.value:
                due = datetime.datetime.strptime(t.due_date, "%Y-%m-%d")
                if now > due:
                    overdue.append(t)
        return overdue

    def update_training_status(self, record_id: str, status: str, score: float = None):
        if record_id in self.training_records:
            self.training_records[record_id].status = status
            if score is not None:
                self.training_records[record_id].score = score
            if status == TrainingStatus.COMPLETED.value:
                self.training_records[record_id].completed_date = datetime.datetime.now().isoformat()

    def add_compliance_audit(self, audit: ComplianceAudit):
        self.compliance_audits[audit.audit_id] = audit

    def add_compliance_document(self, doc: ComplianceDocument):
        self.compliance_documents[doc.doc_id] = doc

    def get_employee_documents(self, employee_id: str) -> List[ComplianceDocument]:
        return [d for d in self.compliance_documents.values() if d.employee_id == employee_id]

    def verify_document(self, doc_id: str, verified_by: str):
        if doc_id in self.compliance_documents:
            self.compliance_documents[doc_id].verified = True
            self.compliance_documents[doc_id].verified_by = verified_by

    def get_compliance_policy(self, policy_type: str) -> str:
        return self.compliance_policies.get(policy_type, "Policy not found")
```

### Part K — Seed Data (`_initialize_data`)

This method is long. It must include all the sample data from the existing project plus new IT/Finance/Compliance seed data.

**HR seed data to preserve exactly** (from current `hr_agent.py`):
- 2 Employees (EMP001 John Doe — Engineering, EMP002 Jane Smith — Marketing)
- 3 Users (admin/admin123, john.doe/pass123, jane.smith/pass123)
- 2 Job Positions with full MCQ test questions (JOB001 Senior Dev — 5 Python/Django questions, JOB002 Marketing Manager — 5 marketing questions)
- 2 Technical Problems with starter code in 3 languages (PROB001 Two Sum, PROB002 Valid Parentheses)
- 4 HR Policies (leave, onboarding, working_hours, code_of_conduct)
- Eligibility criteria defaults

**New IT seed data**:
```python
# IT Policies
self.it_policies = {
    "password_policy": """PASSWORD POLICY: Min 12 chars, uppercase+lowercase+digit+special, rotate every 90 days, MFA required for all accounts.""",
    "software_policy": """SOFTWARE INSTALLATION: Only approved software list. Others require IT admin approval. Approved: VS Code, Slack, Jira, GitHub, Zoom, Chrome, Firefox.""",
    "byod_policy": """BYOD POLICY: Must have antivirus, device must be encrypted, must register with IT department.""",
    "vpn_policy": """VPN POLICY: Required for all remote work. Auto-disconnect after 12 hours inactivity.""",
    "incident_response": """INCIDENT RESPONSE: Report within 1 hour. IT investigates within 4 hours. Critical incidents escalated immediately."""
}

# Software Licenses
self.software_licenses = {
    "LIC001": SoftwareLicense("LIC001", "Jira", 50, 42, 10.0, "2026-12-31"),
    "LIC002": SoftwareLicense("LIC002", "Slack", 100, 85, 8.0, "2026-06-30"),
    "LIC003": SoftwareLicense("LIC003", "GitHub", 30, 25, 15.0, "2026-09-30"),
}

# IT Assets
self.it_assets = {
    "ASSET001": ITAsset("ASSET001", "Laptop", "MacBook Pro 14", "EMP001", "Assigned"),
    "ASSET002": ITAsset("ASSET002", "Laptop", "MacBook Pro 14", "EMP002", "Assigned"),
    "ASSET003": ITAsset("ASSET003", "Laptop", "Dell XPS 15", None, "Available"),
    "ASSET004": ITAsset("ASSET004", "Monitor", "LG 27 4K", "EMP001", "Assigned"),
    "ASSET005": ITAsset("ASSET005", "Laptop", "ThinkPad X1", None, "Available"),
}
```

**New Finance seed data**:
```python
self.finance_policies = {
    "expense_policy": """EXPENSE POLICY: Categories — Travel (50000/trip), Meals (1000/day), Software, Equipment, Training. Receipt required for claims > 500.""",
    "travel_policy": """TRAVEL POLICY: Economy class for flights < 4 hours. Per-diem rates vary by city.""",
    "reimbursement_policy": """REIMBURSEMENT: Submit within 30 days of expense. Receipt required for amounts > 500.""",
    "payroll_policy": """PAYROLL: Pay date 1st of each month. Deductions auto-calculated (tax, insurance)."""
}

self.budgets = {
    "BUD001": Budget("BUD001", "Engineering", "2026", 500000.0, 320000.0, {"salaries": 250000, "tools": 40000, "travel": 30000}),
    "BUD002": Budget("BUD002", "Marketing", "2026", 300000.0, 180000.0, {"salaries": 120000, "campaigns": 40000, "events": 20000}),
}
```

**New Compliance seed data**:
```python
self.compliance_policies = {
    "data_privacy": """DATA PRIVACY: Personal data encrypted at rest and in transit. Access logged. Retention period: 7 years.""",
    "anti_harassment": """ANTI-HARASSMENT: Zero tolerance policy. Report incidents to HR within 24 hours.""",
    "code_of_ethics": """CODE OF ETHICS: Professional behavior expected. Conflict of interest must be disclosed.""",
    "document_retention": """DOCUMENT RETENTION: Employment records 7 years. Financial records 10 years.""",
    "whistleblower": """WHISTLEBLOWER POLICY: Anonymous reporting channel available. Protection from retaliation guaranteed."""
}

# Training records for existing employees
for emp_id in self.employees:
    for i, training in enumerate(MANDATORY_TRAININGS):
        from core.config import MANDATORY_TRAININGS  # import at top
        self.training_records[f"TR-{emp_id}-{i}"] = TrainingRecord(
            record_id=f"TR-{emp_id}-{i}",
            employee_id=emp_id,
            training_name=training["name"],
            required=True,
            status="Completed" if i < 2 else "Not Started",
            due_date="2026-06-30",
            completed_date="2026-01-15" if i < 2 else None,
            score=85.0 if i < 2 else None
        )
```

---

## ✅ Done Checklist

- [ ] `core/config.py` created with all constants
- [ ] `core/database.py` created with all enums, 20+ dataclasses, Database class
- [ ] All HR methods match existing behavior exactly
- [ ] IT/Finance/Compliance methods added
- [ ] `_initialize_data()` has all seed data (employees, users, jobs, problems, policies)
- [ ] Test: `python -c "from core.database import Database; db = Database(); print(len(db.employees))"` prints `2`

---

**Next** → `02_CORE_SERVICES.md` (LLM service, Event Bus, Base Agent)
