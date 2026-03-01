"""
core/base_agent.py — Abstract agent that all domain agents extend

Agentic AI Features (LIVE):
- Tool Registry: agents register their methods as callable tools
- ReAct Loop: Perceive → Reason → Plan → Act → Evaluate → Learn → Respond
- LearningModule integration: every decision is recorded, past decisions inform future ones
- GoalTracker integration: KPIs auto-update after every action
- Environment Perception (handle_event via EventBus)
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Callable, Any
from datetime import datetime
import json, re, traceback

from core.database import AuditLog
from core.learning_module import LearningModule
from core.config import ESCALATION_CONFIDENCE_THRESHOLD


class AgentTool:
    """Descriptor for a tool that an agent can autonomously invoke."""
    def __init__(self, name: str, description: str,
                 parameters: Dict[str, str], function: Callable,
                 requires_employee_id: bool = False):
        self.name = name
        self.description = description
        self.parameters = parameters          # {"param_name": "type  — description"}
        self.function = function
        self.requires_employee_id = requires_employee_id


class BaseAgent(ABC):

    def __init__(self, agent_name: str, database, llm_service, event_bus):
        self.agent_name = agent_name
        self.db = database
        self.llm = llm_service
        self.event_bus = event_bus
        self.goals: Dict[str, Dict] = {}
        self.decision_history: List[Dict] = []

        # ── Agentic additions ──
        self._tools: Dict[str, AgentTool] = {}
        self.learning = LearningModule(agent_name)
        self.goal_tracker = None        # set after GoalTracker is created
        self.chat_histories: Dict[str, List[Dict]] = {}  # user_id → messages

    # ─────────── Abstract (each agent must implement) ───────────

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of action names this agent can perform."""
        pass

    @abstractmethod
    def handle_event(self, event_type: str, event_data: Dict):
        """React to an event from the EventBus."""
        pass

    # ═══════════════════════════════════════════════════════════════
    #  TOOL REGISTRY — agents register their methods as selectable tools
    # ═══════════════════════════════════════════════════════════════

    def register_tool(self, name: str, description: str,
                      parameters: Dict[str, str], function: Callable,
                      requires_employee_id: bool = False):
        """Register an existing method as a tool the agent can autonomously choose."""
        self._tools[name] = AgentTool(
            name=name, description=description,
            parameters=parameters, function=function,
            requires_employee_id=requires_employee_id
        )

    def get_tools_description(self) -> str:
        """Format all tools for the LLM prompt."""
        lines = []
        for t in self._tools.values():
            params = ", ".join(f'{k}: {v}' for k, v in t.parameters.items())
            lines.append(f"- {t.name}({params})\n  Description: {t.description}")
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    #  ReAct LOOP — the core agentic reasoning engine
    # ═══════════════════════════════════════════════════════════════

    def process_request(self, user_message: str, context: Dict = None) -> Dict:
        """
        Main agentic entry point. Processes a natural-language request
        using the full Perceive → Reason → Plan → Act → Evaluate → Learn loop.

        Returns:
            {
              "response": str,         # natural-language reply to user
              "actions_taken": list,    # tools invoked and their results
              "reasoning": str,         # agent's reasoning chain
              "confidence": float,      # 0.0 – 1.0
              "escalated": bool         # True if confidence < threshold
            }
        """
        context = context or {}
        actions_taken = []

        # ── 1. PERCEIVE — gather context ──────────────────────────
        perception = self._perceive(user_message, context)

        # ── 2. REASON & PLAN — LLM decides what to do ────────────
        plan = self._reason_and_plan(user_message, perception)

        if plan.get("error"):
            return {
                "response": plan.get("fallback_response",
                                     "I understand your request but I'm having trouble processing it. Could you please rephrase?"),
                "actions_taken": [],
                "reasoning": plan.get("error", ""),
                "confidence": 0.0,
                "escalated": True
            }

        reasoning = plan.get("reasoning", "")
        confidence = float(plan.get("confidence", 0.7))
        steps = plan.get("steps", [])

        # ── 3. CHECK ESCALATION ───────────────────────────────────
        if confidence < ESCALATION_CONFIDENCE_THRESHOLD:
            self.log_action("Escalated to Human", {
                "request": user_message, "reasoning": reasoning,
                "confidence": confidence
            })
            return {
                "response": (f"I've analyzed your request but I'm not confident enough "
                             f"to act autonomously (confidence: {confidence:.0%}). "
                             f"My reasoning: {reasoning}\n\n"
                             f"This has been escalated for human review."),
                "actions_taken": [],
                "reasoning": reasoning,
                "confidence": confidence,
                "escalated": True
            }

        # ── 4. ACT — execute each planned step ───────────────────
        for step in steps:
            tool_name = step.get("tool")
            tool_params = step.get("parameters", {})

            if tool_name and tool_name in self._tools:
                try:
                    result = self._execute_tool(tool_name, tool_params)
                    actions_taken.append({
                        "tool": tool_name,
                        "parameters": tool_params,
                        "result": result,
                        "success": result.get("status") != "error"
                    })
                except Exception as e:
                    actions_taken.append({
                        "tool": tool_name,
                        "parameters": tool_params,
                        "result": {"status": "error", "message": str(e)},
                        "success": False
                    })
            elif tool_name == "no_tool_needed":
                # Pure conversational / informational response
                pass
            else:
                actions_taken.append({
                    "tool": tool_name or "unknown",
                    "parameters": tool_params,
                    "result": {"status": "error", "message": f"Tool '{tool_name}' not found"},
                    "success": False
                })

        # ── 5. EVALUATE & RESPOND — LLM crafts final answer ──────
        response = self._evaluate_and_respond(
            user_message, reasoning, actions_taken, plan.get("direct_response", ""))

        # ── 6. LEARN — record this decision ───────────────────────
        outcome = "success" if all(a.get("success", True) for a in actions_taken) else "partial_failure"
        self.learning.record_decision(
            task=user_message,
            context={"perception": perception, "tools_used": [a["tool"] for a in actions_taken]},
            decision=reasoning,
            confidence=confidence,
            outcome=outcome
        )
        self.log_decision(user_message, [a["tool"] for a in actions_taken],
                          reasoning, confidence, outcome)

        # ── 7. UPDATE GOALS ───────────────────────────────────────
        self._update_goals(actions_taken)

        return {
            "response": response,
            "actions_taken": actions_taken,
            "reasoning": reasoning,
            "confidence": confidence,
            "escalated": False
        }

    # ─────────── PERCEIVE: gather relevant context ───────────

    def _perceive(self, user_message: str, context: Dict) -> Dict:
        """Collect all relevant context for the LLM to reason about."""
        perception = {
            "user_message": user_message,
            "agent": self.agent_name,
            "available_tools": list(self._tools.keys()),
            "timestamp": datetime.now().isoformat(),
        }

        # Add employee context if employee_id is provided
        emp_id = context.get("employee_id")
        if emp_id:
            emp = self.db.get_employee(emp_id)
            if emp:
                perception["employee"] = {
                    "id": emp.employee_id, "name": emp.name,
                    "department": emp.department, "position": emp.position,
                    "email": emp.email,
                    "leave_balance": getattr(emp, 'leave_balance', {}),
                }

        # Add similar past decisions (learning)
        past = self.learning.get_relevant_examples(user_message, n=3)
        if past:
            perception["similar_past_decisions"] = [
                {"task": d["task"], "decision": d["decision"],
                 "confidence": d["confidence"], "outcome": d.get("outcome")}
                for d in past
            ]

        # Allow subclass to add domain-specific context
        perception.update(self._get_domain_context(user_message, context))

        return perception

    def _get_domain_context(self, user_message: str, context: Dict) -> Dict:
        """Override in subclass to add domain-specific context (e.g., leave balances, open tickets)."""
        return {}

    # ─────────── REASON & PLAN: LLM decides what to do ───────────

    def _reason_and_plan(self, user_message: str, perception: Dict) -> Dict:
        """
        Call 1: LLM analyzes the situation and produces a plan.
        Returns: {"reasoning": str, "confidence": float, "steps": [{"tool": str, "parameters": {}}]}
        """
        tools_desc = self.get_tools_description()

        # Build past-decisions snippet
        past_snippet = ""
        past = perception.get("similar_past_decisions", [])
        if past:
            examples = "\n".join(
                f"  - Task: {d['task']} → Decision: {d['decision']} (confidence: {d['confidence']}, outcome: {d.get('outcome','N/A')})"
                for d in past
            )
            past_snippet = f"\nSimilar Past Decisions (learn from these):\n{examples}\n"

        employee_snippet = ""
        emp = perception.get("employee")
        if emp:
            employee_snippet = f"\nEmployee Context:\n  {json.dumps(emp, default=str)}\n"

        domain_ctx = {k: v for k, v in perception.items()
                      if k not in ("user_message", "agent", "available_tools",
                                   "timestamp", "employee", "similar_past_decisions")}
        domain_snippet = ""
        if domain_ctx:
            domain_snippet = f"\nAdditional Context:\n  {json.dumps(domain_ctx, default=str)}\n"

        prompt = f"""You are {self.agent_name}, an autonomous AI agent in an enterprise system.

TASK: Analyze the user's request and decide what action(s) to take.

USER REQUEST: "{user_message}"
{employee_snippet}{past_snippet}{domain_snippet}
AVAILABLE TOOLS:
{tools_desc}

INSTRUCTIONS:
1. Reason about what the user needs
2. Decide which tool(s) to call (or "no_tool_needed" for conversational responses)
3. Extract the required parameters from the user's message and context
4. Assess your confidence (0.0 to 1.0)

Return ONLY a valid JSON object in this exact format:
{{
  "reasoning": "Your step-by-step reasoning about what the user needs and why you chose this action",
  "confidence": 0.85,
  "steps": [
    {{"tool": "tool_name", "parameters": {{"param1": "value1", "param2": "value2"}}}}
  ],
  "direct_response": "If no tool is needed, put your conversational response here"
}}

RULES:
- Parameter values must be concrete (extracted from the message/context), never placeholders
- If information is missing and you cannot infer it, set confidence low and explain in reasoning
- For date parameters, use YYYY-MM-DD format
- If the request is purely informational/conversational, use tool "no_tool_needed" with empty parameters
- You may plan multiple steps if the request requires sequential actions
"""

        try:
            raw = self.llm.generate_json_response(prompt)
            # Extract JSON from response
            m = re.search(r'\{[\s\S]*\}', raw)
            if m:
                plan = json.loads(m.group(0))
                # Validate structure
                if "reasoning" not in plan:
                    plan["reasoning"] = "Processing request"
                if "confidence" not in plan:
                    plan["confidence"] = 0.7
                if "steps" not in plan:
                    plan["steps"] = [{"tool": "no_tool_needed", "parameters": {}}]
                return plan
            else:
                return {
                    "error": f"Could not parse LLM plan: {raw[:200]}",
                    "fallback_response": self._generate_fallback(user_message)
                }
        except Exception as e:
            return {
                "error": f"Planning error: {str(e)}",
                "fallback_response": self._generate_fallback(user_message)
            }

    # ─────────── EXECUTE: run a tool ───────────

    def _execute_tool(self, tool_name: str, params: Dict) -> Dict:
        """Call 2: Execute the selected tool with extracted parameters."""
        tool = self._tools[tool_name]
        # Filter params to only those the function accepts
        import inspect
        sig = inspect.signature(tool.function)
        valid_params = {}
        for k, v in params.items():
            if k in sig.parameters:
                valid_params[k] = v
        result = tool.function(**valid_params)
        return result if isinstance(result, dict) else {"status": "success", "result": result}

    # ─────────── EVALUATE & RESPOND: craft final answer ───────────

    def _evaluate_and_respond(self, user_message: str, reasoning: str,
                               actions_taken: list, direct_response: str) -> str:
        """Call 3: LLM evaluates results and generates a natural-language response."""
        # If no tools were called and we have a direct response
        if not actions_taken and direct_response:
            return direct_response

        # If tools were called, summarize results for the LLM
        results_summary = []
        for a in actions_taken:
            result_str = json.dumps(a["result"], default=str)
            # Truncate long results
            if len(result_str) > 500:
                result_str = result_str[:500] + "..."
            results_summary.append(
                f"Tool: {a['tool']} | Success: {a['success']} | Result: {result_str}"
            )

        prompt = f"""You are {self.agent_name}. You just processed a user's request.

ORIGINAL REQUEST: "{user_message}"

YOUR REASONING: {reasoning}

ACTIONS TAKEN AND RESULTS:
{chr(10).join(results_summary) if results_summary else "No actions taken."}

Generate a clear, helpful response for the user. Include:
- What you did and the outcome
- Any relevant details (IDs, dates, amounts, etc.)
- If something failed, explain what went wrong and suggest next steps
- Be professional, concise, and helpful

Do NOT mention tool names or internal system details. Speak naturally as an agent helping the user.
"""
        try:
            response = self.llm.generate_response(prompt,
                f"You are a helpful {self.agent_name} assistant. Respond naturally and concisely.")
            return response
        except Exception:
            # Fallback: build a simple response from results
            if actions_taken and actions_taken[0].get("success"):
                return f"Done! I've processed your request. {reasoning}"
            return f"I attempted to process your request but encountered an issue. {reasoning}"

    # ─────────── FALLBACK (when LLM reasoning fails) ───────────

    def _generate_fallback(self, user_message: str) -> str:
        """Simple fallback when the planning LLM call fails."""
        tools_list = ", ".join(self._tools.keys())
        return (f"I can help you with the following: {tools_list}. "
                "Could you please rephrase your request with more details?")

    # ─────────── GOAL TRACKING ───────────

    def _update_goals(self, actions_taken: list):
        """Override in subclass to update KPI metrics after actions."""
        pass

    def set_goal_tracker(self, goal_tracker):
        """Attach the shared GoalTracker instance."""
        self.goal_tracker = goal_tracker

    # ─────────── CHAT HISTORY (per user) ───────────

    def get_chat_history(self, user_id: str) -> List[Dict]:
        """Return chat history for a user."""
        return self.chat_histories.get(user_id, [])

    def add_to_chat_history(self, user_id: str, role: str, content: str):
        """Append a message to a user's chat history."""
        if user_id not in self.chat_histories:
            self.chat_histories[user_id] = []
        self.chat_histories[user_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def clear_chat_history(self, user_id: str):
        """Clear chat history for a user."""
        self.chat_histories[user_id] = []

    # ─────────── Shared: Audit Logging ───────────

    def log_action(self, action: str, details: Dict, user: str = "System"):
        """Write to the shared audit log."""
        log = AuditLog(
            log_id=f"LOG{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            timestamp=datetime.now().isoformat(),
            agent=self.agent_name,
            action=action,
            details=details,
            user=user,
        )
        self.db.add_audit_log(log)

    # ─────────── Shared: Decision History (for Learning) ───────────

    def log_decision(self, task, action, reasoning, confidence, outcome=None):
        """Store decision for the LearningModule to analyze."""
        self.decision_history.append({
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "task": task,
            "action": action,
            "reasoning": reasoning,
            "confidence": confidence,
            "outcome": outcome,
        })

    # ─────────── Shared: Policy Q&A ───────────

    def ask_policy_question(self, question: str, policies: str) -> Dict:
        """Generic LLM-powered policy Q&A. Each agent passes its own policies."""
        system_prompt = (
            f"You are a {self.agent_name} assistant helping with company policies.\n\n"
            f"Policies:\n{policies}\n\n"
            "Answer professionally and concisely. If unsure, say so."
        )
        answer = self.llm.generate_response(question, system_prompt)
        return {"status": "success", "question": question, "answer": answer}
