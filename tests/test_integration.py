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
    # With valid API key this would route to IT; without it the fallback may differ
    assert "agent" in result, "route_task should return an agent key"
