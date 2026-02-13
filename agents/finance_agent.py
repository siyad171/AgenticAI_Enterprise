"""
Finance Agent — Expenses, payroll, budgets, reimbursements
"""
import datetime
from typing import Dict, List
from core.base_agent import BaseAgent
from core.config import EXPENSE_AUTO_APPROVE_LIMIT


class FinanceAgent(BaseAgent):

    def __init__(self, db, llm_service, event_bus=None):
        super().__init__(agent_name="Finance Agent", database=db, llm_service=llm_service, event_bus=event_bus)

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
