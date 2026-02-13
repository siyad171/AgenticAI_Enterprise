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
