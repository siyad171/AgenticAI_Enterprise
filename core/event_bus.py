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
