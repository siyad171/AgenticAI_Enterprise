# 🔌 Step 2: Core Services

> **Requires**: `01_CORE_CONFIG_DB.md` completed  
> **Creates**: `core/llm_service.py`, `core/event_bus.py`, `core/base_agent.py`  
> **Next**: → `03_CORE_ORCHESTRATION.md`

---

## File 1: `core/llm_service.py`

Extracted from the current `LLMInterface` class. **Single LLM gateway for all agents.**

```python
"""
core/llm_service.py — Centralized LLM access via Groq API
All agents and tools call this service instead of Groq directly.
"""
import os
from typing import Optional, Dict, List
from groq import Groq
from core.config import (
    GROQ_API_KEY, LLM_CHAT_MODEL, LLM_ANALYSIS_MODEL,
    LLM_TEMPERATURE, LLM_MAX_TOKENS
)


class LLMService:

    def __init__(self, api_key: str = None, database=None):
        self.api_key = api_key or GROQ_API_KEY
        self.database = database
        self.chat_model = LLM_CHAT_MODEL           # llama-3.1-8b-instant
        self.analysis_model = LLM_ANALYSIS_MODEL    # llama-3.3-70b-versatile

        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None
            print("⚠️ No API key. Using rule-based fallback responses.")

    def generate_response(
        self,
        prompt: str,
        system_prompt: str = "",
        include_employee_data: bool = False,
        model: str = None
    ) -> str:
        """
        General-purpose LLM call.
        - model: defaults to chat_model. Pass analysis_model for deep tasks.
        - include_employee_data: appends DB employee summary to system prompt.
        """
        if not self.client:
            return self._fallback_response(prompt)

        try:
            messages = []

            full_system = system_prompt
            if include_employee_data and self.database:
                full_system += f"\n\n{self.database.get_employee_summary()}"
                full_system += "\nYou have access to the current employee database. "
                full_system += "Use this information to answer specific questions about employees."

            if full_system:
                messages.append({"role": "system", "content": full_system})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=model or self.chat_model,
                messages=messages,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"LLM Error: {e}")
            return self._fallback_response(prompt)

    # Alias kept for backward compatibility with existing code
    def ask_question(self, prompt: str) -> str:
        return self.generate_response(prompt)

    def generate_json_response(
        self, prompt: str, system_prompt: str = ""
    ) -> str:
        """Use the deeper analysis model. Caller parses JSON from response."""
        return self.generate_response(
            prompt, system_prompt, model=self.analysis_model
        )

    def chat_with_history(
        self, messages: List[Dict], model: str = None
    ) -> str:
        """Send a full message list (for multi-turn conversations)."""
        if not self.client:
            return self._fallback_response(messages[-1].get("content", ""))

        try:
            response = self.client.chat.completions.create(
                model=model or self.chat_model,
                messages=messages,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM Error: {e}")
            return "I'm having trouble processing that. Please try again."

    # ─────────── Fallback (preserve exactly from current code) ───────────

    def _fallback_response(self, prompt: str) -> str:
        prompt_lower = prompt.lower()

        # Try employee lookup from DB
        if self.database and ("employee" in prompt_lower or "who is" in prompt_lower):
            for word in prompt.split():
                emp = self.database.search_employee_by_name(word)
                if emp:
                    return (
                        f"{emp.name} (ID: {emp.employee_id}) works as {emp.position} "
                        f"in {emp.department} department. Email: {emp.email}. "
                        f"Leave balance: Casual: {emp.leave_balance.get('Casual Leave', 0)}, "
                        f"Sick: {emp.leave_balance.get('Sick Leave', 0)}, "
                        f"Annual: {emp.leave_balance.get('Annual Leave', 0)} days."
                    )

        if "leave" in prompt_lower and "balance" in prompt_lower:
            return "You can check your leave balance in the employee portal or contact HR."
        elif "policy" in prompt_lower:
            return "Please refer to the employee handbook or ask HR for specific policy details."
        return "I understand your query. Please contact HR for detailed assistance."
```

---

## File 2: `core/event_bus.py`

Pub/Sub system for inter-agent communication. Lightweight, synchronous.

```python
"""
core/event_bus.py — Publish / Subscribe event system
Agentic AI Feature: Environment Perception + Multi-Agent Coordination

Usage:
    bus = EventBus()
    bus.subscribe("employee_onboarded", it_agent.handle_event)
    bus.publish("employee_onboarded", {"employee_id": "EMP003"}, source_agent="HR Agent")
"""
from collections import defaultdict
from datetime import datetime
from typing import Callable, Dict, List, Any


class EventBus:

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_log: List[Dict] = []

    def subscribe(self, event_type: str, callback: Callable):
        """Register a handler for an event type.
        callback signature: callback(event_type: str, data: dict)
        """
        self._subscribers[event_type].append(callback)

    def publish(self, event_type: str, data: Dict, source_agent: str = "System"):
        """Broadcast event to all subscribers. Synchronous."""
        event = {
            "type": event_type,
            "data": data,
            "source": source_agent,
            "timestamp": datetime.now().isoformat(),
        }
        self._event_log.append(event)

        for callback in self._subscribers.get(event_type, []):
            try:
                callback(event_type, data)
            except Exception as e:
                print(f"[EventBus] Handler error for '{event_type}': {e}")

    def get_event_log(self, limit: int = 50) -> List[Dict]:
        """Recent events for the Orchestrator Dashboard."""
        return self._event_log[-limit:]

    def get_subscribers_count(self) -> Dict[str, int]:
        """Debug: how many handlers per event type."""
        return {k: len(v) for k, v in self._subscribers.items()}

    def clear_log(self):
        self._event_log.clear()
```

### Event Type Constants

Create `core/events.py` (optional helper — or just use plain strings):

```python
"""
core/events.py — Event type constants (avoids typos)
"""

# HR Agent events
EMPLOYEE_ONBOARDED = "employee_onboarded"
EMPLOYEE_TERMINATED = "employee_terminated"
LEAVE_APPROVED = "leave_approved"

# IT Agent events
ACCESS_PROVISIONED = "access_provisioned"
ACCESS_REVOKED = "access_revoked"
SECURITY_INCIDENT = "security_incident"

# Finance Agent events
EXPENSE_SUBMITTED = "expense_submitted"
EXPENSE_APPROVED = "expense_approved"
BUDGET_ALERT = "budget_alert"
PAYROLL_SETUP_COMPLETE = "payroll_setup_complete"

# Compliance Agent events
VIOLATION_DETECTED = "violation_detected"
TRAINING_OVERDUE = "training_overdue"
POLICY_UPDATED = "policy_updated"
COMPLIANCE_VERIFIED = "compliance_verified"
```

### Full Event Reference Table

| Event | Publisher | Subscribers | Payload |
|-------|-----------|-------------|---------|
| `employee_onboarded` | HR | IT, Finance, Compliance | `{employee_id, name, department, position, email}` |
| `employee_terminated` | HR | IT, Finance, Compliance | `{employee_id, name, termination_date}` |
| `leave_approved` | HR | Finance | `{employee_id, leave_type, days, start_date, end_date}` |
| `access_provisioned` | IT | Compliance, HR | `{employee_id, systems, provisioned_date}` |
| `access_revoked` | IT | Compliance | `{employee_id, revoked_date}` |
| `security_incident` | IT | Compliance, HR | `{incident_type, severity, details}` |
| `expense_submitted` | Finance | Compliance | `{claim_id, employee_id, amount, category}` |
| `expense_approved` | Finance | HR | `{claim_id, employee_id, amount}` |
| `budget_alert` | Finance | HR, IT | `{department, utilization_percent}` |
| `payroll_setup_complete` | Finance | HR | `{employee_id}` |
| `violation_detected` | Compliance | HR, IT, Finance | `{violation_id, type, severity, employee_id}` |
| `training_overdue` | Compliance | HR | `{employee_id, training_name, days_overdue}` |
| `compliance_verified` | Compliance | HR | `{employee_id, status}` |

---

## File 3: `core/base_agent.py`

Abstract base class. Every agent (HR, IT, Finance, Compliance) extends this.

```python
"""
core/base_agent.py — Abstract agent that all domain agents extend

Agentic AI Features:
- Autonomous Decision-Making (decide method)
- Goal-Oriented Behavior (goals dict)
- Continuous Learning (decision_history)
- Environment Perception (handle_event)
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from core.database import AuditLog


class BaseAgent(ABC):

    def __init__(self, agent_name: str, database, llm_service, event_bus):
        self.agent_name = agent_name
        self.db = database
        self.llm = llm_service
        self.event_bus = event_bus
        self.goals: Dict[str, Dict] = {}
        self.decision_history: List[Dict] = []

    # ─────────── Abstract (each agent must implement) ───────────

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of action names this agent can perform."""
        pass

    @abstractmethod
    def handle_event(self, event_type: str, event_data: Dict):
        """React to an event from the EventBus."""
        pass

    # ─────────── Shared: Autonomous Decision ───────────

    def decide(self, task: str, context: Dict) -> Tuple[str, str, float]:
        """
        Make an autonomous decision.

        Returns:
            (action, reasoning, confidence)
            - action: what to do
            - reasoning: why
            - confidence: 0.0 to 1.0 (if < threshold → escalate)
        """
        # Default implementation — override in agents for domain logic
        prompt = f"""You are {self.agent_name}. Given this task, decide the best action.
Task: {task}
Context: {context}
Return JSON: {{"action": "...", "reasoning": "...", "confidence": 0.0-1.0}}"""

        response = self.llm.generate_json_response(prompt)
        # Parse response or return default
        return ("process", "Default processing", 0.7)

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
```

---

## How These Three Files Connect

```
                    ┌─────────────┐
                    │  EventBus   │  ← agents subscribe & publish
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                  ▼
   ┌───────────┐    ┌───────────┐     ┌───────────┐
   │  HR Agent │    │  IT Agent │     │  Finance  │ ...
   └─────┬─────┘    └─────┬─────┘     └─────┬─────┘
         │                │                  │
         └────────────────┼──────────────────┘
                          ▼
                   ┌─────────────┐
                   │ LLMService  │  ← single shared instance
                   └─────────────┘
                          ▼
                    ┌───────────┐
                    │  Groq API │
                    └───────────┘
```

- `LLMService` — one instance, shared via `st.session_state.llm`
- `EventBus` — one instance, shared via `st.session_state.event_bus`
- `BaseAgent` — each agent gets refs to both at construction time

---

## ✅ Done Checklist

- [ ] `core/llm_service.py` — Groq client, fallback, `generate_response()`, `ask_question()`, `chat_with_history()`
- [ ] `core/event_bus.py` — subscribe, publish, event_log
- [ ] `core/events.py` (optional) — event type constants
- [ ] `core/base_agent.py` — abstract class with `get_capabilities()`, `handle_event()`, `decide()`, `log_action()`, `ask_policy_question()`
- [ ] Test: `python -c "from core.llm_service import LLMService; print('OK')"` → OK
- [ ] Test: `python -c "from core.event_bus import EventBus; eb = EventBus(); print(len(eb.get_event_log()))"` → 0

---

**Next** → `03_CORE_ORCHESTRATION.md` (Orchestrator, GoalTracker, LearningModule)
