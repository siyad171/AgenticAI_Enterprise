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
        self._register_tools()

    def _register_tools(self):
        """Register all IT methods as autonomous tools."""
        self.register_tool(
            name="create_ticket",
            description="Create an IT support ticket for hardware, software, network, or security issues. Uses LLM to suggest resolution.",
            parameters={
                "employee_id": "str — Employee ID reporting the issue",
                "category": "str — One of: Hardware, Software, Network, Security, Other",
                "description": "str — Detailed description of the issue",
                "priority": "str — One of: Low, Medium, High, Critical (default: Medium)"
            },
            function=self.create_ticket,
            requires_employee_id=True
        )
        self.register_tool(
            name="resolve_ticket",
            description="Resolve an open IT ticket with a resolution description.",
            parameters={
                "ticket_id": "str — Ticket ID to resolve (e.g. TKT...)",
                "resolution": "str — Description of how the issue was resolved",
                "resolved_by": "str — Who resolved it (default: IT Agent)"
            },
            function=self.resolve_ticket
        )
        self.register_tool(
            name="get_ticket_status",
            description="Check the current status and details of an IT ticket.",
            parameters={
                "ticket_id": "str — Ticket ID to check"
            },
            function=self.get_ticket_status
        )
        self.register_tool(
            name="grant_access",
            description="Grant an employee access to a system (Email, VPN, JIRA, Slack, GitHub, AWS Console).",
            parameters={
                "employee_id": "str — Employee ID to grant access to",
                "system": "str — System name (e.g. Email, VPN, JIRA, Slack, GitHub, AWS Console)",
                "access_level": "str — One of: Standard, Admin, Read-Only (default: Standard)",
                "approved_by": "str — Who approved (default: IT Admin)"
            },
            function=self.grant_access,
            requires_employee_id=True
        )
        self.register_tool(
            name="revoke_access",
            description="Revoke an employee's access to a specific system.",
            parameters={
                "employee_id": "str — Employee ID",
                "system": "str — System to revoke access from",
                "reason": "str — Reason for revocation"
            },
            function=self.revoke_access,
            requires_employee_id=True
        )
        self.register_tool(
            name="manage_software_license",
            description="Assign or release a software license for an employee.",
            parameters={
                "action": "str — One of: assign, release",
                "software": "str — Software name",
                "employee_id": "str — Employee ID (required for assign)"
            },
            function=self.manage_software_license
        )
        self.register_tool(
            name="track_asset",
            description="Track IT assets. Search by asset ID or employee ID to see assigned hardware/devices.",
            parameters={
                "asset_id": "str — Asset ID to look up (optional)",
                "employee_id": "str — Employee ID to find their assets (optional)"
            },
            function=self.track_asset
        )
        self.register_tool(
            name="get_open_tickets_summary",
            description="Get a summary of all open IT tickets — useful for status reports and identifying patterns.",
            parameters={},
            function=self._get_open_tickets_summary
        )

    def _get_open_tickets_summary(self) -> Dict:
        """Tool: Summarize all open tickets."""
        tickets = getattr(self.db, 'it_tickets', {})
        open_tickets = [
            {"ticket_id": t.ticket_id, "category": t.category,
             "priority": t.priority, "employee_id": t.employee_id,
             "description": t.description, "created": t.created_date}
            for t in tickets.values() if t.status == "Open"
        ]
        by_priority = {}
        by_category = {}
        for t in open_tickets:
            by_priority[t["priority"]] = by_priority.get(t["priority"], 0) + 1
            by_category[t["category"]] = by_category.get(t["category"], 0) + 1
        return {
            "status": "success",
            "total_open": len(open_tickets),
            "by_priority": by_priority,
            "by_category": by_category,
            "tickets": open_tickets
        }

    def _get_domain_context(self, user_message: str, context: Dict) -> Dict:
        """Add IT-specific context for the LLM reasoning."""
        domain = {}
        msg_lower = user_message.lower()

        # Add open tickets summary for ticket-related queries
        if any(w in msg_lower for w in ["ticket", "issue", "problem", "crash", "broken",
                                         "not working", "error", "help", "support", "fix"]):
            tickets = getattr(self.db, 'it_tickets', {})
            open_count = sum(1 for t in tickets.values() if t.status == "Open")
            domain["open_tickets_count"] = open_count
            domain["ticket_categories"] = ["Hardware", "Software", "Network", "Security", "Other"]

        if any(w in msg_lower for w in ["access", "permission", "grant", "revoke", "login"]):
            domain["available_systems"] = ["Email", "VPN", "JIRA", "Slack", "GitHub", "AWS Console"]
            domain["access_levels"] = ["Standard", "Admin", "Read-Only"]

        if any(w in msg_lower for w in ["license", "software", "install"]):
            from core.config import APPROVED_SOFTWARE
            domain["approved_software"] = APPROVED_SOFTWARE

        # Employee lookup
        if self.db.employees:
            domain["known_employees"] = {
                eid: {"name": e.name, "department": e.department}
                for eid, e in self.db.employees.items()
            }
        return domain

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
        # Generate a short subject line from the description
        subject = description[:80] if description else f"{category} issue"
        ticket = ITTicket(
            ticket_id=ticket_id, employee_id=employee_id,
            category=category, subject=subject, description=description,
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
            employee_id=employee_id, systems=[system],
            role_permissions=access_level,
            provisioned_date=datetime.datetime.now().isoformat(),
            status="Active"
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
            if system in getattr(r, 'systems', []) and r.status == "Active":
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

    # ── Goal Tracking ─────────────────────────────────────────────
    def _update_goals(self, actions_taken: list):
        """Update IT KPIs after agentic actions."""
        if not self.goal_tracker:
            return
        for action in actions_taken:
            if action.get("success") and action["tool"] == "resolve_ticket":
                # Count open tickets to update KPI
                tickets = getattr(self.db, 'it_tickets', {})
                open_count = sum(1 for t in tickets.values() if t.status == "Open")
                self.goal_tracker.record_metric("IT Agent", "Open tickets", open_count)
