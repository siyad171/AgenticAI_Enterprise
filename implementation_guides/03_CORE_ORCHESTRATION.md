# 🎯 Step 3: Core Orchestration

> **Requires**: `02_CORE_SERVICES.md` completed  
> **Creates**: `core/orchestrator.py`, `core/goal_tracker.py`, `core/learning_module.py`  
> **Next**: → `04_TOOLS_LAYER.md`

---

## File 1: `core/orchestrator.py`

Coordinates multi-agent workflows. Routes free-text tasks. Manages escalations.

```python
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
```

---

## File 2: `core/goal_tracker.py`

Tracks KPIs per agent. Dashboard shows progress bars.

```python
"""
core/goal_tracker.py — KPI tracking for each agent

Agentic AI Feature: Goal-Oriented Behavior
Each agent has measurable targets. The dashboard shows progress.
"""
from datetime import datetime
from typing import Dict, List, Optional


class GoalTracker:

    def __init__(self):
        self.goals: Dict[str, List[Dict]] = {}  # agent_name → [goal, ...]
        self._initialize_default_goals()

    def _initialize_default_goals(self):
        self.goals = {
            "HR Agent": [
                {"name": "Time-to-hire", "target": 7, "actual": None, "unit": "days", "direction": "lower"},
                {"name": "Candidate satisfaction", "target": 80, "actual": None, "unit": "%", "direction": "higher"},
            ],
            "IT Agent": [
                {"name": "Provisioning SLA", "target": 100, "actual": None, "unit": "%", "direction": "higher"},
                {"name": "Open tickets", "target": 5, "actual": None, "unit": "count", "direction": "lower"},
            ],
            "Finance Agent": [
                {"name": "Budget variance", "target": 5, "actual": None, "unit": "%", "direction": "lower"},
                {"name": "Avg reimbursement time", "target": 3, "actual": None, "unit": "days", "direction": "lower"},
            ],
            "Compliance Agent": [
                {"name": "Policy violations", "target": 0, "actual": None, "unit": "count", "direction": "lower"},
                {"name": "Training completion", "target": 100, "actual": None, "unit": "%", "direction": "higher"},
            ],
        }

    def set_goal(self, agent_name: str, goal_name: str, target_value: float, unit: str, direction: str = "higher"):
        if agent_name not in self.goals:
            self.goals[agent_name] = []
        # Update existing or add new
        for g in self.goals[agent_name]:
            if g["name"] == goal_name:
                g["target"] = target_value
                g["unit"] = unit
                g["direction"] = direction
                return
        self.goals[agent_name].append({
            "name": goal_name, "target": target_value,
            "actual": None, "unit": unit, "direction": direction
        })

    def record_metric(self, agent_name: str, goal_name: str, actual_value: float):
        for g in self.goals.get(agent_name, []):
            if g["name"] == goal_name:
                g["actual"] = actual_value
                g["last_updated"] = datetime.now().isoformat()
                return

    def get_agent_performance(self, agent_name: str) -> List[Dict]:
        return self.goals.get(agent_name, [])

    def get_all_performance(self) -> Dict[str, List[Dict]]:
        return self.goals

    def is_goal_met(self, agent_name: str, goal_name: str) -> Optional[bool]:
        for g in self.goals.get(agent_name, []):
            if g["name"] == goal_name and g["actual"] is not None:
                if g["direction"] == "higher":
                    return g["actual"] >= g["target"]
                else:
                    return g["actual"] <= g["target"]
        return None  # Not yet measured
```

---

## File 3: `core/learning_module.py`

Stores decision history on disk. Admin overrides = learning signals. Past decisions → few-shot prompts.

```python
"""
core/learning_module.py — Decision history + adaptive learning

Agentic AI Feature: Continuous Learning & Improvement
- Records every autonomous decision with context
- Records admin overrides (critical learning signal)
- Retrieves similar past decisions for few-shot LLM prompting
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from core.config import LEARNING_DATA_DIR


class LearningModule:

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.storage_dir = LEARNING_DATA_DIR
        self.decisions: List[Dict] = []
        self.overrides: List[Dict] = []
        self._load_history()

    # ─────────── Record ───────────

    def record_decision(self, task: str, context: Dict, decision: str,
                        confidence: float, outcome: str = None):
        entry = {
            "id": f"DEC-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "agent": self.agent_name,
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "context": context,
            "decision": decision,
            "confidence": confidence,
            "outcome": outcome,
        }
        self.decisions.append(entry)
        self._save_history()

    def record_override(self, decision_id: str, original_decision: str,
                        admin_decision: str, reason: str):
        """Admin overrides agent decision — high-value learning signal."""
        override = {
            "decision_id": decision_id,
            "agent": self.agent_name,
            "timestamp": datetime.now().isoformat(),
            "original_decision": original_decision,
            "admin_decision": admin_decision,
            "reason": reason,
        }
        self.overrides.append(override)
        self._save_history()

    # ─────────── Retrieve ───────────

    def get_relevant_examples(self, current_task: str, n: int = 3) -> List[Dict]:
        """Simple keyword-based retrieval of similar past decisions.
        (Could be upgraded to vector similarity search later.)
        """
        keywords = set(current_task.lower().split())
        scored = []
        for d in self.decisions:
            task_words = set(d["task"].lower().split())
            overlap = len(keywords & task_words)
            if overlap > 0:
                scored.append((overlap, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:n]]

    def get_performance_stats(self) -> Dict:
        total = len(self.decisions)
        overridden = len(self.overrides)
        avg_conf = (
            sum(d["confidence"] for d in self.decisions) / total
            if total > 0 else 0
        )
        return {
            "total_decisions": total,
            "total_overrides": overridden,
            "override_rate": (overridden / total * 100) if total > 0 else 0,
            "average_confidence": round(avg_conf, 2),
        }

    # ─────────── Persistence ───────────

    def _file_path(self) -> str:
        safe_name = self.agent_name.lower().replace(" ", "_")
        return os.path.join(self.storage_dir, f"{safe_name}_learning.json")

    def _load_history(self):
        path = self._file_path()
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    self.decisions = data.get("decisions", [])
                    self.overrides = data.get("overrides", [])
            except Exception:
                self.decisions = []
                self.overrides = []

    def _save_history(self):
        os.makedirs(self.storage_dir, exist_ok=True)
        path = self._file_path()
        with open(path, "w") as f:
            json.dump({
                "decisions": self.decisions[-500:],   # keep last 500
                "overrides": self.overrides[-100:],
            }, f, indent=2)
```

---

## How Orchestration Connects Everything

```
┌──────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR                          │
│  • route_task() → picks the right agent                  │
│  • execute_workflow() → runs multi-agent pipelines       │
│  • escalation_queue → low-confidence decisions           │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   HR Agent ──┐                                           │
│   IT Agent ──┤── each has: GoalTracker + LearningModule  │
│   Fin Agent ─┤                                           │
│   Comp Agent ┘                                           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## ✅ Done Checklist

- [ ] `core/orchestrator.py` — route_task, execute_workflow, 4 predefined workflows
- [ ] `core/goal_tracker.py` — default goals for 4 agents, record/query metrics
- [ ] `core/learning_module.py` — record decisions, record overrides, retrieve examples, file persistence
- [ ] All three import cleanly: `python -c "from core.orchestrator import Orchestrator; print('OK')"`

---

**Next** → `04_TOOLS_LAYER.md` (All 9 tools: email, code execution, video, interview, psychometric, storage)
