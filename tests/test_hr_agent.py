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
        phone="1234567890",
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
    assert "answer" in result or "status" in result

def test_audit_report(hr_agent, db):
    result = hr_agent.generate_audit_report("2025-01-01", "2025-12-31")
    assert "summary" in result or "report_id" in result
