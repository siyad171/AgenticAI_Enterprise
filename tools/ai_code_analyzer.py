"""
AI Code Analyzer — Uses Groq LLM to evaluate code quality and complexity
"""
import os, json
from groq import Groq
from dotenv import load_dotenv
from typing import Dict

load_dotenv()


class AICodeAnalyzer:
    """Analyzes code quality, complexity, and provides interview follow-ups"""

    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

    def analyze_code(self, code: str, language: str, problem_description: str = "") -> Dict:
        prompt = f"""You are an expert code reviewer analyzing a {language} solution.

Problem: {problem_description if problem_description else "Not provided"}

Code:
```{language}
{code}
```

Analyze this code and provide evaluation in JSON format:
{{
  "code_quality_score": <0-100>,
  "quality_breakdown": {{
    "naming_conventions": <0-100>, "readability": <0-100>,
    "modularity": <0-100>, "comments": <0-100>
  }},
  "time_complexity": "<Big-O>",
  "space_complexity": "<Big-O>",
  "strengths": ["..."], "weaknesses": ["..."],
  "optimization_suggestions": ["..."],
  "best_practices_score": <0-100>,
  "overall_feedback": "<2-3 sentence summary>"
}}"""
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Expert programming interviewer. Provide valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile", temperature=0.3, max_tokens=1500
            )
            text = response.choices[0].message.content.strip()
            if text.startswith('```'):
                lines = text.split('\n')
                text = '\n'.join(lines[1:-1])
                if text.startswith('json'): text = text[4:].strip()
            result = json.loads(text)
            result['status'] = 'success'
            return result
        except json.JSONDecodeError as e:
            return self._fallback_response(f"JSON parse error: {e}")
        except Exception as e:
            return self._fallback_response(str(e))

    def ask_followup_question(self, code: str, language: str, context: str = "") -> str:
        prompt = f"""You are a technical interviewer. The candidate wrote this {language} code:

```{language}
{code}
```

{context}

Ask ONE thoughtful follow-up question. Return only the question."""
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Experienced technical interviewer."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile", temperature=0.5, max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "Can you explain the time complexity of your solution?"

    def evaluate_explanation(self, question: str, answer: str, code: str) -> Dict:
        prompt = f"""Evaluate this technical interview response:
Question: {question}
Answer: {answer}
Code:
```
{code}
```
Provide JSON: {{"accuracy_score":<0-100>,"clarity_score":<0-100>,
"depth_score":<0-100>,"overall_score":<0-100>,"feedback":"<brief>"}}"""
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Evaluating a technical interview response."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile", temperature=0.3, max_tokens=400
            )
            text = response.choices[0].message.content.strip()
            if text.startswith('```'):
                lines = text.split('\n')
                text = '\n'.join(lines[1:-1])
                if text.startswith('json'): text = text[4:].strip()
            result = json.loads(text)
            result['status'] = 'success'
            return result
        except Exception:
            return {'status': 'error', 'accuracy_score': 50, 'clarity_score': 50,
                    'depth_score': 50, 'overall_score': 50, 'feedback': 'Could not evaluate'}

    def _fallback_response(self, error_msg: str) -> Dict:
        return {
            'status': 'error', 'error': error_msg,
            'code_quality_score': 50,
            'quality_breakdown': {'naming_conventions': 50, 'readability': 50, 'modularity': 50, 'comments': 50},
            'time_complexity': 'Unable to analyze', 'space_complexity': 'Unable to analyze',
            'strengths': [], 'weaknesses': [], 'optimization_suggestions': [],
            'best_practices_score': 50,
            'overall_feedback': 'AI analysis failed. Manual review recommended.'
        }
