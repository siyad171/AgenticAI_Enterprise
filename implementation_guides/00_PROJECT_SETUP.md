# 📦 Step 0: Project Setup

> **Requires**: Nothing — this is the starting point  
> **Creates**: Folder structure, virtual env, dependencies, .env  
> **Next**: → `01_CORE_CONFIG_DB.md`

---

## Updated Folder Structure

```
AgenticAI_Enterprise/
│
├── app.py                              # Main Streamlit entry point
├── requirements.txt                    # All dependencies
├── .env                                # API keys (not committed to git)
├── .env.example                        # Template for .env
├── .gitignore
├── README.md
│
├── core/                               # 🧠 Framework Foundation
│   ├── __init__.py
│   ├── config.py                       # Centralized settings & thresholds
│   ├── database.py                     # Unified in-memory DB (all models)
│   ├── llm_service.py                  # Shared Groq LLM interface
│   ├── event_bus.py                    # Pub/Sub inter-agent messaging
│   ├── base_agent.py                   # Abstract BaseAgent class
│   ├── orchestrator.py                 # Multi-agent workflow coordinator
│   ├── goal_tracker.py                 # Per-agent KPI tracking
│   └── learning_module.py             # Decision history & adaptive learning
│
├── agents/                             # 🤖 Domain Agents
│   ├── __init__.py
│   ├── hr_agent.py                     # HR Agent (hiring, leave, onboarding)
│   ├── it_agent.py                     # IT Agent (access, tickets, security)
│   ├── finance_agent.py               # Finance Agent (expenses, payroll, budget)
│   └── compliance_agent.py            # Compliance Agent (audit, training, violations)
│
├── tools/                              # 🔧 Shared Utilities & External Services
│   ├── __init__.py
│   ├── email_service.py               # SMTP email sender (used by all agents)
│   ├── code_executor.py               # Judge0 API + local Python fallback
│   ├── local_executor.py              # Local subprocess Python runner
│   ├── ai_code_analyzer.py            # LLM-powered code quality analysis
│   ├── video_analyzer.py              # OpenCV + DeepFace + SpeechBrain
│   ├── video_analyzer_hybrid.py       # Hybrid heuristic + AI video analysis
│   ├── technical_interview_chat.py    # Chat-based multi-stage AI interviewer
│   ├── psychometric_assessment.py     # EQ/AQ/BQ/SQ 20-question assessment
│   └── interview_storage.py           # JSON file persistence for results
│
├── prompts/                            # 📝 All LLM Prompt Templates
│   ├── __init__.py
│   ├── hr/                             # HR Agent prompts
│   │   ├── __init__.py
│   │   ├── leave_email.py             # Leave notification email generation
│   │   ├── resume_parser.py           # Resume skill/experience extraction
│   │   ├── policy_qa.py              # HR policy Q&A system prompts
│   │   ├── candidate_eval.py         # Candidate evaluation prompts
│   │   └── test_result_email.py      # Test pass/fail email generation
│   │
│   ├── it/                             # IT Agent prompts
│   │   ├── __init__.py
│   │   ├── ticket_resolution.py       # IT ticket auto-resolution prompts
│   │   └── policy_qa.py              # IT policy Q&A prompts
│   │
│   ├── finance/                        # Finance Agent prompts
│   │   ├── __init__.py
│   │   ├── expense_review.py          # Expense validation prompts
│   │   └── policy_qa.py              # Finance policy Q&A prompts
│   │
│   ├── compliance/                     # Compliance Agent prompts
│   │   ├── __init__.py
│   │   ├── violation_analysis.py      # Violation detection prompts
│   │   ├── audit_report.py           # Compliance audit prompts
│   │   └── policy_qa.py              # Compliance policy Q&A prompts
│   │
│   ├── interview/                      # Technical Interview prompts
│   │   ├── __init__.py
│   │   ├── code_analysis.py           # Code quality analysis prompts
│   │   ├── chat_interviewer.py        # Multi-stage interview prompts
│   │   └── explanation_eval.py        # Answer evaluation prompts
│   │
│   └── shared/                         # Shared / Cross-agent prompts
│       ├── __init__.py
│       ├── routing.py                 # Task routing prompts (orchestrator)
│       └── fallback.py               # Generic fallback responses
│
├── ui/                                 # 🌐 Streamlit UI Pages
│   ├── __init__.py
│   ├── styles.py                       # All CSS/styling centralized
│   ├── login_ui.py                     # Login page (multi-role tabs)
│   ├── candidate_portal_ui.py         # Candidate application pipeline
│   ├── employee_portal_ui.py          # Employee self-service portal
│   ├── admin_portal_ui.py             # Admin management portal
│   ├── it_portal_ui.py                # IT admin portal (new)
│   ├── finance_portal_ui.py           # Finance admin portal (new)
│   ├── compliance_portal_ui.py        # Compliance portal (new)
│   ├── orchestrator_dashboard_ui.py   # Multi-agent dashboard (new)
│   ├── chat_interview_ui.py           # Chat-mode technical interview
│   ├── technical_interview_ui.py      # Quick-mode technical interview
│   ├── psychometric_ui.py             # Psychometric assessment UI
│   ├── video_interview_ui.py          # Video confidence analysis UI
│   └── results_viewer_ui.py           # Interview results browser (admin)
│
├── data/                               # 📁 Persistent Storage (git-ignored)
│   ├── interview_results/              # Per-candidate interview JSONs
│   ├── learning/                       # Agent decision history JSONs
│   └── uploads/                        # Uploaded files (resumes, videos)
│       └── interview_videos/
│
└── tests/                              # 🧪 Test Suite
    ├── __init__.py
    ├── test_hr_agent.py
    ├── test_it_agent.py
    ├── test_finance_agent.py
    ├── test_compliance_agent.py
    ├── test_orchestrator.py
    ├── test_event_bus.py
    └── test_workflows.py
```

---

## Why the `prompts/` Folder?

| Benefit | Explanation |
|---------|-------------|
| **Single Source of Truth** | All LLM prompts in one place — easy to find, review, and update |
| **Version Control** | Track prompt changes over time in git |
| **Agent Isolation** | Each agent's prompts are in their own subfolder |
| **Reusability** | `shared/` folder for cross-agent prompts |
| **A/B Testing** | Easy to swap prompt versions without touching agent code |
| **Prompt Engineering** | Non-developers can review/improve prompts without touching logic |

### Prompt File Pattern

Every prompt file follows this pattern:

```python
"""
prompts/hr/leave_email.py — Leave notification email prompts
"""

# System prompt for the LLM
SYSTEM_PROMPT = """You are an HR assistant generating professional email notifications..."""

# Template with placeholders — agent fills in the variables
def get_leave_email_prompt(employee_name, leave_type, start_date, end_date, days, reason, status):
    return f"""
    Generate a professional email for {employee_name} regarding their {leave_type} request.
    
    Details:
    - Period: {start_date} to {end_date} ({days} days)
    - Reason: {reason}
    - Decision: {status}
    
    Tone: {"Compassionate" if leave_type == "Sick Leave" else "Professional and warm"}
    
    Return ONLY: Subject line on first line, then blank line, then email body.
    """

# Fallback template when LLM is unavailable
FALLBACK_APPROVED = """Subject: Leave Request {request_id} - Approved
    
Dear {employee_name},
Your {leave_type} request from {start_date} to {end_date} ({days} days) has been approved.
Remaining balance: {remaining_balance} days.
"""

FALLBACK_REJECTED = """Subject: Leave Request {request_id} - Rejected
...
"""
```

---

## Step-by-Step Setup

### 1. Create Root Folder

```powershell
mkdir AgenticAI_Enterprise
cd AgenticAI_Enterprise
```

### 2. Create All Directories

```powershell
# Core packages
mkdir core, agents, tools, ui, tests

# Prompts (organized by agent)
mkdir prompts
mkdir prompts\hr, prompts\it, prompts\finance, prompts\compliance
mkdir prompts\interview, prompts\shared

# Data storage
mkdir data
mkdir data\interview_results, data\learning, data\uploads
mkdir data\uploads\interview_videos
```

### 3. Create All `__init__.py` Files

```powershell
# One-liner to create all init files
foreach ($dir in @("core", "agents", "tools", "ui", "tests", "prompts", "prompts\hr", "prompts\it", "prompts\finance", "prompts\compliance", "prompts\interview", "prompts\shared")) {
    "" | Out-File -Encoding utf8 "$dir\__init__.py"
}
```

### 4. Create Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 5. Create `requirements.txt`

```
# === Core (Required) ===
groq==0.33.0
python-dotenv==1.1.1

# === Web UI (Required) ===
streamlit==1.50.0
streamlit-ace==0.1.1

# === PDF Parsing (Required for resume upload) ===
PyPDF2==3.0.1

# === HTTP Requests (Required for Judge0 code execution) ===
requests==2.31.0

# === Video Analysis (Optional — heavy dependencies) ===
# Uncomment these if you want video confidence analysis:
# opencv-python==4.9.0.80
# numpy==1.26.4
# librosa==0.10.1
# moviepy==1.0.3
# deepface==0.0.89
# speechbrain==0.5.16
# torchaudio==2.1.0
```

### 6. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 7. Create `.env.example`

```env
# ============================================
# Agentic AI Enterprise Platform — Configuration
# ============================================

# === LLM Provider (REQUIRED) ===
# Get a free API key at: https://console.groq.com/
GROQ_API_KEY=your_groq_api_key_here

# === Email Notifications (OPTIONAL) ===
# Used for: leave notifications, test results, welcome emails
# Setup: Gmail → Settings → Security → 2-Step Verification → App Passwords
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_gmail_app_password

# === Code Execution (OPTIONAL) ===
# Leave blank to use the free public Judge0 instance
# Or get a key from: https://rapidapi.com/judge0-official/api/judge0-ce
JUDGE0_API_KEY=
```

### 8. Create `.gitignore`

```
# Environment
.venv/
.env
__pycache__/
*.pyc

# Data (user-generated)
data/interview_results/
data/learning/
data/uploads/

# IDE
.vscode/
.idea/
*.swp
```

---

## ✅ Done Checklist

After completing this step, verify:

- [ ] All folders created (core, agents, tools, prompts, ui, data, tests)
- [ ] All `__init__.py` files exist
- [ ] `.venv` activated and dependencies installed
- [ ] `.env` file created with your GROQ_API_KEY
- [ ] `.gitignore` in place
- [ ] Running `python -c "import streamlit; print(streamlit.__version__)"` prints `1.50.0`
- [ ] Running `python -c "from groq import Groq; print('OK')"` prints `OK`

---

**Next** → `01_CORE_CONFIG_DB.md` (config.py + all data models + database class)
