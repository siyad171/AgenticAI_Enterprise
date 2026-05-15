"""
Compliance Agent — Violations, training, audits, document management
"""
import datetime
from typing import Dict, List
from core.base_agent import BaseAgent


class ComplianceAgent(BaseAgent):

    def __init__(self, db, llm_service, event_bus=None):
        super().__init__(agent_name="Compliance Agent", database=db, llm_service=llm_service, event_bus=event_bus)
        self._register_tools()

    def _register_tools(self):
        """Register all compliance methods as autonomous tools."""
        self.register_tool(
            name="report_violation",
            description="Report a compliance violation and create a trackable violation ID.",
            parameters={
                "reported_by": "str — reporter ID/name",
                "category": "str — violation category",
                "description": "str — violation details",
                "severity": "str — Low|Medium|High|Critical",
                "employee_id": "str — impacted employee ID (optional)",
            },
            function=self.report_violation,
        )
        self.register_tool(
            name="get_violation_status",
            description="Fetch status/details for a violation using its ID.",
            parameters={"violation_id": "str — violation ID"},
            function=self.get_violation_status,
        )
        self.register_tool(
            name="resolve_violation",
            description="Resolve an existing compliance violation with resolution notes.",
            parameters={
                "violation_id": "str — violation ID",
                "resolution": "str — resolution summary",
                "resolved_by": "str — resolver name (optional)",
            },
            function=self.resolve_violation,
        )
        self.register_tool(
            name="schedule_training",
            description="Schedule compliance training for an employee.",
            parameters={
                "employee_id": "str — employee ID",
                "training_type": "str — training/course name",
                "due_date": "str — due date in YYYY-MM-DD",
                "mandatory": "bool — whether training is mandatory",
            },
            function=self.schedule_training,
            requires_employee_id=True,
        )
        self.register_tool(
            name="get_training_status",
            description="Get compliance training status by employee or training ID.",
            parameters={
                "employee_id": "str — employee ID (optional)",
                "training_id": "str — training ID (optional)",
            },
            function=self.get_training_status,
        )
        self.register_tool(
            name="run_compliance_audit",
            description="Run a compliance audit and return findings.",
            parameters={"scope": "str — audit scope, e.g. full"},
            function=self.run_compliance_audit,
        )
        self.register_tool(
            name="manage_document",
            description="Upload or list compliance documents.",
            parameters={
                "action": "str — upload|list",
                "doc_type": "str — document type",
                "title": "str — document title (upload)",
            },
            function=self.manage_document,
        )
        self.register_tool(
            name="ask_compliance_policy",
            description="Answer compliance policy questions.",
            parameters={"question": "str — policy question"},
            function=self.ask_compliance_policy,
        )

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
            violation_id=vid,
            violation_type=category,
            employee_id=employee_id or "Unknown",
            description=description,
            severity=severity,
            detected_date=datetime.datetime.now().isoformat(),
            detected_by=reported_by,
            status="Open",
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
        v = self.db.violations.get(violation_id)
        if not v:
            return {"status": "error", "message": "Violation not found"}
        return {"status": "success", "violation_id": violation_id,
                "category": v.violation_type, "severity": v.severity,
                "current_status": v.status}

    # ── 3. Resolve Violation ──────────────────────────────────────
    def resolve_violation(self, violation_id: str, resolution: str,
                          resolved_by: str = "Compliance Agent") -> Dict:
        v = self.db.violations.get(violation_id)
        if not v:
            return {"status": "error", "message": "Violation not found"}
        v.status = "Resolved"
        v.resolution = resolution
        v.resolved_date = datetime.datetime.now().isoformat()
        result = {"status": "success", "violation_id": violation_id}
        self.log_action("Resolve Violation", result)
        return result

    # ── 4. Schedule Training ──────────────────────────────────────
    def schedule_training(self, employee_id: str, training_type: str,
                          due_date: str, mandatory: bool = True) -> Dict:
        from core.database import TrainingRecord
        tid = f"TRN{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        rec = TrainingRecord(
            record_id=tid,
            employee_id=employee_id,
            training_name=training_type,
            required=mandatory,
            status="Scheduled",
            due_date=due_date,
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
            rec = self.db.training_records.get(training_id)
            if not rec:
                return {"status": "error", "message": "Training not found"}
            return {"status": "success", "training_id": training_id,
                    "type": rec.training_name, "status": rec.status}
        if employee_id:
            records = self.db.get_employee_training(employee_id)
            return {"status": "success", "trainings": [
                {"id": r.record_id, "type": r.training_name,
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
            trainings = self.db.get_employee_training(emp_id)
            for t in trainings:
                if t.status == "Scheduled" and t.required:
                    due = datetime.datetime.strptime(t.due_date, "%Y-%m-%d")
                    if due < datetime.datetime.now():
                        findings.append({
                            "area": "Training",
                            "issue": f"Overdue training: {t.training_name} for {emp_id}",
                            "severity": "Medium",
                        })

        # Check open violations
        open_violations = [v for v in self.db.get_open_violations() if v.status == "Open"]
        if open_violations:
            findings.append({
                "area": "Violations",
                "issue": f"{len(open_violations)} open violation(s)",
                "severity": "High" if len(open_violations) >= 3 else "Medium",
            })

        status = "COMPLIANT" if not findings else "ISSUES_FOUND"
        audit = ComplianceAudit(
            audit_id=audit_id,
            audit_date=datetime.datetime.now().isoformat(),
            scope=scope,
            score=100.0 if status == "COMPLIANT" else max(0.0, 100.0 - (len(findings) * 15.0)),
            findings=findings,
            recommendations=[
                "Close open violations and re-run audit",
                "Complete overdue mandatory trainings",
            ] if findings else ["Maintain current compliance controls"],
            conducted_by="Compliance Agent",
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
                doc_id=doc_id,
                employee_id=kwargs.get("employee_id", "SYSTEM"),
                document_type=doc_type,
                uploaded_date=datetime.datetime.now().isoformat(),
                verified=False,
                verified_by=None,
            )
            self.db.add_compliance_document(doc)
            return {"status": "success", "document_id": doc_id}
        elif action == "list":
            docs = [d for d in self.db.compliance_documents.values() if d.document_type == doc_type]
            return {"status": "success", "documents": [
                {"id": d.doc_id, "document_type": d.document_type, "employee_id": d.employee_id, "verified": d.verified}
                for d in docs
            ]}
        return {"status": "error", "message": f"Unknown action: {action}"}

    # ── 8. Ask Compliance Policy ──────────────────────────────────
    def ask_compliance_policy(self, question: str) -> Dict:
        policies = "\n".join(
            f"{k}: {v}" for k, v in getattr(self.db, "compliance_policies", {}).items()
        )
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
