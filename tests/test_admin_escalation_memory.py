"""Tests for admin escalation resolution and learning persistence."""


def test_resolve_escalation_records_learning(orchestrator):
    hr_agent = orchestrator.agents["hr"]
    before = len(hr_agent.learning.overrides)

    case = orchestrator._create_escalation_case(
        user_message="I need to adjust leave dates due to emergency",
        context={"employee_id": "EMP001"},
        agent_key="hr",
        agent_label="🏥 HR Agent",
        result_data={
            "confidence": 0.42,
            "reasoning": "Low confidence on policy interpretation.",
            "escalation_reason": "Low confidence (42%)",
            "human_reason": "",
            "escalation_type": "low_confidence",
            "response": "Escalated for human review.",
        },
    )

    result = orchestrator.resolve_escalation(
        case_id=case["case_id"],
        admin_decision="Override with corrected decision",
        reason="Emergency leave can be approved with manager confirmation.",
        resolved_by="Admin",
    )

    assert result["status"] == "success"
    assert len(hr_agent.learning.overrides) == before + 1

    learned = hr_agent.learning.overrides[-1]
    assert learned["decision_id"] == case["case_id"]
    assert learned["task"] == "I need to adjust leave dates due to emergency"
    assert learned["context"]["escalation_type"] == "low_confidence"


def test_get_escalation_queue_filters_by_status(orchestrator):
    case = orchestrator._create_escalation_case(
        user_message="Payroll discrepancy",
        context={"employee_id": "EMP001"},
        agent_key="finance",
        agent_label="💰 Finance Agent",
        result_data={
            "confidence": 0.30,
            "reasoning": "Potential payroll anomaly",
            "escalation_reason": "Policy-sensitive request",
            "human_reason": "",
            "escalation_type": "policy_sensitive",
            "response": "Escalated for human review.",
        },
    )

    open_cases = orchestrator.get_escalation_queue(status="Open")
    assert any(c["case_id"] == case["case_id"] for c in open_cases)

    orchestrator.resolve_escalation(
        case_id=case["case_id"],
        admin_decision="Escalate to specialist team",
        reason="Needs payroll specialist validation.",
    )

    resolved_cases = orchestrator.get_escalation_queue(status="Resolved")
    assert any(c["case_id"] == case["case_id"] for c in resolved_cases)
