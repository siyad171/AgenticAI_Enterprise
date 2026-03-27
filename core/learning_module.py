"""
core/learning_module.py — Decision history + adaptive learning

Agentic AI Feature: Continuous Learning & Improvement
- Policy memory (admin overrides) used for future autonomous handling
- Decision audit log (agent reasoning/actions) kept separate from policy memory
- Retrieval helpers for few-shot prompting and override matching
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
                        admin_decision: str, reason: str,
                        task: str = None, context: Dict = None,
                        employee_response: str = None):
        """Admin overrides agent decision — high-value learning signal."""
        override = {
            "decision_id": decision_id,
            "agent": self.agent_name,
            "timestamp": datetime.now().isoformat(),
            "original_decision": original_decision,
            "admin_decision": admin_decision,
            "employee_response": employee_response,
            "reason": reason,
            "task": task,
            "context": context or {},
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

    def get_relevant_overrides(self, current_task: str, n: int = 3) -> List[Dict]:
        """Retrieve similar admin override outcomes to guide future decisions."""
        keywords = set(current_task.lower().split())
        scored = []

        for o in self.overrides:
            task_text = (o.get("task") or "").lower()
            if not task_text:
                continue
            task_words = set(task_text.split())
            overlap = len(keywords & task_words)
            if overlap > 0:
                scored.append((overlap, o))

        if not scored:
            return self.overrides[-n:]

        scored.sort(key=lambda x: x[0], reverse=True)
        return [o for _, o in scored[:n]]

    def find_best_override(self, current_task: str, min_overlap: int = 2) -> Optional[Dict]:
        """Find the strongest override match for the current task.

        A small keyword-overlap threshold keeps matching deterministic and low-risk.
        """
        keywords = set((current_task or "").lower().split())
        if not keywords:
            return None

        best_match = None
        best_score = 0
        for o in self.overrides:
            task_text = (o.get("task") or "").lower()
            if not task_text:
                continue
            overlap = len(keywords & set(task_text.split()))
            if overlap > best_score:
                best_score = overlap
                best_match = o

        if best_score < min_overlap:
            return None
        return best_match

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

    def _audit_file_path(self) -> str:
        safe_name = self.agent_name.lower().replace(" ", "_")
        return os.path.join(self.storage_dir, f"{safe_name}_decisions_audit.json")

    def _load_history(self):
        learning_path = self._file_path()
        audit_path = self._audit_file_path()

        self.decisions = []
        self.overrides = []

        # Load policy-memory file (primary source for overrides).
        legacy_decisions: List[Dict] = []
        if os.path.exists(learning_path):
            try:
                with open(learning_path, "r") as f:
                    data = json.load(f)
                    self.overrides = data.get("overrides", [])
                    # Backward compatibility: old files kept decisions here.
                    legacy_decisions = data.get("decisions", [])
            except Exception:
                self.overrides = []

        # Load audit-memory file for decisions.
        if os.path.exists(audit_path):
            try:
                with open(audit_path, "r") as f:
                    data = json.load(f)
                    self.decisions = data.get("decisions", [])
            except Exception:
                self.decisions = []

        # Backward compatibility fallback when audit file doesn't exist yet.
        if not self.decisions and legacy_decisions:
            self.decisions = legacy_decisions

    def _read_json_object(self, path: str) -> Dict:
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _merge_by_key(self, existing: List[Dict], incoming: List[Dict], key_field: str) -> List[Dict]:
        """Merge two record lists while letting newer incoming entries overwrite by key."""
        merged: List[Dict] = []
        positions: Dict[str, int] = {}

        for item in (existing or []) + (incoming or []):
            key = item.get(key_field)
            if not key:
                merged.append(item)
                continue
            if key in positions:
                merged[positions[key]] = item
            else:
                positions[key] = len(merged)
                merged.append(item)
        return merged

    def _save_history(self):
        os.makedirs(self.storage_dir, exist_ok=True)

        # Policy memory: keep high-value admin decisions only.
        learning_path = self._file_path()
        learning_data = self._read_json_object(learning_path)
        existing_overrides = learning_data.get("overrides", [])
        merged_overrides = self._merge_by_key(existing_overrides, self.overrides, "decision_id")
        self.overrides = merged_overrides[-100:]
        with open(learning_path, "w") as f:
            json.dump({
                "overrides": self.overrides,
            }, f, indent=2)

        # Decision audit: keep detailed autonomous decision traces separately.
        audit_path = self._audit_file_path()
        audit_data = self._read_json_object(audit_path)
        existing_decisions = audit_data.get("decisions", [])
        merged_decisions = self._merge_by_key(existing_decisions, self.decisions, "id")
        self.decisions = merged_decisions[-500:]
        with open(audit_path, "w") as f:
            json.dump({
                "decisions": self.decisions,
            }, f, indent=2)
