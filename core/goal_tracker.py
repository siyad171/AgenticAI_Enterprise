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
