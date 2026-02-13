"""
Compliance Agent — Violations, training, audits, document management
"""
import datetime
from typing import Dict, List
from core.base_agent import BaseAgent


class ComplianceAgent(BaseAgent):

    def __init__(self, db, llm_service, event_bus=None):
        super().__init__(agent_name="Compliance Agent", database=db, llm_service=llm_service, event_bus=event_bus)

    def get_capabilities(self) -> List[str]:
        return [
            "report_violation", "get_violation_status", "resolve_violation",
            "schedule_training", "get_training_status",
            "run_compliance_audit", "manage_document",
            "ask_compliance_policy"
        ]

    def handle_event(self, event_type: str, data: dict):
        if event_type == "employee_onboarded":
            self._schedule_mandatory_training(data)
        elif event_type == "violation_reported":
            self._assess_violation(data)
        elif event_type == "security_incident":
            self.report_violation("SYSTEM", "Security", data.get("description",""),
                                  severity="High")

    # ── 1. Report Violation ───────────────────────────────────────
    def report_violation(self, reported_by: str, category: str,
                         description: str, severity: str = "Medium",
                         employee_id: str = None) -> Dict:
        from core.database import Violation
        vid = f"VIO{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        v = Violation(
            violation_id=vid, reported_by=reported_by,
            employee_id=employee_id or "Unknown",
            category=category, description=description,
            severity=severity, status="Open",
            reported_date=datetime.datetime.now().isoformat()
        )
        self.db.add_violation(v)

        if self.event_bus:
            self.event_bus.publish("violation_reported", {
                "violation_id": vid, "severity": severity})

        result = {"status": "success", "violation_id": vid, "severity": severity}
        self.log_action("Report Violation", result, reported_by)
        return result

    # ── 2. Get Violation Status ───────────────────────────────────
    def get_violation_status(self, violation_id: str) -> Dict:
        v = self.db.get_violation(violation_id)
        if not v:
            return {"status": "error", "message": "Violation not found"}
        return {"status": "success", "violation_id": violation_id,
                "category": v.category, "severity": v.severity,
                "current_status": v.status}

    # ── 3. Resolve Violation ──────────────────────────────────────
    def resolve_violation(self, violation_id: str, resolution: str,
                          resolved_by: str = "Compliance Agent") -> Dict:
        v = self.db.get_violation(violation_id)
        if not v:
            return {"status": "error", "message": "Violation not found"}
        v.status = "Resolved"
        v.resolution = resolution
        v.resolved_date = datetime.datetime.now().isoformat()
        v.resolved_by = resolved_by
        result = {"status": "success", "violation_id": violation_id}
        self.log_action("Resolve Violation", result)
        return result

    # ── 4. Schedule Training ──────────────────────────────────────
    def schedule_training(self, employee_id: str, training_type: str,
                          due_date: str, mandatory: bool = True) -> Dict:
        from core.database import TrainingRecord
        tid = f"TRN{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        rec = TrainingRecord(
            training_id=tid, employee_id=employee_id,
            training_type=training_type, status="Scheduled",
            due_date=due_date, mandatory=mandatory,
            scheduled_date=datetime.datetime.now().isoformat()
        )
        self.db.add_training_record(rec)
        result = {"status": "success", "training_id": tid,
                  "training_type": training_type, "due_date": due_date}
        self.log_action("Schedule Training", result, employee_id)
        return result

    # ── 5. Get Training Status ────────────────────────────────────
    def get_training_status(self, employee_id: str = None,
                            training_id: str = None) -> Dict:
        if training_id:
            rec = self.db.get_training_record(training_id)
            if not rec:
                return {"status": "error", "message": "Training not found"}
            return {"status": "success", "training_id": training_id,
                    "type": rec.training_type, "status": rec.status}
        if employee_id:
            records = self.db.get_employee_trainings(employee_id)
            return {"status": "success", "trainings": [
                {"id": r.training_id, "type": r.training_type,
                 "status": r.status, "due": r.due_date}
                for r in records
            ]}
        return {"status": "error", "message": "Provide employee_id or training_id"}

    # ── 6. Run Compliance Audit ───────────────────────────────────
    def run_compliance_audit(self, scope: str = "full") -> Dict:
        from core.database import ComplianceAudit
        audit_id = f"AUD{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        findings = []
        # Check overdue trainings
        for emp_id in self.db.employees:
            trainings = self.db.get_employee_trainings(emp_id)
            for t in trainings:
                if t.status == "Scheduled" and t.mandatory:
                    due = datetime.datetime.strptime(t.due_date, "%Y-%m-%d")
                    if due < datetime.datetime.now():
                        findings.append(f"Overdue training: {t.training_type} for {emp_id}")

        # Check open violations
        open_violations = [v for v in self.db.get_all_violations()
                           if v.status == "Open"]
        if open_violations:
            findings.append(f"{len(open_violations)} open violation(s)")

        status = "COMPLIANT" if not findings else "ISSUES_FOUND"
        audit = ComplianceAudit(
            audit_id=audit_id, scope=scope,
            findings=findings, status=status,
            audit_date=datetime.datetime.now().isoformat()
        )
        self.db.add_compliance_audit(audit)

        result = {"status": "success", "audit_id": audit_id,
                  "compliance_status": status,
                  "findings_count": len(findings), "findings": findings}
        self.log_action("Run Compliance Audit", result)
        return result

    # ── 7. Manage Document ────────────────────────────────────────
    def manage_document(self, action: str, doc_type: str,
                         title: str = "", **kwargs) -> Dict:
        if action == "upload":
            from core.database import ComplianceDocument
            doc_id = f"DOC{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            doc = ComplianceDocument(
                document_id=doc_id, doc_type=doc_type, title=title,
                version=kwargs.get("version", "1.0"),
                uploaded_by=kwargs.get("uploaded_by", "Compliance"),
                upload_date=datetime.datetime.now().isoformat(),
                status="Active"
            )
            self.db.add_compliance_document(doc)
            return {"status": "success", "document_id": doc_id}
        elif action == "list":
            docs = self.db.get_compliance_documents(doc_type)
            return {"status": "success", "documents": [
                {"id": d.document_id, "title": d.title, "version": d.version}
                for d in docs
            ]}
        return {"status": "error", "message": f"Unknown action: {action}"}

    # ── 8. Ask Compliance Policy ──────────────────────────────────
    def ask_compliance_policy(self, question: str) -> Dict:
        policies = self.db.get_compliance_policies()
        answer = self.llm.generate_response(
            question,
            f"You are a compliance officer. Policies:\n{policies}\nBe precise."
        )
        return {"status": "success", "answer": answer}

    # ── Event Helpers ─────────────────────────────────────────────
    def _schedule_mandatory_training(self, data):
        emp_id = data.get("employee_id")
        due = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        for training in ["Code of Conduct", "Data Privacy", "Anti-Harassment"]:
            self.schedule_training(emp_id, training, due, mandatory=True)

    def _assess_violation(self, data):
        severity = data.get("severity", "Medium")
        if severity in ("High", "Critical"):
            self.log_action("Urgent Violation Alert", data)
