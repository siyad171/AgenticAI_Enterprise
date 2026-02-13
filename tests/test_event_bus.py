"""Test event bus pub/sub"""

def test_subscribe_and_publish(event_bus):
    received = []
    event_bus.subscribe("test_event", lambda evt_type, data: received.append(data))
    event_bus.publish("test_event", {"msg": "hello"})
    assert len(received) == 1
    assert received[0]["msg"] == "hello"

def test_multiple_subscribers(event_bus):
    results = []
    event_bus.subscribe("evt", lambda evt_type, d: results.append("A"))
    event_bus.subscribe("evt", lambda evt_type, d: results.append("B"))
    event_bus.publish("evt", {})
    assert results == ["A", "B"]

def test_event_log(event_bus):
    event_bus.publish("log_test", {"data": 1})
    log = event_bus.get_event_log()
    assert len(log) >= 1
    assert log[-1]["type"] == "log_test"
