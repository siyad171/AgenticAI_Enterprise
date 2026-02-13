"""Shared pytest fixtures for all tests"""
import pytest
import os

# Force test mode
os.environ["TESTING"] = "1"


@pytest.fixture
def db():
    """Fresh database instance with seed data (auto-seeded in __init__)"""
    from core.database import Database
    database = Database()
    return database


@pytest.fixture
def llm():
    """LLM service (real or mocked based on env)"""
    from core.llm_service import LLMService
    return LLMService()


@pytest.fixture
def event_bus():
    """Fresh event bus"""
    from core.event_bus import EventBus
    return EventBus()


@pytest.fixture
def hr_agent(db, llm, event_bus):
    """HR Agent with dependencies"""
    from agents.hr_agent import HRAgent
    return HRAgent(db=db, llm_service=llm, event_bus=event_bus)


@pytest.fixture
def it_agent(db, llm, event_bus):
    from agents.it_agent import ITAgent
    return ITAgent(db=db, llm_service=llm, event_bus=event_bus)


@pytest.fixture
def finance_agent(db, llm, event_bus):
    from agents.finance_agent import FinanceAgent
    return FinanceAgent(db=db, llm_service=llm, event_bus=event_bus)


@pytest.fixture
def compliance_agent(db, llm, event_bus):
    from agents.compliance_agent import ComplianceAgent
    return ComplianceAgent(db=db, llm_service=llm, event_bus=event_bus)


@pytest.fixture
def all_agents(hr_agent, it_agent, finance_agent, compliance_agent):
    """Dict of all agents"""
    return {
        'hr': hr_agent,
        'it': it_agent,
        'finance': finance_agent,
        'compliance': compliance_agent
    }


@pytest.fixture
def orchestrator(all_agents, llm, event_bus):
    from core.orchestrator import Orchestrator
    return Orchestrator(agents=all_agents, event_bus=event_bus, llm_service=llm)
