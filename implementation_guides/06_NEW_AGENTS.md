# 06 — New Agents (IT, Finance, Compliance)

> **Depends on:** `01_CORE_CONFIG_DB.md`, `02_CORE_SERVICES.md`, `04_TOOLS_LAYER.md`
> **Creates:** `agents/it_agent.py`, `agents/finance_agent.py`, `agents/compliance_agent.py`, `agents/__init__.py`

---

## `agents/it_agent.py`

```python
"""
IT Agent — Ticket management, access control, software licenses, asset tracking
"""
import datetime
from typing import Dict, List
from core.base_agent import BaseAgent
from tools.email_service import EmailService


class ITAgent(BaseAgent):

    def __init__(self, db, llm_service, event_bus=None):
        super().__init__(name="IT Agent", db=db, llm_service=llm_service, event_bus=event_bus)
        self.email = EmailService(llm_service)

    def get_capabilities(self) -> List[str]:
        return [
            "create_ticket", "resolve_ticket", "get_ticket_status",
            "grant_access", "revoke_access",
            "manage_software_license", "track_asset"
        ]

    def handle_event(self, event_type: str, data: dict):
        if event_type == "employee_onboarded":
            self._setup_new_employee_it(data)
        elif event_type == "employee_offboarded":
            self._revoke_all_access(data)
        elif event_type == "security_incident":
            self._handle_security_incident(data)

    # ── 1. Create Ticket ─────────────────────────────────────────
    def create_ticket(self, employee_id: str, category: str,
                      description: str, priority: str = "Medium") -> Dict:
        from core.database import ITTicket
        ticket_id = f"TKT{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        ticket = ITTicket(
            ticket_id=ticket_id, employee_id=employee_id,
            category=category, description=description,
            priority=priority, status="Open",
            created_date=datetime.datetime.now().isoformat()
        )
        self.db.add_it_ticket(ticket)

        # Use LLM to suggest resolution
        suggestion = ""
        if self.llm:
            prompt = (f"IT support ticket:\nCategory: {category}\n"
                      f"Description: {description}\nPriority: {priority}\n\n"
                      "Suggest a brief resolution approach (2-3 sentences).")
            suggestion = self.llm.generate_response(prompt,
                "You are an IT support specialist.")

        if self.event_bus:
            self.event_bus.publish("ticket_created", {
                "ticket_id": ticket_id, "priority": priority})

        result = {"status": "success", "ticket_id": ticket_id,
                  "suggestion": suggestion}
        self.log_action("Create IT Ticket", result, employee_id)
        return result

    # ── 2. Resolve Ticket ─────────────────────────────────────────
    def resolve_ticket(self, ticket_id: str, resolution: str,
                       resolved_by: str = "IT Agent") -> Dict:
        ticket = self.db.get_it_ticket(ticket_id)
        if not ticket:
            return {"status": "error", "message": "Ticket not found"}
        ticket.status = "Resolved"
        ticket.resolution = resolution
        ticket.resolved_date = datetime.datetime.now().isoformat()
        ticket.resolved_by = resolved_by

        if self.event_bus:
            self.event_bus.publish("ticket_resolved", {"ticket_id": ticket_id})

        result = {"status": "success", "ticket_id": ticket_id,
                  "resolution": resolution}
        self.log_action("Resolve IT Ticket", result)
        return result

    # ── 3. Get Ticket Status ──────────────────────────────────────
    def get_ticket_status(self, ticket_id: str) -> Dict:
        ticket = self.db.get_it_ticket(ticket_id)
        if not ticket:
            return {"status": "error", "message": "Ticket not found"}
        return {"status": "success", "ticket": {
            "ticket_id": ticket.ticket_id, "category": ticket.category,
            "priority": ticket.priority, "status": ticket.status,
            "description": ticket.description,
            "created": ticket.created_date,
            "resolved": getattr(ticket, 'resolved_date', None)
        }}

    # ── 4. Grant Access ───────────────────────────────────────────
    def grant_access(self, employee_id: str, system: str,
                     access_level: str = "Standard",
                     approved_by: str = "IT Admin") -> Dict:
        from core.database import AccessRecord
        record = AccessRecord(
            record_id=f"ACC{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            employee_id=employee_id, system=system,
            access_level=access_level, granted_date=datetime.datetime.now().isoformat(),
            status="Active", approved_by=approved_by
        )
        self.db.add_access_record(record)
        result = {"status": "success", "record_id": record.record_id,
                  "system": system, "access_level": access_level}
        self.log_action("Grant Access", result, employee_id)
        return result

    # ── 5. Revoke Access ──────────────────────────────────────────
    def revoke_access(self, employee_id: str, system: str,
                      reason: str = "Policy change") -> Dict:
        records = self.db.get_employee_access(employee_id)
        revoked = []
        for r in records:
            if r.system == system and r.status == "Active":
                r.status = "Revoked"
                r.revoked_date = datetime.datetime.now().isoformat()
                revoked.append(r.record_id)
        result = {"status": "success", "revoked": revoked, "reason": reason}
        self.log_action("Revoke Access", result, employee_id)
        return result

    # ── 6. Manage Software License ────────────────────────────────
    def manage_software_license(self, action: str, software: str,
                                 employee_id: str = None, **kwargs) -> Dict:
        if action == "assign":
            license_rec = self.db.get_available_license(software)
            if not license_rec:
                return {"status": "error", "message": f"No available license for {software}"}
            license_rec.assigned_to = employee_id
            license_rec.status = "In Use"
            return {"status": "success", "license_id": license_rec.license_id}
        elif action == "release":
            # release logic
            return {"status": "success", "message": f"License released for {software}"}
        return {"status": "error", "message": f"Unknown action: {action}"}

    # ── 7. Track Asset ────────────────────────────────────────────
    def track_asset(self, asset_id: str = None, employee_id: str = None) -> Dict:
        if asset_id:
            asset = self.db.get_it_asset(asset_id)
            if not asset:
                return {"status": "error", "message": "Asset not found"}
            return {"status": "success", "asset": {
                "asset_id": asset.asset_id, "type": asset.asset_type,
                "assigned_to": asset.assigned_to, "status": asset.status
            }}
        if employee_id:
            assets = self.db.get_employee_assets(employee_id)
            return {"status": "success", "assets": [
                {"asset_id": a.asset_id, "type": a.asset_type, "status": a.status}
                for a in assets
            ]}
        return {"status": "error", "message": "Provide asset_id or employee_id"}

    # ── Event Helpers ─────────────────────────────────────────────
    def _setup_new_employee_it(self, data):
        emp_id = data.get("employee_id")
        for system in ["Email", "VPN", "JIRA", "Slack"]:
            self.grant_access(emp_id, system)
        self.log_action("Auto IT Setup", {"employee_id": emp_id,
                        "systems": ["Email","VPN","JIRA","Slack"]})

    def _revoke_all_access(self, data):
        emp_id = data.get("employee_id")
        for system in ["Email", "VPN", "JIRA", "Slack"]:
            self.revoke_access(emp_id, system, "Employee offboarded")

    def _handle_security_incident(self, data):
        self.create_ticket("SYSTEM", "Security",
                           f"Security incident: {data.get('description','')}",
                           priority="Critical")
```

---

## `agents/finance_agent.py`

```python
"""
Finance Agent — Expenses, payroll, budgets, reimbursements
"""
import datetime
from typing import Dict, List
from core.base_agent import BaseAgent
from core.config import EXPENSE_AUTO_APPROVE_LIMIT


class FinanceAgent(BaseAgent):

    def __init__(self, db, llm_service, event_bus=None):
        super().__init__(name="Finance Agent", db=db, llm_service=llm_service, event_bus=event_bus)

    def get_capabilities(self) -> List[str]:
        return [
            "submit_expense", "approve_expense", "get_expense_status",
            "process_payroll", "get_payroll_summary",
            "manage_budget", "process_reimbursement", "ask_finance_policy"
        ]

    def handle_event(self, event_type: str, data: dict):
        if event_type == "employee_onboarded":
            self._setup_payroll(data)
        elif event_type == "expense_submitted":
            self._auto_review_expense(data)

    # ── 1. Submit Expense ─────────────────────────────────────────
    def submit_expense(self, employee_id: str, category: str,
                       amount: float, description: str,
                       receipt_path: str = None) -> Dict:
        from core.database import ExpenseClaim
        expense_id = f"EXP{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        status = "Approved" if amount <= EXPENSE_AUTO_APPROVE_LIMIT else "Pending"

        claim = ExpenseClaim(
            expense_id=expense_id, employee_id=employee_id,
            category=category, amount=amount, description=description,
            receipt_path=receipt_path or "", status=status,
            submitted_date=datetime.datetime.now().isoformat()
        )
        self.db.add_expense(claim)

        if self.event_bus:
            self.event_bus.publish("expense_submitted", {
                "expense_id": expense_id, "amount": amount, "status": status})

        result = {"status": "success", "expense_id": expense_id,
                  "approval_status": status,
                  "message": f"Auto-approved (≤${EXPENSE_AUTO_APPROVE_LIMIT})" if status == "Approved"
                             else "Pending manager approval"}
        self.log_action("Submit Expense", result, employee_id)
        return result

    # ── 2. Approve Expense ────────────────────────────────────────
    def approve_expense(self, expense_id: str, approved_by: str,
                        decision: str = "Approved", notes: str = "") -> Dict:
        expense = self.db.get_expense(expense_id)
        if not expense:
            return {"status": "error", "message": "Expense not found"}
        expense.status = decision
        expense.approved_by = approved_by
        expense.approved_date = datetime.datetime.now().isoformat()
        expense.notes = notes
        result = {"status": "success", "expense_id": expense_id, "decision": decision}
        self.log_action("Approve Expense", result, approved_by)
        return result

    # ── 3. Get Expense Status ─────────────────────────────────────
    def get_expense_status(self, expense_id: str) -> Dict:
        expense = self.db.get_expense(expense_id)
        if not expense:
            return {"status": "error", "message": "Expense not found"}
        return {"status": "success", "expense_id": expense_id,
                "approval_status": expense.status, "amount": expense.amount}

    # ── 4. Process Payroll ────────────────────────────────────────
    def process_payroll(self, month: str, year: int) -> Dict:
        from core.database import PayrollRecord
        records = []
        for emp_id, emp in self.db.employees.items():
            record_id = f"PAY{year}{month}{emp_id}"
            record = PayrollRecord(
                record_id=record_id, employee_id=emp_id,
                month=month, year=year,
                base_salary=self._get_base_salary(emp.position),
                deductions=0, net_salary=0,
                status="Processed",
                processed_date=datetime.datetime.now().isoformat()
            )
            record.net_salary = record.base_salary - record.deductions
            self.db.add_payroll_record(record)
            records.append({"employee_id": emp_id, "net_salary": record.net_salary})

        if self.event_bus:
            self.event_bus.publish("payroll_processed", {"month": month, "year": year})

        result = {"status": "success", "month": month, "year": year,
                  "total_employees": len(records), "records": records}
        self.log_action("Process Payroll", {"month": month, "year": year})
        return result

    def _get_base_salary(self, position: str) -> float:
        defaults = {"Senior Developer": 95000, "Marketing Manager": 85000,
                     "Sales Executive": 65000}
        return defaults.get(position, 60000)

    # ── 5. Get Payroll Summary ────────────────────────────────────
    def get_payroll_summary(self, month: str, year: int) -> Dict:
        records = self.db.get_payroll_by_period(month, year)
        total = sum(r.net_salary for r in records)
        return {"status": "success", "month": month, "year": year,
                "total_employees": len(records), "total_payroll": total}

    # ── 6. Manage Budget ──────────────────────────────────────────
    def manage_budget(self, department: str, action: str = "view",
                      amount: float = 0, **kwargs) -> Dict:
        budget = self.db.get_department_budget(department)
        if action == "view":
            if not budget:
                return {"status": "error", "message": f"No budget for {department}"}
            return {"status": "success", "department": department,
                    "allocated": budget.allocated, "spent": budget.spent,
                    "remaining": budget.allocated - budget.spent}
        elif action == "allocate":
            from core.database import Budget
            if not budget:
                budget = Budget(budget_id=f"BUD{department[:3].upper()}",
                                department=department, allocated=amount,
                                spent=0, fiscal_year=kwargs.get("year", 2026))
                self.db.add_budget(budget)
            else:
                budget.allocated = amount
            return {"status": "success", "department": department, "allocated": amount}
        return {"status": "error", "message": f"Unknown action: {action}"}

    # ── 7. Process Reimbursement ──────────────────────────────────
    def process_reimbursement(self, expense_id: str) -> Dict:
        expense = self.db.get_expense(expense_id)
        if not expense or expense.status != "Approved":
            return {"status": "error", "message": "Expense not approved"}
        from core.database import Reimbursement
        reimb = Reimbursement(
            reimbursement_id=f"RMB{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            expense_id=expense_id, employee_id=expense.employee_id,
            amount=expense.amount, status="Processed",
            processed_date=datetime.datetime.now().isoformat()
        )
        self.db.add_reimbursement(reimb)
        return {"status": "success", "reimbursement_id": reimb.reimbursement_id,
                "amount": expense.amount}

    # ── 8. Ask Finance Policy ─────────────────────────────────────
    def ask_finance_policy(self, question: str) -> Dict:
        policies = self.db.get_finance_policies()
        answer = self.llm.generate_response(
            question,
            f"You are a finance assistant. Policies:\n{policies}\nBe concise."
        )
        return {"status": "success", "answer": answer}

    # ── Event Helpers ─────────────────────────────────────────────
    def _setup_payroll(self, data):
        self.log_action("Setup Payroll Record", data, data.get("employee_id"))

    def _auto_review_expense(self, data):
        if data.get("amount", 0) > EXPENSE_AUTO_APPROVE_LIMIT:
            self.log_action("Expense Flagged for Review", data)
```

---

## `agents/compliance_agent.py`

```python
"""
Compliance Agent — Violations, training, audits, document management
"""
import datetime
from typing import Dict, List
from core.base_agent import BaseAgent


class ComplianceAgent(BaseAgent):

    def __init__(self, db, llm_service, event_bus=None):
        super().__init__(name="Compliance Agent", db=db, llm_service=llm_service, event_bus=event_bus)

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
        return {"status": "success", "violation_id": vid,
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
            return {"status": "success", "training_id": tid,
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
```

---

## `agents/__init__.py`

```python
"""Agent layer — all domain agents"""
from agents.hr_agent import HRAgent
from agents.it_agent import ITAgent
from agents.finance_agent import FinanceAgent
from agents.compliance_agent import ComplianceAgent
```

---

## ✅ Done Checklist

- [ ] `agents/__init__.py` with all 4 agent imports
- [ ] `agents/hr_agent.py` — see guide 05
- [ ] `agents/it_agent.py` — 7 capabilities + event handlers
- [ ] `agents/finance_agent.py` — 8 capabilities + event handlers
- [ ] `agents/compliance_agent.py` — 8 capabilities + event handlers
- [ ] All agents extend `BaseAgent` (from `core/base_agent.py`)
- [ ] All agents publish events via `event_bus`
- [ ] All agents respond to cross-agent events (onboarded, offboarded, etc.)
- [ ] Each agent has `get_capabilities()` and `handle_event()` implemented
