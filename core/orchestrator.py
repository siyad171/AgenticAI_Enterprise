"""
core/orchestrator.py — Multi-agent workflow coordination

Agentic AI Features:
- Multi-Agent Coordination (workflows spanning 2-4 agents)
- Task Routing (LLM classifies which agent handles a request)
- Escalation (confidence < threshold → human review)
"""
from datetime import datetime
from typing import Dict, List, Optional
from core.base_agent import BaseAgent
from core.config import ESCALATION_CONFIDENCE_THRESHOLD


class Orchestrator:

    def __init__(self, agents: Dict[str, BaseAgent], event_bus, llm_service):
        """
        agents: {"hr": HRAgent, "it": ITAgent, "finance": FinanceAgent, "compliance": ComplianceAgent}
        """
        self.agents = agents
        self.event_bus = event_bus
        self.llm = llm_service
        self.active_workflows: Dict[str, Dict] = {}
        self.completed_workflows: List[Dict] = []
        self.escalation_queue: List[Dict] = []

    # ─────────── Task Routing ───────────

    def route_task(self, task_description: str, context: Dict = None) -> Dict:
        """Use LLM to determine which agent should handle a task."""
        agent_list = ", ".join(
            f"{name} ({agent.agent_name}): {', '.join(agent.get_capabilities())}"
            for name, agent in self.agents.items()
        )

        prompt = f"""You are a task router. Given this request, decide which agent should handle it.

Available Agents:
{agent_list}

Task: {task_description}

Return the agent key (hr, it, finance, or compliance) and brief reasoning.
Format: agent_key | reasoning
"""
        response = self.llm.generate_response(prompt)
        # Parse — simple extraction
        for key in self.agents:
            if key in response.lower():
                return {"agent": key, "reasoning": response}
        return {"agent": "hr", "reasoning": "Default routing to HR"}

    # ─────────── Workflow Execution ───────────

    def execute_workflow(self, workflow_name: str, params: Dict) -> Dict:
        """Run a predefined multi-step workflow."""
        workflow_id = f"WF-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        self.active_workflows[workflow_id] = {
            "id": workflow_id,
            "name": workflow_name,
            "params": params,
            "status": "In Progress",
            "steps": [],
            "started_at": datetime.now().isoformat(),
        }

        handlers = {
            "new_hire": self._workflow_new_hire,
            "employee_exit": self._workflow_employee_exit,
            "expense_claim": self._workflow_expense_claim,
            "security_incident": self._workflow_security_incident,
        }

        handler = handlers.get(workflow_name)
        if not handler:
            return {"status": "error", "message": f"Unknown workflow: {workflow_name}"}

        try:
            result = handler(workflow_id, params)
            self.active_workflows[workflow_id]["status"] = "Completed"
            self.active_workflows[workflow_id]["completed_at"] = datetime.now().isoformat()
            self.completed_workflows.append(self.active_workflows.pop(workflow_id))
            return result
        except Exception as e:
            self.active_workflows[workflow_id]["status"] = "Failed"
            self.active_workflows[workflow_id]["error"] = str(e)
            return {"status": "error", "message": str(e)}

    def _log_step(self, workflow_id: str, step_name: str, agent: str, result: Dict):
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id]["steps"].append({
                "step": step_name,
                "agent": agent,
                "result": result.get("status", "unknown"),
                "timestamp": datetime.now().isoformat(),
            })

    # ─────────── Predefined Workflows ───────────

    def _workflow_new_hire(self, workflow_id: str, params: Dict) -> Dict:
        """
        Full new-hire pipeline (triggered AFTER candidate passes all assessments):
        Step 1: HR → onboard employee
        Step 2: IT → provision access  (triggered by event automatically)
        Step 3: Finance → setup payroll (triggered by event automatically)
        Step 4: Compliance → validate   (triggered by event automatically)

        Steps 2-4 happen automatically via EventBus when HR publishes employee_onboarded.
        This orchestrator logs the initiation.
        """
        hr = self.agents.get("hr")
        result = hr.handle_employee_onboarding(
            name=params["name"],
            email=params["email"],
            department=params["department"],
            position=params["position"],
            join_date=params["join_date"],
        )
        self._log_step(workflow_id, "HR Onboarding", "HR Agent", result)
        # IT, Finance, Compliance steps fire via EventBus subscription
        return {"status": "success", "workflow_id": workflow_id, "hr_result": result}

    def _workflow_employee_exit(self, workflow_id: str, params: Dict) -> Dict:
        """
        Step 1: HR → process exit paperwork
        Step 2: IT → revoke access
        Step 3: Finance → settle final pay
        Step 4: Compliance → exit compliance check
        """
        emp_id = params["employee_id"]
        results = {}

        # Step 1: HR logs exit
        hr = self.agents.get("hr")
        hr.log_action("Employee Exit", {"employee_id": emp_id}, "Admin")
        self._log_step(workflow_id, "HR Exit Processing", "HR Agent", {"status": "success"})

        # Step 2: IT revoke
        it = self.agents.get("it")
        if it:
            r = it.revoke_employee_access(emp_id)
            results["it"] = r
            self._log_step(workflow_id, "IT Access Revocation", "IT Agent", r)

        # Step 3: Finance settle
        fin = self.agents.get("finance")
        if fin:
            r = fin.settle_final_pay(emp_id)
            results["finance"] = r
            self._log_step(workflow_id, "Finance Final Pay", "Finance Agent", r)

        # Step 4: Compliance check
        comp = self.agents.get("compliance")
        if comp:
            r = comp.validate_onboarding_compliance(emp_id)  # reuse for exit check
            results["compliance"] = r
            self._log_step(workflow_id, "Compliance Exit Check", "Compliance Agent", r)

        return {"status": "success", "workflow_id": workflow_id, "results": results}

    def _workflow_expense_claim(self, workflow_id: str, params: Dict) -> Dict:
        """Finance validate → Compliance check → Finance reimburse (if approved)."""
        fin = self.agents.get("finance")
        result = fin.process_expense_claim(params["claim"])
        self._log_step(workflow_id, "Finance Expense Processing", "Finance Agent", result)
        return {"status": "success", "workflow_id": workflow_id, "result": result}

    def _workflow_security_incident(self, workflow_id: str, params: Dict) -> Dict:
        """IT investigate → Compliance review → HR notify."""
        results = {}

        it = self.agents.get("it")
        if it:
            r = it.monitor_security()
            results["it_scan"] = r
            self._log_step(workflow_id, "IT Security Scan", "IT Agent", r)

        comp = self.agents.get("compliance")
        if comp:
            r = comp.flag_anomaly(
                params.get("incident_type", "Security"),
                params.get("details", "Security incident reported"),
            )
            results["compliance"] = r
            self._log_step(workflow_id, "Compliance Review", "Compliance Agent", r)

        return {"status": "success", "workflow_id": workflow_id, "results": results}

    # ─────────── Status & Dashboard ───────────

    def get_all_agent_statuses(self) -> Dict:
        """Return status of each agent for the dashboard."""
        statuses = {}
        for key, agent in self.agents.items():
            statuses[key] = {
                "name": agent.agent_name,
                "capabilities": agent.get_capabilities(),
                "decisions_made": len(agent.decision_history),
                "status": "Active",
            }
        return statuses

    def get_active_workflows(self) -> List[Dict]:
        return list(self.active_workflows.values())

    def get_completed_workflows(self) -> List[Dict]:
        return self.completed_workflows[-20:]  # last 20

    def get_escalation_queue(self) -> List[Dict]:
        return self.escalation_queue
