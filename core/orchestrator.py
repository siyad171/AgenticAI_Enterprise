"""
core/orchestrator.py — Multi-agent workflow coordination

Agentic AI Features:
- Multi-Agent Coordination (workflows spanning 2-4 agents)
- Intelligent Chat Routing (LLM classifies which agent handles a request)
- Agentic Delegation (routes chat to agent's process_request ReAct loop)
- Escalation (confidence < threshold → human review)
"""
import json, re, os
from datetime import datetime
from typing import Dict, List, Optional
from core.base_agent import BaseAgent
from core.config import ESCALATION_CONFIDENCE_THRESHOLD


class Orchestrator:

    def __init__(self, agents: Dict[str, BaseAgent], llm_service, event_bus):
        """
        agents: {"hr": HRAgent, "it": ITAgent, "finance": FinanceAgent, "compliance": ComplianceAgent}
        """
        self.agents = agents
        self.event_bus = event_bus
        self.llm = llm_service
        self.active_workflows: Dict[str, Dict] = {}
        self.completed_workflows: List[Dict] = []
        self.escalation_queue: List[Dict] = []

    # - - - - - - - - - Escalation lifecycle - - - - - - - - -

    def _create_escalation_case(self, user_message: str, context: Dict,
                                agent_key: str, agent_label: str,
                                result_data: Dict) -> Dict:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        case_id = f"ESC-{timestamp}"
        employee_id = context.get("employee_id")

        employee_name = "Unknown"
        try:
            if employee_id:
                db = next(iter(self.agents.values())).db
                emp = db.get_employee(employee_id)
                if emp:
                    employee_name = emp.name
        except Exception:
            pass

        case = {
            "case_id": case_id,
            "status": "Open",
            "created_at": datetime.now().isoformat(),
            "request": user_message,
            "employee_id": employee_id,
            "employee_name": employee_name,
            "agent": agent_key,
            "agent_label": agent_label,
            "confidence": float(result_data.get("confidence", 0.0) or 0.0),
            "reasoning": result_data.get("reasoning", ""),
            "escalation_reason": result_data.get("escalation_reason", ""),
            "human_reason": result_data.get("human_reason", ""),
            "escalation_type": result_data.get("escalation_type", ""),
            "proposed_response": result_data.get("response", ""),
            "context": context,
            "admin_decision": None,
            "admin_decision_type": None,
            "admin_reason": None,
            "employee_response": None,
            "resolved_by": None,
            "resolved_at": None,
            "learning_recorded": False,
        }
        self.escalation_queue.append(case)
        return case

    def _generate_employee_resolution_response(self, agent: BaseAgent, case: Dict) -> str:
        """Build the final employee-facing response using the responsible domain agent."""
        admin_decision = (case.get("admin_decision") or "").strip()
        admin_reason = (case.get("admin_reason") or "").strip()
        decision_type = case.get("admin_decision_type") or "custom"

        # Keep tests deterministic and avoid external dependency calls.
        if os.getenv("TESTING") == "1":
            return admin_decision or "Your request was reviewed by admin and has been resolved."

        if not admin_decision:
            return "Your request was reviewed by admin and has been resolved."

        prompt = f"""Create the final employee-facing response for this resolved escalation.

Employee request: {case.get("request", "")}
Escalation reason: {case.get("escalation_reason") or case.get("human_reason") or "N/A"}
Admin decision type: {decision_type}
Admin decision content: {admin_decision}
Admin rationale: {admin_reason or "N/A"}

Requirements:
- 2-4 concise, professional sentences.
- Natural language that the employee can understand.
- Reflect the admin decision accurately.
- Do not mention internal tools, prompts, or implementation details.
"""

        try:
            generated = agent.llm.generate_response(
                prompt,
                f"You are {agent.agent_name}. Draft clear enterprise support responses.",
            )
            return (generated or "").strip() or admin_decision
        except Exception:
            return admin_decision

    def resolve_escalation(self, case_id: str, admin_decision: str,
                           reason: str, resolved_by: str = "Admin",
                           decision_type: str = "custom") -> Dict:
        case = next((c for c in self.escalation_queue if c.get("case_id") == case_id), None)
        if not case:
            return {"status": "error", "message": f"Escalation case {case_id} not found"}

        case["status"] = "Resolved"
        case["admin_decision"] = admin_decision
        case["admin_decision_type"] = decision_type
        case["admin_reason"] = reason
        case["resolved_by"] = resolved_by
        case["resolved_at"] = datetime.now().isoformat()

        agent = self.agents.get(case.get("agent"))
        if agent:
            case["employee_response"] = self._generate_employee_resolution_response(agent, case)
        else:
            case["employee_response"] = admin_decision

        learning_result = self._record_admin_learning(case)
        return {
            "status": "success",
            "case_id": case_id,
            "learning_recorded": learning_result.get("status") == "success",
            "learning_message": learning_result.get("message", "")
        }

    def _record_admin_learning(self, case: Dict) -> Dict:
        agent_key = case.get("agent")
        agent = self.agents.get(agent_key)
        if not agent:
            return {"status": "error", "message": f"Unknown agent: {agent_key}"}

        original_decision = case.get("reasoning") or case.get("escalation_reason") or "Escalated to human review"
        admin_decision_text = case.get("admin_decision", "")
        admin_reason = case.get("admin_reason", "")

        try:
            agent.learning.record_override(
                decision_id=case.get("case_id", ""),
                original_decision=original_decision,
                admin_decision=admin_decision_text,
                reason=admin_reason,
                task=case.get("request", ""),
                context={
                    "employee_id": case.get("employee_id"),
                    "escalation_reason": case.get("escalation_reason"),
                    "escalation_type": case.get("escalation_type"),
                    "admin_decision_type": case.get("admin_decision_type"),
                    "agent_confidence": case.get("confidence"),
                    "agent": agent_key,
                },
            )
            case["learning_recorded"] = True
            return {"status": "success", "message": "Admin decision persisted to learning memory"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to persist learning: {e}"}

    # ─────────── Agentic Chat: Route & Delegate ───────────

    def chat(self, user_message: str, context: Dict = None) -> Dict:
        """
        Main agentic entry point for the unified chat.
        Routes the message to the right agent, which then runs its ReAct loop.
        Returns planning_steps for UI transparency.
        """
        context = context or {}

        # Agent display labels
        agent_labels = {
            "hr": "🏥 HR Agent",
            "it": "🔧 IT Agent",
            "finance": "💰 Finance Agent",
            "compliance": "📋 Compliance Agent",
        }

        # Step 1: Route to the right agent
        routing = self.route_task(user_message, context)
        agent_key = routing.get("agent", "hr")
        agent = self.agents.get(agent_key)

        routing_step = {
            "step": "Routing",
            "status": "completed",
            "detail": f"Routed to {agent_labels.get(agent_key, agent_key)}"
        }

        if not agent:
            return {
                "response": "I couldn't determine which department can help with this. Could you provide more details?",
                "agent": "unknown",
                "agent_label": "🤖 AI",
                "planning_steps": [{
                    "step": "Routing",
                    "status": "failed",
                    "detail": "Could not determine the right agent"
                }],
                "routing_reasoning": routing.get("reasoning", "")
            }

        # Step 2: Delegate to the agent's agentic process_request
        result = agent.process_request(user_message, context)

        # Prepend routing step to the agent's planning_steps
        result["planning_steps"] = [routing_step] + result.get("planning_steps", [])
        result["agent"] = agent_key
        result["agent_label"] = agent_labels.get(agent_key, agent_key)
        result["agent_name"] = agent.agent_name
        result["routing_reasoning"] = routing.get("reasoning", "")

        if result.get("escalated"):
            case = self._create_escalation_case(
                user_message=user_message,
                context=context,
                agent_key=agent_key,
                agent_label=result["agent_label"],
                result_data=result,
            )
            result["escalation_id"] = case.get("case_id")
        return result

    def chat_stream(self, user_message: str, context: Dict = None):
        """
        Streaming generator version of chat().
        Yields {"type": "step", "step": {...}} for each planning step as it completes.
        Finally yields {"type": "result", ...} with the full response payload.
        """
        context = context or {}

        agent_labels = {
            "hr": "🏥 HR Agent",
            "it": "🔧 IT Agent",
            "finance": "💰 Finance Agent",
            "compliance": "📋 Compliance Agent",
        }

        # Step 1: Route (LLM call — yield routing step as soon as it returns)
        routing = self.route_task(user_message, context)
        agent_key = routing.get("agent", "hr")
        agent = self.agents.get(agent_key)

        yield {
            "type": "step",
            "step": {
                "step": "Routing",
                "status": "completed",
                "detail": f"Routed to {agent_labels.get(agent_key, agent_key)}"
            }
        }

        if not agent:
            yield {
                "type": "result",
                "response": "I couldn't determine which department can help with this. Could you provide more details?",
                "agent": "unknown",
                "agent_label": "🤖 AI",
                "actions_taken": [],
                "reasoning": "",
                "confidence": 0.0,
                "escalated": False,
                "routing_reasoning": routing.get("reasoning", "")
            }
            return

        # Step 2: Stream steps from the agent's ReAct loop
        result_data = None
        for item in agent.process_request_stream(user_message, context):
            if item["type"] == "step":
                yield item
            elif item["type"] == "result":
                result_data = item

        if result_data is None:
            result_data = {
                "type": "result",
                "response": "An unexpected error occurred. Please try again.",
                "actions_taken": [],
                "reasoning": "",
                "confidence": 0.0,
                "escalated": False
            }

        result_data["agent"] = agent_key
        result_data["agent_label"] = agent_labels.get(agent_key, agent_key)
        result_data["agent_name"] = agent.agent_name
        result_data["routing_reasoning"] = routing.get("reasoning", "")

        if result_data.get("escalated"):
            case = self._create_escalation_case(
                user_message=user_message,
                context=context,
                agent_key=agent_key,
                agent_label=result_data["agent_label"],
                result_data=result_data,
            )
            result_data["escalation_id"] = case.get("case_id")
        yield result_data

    # ─────────── Task Routing ───────────

    def route_task(self, task_description: str, context: Dict = None) -> Dict:
        """Use LLM to determine which agent should handle a task."""
        agent_list = "\n".join(
            f"- {name}: {', '.join(agent.get_capabilities())}"
            for name, agent in self.agents.items()
        )

        prompt = f"""You are a task router for an enterprise AI system. Route this request to the right agent.

Available Agents:
{agent_list}

User Request: "{task_description}"

Return ONLY a JSON object: {{"agent": "hr|it|finance|compliance", "reasoning": "brief reason"}}
"""
        try:
            response = self.llm.generate_json_response(prompt)
            m = re.search(r'\{[^{}]*\}', response)
            if m:
                data = json.loads(m.group(0))
                agent_key = data.get("agent", "").lower()
                if agent_key in self.agents:
                    return {"agent": agent_key, "reasoning": data.get("reasoning", "")}
        except Exception:
            pass

        # Fallback: keyword-based routing
        task_lower = task_description.lower()
        if any(w in task_lower for w in ["leave", "onboard", "hire", "policy", "employee", "vacation", "absent"]):
            return {"agent": "hr", "reasoning": "Keyword match: HR-related request"}
        if any(w in task_lower for w in ["ticket", "access", "software", "hardware", "vpn", "crash", "error", "network", "password"]):
            return {"agent": "it", "reasoning": "Keyword match: IT-related request"}
        if any(w in task_lower for w in ["expense", "budget", "payroll", "salary", "reimburse", "payment"]):
            return {"agent": "finance", "reasoning": "Keyword match: Finance-related request"}
        if any(w in task_lower for w in ["compliance", "violation", "audit", "training", "regulation"]):
            return {"agent": "compliance", "reasoning": "Keyword match: Compliance-related request"}

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

    def get_escalation_queue(self, status: Optional[str] = None) -> List[Dict]:
        if not status:
            return self.escalation_queue
        return [e for e in self.escalation_queue if e.get("status") == status]

    def get_escalation_metrics(self) -> Dict:
        open_cases = len([e for e in self.escalation_queue if e.get("status") == "Open"])
        resolved_cases = len([e for e in self.escalation_queue if e.get("status") == "Resolved"])
        return {
            "open": open_cases,
            "resolved": resolved_cases,
            "total": len(self.escalation_queue),
        }
