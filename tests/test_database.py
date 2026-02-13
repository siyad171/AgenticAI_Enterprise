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
        phone="1234567890",
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
        log_id="TEST001", timestamp="2025-01-01T00:00:00", agent="hr",
        action="test_action", details={"test": True}, user="admin"
    )
    db.add_audit_log(log)
    assert len(db.audit_logs) >= 1
