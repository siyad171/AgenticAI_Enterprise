"""Verify all modules import correctly"""
import sys

checks = [
    ("core.config",              "from core.config import GROQ_API_KEY"),
    ("core.database",            "from core.database import Database"),
    ("core.llm_service",         "from core.llm_service import LLMService"),
    ("core.event_bus",           "from core.event_bus import EventBus"),
    ("core.base_agent",          "from core.base_agent import BaseAgent"),
    ("core.orchestrator",        "from core.orchestrator import Orchestrator"),
    ("core.goal_tracker",        "from core.goal_tracker import GoalTracker"),
    ("core.learning_module",     "from core.learning_module import LearningModule"),
    ("agents.hr_agent",          "from agents.hr_agent import HRAgent"),
    ("agents.it_agent",          "from agents.it_agent import ITAgent"),
    ("agents.finance_agent",     "from agents.finance_agent import FinanceAgent"),
    ("agents.compliance_agent",  "from agents.compliance_agent import ComplianceAgent"),
    ("tools.email_service",      "from tools.email_service import EmailService"),
    ("tools.code_executor",      "from tools.code_executor import CodeExecutor"),
    ("tools.local_executor",     "from tools.local_executor import LocalPythonExecutor"),
    ("tools.ai_code_analyzer",   "from tools.ai_code_analyzer import AICodeAnalyzer"),
    ("tools.interview_storage",  "from tools.interview_storage import InterviewStorage"),
    ("tools.psychometric_assessment", "from tools.psychometric_assessment import PsychometricAssessment"),
    ("tools.technical_interview_chat","from tools.technical_interview_chat import TechnicalInterviewChat"),
]

passed = 0
failed = 0
for name, stmt in checks:
    try:
        exec(stmt)
        print(f"  ✅ {name}")
        passed += 1
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        failed += 1

print(f"\n{'='*40}")
print(f"Results: {passed} passed, {failed} failed out of {len(checks)}")
if failed:
    sys.exit(1)
else:
    print("All imports OK! Ready to run.")
