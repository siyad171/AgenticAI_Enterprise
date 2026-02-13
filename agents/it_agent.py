"""
IT Agent — Ticket management, access control, software licenses, asset tracking
"""
import datetime
from typing import Dict, List
from core.base_agent import BaseAgent
from tools.email_service import EmailService


class ITAgent(BaseAgent):

    def __init__(self, db, llm_service, event_bus=None):
        super().__init__(agent_name="IT Agent", database=db, llm_service=llm_service, event_bus=event_bus)
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
