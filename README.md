# 🤖 Agentic AI Enterprise Platform

An intelligent multi-agent enterprise management system powered by LLMs (Groq/Llama), featuring autonomous HR, IT, Finance, and Compliance agents that collaborate through an event-driven architecture.

## Features

- **Multi-Agent Architecture**: 4 specialized agents (HR, IT, Finance, Compliance)
- **Event-Driven Communication**: Pub/sub event bus for inter-agent messaging
- **AI-Powered Decision Making**: Groq LLM integration for intelligent processing
- **Smart Hiring Pipeline**: Resume parsing → Technical interview → Psychometric assessment → Video analysis
- **Self-Service Portals**: Employee, Admin, IT, Finance, and Compliance dashboards
- **Adaptive Learning**: Agents learn from human overrides to improve decisions
- **Workflow Orchestration**: Cross-agent workflows (new hire, employee exit, etc.)

## Tech Stack

- **Backend**: Python 3.11+
- **LLM**: Groq API (Llama 3.1/3.3)
- **UI**: Streamlit
- **Code Execution**: Judge0 API
- **Architecture**: Event-driven multi-agent system

## Quick Start

```bash
# 1. Clone and enter project
cd AgenticAI_Enterprise

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 5. Run the application
streamlit run app.py
```

## Project Structure

```
AgenticAI_Enterprise/
├── core/           # Framework foundation (config, DB, LLM, event bus)
├── agents/         # Domain agents (HR, IT, Finance, Compliance)
├── tools/          # Shared utilities (email, code exec, video analysis)
├── prompts/        # All LLM prompt templates (organized by agent)
├── ui/             # Streamlit UI pages and portals
├── data/           # Persistent storage (git-ignored)
└── tests/          # Test suite
```

## Default Login Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| john | john123 | Employee |
| jane | jane123 | Employee |

## License

MIT
