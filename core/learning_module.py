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
