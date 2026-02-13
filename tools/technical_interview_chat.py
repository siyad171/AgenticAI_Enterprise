"""
Technical Interview Chat — AI Interviewer with Context-Aware Hints
Dual LLM: llama-3.1-8b-instant (chat) + llama-3.3-70b (analysis)
"""
import os, json
from groq import Groq
from dotenv import load_dotenv
from typing import Dict, List
from datetime import datetime

load_dotenv()


class TechnicalInterviewChat:
    """
    AI-powered technical interviewer:
    - 6 stages: introduction → clarification → approach → coding → review → complete
    - Context-aware hints (max 3)
    - Socratic debugging conversations
    """

    STAGES = {
        'INTRODUCTION': 'introduction', 'CLARIFICATION': 'clarification',
        'APPROACH': 'approach', 'CODING': 'coding',
        'REVIEW': 'review', 'COMPLETE': 'complete'
    }

    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.chat_model = "llama-3.1-8b-instant"
        self.analysis_model = "llama-3.3-70b-versatile"
        self.current_stage = self.STAGES['INTRODUCTION']
        self.conversation_history = []
        self.problem_data = {}
        self.hint_count = 0
        self.max_hints = 3
        self.candidate_code = ""
        self.approach_quality = 0
        self.communication_score = 0

    # ── Stage 1: Introduction ─────────────────────────────────────
    def start_interview(self, problem: Dict) -> str:
        self.problem_data = problem
        self.current_stage = self.STAGES['INTRODUCTION']
        prompt = (
            f"You are a friendly technical interviewer.\n\n"
            f"Problem: {problem['title']} ({problem['difficulty']})\n"
            f"Description:\n{problem['description']}\n"
            f"Examples:\n{self._format_examples(problem['examples'])}\n\n"
            "1. Brief warm greeting\n2. Introduce problem conversationally\n"
            "3. Show ONE example\n4. Ask if they have clarifying questions\n"
            "Max 5 sentences. Be encouraging."
        )
        response = self._call_llm(prompt, self.chat_model)
        self._add_to_history('assistant', response, 'introduction')
        return response

    # ── Stage 2: Clarification ────────────────────────────────────
    def handle_clarification(self, candidate_question: str) -> str:
        self.current_stage = self.STAGES['CLARIFICATION']
        self._add_to_history('user', candidate_question, 'clarification')
        prompt = (
            f'Candidate said: "{candidate_question}"\n\n'
            f"Problem:\n{self._get_problem_context()}\n"
            f"Recent conversation:\n{self._get_recent_conversation(5)}\n\n"
            "If explaining approach → say 'Walk me through your solution step by step.'\n"
            "If asking question → answer clearly (2-3 sentences max)."
        )
        response = self._call_llm(prompt, self.chat_model)
        self._add_to_history('assistant', response, 'clarification')
        return response

    # ── Stage 3: Approach Discussion ──────────────────────────────
    def discuss_approach(self, candidate_explanation: str) -> Dict:
        self.current_stage = self.STAGES['APPROACH']
        self._add_to_history('user', candidate_explanation, 'approach')
        prompt = (
            f"Problem: {self.problem_data['title']}\n"
            f'Candidate explanation: "{candidate_explanation}"\n\n'
            "Analyze approach. Return JSON:\n"
            '{"approach_valid":bool,"approach_score":<0-100>,'
            '"time_complexity":"O(...)","space_complexity":"O(...)",'
            '"strengths":["..."],"concerns":["..."],'
            '"follow_up_question":"...","feedback_message":"2-3 sentences"}\n\n'
            "Brute force→score 60-70, ask to optimize. Optimal→90-100, praise."
        )
        response = self._call_llm(prompt, self.analysis_model, json_mode=True)
        try:
            feedback = json.loads(response)
            self.approach_quality = feedback.get('approach_score', 50)
            self._add_to_history('assistant', feedback['feedback_message'], 'approach')
            return feedback
        except Exception:
            self._add_to_history('assistant', response, 'approach')
            return {'approach_valid': True, 'approach_score': 70, 'feedback_message': response}

    # ── Stage 4: Context-Aware Hints ──────────────────────────────
    def get_context_aware_hint(self, current_code: str, error_message: str = "") -> str:
        if self.hint_count >= self.max_hints:
            return "You've used all hints. Try to debug this yourself — you're close!"
        self.hint_count += 1
        self.candidate_code = current_code
        prompt = (
            f"Problem: {self.problem_data['title']}\n"
            f"Code:\n```\n{current_code if current_code.strip() else 'No code yet'}\n```\n"
            f"Error: {error_message or 'Just stuck'}\n"
            f"Hint #{self.hint_count}/{self.max_hints}\n\n"
            "Use Socratic questioning. Don't give the answer. Under 3 sentences."
        )
        response = self._call_llm(prompt, self.chat_model)
        self._add_to_history('assistant', response, 'hint', {'hint_number': self.hint_count})
        return response

    # ── Stage 4b: Debugging Conversation ──────────────────────────
    def debug_conversation(self, candidate_message: str, failing_code: str,
                           test_results: List[Dict]) -> str:
        self.candidate_code = failing_code
        self._add_to_history('user', candidate_message, 'debugging')
        failed = [t for t in test_results if t['status'] != 'passed']
        passed = [t for t in test_results if t['status'] == 'passed']
        prompt = (
            f"Problem: {self.problem_data['title']}\n"
            f"Code:\n```\n{failing_code}\n```\n"
            f"Passed: {len(passed)}, Failed: {len(failed)}\n"
            f"Failed examples:\n{self._format_failed_tests(failed[:2])}\n"
            f'Candidate says: "{candidate_message}"\n\n'
            "Guide them with Socratic questions. Don't give the answer. ≤4 sentences."
        )
        response = self._call_llm(prompt, self.chat_model)
        self._add_to_history('assistant', response, 'debugging')
        return response

    # ── Stage 5: Code Review ──────────────────────────────────────
    def analyze_code_submission(self, code: str, test_results: List[Dict]) -> Dict:
        self.current_stage = self.STAGES['REVIEW']
        self.candidate_code = code
        passed_count = sum(1 for t in test_results if t['status'] == 'passed')
        prompt = (
            f"Problem: {self.problem_data['title']}\n"
            f"Solution:\n```\n{code}\n```\n"
            f"Tests: {passed_count}/{len(test_results)} passed\n"
            f"Approach discussion:\n{self._get_approach_discussion()}\n\n"
            "Return JSON with: code_quality_score, correctness, efficiency, "
            "readability, time_complexity, space_complexity, strengths, weaknesses, "
            "optimization_suggestions, follow_up_questions, overall_feedback"
        )
        response = self._call_llm(prompt, self.analysis_model, json_mode=True)
        try:
            analysis = json.loads(response)
            self._add_to_history('assistant', analysis.get('overall_feedback', ''), 'review')
            return analysis
        except Exception:
            return {'code_quality_score': 70, 'overall_feedback': response}

    def ask_follow_up_question(self, topic: str = "optimization") -> str:
        prompt = (
            f"Problem: {self.problem_data['title']}\n"
            f"Solution:\n```\n{self.candidate_code[:500]}\n```\n"
            f"Recent:\n{self._get_recent_conversation(3)}\n\n"
            f"Ask a follow-up about {topic}. 2-3 sentences."
        )
        response = self._call_llm(prompt, self.chat_model)
        self._add_to_history('assistant', response, 'follow_up')
        return response

    def evaluate_explanation(self, candidate_answer: str) -> Dict:
        self._add_to_history('user', candidate_answer, 'follow_up')
        prompt = (
            f'Evaluate: "{candidate_answer}"\n\n'
            'JSON: {{"accuracy":<0-100>,"clarity":<0-100>,"depth":<0-100>,'
            '"overall_score":<0-100>,"feedback":"brief"}}'
        )
        response = self._call_llm(prompt, self.analysis_model, json_mode=True)
        try:
            scores = json.loads(response)
            self.communication_score = scores.get('overall_score', 70)
            self._add_to_history('assistant', scores.get('feedback', ''), 'evaluation')
            return scores
        except Exception:
            return {'overall_score': 70, 'feedback': response}

    # ── Final Report ──────────────────────────────────────────────
    def get_final_report(self) -> Dict:
        return {
            'interview_id': f"INT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'problem': self.problem_data.get('title', 'Unknown'),
            'stages_completed': self._get_completed_stages(),
            'approach_quality': self.approach_quality,
            'communication_score': self.communication_score,
            'hints_used': self.hint_count,
            'conversation_history': self.conversation_history,
            'total_messages': len(self.conversation_history),
            'duration_estimate': len(self.conversation_history) * 2,
        }

    # ── Helpers ───────────────────────────────────────────────────
    def _call_llm(self, prompt: str, model: str, json_mode: bool = False) -> str:
        try:
            params = {"model": model, "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.7, "max_tokens": 1024}
            if json_mode:
                params["response_format"] = {"type": "json_object"}
            resp = self.groq_client.chat.completions.create(**params)
            return resp.choices[0].message.content
        except Exception as e:
            return f"Processing error. Could you rephrase? ({str(e)[:50]})"

    def _add_to_history(self, role, content, stage, metadata=None):
        self.conversation_history.append({
            'role': role, 'content': content, 'stage': stage,
            'timestamp': datetime.now().isoformat(), 'metadata': metadata or {}
        })

    def _get_problem_context(self):
        return (f"Title: {self.problem_data.get('title', 'N/A')}\n"
                f"Difficulty: {self.problem_data.get('difficulty', 'N/A')}\n"
                f"Description: {self.problem_data.get('description', 'N/A')[:200]}")

    def _get_recent_conversation(self, n=5):
        return "\n".join(
            f"{'AI' if m['role'] == 'assistant' else 'Candidate'}: {m['content'][:100]}..."
            for m in self.conversation_history[-n:]
        )

    def _get_approach_discussion(self):
        msgs = [m for m in self.conversation_history if m['stage'] == 'approach']
        return "\n".join(f"{m['role']}: {m['content']}" for m in msgs[-3:])

    def _format_examples(self, examples):
        parts = []
        for i, ex in enumerate(examples[:2], 1):
            parts.append(f"Example {i}: Input: {ex.get('input', 'N/A')}, Output: {ex.get('output', 'N/A')}")
            if ex.get('explanation'): parts.append(f"  Explanation: {ex['explanation']}")
        return "\n".join(parts)

    def _format_failed_tests(self, tests):
        return "\n".join(
            f"- In: {t.get('input', 'N/A')}, Expected: {t.get('expected', 'N/A')}, Got: {t.get('output', 'N/A')}"
            for t in tests
        ) or "No failed tests"

    def _get_completed_stages(self):
        return list({m['stage'] for m in self.conversation_history})

    def get_conversation_for_display(self):
        return [{'role': m['role'], 'content': m['content'],
                 'stage': m['stage'], 'timestamp': m['timestamp']}
                for m in self.conversation_history]
