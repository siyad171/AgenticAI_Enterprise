"""Tests for admin escalation resolution and learning persistence."""

import json

from core.learning_module import LearningModule


def test_resolve_escalation_records_learning(orchestrator):
    hr_agent = orchestrator.agents["hr"]

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
    assert any(o.get("decision_id") == case["case_id"] for o in hr_agent.learning.overrides)

    learned = hr_agent.learning.overrides[-1]
    assert learned["decision_id"] == case["case_id"]
    assert learned["task"] == "I need to adjust leave dates due to emergency"
    assert learned["context"]["escalation_type"] == "low_confidence"

    resolved_case = next(c for c in orchestrator.get_escalation_queue() if c["case_id"] == case["case_id"])
    assert resolved_case.get("employee_response")


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


def test_low_confidence_reuses_admin_override_without_escalation(orchestrator, monkeypatch):
    hr_agent = orchestrator.agents["hr"]
    unique_task = "escalation learning test unique manager transfer request"
    hr_agent.learning.record_override(
        decision_id="ESC-LEARN-001",
        original_decision="Low confidence on disciplinary guidance",
        admin_decision="Ask employee to share details and email HR team",
        reason="Sensitive disciplinary action must be manually reviewed by HR",
        task=unique_task,
        context={"escalation_type": "policy_sensitive", "agent": "hr"},
    )

    def fake_plan(_user_message, _perception):
        return {
            "reasoning": "I am unsure this should be handled automatically.",
            "confidence": 0.2,
            "requires_human": False,
            "human_reason": "",
            "steps": [{"tool": "no_tool_needed", "parameters": {}}],
            "direct_response": "",
        }

    monkeypatch.setattr(hr_agent, "_reason_and_plan", fake_plan)

    result = hr_agent.process_request(
        user_message=unique_task,
        context={"employee_id": "EMP001"},
    )

    assert result["escalated"] is False
    assert result.get("learning_applied") is True
    assert result.get("learning_source_decision_id") == "ESC-LEARN-001"
    assert "email hr team" in result["response"].lower()


def test_learning_persistence_splits_policy_and_audit(orchestrator):
    hr_agent = orchestrator.agents["hr"]

    hr_agent.learning.record_decision(
        task="Sample autonomous decision",
        context={"tools_used": ["no_tool_needed"]},
        decision="Handled informational request",
        confidence=0.9,
        outcome="success",
    )
    hr_agent.learning.record_override(
        decision_id="ESC-LEARN-002",
        original_decision="Low confidence",
        admin_decision="Use approved policy response",
        reason="Matched prior approved case",
        task="Sample escalation task",
        context={"escalation_type": "low_confidence"},
    )

    with open(hr_agent.learning._file_path(), "r") as f:
        learning_data = json.load(f)
    with open(hr_agent.learning._audit_file_path(), "r") as f:
        audit_data = json.load(f)

    assert "overrides" in learning_data
    assert "decisions" not in learning_data
    assert "decisions" in audit_data
    assert "overrides" not in audit_data


def test_learning_save_does_not_erase_overrides_across_sessions(tmp_path):
    lm_admin = LearningModule("HR Agent")
    lm_runtime = LearningModule("HR Agent")

    # Isolate storage to temp path for deterministic test behavior.
    lm_admin.storage_dir = str(tmp_path)
    lm_runtime.storage_dir = str(tmp_path)
    lm_admin.decisions = []
    lm_admin.overrides = []
    lm_runtime.decisions = []
    lm_runtime.overrides = []

    lm_admin.record_override(
        decision_id="ESC-TMP-1",
        original_decision="Low confidence",
        admin_decision="Please email HR with full details for manual review.",
        reason="Sensitive action requires manual validation",
        task="Can you fire my manager?",
        context={"escalation_type": "policy_sensitive"},
    )

    # Simulate another runtime instance that only writes a decision audit entry.
    lm_runtime.record_decision(
        task="Status check",
        context={"tools_used": ["no_tool_needed"]},
        decision="Provided status update",
        confidence=0.8,
        outcome="success",
    )

    with open(lm_admin._file_path(), "r") as f:
        learning_data = json.load(f)

    assert any(o.get("decision_id") == "ESC-TMP-1" for o in learning_data.get("overrides", []))


def test_requires_human_can_use_learned_override_without_escalation(orchestrator, monkeypatch):
    hr_agent = orchestrator.agents["hr"]
    task = "policy escalation unique test: manager misconduct complaint"
    learned_response = (
        "Please email HR with full details so a specialist can review this concern "
        "through the formal process."
    )

    hr_agent.learning.record_override(
        decision_id="ESC-POLICY-001",
        original_decision="Sensitive HR action",
        admin_decision=learned_response,
        reason="Sensitive requests require structured manual HR handling",
        task=task,
        context={"escalation_type": "policy_sensitive", "agent": "hr"},
    )

    def fake_plan(_user_message, _perception):
        return {
            "reasoning": "Sensitive HR request detected.",
            "confidence": 0.9,
            "requires_human": True,
            "human_reason": "Request to fire a manager is sensitive.",
            "steps": [],
            "direct_response": "",
        }

    monkeypatch.setattr(hr_agent, "_reason_and_plan", fake_plan)

    result = hr_agent.process_request(task, context={"employee_id": "EMP001"})

    assert result["escalated"] is False
    assert result.get("learning_applied") is True
    assert result["response"] == learned_response
