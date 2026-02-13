"""
core/config.py — Centralized configuration
All agents and tools read from this single file.
Admin can override some values via the UI (stored in DB).
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# ──────────────────────────────────────────────
# LLM Provider (Groq — free tier)
# ──────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_CHAT_MODEL = "llama-3.1-8b-instant"       # Fast: conversation, chat
LLM_ANALYSIS_MODEL = "llama-3.3-70b-versatile" # Deep: analysis, evaluation
LLM_WHISPER_MODEL = "whisper-large-v3-turbo"   # Audio transcription
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 800

# ──────────────────────────────────────────────
# Email (SMTP)
# ──────────────────────────────────────────────
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# ──────────────────────────────────────────────
# Code Execution (Judge0)
# ──────────────────────────────────────────────
JUDGE0_API_KEY = os.getenv("JUDGE0_API_KEY", "")

# ──────────────────────────────────────────────
# HR Agent
# ──────────────────────────────────────────────
LEAVE_AUTO_APPROVE_MAX_DAYS = 10
LEAVE_BALANCE_DEFAULT = {
    "Casual Leave": 12,
    "Sick Leave": 15,
    "Annual Leave": 20
}
CANDIDATE_ACCEPT_THRESHOLD = 50
CANDIDATE_REVIEW_THRESHOLD = 40
TEST_PASS_THRESHOLD = 60
EXPERIENCE_PENALTY_FACTOR = 0.7
EDUCATION_PENALTY_FACTOR = 0.8

# ──────────────────────────────────────────────
# IT Agent
# ──────────────────────────────────────────────
IT_PROVISIONING_SLA_HOURS = 24
PASSWORD_MIN_LENGTH = 12
PASSWORD_ROTATION_DAYS = 90
APPROVED_SOFTWARE = [
    "VS Code", "Slack", "Jira", "GitHub",
    "Zoom", "Chrome", "Firefox"
]

# ──────────────────────────────────────────────
# Finance Agent
# ──────────────────────────────────────────────
EXPENSE_AUTO_APPROVE_LIMIT = 5000
EXPENSE_MANAGER_NOTIFY_LIMIT = 25000
BUDGET_ALERT_THRESHOLD_PERCENT = 90
DEFAULT_SALARIES = {
    "Engineering": 80000,
    "Marketing": 70000,
    "Sales": 60000,
    "HR": 65000,
    "Finance": 75000,
}

# ──────────────────────────────────────────────
# Compliance Agent
# ──────────────────────────────────────────────
TRAINING_OVERDUE_DAYS = 30
AUDIT_PASS_SCORE = 70
DOCUMENT_RETENTION_YEARS = 7
MANDATORY_TRAININGS = [
    {"name": "Data Privacy & Protection", "frequency": "Annual", "duration": "2 hours"},
    {"name": "Workplace Safety", "frequency": "Annual", "duration": "1 hour"},
    {"name": "Anti-Harassment Awareness", "frequency": "Annual", "duration": "1.5 hours"},
    {"name": "Security Awareness", "frequency": "Quarterly", "duration": "30 minutes"},
]

# ──────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────
ESCALATION_CONFIDENCE_THRESHOLD = 0.6

# ──────────────────────────────────────────────
# Storage Paths
# ──────────────────────────────────────────────
INTERVIEW_RESULTS_DIR = "data/interview_results"
LEARNING_DATA_DIR = "data/learning"
UPLOADS_DIR = "data/uploads"
