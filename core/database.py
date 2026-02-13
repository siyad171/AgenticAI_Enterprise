"""
core/database.py — Unified in-memory database for all agents
"""
import datetime
import random
import string
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from core.config import MANDATORY_TRAININGS

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

    # ═══════════════════ SEED DATA ═══════════════════

    def _initialize_data(self):
        """Populate all tables with realistic seed data."""

        # ───────── Employees ─────────
        self.employees = {
            "EMP001": Employee(
                employee_id="EMP001",
                name="John Doe",
                email="john.doe@company.com",
                department="Engineering",
                position="Senior Developer",
                join_date="2023-01-15",
                leave_balance={"Casual Leave": 12, "Sick Leave": 15, "Annual Leave": 20}
            ),
            "EMP002": Employee(
                employee_id="EMP002",
                name="Jane Smith",
                email="jane.smith@company.com",
                department="Marketing",
                position="Marketing Manager",
                join_date="2023-03-20",
                leave_balance={"Casual Leave": 10, "Sick Leave": 15, "Annual Leave": 18}
            ),
        }

        # ───────── Users ─────────
        self.users = {
            "admin": User(username="admin", password="admin123", role="Admin", employee_id="EMP001"),
            "john.doe": User(username="john.doe", password="pass123", role="Employee", employee_id="EMP001"),
            "jane.smith": User(username="jane.smith", password="pass123", role="Employee", employee_id="EMP002"),
        }

        # ───────── Job Positions ─────────
        self.job_positions = {
            "JOB001": JobPosition(
                job_id="JOB001",
                title="Senior Python Developer",
                department="Engineering",
                description="Looking for an experienced Python developer with expertise in Django, FastAPI, and cloud services.",
                required_skills=["Python", "Django", "FastAPI", "PostgreSQL", "AWS", "Docker", "Git"],
                min_experience=3,
                min_education="Bachelor's in Computer Science or related field",
                status="Active",
                test_questions=[
                    {
                        "question": "What is the output of: print(type(lambda: None))?",
                        "options": ["<class 'function'>", "<class 'lambda'>", "<class 'NoneType'>", "SyntaxError"],
                        "correct_answer": "<class 'function'>"
                    },
                    {
                        "question": "Which Python built-in is used to create an iterator from an iterable?",
                        "options": ["next()", "iter()", "yield()", "map()"],
                        "correct_answer": "iter()"
                    },
                    {
                        "question": "In Django, what does ORM stand for?",
                        "options": ["Object Relational Mapping", "Object Resource Model", "Online Request Manager", "Open Runtime Module"],
                        "correct_answer": "Object Relational Mapping"
                    },
                    {
                        "question": "What HTTP method is used by FastAPI for creating new resources by default?",
                        "options": ["GET", "POST", "PUT", "PATCH"],
                        "correct_answer": "POST"
                    },
                    {
                        "question": "Which AWS service is primarily used for deploying containerized applications?",
                        "options": ["S3", "EC2", "ECS", "RDS"],
                        "correct_answer": "ECS"
                    }
                ]
            ),
            "JOB002": JobPosition(
                job_id="JOB002",
                title="Marketing Manager",
                department="Marketing",
                description="Seeking a creative marketing manager with digital marketing expertise and team leadership skills.",
                required_skills=["Digital Marketing", "SEO", "Content Strategy", "Analytics", "Social Media", "Team Leadership"],
                min_experience=4,
                min_education="Bachelor's in Marketing or Business",
                status="Active",
                test_questions=[
                    {
                        "question": "What does SEO stand for?",
                        "options": ["Search Engine Optimization", "Social Engine Output", "Search Email Outreach", "Site Enhancement Operation"],
                        "correct_answer": "Search Engine Optimization"
                    },
                    {
                        "question": "Which metric measures the percentage of visitors who leave after viewing only one page?",
                        "options": ["Click-through rate", "Bounce rate", "Conversion rate", "Impression rate"],
                        "correct_answer": "Bounce rate"
                    },
                    {
                        "question": "What is A/B testing primarily used for?",
                        "options": ["Testing server speed", "Comparing two versions of content", "Checking for bugs", "Database optimization"],
                        "correct_answer": "Comparing two versions of content"
                    },
                    {
                        "question": "Which platform is best known for B2B marketing?",
                        "options": ["TikTok", "Instagram", "LinkedIn", "Snapchat"],
                        "correct_answer": "LinkedIn"
                    },
                    {
                        "question": "What does CPA stand for in digital marketing?",
                        "options": ["Cost Per Action", "Click Per Advertisement", "Content Performance Analysis", "Customer Purchase Agreement"],
                        "correct_answer": "Cost Per Action"
                    }
                ]
            ),
        }

        # ───────── Technical Problems ─────────
        self.technical_problems = {
            "PROB001": TechnicalProblem(
                problem_id="PROB001",
                title="Two Sum",
                difficulty="Easy",
                description="Given an array of integers `nums` and an integer `target`, return the indices of the two numbers that add up to `target`.\n\nYou may assume that each input has exactly one solution, and you may not use the same element twice.",
                input_format="First line: space-separated integers (nums array)\nSecond line: integer (target)",
                output_format="Two space-separated integers (indices)",
                constraints="2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9\nOnly one valid answer exists.",
                examples=[
                    {"input": "2 7 11 15\n9", "output": "0 1", "explanation": "nums[0] + nums[1] = 2 + 7 = 9"},
                    {"input": "3 2 4\n6", "output": "1 2", "explanation": "nums[1] + nums[2] = 2 + 4 = 6"},
                ],
                test_cases=[
                    {"input": "2 7 11 15\n9", "expected": "0 1", "visible": True},
                    {"input": "3 2 4\n6", "expected": "1 2", "visible": True},
                    {"input": "3 3\n6", "expected": "0 1", "visible": False},
                    {"input": "1 5 3 7 2\n9", "expected": "1 3", "visible": False},
                    {"input": "-1 -2 -3 -4 -5\n-8", "expected": "2 4", "visible": False},
                ],
                time_limit=2.0,
                memory_limit=256000,
                tags=["Array", "Hash Table"],
                starter_code={
                    "python": "def two_sum(nums, target):\n    # Write your solution here\n    pass\n\n# Read input\nnums = list(map(int, input().split()))\ntarget = int(input())\nresult = two_sum(nums, target)\nprint(result[0], result[1])",
                    "java": "import java.util.*;\n\npublic class Main {\n    public static int[] twoSum(int[] nums, int target) {\n        // Write your solution here\n        return new int[]{};\n    }\n\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String[] parts = sc.nextLine().split(\" \");\n        int[] nums = new int[parts.length];\n        for (int i = 0; i < parts.length; i++) nums[i] = Integer.parseInt(parts[i]);\n        int target = sc.nextInt();\n        int[] result = twoSum(nums, target);\n        System.out.println(result[0] + \" \" + result[1]);\n    }\n}",
                    "cpp": "#include <iostream>\n#include <vector>\n#include <sstream>\nusing namespace std;\n\nvector<int> twoSum(vector<int>& nums, int target) {\n    // Write your solution here\n    return {};\n}\n\nint main() {\n    string line;\n    getline(cin, line);\n    istringstream iss(line);\n    vector<int> nums;\n    int n;\n    while (iss >> n) nums.push_back(n);\n    int target;\n    cin >> target;\n    auto result = twoSum(nums, target);\n    cout << result[0] << \" \" << result[1] << endl;\n    return 0;\n}"
                }
            ),
            "PROB002": TechnicalProblem(
                problem_id="PROB002",
                title="Valid Parentheses",
                difficulty="Easy",
                description="Given a string `s` containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.\n\nAn input string is valid if:\n1. Open brackets must be closed by the same type of brackets.\n2. Open brackets must be closed in the correct order.\n3. Every close bracket has a corresponding open bracket of the same type.",
                input_format="A string containing only parentheses characters",
                output_format="'true' or 'false'",
                constraints="1 <= s.length <= 10^4\ns consists of parentheses only '()[]{}'",
                examples=[
                    {"input": "()", "output": "true", "explanation": "Simple matching pair"},
                    {"input": "()[]{}", "output": "true", "explanation": "All types match correctly"},
                    {"input": "(]", "output": "false", "explanation": "Mismatched brackets"},
                ],
                test_cases=[
                    {"input": "()", "expected": "true", "visible": True},
                    {"input": "()[]{}", "expected": "true", "visible": True},
                    {"input": "(]", "expected": "false", "visible": True},
                    {"input": "([)]", "expected": "false", "visible": False},
                    {"input": "{[]}", "expected": "true", "visible": False},
                    {"input": "", "expected": "true", "visible": False},
                    {"input": "((((", "expected": "false", "visible": False},
                ],
                time_limit=1.0,
                memory_limit=128000,
                tags=["Stack", "String"],
                starter_code={
                    "python": "def is_valid(s):\n    # Write your solution here\n    pass\n\ns = input()\nprint('true' if is_valid(s) else 'false')",
                    "java": "import java.util.*;\n\npublic class Main {\n    public static boolean isValid(String s) {\n        // Write your solution here\n        return false;\n    }\n\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String s = sc.nextLine();\n        System.out.println(isValid(s) ? \"true\" : \"false\");\n    }\n}",
                    "cpp": "#include <iostream>\n#include <stack>\n#include <string>\nusing namespace std;\n\nbool isValid(string s) {\n    // Write your solution here\n    return false;\n}\n\nint main() {\n    string s;\n    getline(cin, s);\n    cout << (isValid(s) ? \"true\" : \"false\") << endl;\n    return 0;\n}"
                }
            ),
        }

        # ───────── HR Policies ─────────
        self.hr_policies = {
            "leave": """LEAVE POLICY:
- Casual Leave: 12 days/year, max 3 consecutive days, 2 days advance notice
- Sick Leave: 15 days/year, medical certificate for 3+ days
- Annual Leave: 20 days/year, 2 weeks advance notice for 5+ days
- Unpaid Leave: Manager + HR approval, max 30 days/year
- Leave cannot be carried over to next year (except 5 days Annual Leave)
- Public holidays: As per regional calendar""",

            "onboarding": """ONBOARDING POLICY:
- IT setup (laptop, email, accounts) within 24 hours
- Mandatory trainings: Data Privacy, Workplace Safety, Anti-Harassment, Security Awareness
- Buddy system: Senior employee assigned for first 30 days
- Probation period: 6 months with monthly reviews
- Welcome kit provided on Day 1""",

            "working_hours": """WORKING HOURS POLICY:
- Standard: 9 AM - 6 PM, Monday to Friday
- Flexible: Core hours 10 AM - 4 PM, complete 8 hours
- Remote work: Up to 3 days/week with manager approval
- Overtime: Pre-approved only, compensated at 1.5x""",

            "code_of_conduct": """CODE OF CONDUCT:
- Professional behavior at all times
- Respect diversity and inclusion
- No harassment or discrimination
- Protect company confidential information
- Report violations to HR immediately
- Social media policy: Do not share internal information"""
        }

        # ───────── Eligibility Criteria ─────────
        self.eligibility_criteria = {
            "skill_weight": 40,
            "experience_weight": 30,
            "education_weight": 20,
            "test_weight": 10,
            "min_skill_match": 40,
            "min_experience_ratio": 0.5,
            "passing_score": 50,
            "review_score": 40
        }

        # ───────── IT Policies ─────────
        self.it_policies = {
            "password_policy": """PASSWORD POLICY: Min 12 chars, uppercase+lowercase+digit+special, rotate every 90 days, MFA required for all accounts.""",
            "software_policy": """SOFTWARE INSTALLATION: Only approved software list. Others require IT admin approval. Approved: VS Code, Slack, Jira, GitHub, Zoom, Chrome, Firefox.""",
            "byod_policy": """BYOD POLICY: Must have antivirus, device must be encrypted, must register with IT department.""",
            "vpn_policy": """VPN POLICY: Required for all remote work. Auto-disconnect after 12 hours inactivity.""",
            "incident_response": """INCIDENT RESPONSE: Report within 1 hour. IT investigates within 4 hours. Critical incidents escalated immediately."""
        }

        # ───────── IT Software Licenses ─────────
        self.software_licenses = {
            "LIC001": SoftwareLicense("LIC001", "Jira", 50, 42, 10.0, "2026-12-31"),
            "LIC002": SoftwareLicense("LIC002", "Slack", 100, 85, 8.0, "2026-06-30"),
            "LIC003": SoftwareLicense("LIC003", "GitHub", 30, 25, 15.0, "2026-09-30"),
        }

        # ───────── IT Assets ─────────
        self.it_assets = {
            "ASSET001": ITAsset("ASSET001", "Laptop", "MacBook Pro 14", "EMP001", "Assigned"),
            "ASSET002": ITAsset("ASSET002", "Laptop", "MacBook Pro 14", "EMP002", "Assigned"),
            "ASSET003": ITAsset("ASSET003", "Laptop", "Dell XPS 15", None, "Available"),
            "ASSET004": ITAsset("ASSET004", "Monitor", "LG 27 4K", "EMP001", "Assigned"),
            "ASSET005": ITAsset("ASSET005", "Laptop", "ThinkPad X1", None, "Available"),
        }

        # ───────── Finance Policies ─────────
        self.finance_policies = {
            "expense_policy": """EXPENSE POLICY: Categories — Travel (50000/trip), Meals (1000/day), Software, Equipment, Training. Receipt required for claims > 500.""",
            "travel_policy": """TRAVEL POLICY: Economy class for flights < 4 hours. Per-diem rates vary by city.""",
            "reimbursement_policy": """REIMBURSEMENT: Submit within 30 days of expense. Receipt required for amounts > 500.""",
            "payroll_policy": """PAYROLL: Pay date 1st of each month. Deductions auto-calculated (tax, insurance)."""
        }

        # ───────── Finance Budgets ─────────
        self.budgets = {
            "BUD001": Budget("BUD001", "Engineering", "2026", 500000.0, 320000.0, {"salaries": 250000, "tools": 40000, "travel": 30000}),
            "BUD002": Budget("BUD002", "Marketing", "2026", 300000.0, 180000.0, {"salaries": 120000, "campaigns": 40000, "events": 20000}),
        }

        # ───────── Compliance Policies ─────────
        self.compliance_policies = {
            "data_privacy": """DATA PRIVACY: Personal data encrypted at rest and in transit. Access logged. Retention period: 7 years.""",
            "anti_harassment": """ANTI-HARASSMENT: Zero tolerance policy. Report incidents to HR within 24 hours.""",
            "code_of_ethics": """CODE OF ETHICS: Professional behavior expected. Conflict of interest must be disclosed.""",
            "document_retention": """DOCUMENT RETENTION: Employment records 7 years. Financial records 10 years.""",
            "whistleblower": """WHISTLEBLOWER POLICY: Anonymous reporting channel available. Protection from retaliation guaranteed."""
        }

        # ───────── Compliance Training Records ─────────
        for emp_id in self.employees:
            for i, training in enumerate(MANDATORY_TRAININGS):
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
