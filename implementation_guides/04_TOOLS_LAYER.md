# 04 — Tools Layer

> **Depends on:** `01_CORE_CONFIG_DB.md`, `02_CORE_SERVICES.md`
> **Creates:** `tools/email_service.py`, `tools/code_executor.py`, `tools/local_executor.py`, `tools/ai_code_analyzer.py`, `tools/video_analyzer.py`, `tools/video_analyzer_hybrid.py`, `tools/technical_interview_chat.py`, `tools/psychometric_assessment.py`, `tools/interview_storage.py`

---

## Tool 1 — `tools/email_service.py`

Unified email service extracted from `hr_agent.py`. Supports LLM-generated content with deterministic fallback.

```python
"""
Email Service — Unified SMTP email sender with LLM-generated content
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from core.config import (
    SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD
)


class EmailService:
    """Sends transactional emails (leave notifications, test results, tickets, etc.)"""

    def __init__(self, llm_service=None):
        self.llm = llm_service          # Optional — for AI-generated bodies

    # ── generic send ──────────────────────────────────────────────
    def send_email(self, to: str, subject: str, body: str) -> Dict:
        """Send a plain-text email. Returns {'status': 'success'|'error', 'message': ...}"""
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            return {
                "status": "error",
                "message": "Email credentials not configured in .env",
                "email_content": body
            }
        try:
            msg = MIMEMultipart()
            msg["From"] = SENDER_EMAIL
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)

            return {"status": "success", "message": f"Email sent to {to}"}
        except Exception as e:
            return {"status": "error", "message": str(e), "email_content": body}

    # ── leave notification ────────────────────────────────────────
    def send_leave_email(
        self, employee_name: str, employee_email: str,
        leave_type: str, start_date: str, end_date: str,
        days: int, reason: str, status: str, message: str,
        request_id: str
    ) -> Dict:
        """Send leave request notification — uses LLM body with fallback."""
        subject, body = self._generate_leave_email(
            employee_name, leave_type, start_date, end_date,
            days, reason, status, message, request_id
        )
        return self.send_email(employee_email, subject, body)

    def _generate_leave_email(self, name, leave_type, start, end, days,
                              reason, status, message, req_id):
        """Try LLM, fall back to template."""
        if self.llm:
            try:
                prompt = (
                    f"Generate a professional leave notification email.\n"
                    f"Employee: {name}\nLeave Type: {leave_type}\n"
                    f"Period: {start} to {end} ({days} days)\nReason: {reason}\n"
                    f"Status: {status}\nNote: {message}\nRequest ID: {req_id}\n\n"
                    "Tailor tone to leave type (sick→recovery, annual→enjoy break). "
                    "Return ONLY the email body."
                )
                body = self.llm.ask_question(prompt)
                subj_prompt = (
                    f"Short subject line (<10 words) for leave request {status.lower()}. "
                    f"Type: {leave_type}. Return ONLY the subject."
                )
                subject = self.llm.ask_question(subj_prompt).strip().strip('"\'')
                return subject, body
            except Exception:
                pass

        # ── deterministic fallback ────────────────────────────────
        if status.upper() == "APPROVED":
            tone = {
                "sick": "We wish you a speedy recovery.",
                "annual": "Enjoy your well-deserved break!",
                "unpaid": "We hope everything goes well.",
            }
            closing = tone.get(leave_type.split()[0].lower(), "Have a pleasant time off.")
            subject = f"Leave Request Approved - {leave_type}"
            body = (
                f"Dear {name},\n\nYour leave request has been approved!\n\n"
                f"Request ID: {req_id}\nType: {leave_type}\n"
                f"Period: {start} to {end} ({days} days)\nReason: {reason}\n\n"
                f"Status: APPROVED ✓\n\n{message}\n\n{closing}\n\n"
                "Best regards,\nHR Department"
            )
        elif status.upper() == "REJECTED":
            subject = f"Leave Request Status - {leave_type}"
            body = (
                f"Dear {name},\n\nThank you for submitting your leave request.\n\n"
                f"Request ID: {req_id}\nType: {leave_type}\n"
                f"Period: {start} to {end} ({days} days)\nReason: {reason}\n\n"
                f"Status: NOT APPROVED\n\n{message}\n\n"
                "Please contact HR to discuss alternatives.\n\n"
                "Best regards,\nHR Department"
            )
        else:
            subject = f"Leave Request Under Review - {leave_type}"
            body = (
                f"Dear {name},\n\nYour leave request is under review.\n\n"
                f"Request ID: {req_id}\nType: {leave_type}\n"
                f"Period: {start} to {end} ({days} days)\nReason: {reason}\n\n"
                f"Status: PENDING APPROVAL\n\n{message}\n\n"
                "You will be notified once reviewed.\n\n"
                "Best regards,\nHR Department"
            )
        return subject, body

    # ── test result notification ──────────────────────────────────
    def send_test_result_email(
        self, candidate_email: str, candidate_name: str,
        passed: bool, test_score: float, position: str,
        username: str = None, password: str = None
    ) -> Dict:
        """Send test result email — uses LLM body with fallback."""
        subject, body = self._generate_test_result_email(
            candidate_name, passed, test_score, position, username, password
        )
        return self.send_email(candidate_email, subject, body)

    def _generate_test_result_email(self, name, passed, score, position,
                                     username, password):
        if self.llm:
            try:
                prompt = (
                    f"Professional email for test results.\n"
                    f"Candidate: {name}\nPosition: {position}\n"
                    f"Score: {score:.1f}%\nResult: {'PASSED' if passed else 'FAILED'}\n"
                )
                if passed and username:
                    prompt += f"Include portal credentials — User: {username}, Pass: {password}\n"
                prompt += "Return ONLY the email body."
                body = self.llm.ask_question(prompt)
                subj_prompt = (
                    f"Short subject for test result ({'passed' if passed else 'failed'}) "
                    f"for {position}. Return ONLY subject."
                )
                subject = self.llm.ask_question(subj_prompt).strip().strip('"\'')
                return subject, body
            except Exception:
                pass

        if passed:
            subject = f"Congratulations! Selected for {position}"
            body = (
                f"Dear {name},\n\nCongratulations! You passed the {position} "
                f"assessment with {score:.1f}%.\n\n"
            )
            if username:
                body += f"Portal credentials:\nUsername: {username}\nPassword: {password}\n\n"
            body += "Best regards,\nHR Department"
        else:
            subject = f"Test Results for {position} Position"
            body = (
                f"Dear {name},\n\nThank you for taking the {position} assessment.\n"
                f"Your score of {score:.1f}% did not meet requirements.\n\n"
                "We encourage you to apply for other positions.\n\n"
                "Best regards,\nHR Department"
            )
        return subject, body
```

---

## Tool 2 — `tools/local_executor.py`

Copy exactly — lightweight local Python subprocess runner (fallback for Judge0).

```python
"""
Local Python Code Executor — Fallback for when Judge0 is unavailable
Runs Python code safely in subprocess with timeout
"""
import subprocess
import time
from typing import Dict


class LocalPythonExecutor:
    """Execute Python code locally in a safe subprocess"""

    def execute_python(self, code: str, stdin: str = "", timeout: float = 5.0) -> Dict:
        try:
            start_time = time.time()
            process = subprocess.Popen(
                ['python', '-c', code],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            try:
                stdout, stderr = process.communicate(input=stdin, timeout=timeout)
                execution_time = time.time() - start_time
                if process.returncode == 0:
                    return {'status': 'success', 'output': stdout.strip(),
                            'error': '', 'time': execution_time, 'memory': 0}
                else:
                    return {'status': 'error', 'output': stdout.strip(),
                            'error': stderr.strip(), 'time': execution_time, 'memory': 0}
            except subprocess.TimeoutExpired:
                process.kill()
                return {'status': 'error', 'output': '',
                        'error': f'Time Limit Exceeded ({timeout}s)',
                        'time': timeout, 'memory': 0}
        except Exception as e:
            return {'status': 'error', 'output': '',
                    'error': f'Execution failed: {str(e)}', 'time': 0, 'memory': 0}
```

---

## Tool 3 — `tools/code_executor.py`

Judge0 API integration + local fallback. Preserve all URLs, language IDs, polling logic.

```python
"""
Code Execution Service — Judge0 API Integration with Local Fallback
"""
import requests
import time
import base64
import os
from typing import Dict, List
from dotenv import load_dotenv
from tools.local_executor import LocalPythonExecutor   # ← updated import

load_dotenv()


class CodeExecutor:
    """Handles code execution via Judge0 API with local Python fallback"""

    BASE_URL = "https://judge0-ce.p.rapidapi.com"
    SULU_URL = "https://ce.judge0.com"
    BACKUP_URL = "https://judge0.p.rapidapi.com"
    EXTRA_URL = "https://judge0-extra.p.rapidapi.com"

    LANGUAGES = {
        'python': 71, 'java': 62, 'cpp': 54, 'c': 50, 'javascript': 63
    }

    def __init__(self):
        self.api_key = os.getenv('JUDGE0_API_KEY', '')
        self.local_executor = LocalPythonExecutor()
        self.use_local = False
        if not self.api_key:
            self.base_url = self.SULU_URL
            self.headers = {"content-type": "application/json"}
        else:
            self.base_url = self.BASE_URL
            self.headers = {
                "content-type": "application/json",
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com"
            }

    def execute_code(self, code: str, language: str, stdin: str = "",
                     time_limit: float = 2.0, memory_limit: int = 128000) -> Dict:
        if self.use_local and language.lower() == 'python':
            return self.local_executor.execute_python(code, stdin, time_limit)
        try:
            language_id = self.LANGUAGES.get(language.lower())
            if not language_id:
                return {'status': 'error', 'error': f'Unsupported language: {language}', 'output': ''}

            code_b64 = base64.b64encode(code.encode()).decode()
            stdin_b64 = base64.b64encode(stdin.encode()).decode() if stdin else ""

            submission_data = {
                "language_id": language_id,
                "source_code": code_b64,
                "stdin": stdin_b64,
                "cpu_time_limit": time_limit,
                "memory_limit": memory_limit
            }

            response = requests.post(
                f"{self.base_url}/submissions?base64_encoded=true&wait=false",
                json=submission_data, headers=self.headers, timeout=10
            )

            if response.status_code in (504, 429) or response.status_code != 201:
                if language.lower() == 'python':
                    self.use_local = True
                    return self.local_executor.execute_python(code, stdin, time_limit)
                return {'status': 'error', 'error': f'Submission failed: {response.text}', 'output': ''}

            token = response.json()['token']
            return self._get_submission_result(token)

        except requests.exceptions.Timeout:
            if language.lower() == 'python':
                self.use_local = True
                return self.local_executor.execute_python(code, stdin, time_limit)
            return {'status': 'error', 'error': 'Request timeout', 'output': '', 'time': 0, 'memory': 0}
        except Exception as e:
            if language.lower() == 'python':
                self.use_local = True
                return self.local_executor.execute_python(code, stdin, time_limit)
            return {'status': 'error', 'error': str(e), 'output': '', 'time': 0, 'memory': 0}

    def _get_submission_result(self, token: str, max_attempts: int = 10) -> Dict:
        for _ in range(max_attempts):
            try:
                response = requests.get(
                    f"{self.base_url}/submissions/{token}?base64_encoded=true",
                    headers=self.headers
                )
                if response.status_code != 200:
                    time.sleep(1); continue
                result = response.json()
                status_id = result.get('status', {}).get('id')
                if status_id in [1, 2]:
                    time.sleep(1); continue
                stdout = base64.b64decode(result.get('stdout', '') or '').decode('utf-8', errors='ignore')
                stderr = base64.b64decode(result.get('stderr', '') or '').decode('utf-8', errors='ignore')
                compile_out = base64.b64decode(result.get('compile_output', '') or '').decode('utf-8', errors='ignore')
                if status_id == 3:
                    return {'status': 'success', 'output': stdout.strip(), 'error': '',
                            'time': float(result.get('time', 0) or 0),
                            'memory': int(result.get('memory', 0) or 0)}
                error_msg = stderr or compile_out or result.get('status', {}).get('description', 'Unknown error')
                return {'status': 'error', 'output': stdout.strip(), 'error': error_msg,
                        'time': float(result.get('time', 0) or 0),
                        'memory': int(result.get('memory', 0) or 0)}
            except Exception:
                time.sleep(1); continue
        return {'status': 'error', 'error': 'Execution timeout', 'output': '', 'time': 0, 'memory': 0}

    def run_test_cases(self, code: str, language: str, test_cases: List[Dict],
                       time_limit: float = 2.0) -> Dict:
        results = {'total': len(test_cases), 'passed': 0, 'failed': 0,
                   'error': 0, 'test_results': [], 'all_passed': False}
        for i, tc in enumerate(test_cases):
            result = self.execute_code(code, language, tc.get('input', ''), time_limit)
            actual = result['output'].strip()
            expected = tc.get('expected', '').strip()
            passed = self._compare_outputs(actual, expected)
            if result['status'] == 'success' and passed:
                results['passed'] += 1; status = 'passed'
            elif result['status'] == 'success':
                results['failed'] += 1; status = 'failed'
            else:
                results['error'] += 1; status = 'error'

            if tc.get('visible', True):
                results['test_results'].append({
                    'test_number': i+1, 'status': status,
                    'input': tc.get('input',''), 'expected': expected,
                    'actual': actual, 'error': result.get('error',''),
                    'time': result.get('time',0), 'memory': result.get('memory',0)
                })
            else:
                results['test_results'].append({
                    'test_number': i+1, 'status': status,
                    'input': 'Hidden', 'expected': 'Hidden',
                    'actual': 'Hidden' if status != 'passed' else expected,
                    'error': result.get('error','') if status == 'error' else '',
                    'time': result.get('time',0), 'memory': result.get('memory',0),
                    'hidden': True
                })
        results['all_passed'] = (results['passed'] == results['total'])
        return results

    @staticmethod
    def _compare_outputs(actual: str, expected: str) -> bool:
        if actual == expected:
            return True
        def normalize(s):
            s = s.replace('[','').replace(']','').replace('(','').replace(')','')
            s = s.replace(',', ' ').replace('\t', ' ')
            return ' '.join(s.split())
        return normalize(actual) == normalize(expected)
```

---

## Tool 4 — `tools/ai_code_analyzer.py`

Groq LLM code reviewer. Preserve `analyze_code`, `ask_followup_question`, `evaluate_explanation`.

```python
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
            return {'status':'error','accuracy_score':50,'clarity_score':50,
                    'depth_score':50,'overall_score':50,'feedback':'Could not evaluate'}

    def _fallback_response(self, error_msg: str) -> Dict:
        return {
            'status': 'error', 'error': error_msg,
            'code_quality_score': 50,
            'quality_breakdown': {'naming_conventions':50,'readability':50,'modularity':50,'comments':50},
            'time_complexity': 'Unable to analyze', 'space_complexity': 'Unable to analyze',
            'strengths': [], 'weaknesses': [], 'optimization_suggestions': [],
            'best_practices_score': 50,
            'overall_feedback': 'AI analysis failed. Manual review recommended.'
        }
```

---

## Tool 5 — `tools/video_analyzer.py`

Heavy-dependency video analyzer (DeepFace + SpeechBrain + OpenCV + librosa). **This file is 593 lines.** Because it uses optional heavy dependencies, copy it verbatim from the current `video_analyzer.py`.

**Instructions for the implementing agent:**
1. Copy the **entire** contents of the existing `video_analyzer.py` (593 lines) into `tools/video_analyzer.py`
2. No import changes needed — it uses no project-internal imports
3. Make sure the file-level function `analyze_candidate_video(video_path)` is preserved at the bottom
4. This tool is **optional** — it requires `deepface`, `speechbrain`, `opencv-python`, `librosa`, `moviepy`

---

## Tool 6 — `tools/video_analyzer_hybrid.py`

Combines heuristic + Groq AI analysis. Update the import path.

```python
"""
Hybrid Video Analyzer — Heuristic + Groq AI transcript analysis
60% visual/audio heuristics + 40% AI communication scoring
"""
import os, json, re
from typing import Dict
from tools.video_analyzer import analyze_candidate_video   # ← updated import
from moviepy.editor import VideoFileClip
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class HybridVideoAnalyzer:
    """Combines heuristic video analysis with AI transcript analysis"""

    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

    def _extract_audio(self, video_path: str) -> str:
        try:
            video = VideoFileClip(video_path)
            audio_path = video_path.rsplit('.', 1)[0] + '_temp_audio.wav'
            video.audio.write_audiofile(audio_path, verbose=False, logger=None)
            video.close()
            return audio_path
        except Exception as e:
            print(f"Audio extraction error: {e}")
            return None

    def _transcribe_audio(self, audio_path: str) -> str:
        try:
            with open(audio_path, "rb") as f:
                transcription = self.groq_client.audio.transcriptions.create(
                    file=(audio_path, f.read()),
                    model="whisper-large-v3-turbo",
                    response_format="json", language="en", temperature=0.0
                )
            return transcription.text
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

    def _analyze_transcript(self, transcript: str) -> Dict:
        if not transcript or len(transcript.strip()) < 20:
            return {'communication_score': 0, 'feedback': 'Transcript too short'}
        prompt = (
            f'Analyze this interview transcript and provide communication_score (0-100) '
            f'and brief feedback in JSON.\n\nTranscript:\n"{transcript}"\n\n'
            'Respond: {{"communication_score":<score>,"feedback":"<brief>"}}'
        )
        try:
            resp = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Expert HR interviewer. Be concise."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile", temperature=0.3, max_tokens=300
            )
            text = resp.choices[0].message.content.strip()
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'): text = text[4:]
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                score_match = re.search(r'"communication_score":\s*(\d+)', text)
                return {'communication_score': int(score_match.group(1)) if score_match else 50,
                        'feedback': text[:200]}
        except Exception as e:
            return {'communication_score': 0, 'feedback': f'AI analysis failed: {e}'}

    def analyze(self, video_path: str) -> Dict:
        try:
            print("🔍 Running visual and audio analysis...")
            heuristic_results = analyze_candidate_video(video_path)
            heuristic_score = heuristic_results.get('overall_confidence_score') or \
                              heuristic_results.get('confidence_score', 5.0)

            audio_path = self._extract_audio(video_path)
            transcript = ""
            ai_results = {'communication_score': 0, 'feedback': 'Transcription failed'}

            if audio_path:
                transcript = self._transcribe_audio(audio_path)
                if transcript:
                    ai_results = self._analyze_transcript(transcript)
                try:
                    os.remove(audio_path)
                except Exception:
                    pass

            ai_norm = ai_results['communication_score'] / 10.0
            final_score = (heuristic_score * 0.6) + (ai_norm * 0.4)

            visual = heuristic_results.get('visual_analysis', {})
            audio = heuristic_results.get('audio_analysis', {})
            breakdown = {
                'nervousness_score': visual.get('nervousness_indicators', 0),
                'eye_contact_score': visual.get('eye_contact_rate', 0),
                'smile_score': visual.get('smile_rate', 0),
                'fidgeting_score': 100 - visual.get('head_stability', 0),
                'audio_score': audio.get('confidence_score', 0),
                'pitch_variation': audio.get('pitch_variation', 0),
                'energy': audio.get('energy', 0),
                'speech_rate': audio.get('speech_rate', 0),
                'emotional_positivity': visual.get('emotional_positivity', 0),
                'head_stability': visual.get('head_stability', 0)
            }

            return {
                'status': 'success',
                'overall_confidence_score': final_score,
                'heuristic_score': heuristic_score,
                'ai_communication_score': ai_results['communication_score'],
                'ai_feedback': ai_results['feedback'],
                'transcript': transcript,
                'breakdown': breakdown,
                'video_path': video_path
            }
        except Exception as e:
            import traceback; traceback.print_exc()
            return {'status': 'error', 'error': str(e), 'overall_confidence_score': 0}


def analyze_candidate_video_ai(video_path: str) -> Dict:
    """Convenience function for hybrid analysis"""
    try:
        return HybridVideoAnalyzer().analyze(video_path)
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'overall_confidence_score': 0}
```

---

## Tool 7 — `tools/technical_interview_chat.py`

6-stage AI interviewer with dual-model architecture. Preserve all stages, Socratic hints, debugging conversation.

```python
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
        return (f"Title: {self.problem_data.get('title','N/A')}\n"
                f"Difficulty: {self.problem_data.get('difficulty','N/A')}\n"
                f"Description: {self.problem_data.get('description','N/A')[:200]}")

    def _get_recent_conversation(self, n=5):
        return "\n".join(
            f"{'AI' if m['role']=='assistant' else 'Candidate'}: {m['content'][:100]}..."
            for m in self.conversation_history[-n:]
        )

    def _get_approach_discussion(self):
        msgs = [m for m in self.conversation_history if m['stage'] == 'approach']
        return "\n".join(f"{m['role']}: {m['content']}" for m in msgs[-3:])

    def _format_examples(self, examples):
        parts = []
        for i, ex in enumerate(examples[:2], 1):
            parts.append(f"Example {i}: Input: {ex.get('input','N/A')}, Output: {ex.get('output','N/A')}")
            if ex.get('explanation'): parts.append(f"  Explanation: {ex['explanation']}")
        return "\n".join(parts)

    def _format_failed_tests(self, tests):
        return "\n".join(
            f"- In: {t.get('input','N/A')}, Expected: {t.get('expected','N/A')}, Got: {t.get('output','N/A')}"
            for t in tests
        ) or "No failed tests"

    def _get_completed_stages(self):
        return list({m['stage'] for m in self.conversation_history})

    def get_conversation_for_display(self):
        return [{'role': m['role'], 'content': m['content'],
                 'stage': m['stage'], 'timestamp': m['timestamp']}
                for m in self.conversation_history]
```

---

## Tool 8 — `tools/psychometric_assessment.py`

20-question assessment (EQ/AQ/SQ/BQ). Preserve all questions, scoring, and recommendations.

```python
"""
Psychometric Assessment — EQ, AQ, SQ, BQ
20 questions | 5 per quotient | Weighted scoring | Auto-recommendations
"""
import json
from typing import Dict, List, Tuple
from datetime import datetime


class PsychometricAssessment:
    """
    Validated psychometric assessment:
    - EQ (Emotional): Self-awareness, empathy, regulation, social, motivation
    - AQ (Adaptability): Change, ambiguity, learning, resilience, innovation
    - SQ (Social / FIRO-B): Inclusion, control, affection, collaboration
    - BQ (Behavioral / SJT): Conflict, time, initiative, accountability, decisions
    """

    # ══════════════════════════════════════════════════════════════
    # All 20 questions — COPY EXACTLY from current psychometric_assessment.py
    # ══════════════════════════════════════════════════════════════
    QUESTIONS = [
        # ── EQ (5 questions) ──────────────────────────────────────
        {'id':'eq1','category':'EQ','subcategory':'Self-Awareness',
         'question':'When facing a stressful deadline, I typically:',
         'options':[
             {'text':'Stay calm and break down tasks systematically','score':5},
             {'text':'Feel anxious but push through with effort','score':3},
             {'text':'Feel overwhelmed and need support','score':1},
             {'text':'Get frustrated and lose focus','score':0}]},
        {'id':'eq2','category':'EQ','subcategory':'Empathy',
         'question':'A teammate is struggling with personal issues affecting their work. You:',
         'options':[
             {'text':'Proactively offer support and adjust workload','score':5},
             {'text':'Express concern and wait for them to ask for help','score':3},
             {'text':'Focus on completing the project regardless','score':1},
             {'text':'Feel uncomfortable and avoid the situation','score':0}]},
        {'id':'eq3','category':'EQ','subcategory':'Emotion Regulation',
         'question':'After receiving critical feedback, I:',
         'options':[
             {'text':'Welcome it as a growth opportunity and create action plan','score':5},
             {'text':'Feel defensive initially but accept it after reflection','score':3},
             {'text':'Take it personally and feel discouraged','score':1},
             {'text':'Dismiss it as unfair or irrelevant','score':0}]},
        {'id':'eq4','category':'EQ','subcategory':'Social Skills',
         'question':'In a heated team debate, I:',
         'options':[
             {'text':'Mediate calmly and guide toward consensus','score':5},
             {'text':'Present my view and listen to others','score':3},
             {'text':'Wait for others to resolve the conflict','score':1},
             {'text':'Argue strongly for my position','score':0}]},
        {'id':'eq5','category':'EQ','subcategory':'Motivation',
         'question':'When working on a long-term project with minimal supervision:',
         'options':[
             {'text':'I set milestones and maintain consistent momentum','score':5},
             {'text':'I work in bursts when deadlines approach','score':3},
             {'text':'I struggle without external accountability','score':1},
             {'text':'I often procrastinate until the last minute','score':0}]},
        # ── AQ (5 questions) ──────────────────────────────────────
        {'id':'aq1','category':'AQ','subcategory':'Change Response',
         'question':'Your company suddenly shifts to a new technology stack. You:',
         'options':[
             {'text':'Dive in immediately and learn through practice','score':5},
             {'text':'Take time to plan my learning approach first','score':3},
             {'text':'Feel anxious but eventually adapt','score':1},
             {'text':'Resist the change and prefer old methods','score':0}]},
        {'id':'aq2','category':'AQ','subcategory':'Ambiguity Tolerance',
         'question':'You receive a project with unclear requirements. You:',
         'options':[
             {'text':'See it as an opportunity to innovate and clarify through action','score':5},
             {'text':'Seek clarification from stakeholders first','score':3},
             {'text':'Feel frustrated by the lack of clarity','score':1},
             {'text':'Avoid starting until everything is defined','score':0}]},
        {'id':'aq3','category':'AQ','subcategory':'Learning Agility',
         'question':'When faced with a problem outside your expertise:',
         'options':[
             {'text':'I quickly research and experiment with solutions','score':5},
             {'text':'I consult experts and learn from them','score':3},
             {'text':'I try but often need significant guidance','score':1},
             {'text':'I prefer to pass it to someone more qualified','score':0}]},
        {'id':'aq4','category':'AQ','subcategory':'Resilience',
         'question':'After a major project failure, I:',
         'options':[
             {'text':'Analyze lessons learned and apply them immediately','score':5},
             {'text':'Need time to recover but bounce back','score':3},
             {'text':'Feel demotivated for an extended period','score':1},
             {'text':'Blame external factors and move on','score':0}]},
        {'id':'aq5','category':'AQ','subcategory':'Innovation Mindset',
         'question':'When you see an inefficient process at work:',
         'options':[
             {'text':'I proactively propose and implement improvements','score':5},
             {'text':'I suggest improvements to management','score':3},
             {'text':'I mention it but follow existing procedures','score':1},
             {'text':'I accept it as "the way things are done"','score':0}]},
        # ── SQ / FIRO-B (5 questions) ────────────────────────────
        {'id':'sq1','category':'SQ','subcategory':'Inclusion (Expressed)',
         'question':'In social/work gatherings, I:',
         'options':[
             {'text':'Actively seek out and engage with many people','score':5},
             {'text':'Interact comfortably with familiar faces','score':3},
             {'text':'Prefer small conversations with few people','score':2},
             {'text':'Usually keep to myself','score':1}]},
        {'id':'sq2','category':'SQ','subcategory':'Inclusion (Wanted)',
         'question':'I feel most comfortable when others:',
         'options':[
             {'text':'Actively include me in activities and decisions','score':5},
             {'text':'Invite me but give me space to choose','score':3},
             {'text':'Allow me to participate at my own pace','score':2},
             {'text':'Let me work independently without much interaction','score':1}]},
        {'id':'sq3','category':'SQ','subcategory':'Control (Expressed)',
         'question':'In group projects, I naturally:',
         'options':[
             {'text':'Take charge and organize the team','score':5},
             {'text':'Lead when needed but also follow','score':4},
             {'text':'Contribute ideas but prefer others lead','score':2},
             {'text':'Follow directions and complete assigned tasks','score':1}]},
        {'id':'sq4','category':'SQ','subcategory':'Affection (Expressed)',
         'question':'With colleagues, I:',
         'options':[
             {'text':'Build deep personal connections beyond work','score':5},
             {'text':'Develop friendly professional relationships','score':3},
             {'text':'Keep interactions mostly work-focused','score':2},
             {'text':'Maintain formal professional distance','score':1}]},
        {'id':'sq5','category':'SQ','subcategory':'Collaboration',
         'question':'When collaborating on complex problems:',
         'options':[
             {'text':'I thrive on brainstorming and co-creating with others','score':5},
             {'text':'I balance individual and collaborative work','score':3},
             {'text':'I prefer working alone then sharing results','score':2},
             {'text':'I find collaboration slows me down','score':1}]},
        # ── BQ / Situational Judgment (5 questions) ──────────────
        {'id':'bq1','category':'BQ','subcategory':'Conflict Resolution',
         'question':'Two team members have conflicting approaches to a critical task. You:',
         'options':[
             {'text':'Facilitate a discussion to find a hybrid solution','score':5},
             {'text':'Listen to both and make the final decision','score':3},
             {'text':'Ask your manager to resolve it','score':1},
             {'text':'Let them figure it out themselves','score':0}]},
        {'id':'bq2','category':'BQ','subcategory':'Time Management',
         'question':'You have 3 urgent tasks and can only complete 2 today. You:',
         'options':[
             {'text':'Assess impact, communicate proactively, prioritize strategically','score':5},
             {'text':'Work as fast as possible and hope to finish all three','score':2},
             {'text':'Complete the easiest two first','score':1},
             {'text':'Wait for someone to tell you which to prioritize','score':0}]},
        {'id':'bq3','category':'BQ','subcategory':'Initiative',
         'question':'You notice a potential risk in an upcoming product release. You:',
         'options':[
             {'text':'Document the risk and propose mitigation strategies immediately','score':5},
             {'text':'Mention it to your manager and wait for guidance','score':3},
             {'text':'Assume others have seen it and will handle it','score':1},
             {'text':"Hope it won't materialize and continue as planned",'score':0}]},
        {'id':'bq4','category':'BQ','subcategory':'Accountability',
         'question':'You made an error that caused a project delay. You:',
         'options':[
             {'text':'Immediately inform the team, take ownership, and fix it','score':5},
             {'text':'Fix it quickly and inform stakeholders after','score':3},
             {'text':'Fix it quietly without mentioning it','score':1},
             {'text':'Point out that unclear requirements contributed','score':0}]},
        {'id':'bq5','category':'BQ','subcategory':'Decision Making',
         'question':'You must make a decision with incomplete information and time pressure. You:',
         'options':[
             {'text':'Gather key facts quickly, assess risks, and decide confidently','score':5},
             {'text':'Make the best guess based on available data','score':3},
             {'text':'Seek consensus before deciding','score':2},
             {'text':'Delay until more information is available','score':0}]},
    ]

    def __init__(self):
        self.responses = {}

    def get_questions(self) -> List[Dict]:
        return self.QUESTIONS

    def record_response(self, question_id: str, selected_option_index: int):
        question = next(q for q in self.QUESTIONS if q['id'] == question_id)
        score = question['options'][selected_option_index]['score']
        self.responses[question_id] = {
            'question': question['question'],
            'category': question['category'],
            'subcategory': question['subcategory'],
            'selected_option': question['options'][selected_option_index]['text'],
            'score': score,
            'timestamp': datetime.now().isoformat()
        }

    def calculate_quotients(self) -> Dict:
        """Weighted scoring: EQ 30%, AQ 25%, BQ 25%, SQ 20%"""
        cat_scores = {'EQ': [], 'AQ': [], 'SQ': [], 'BQ': []}
        sub_scores = {}
        for resp in self.responses.values():
            cat_scores[resp['category']].append(resp['score'])
            sub_scores.setdefault(resp['subcategory'], []).append(resp['score'])

        def calc(scores):
            if not scores: return 0.0, "Insufficient Data"
            q = (sum(scores) / (len(scores) * 5)) * 100
            q = round(q, 1)
            if q >= 85: return q, "Exceptional"
            if q >= 70: return q, "Strong"
            if q >= 55: return q, "Moderate"
            if q >= 40: return q, "Developing"
            return q, "Needs Development"

        eq_s, eq_i = calc(cat_scores['EQ'])
        aq_s, aq_i = calc(cat_scores['AQ'])
        sq_s, sq_i = calc(cat_scores['SQ'])
        bq_s, bq_i = calc(cat_scores['BQ'])
        sub_pct = {k: round((sum(v)/(len(v)*5))*100, 1) for k, v in sub_scores.items()}
        overall = eq_s*0.30 + aq_s*0.25 + bq_s*0.25 + sq_s*0.20

        return {
            'overall_psychometric_score': round(overall, 1),
            'emotional_quotient': {'score': eq_s, 'interpretation': eq_i,
                'breakdown': {
                    'self_awareness': sub_pct.get('Self-Awareness',0),
                    'empathy': sub_pct.get('Empathy',0),
                    'emotion_regulation': sub_pct.get('Emotion Regulation',0),
                    'social_skills': sub_pct.get('Social Skills',0),
                    'motivation': sub_pct.get('Motivation',0)}},
            'adaptability_quotient': {'score': aq_s, 'interpretation': aq_i,
                'breakdown': {
                    'change_response': sub_pct.get('Change Response',0),
                    'ambiguity_tolerance': sub_pct.get('Ambiguity Tolerance',0),
                    'learning_agility': sub_pct.get('Learning Agility',0),
                    'resilience': sub_pct.get('Resilience',0),
                    'innovation_mindset': sub_pct.get('Innovation Mindset',0)}},
            'social_quotient': {'score': sq_s, 'interpretation': sq_i,
                'breakdown': {
                    'inclusion_expressed': sub_pct.get('Inclusion (Expressed)',0),
                    'inclusion_wanted': sub_pct.get('Inclusion (Wanted)',0),
                    'control_expressed': sub_pct.get('Control (Expressed)',0),
                    'affection_expressed': sub_pct.get('Affection (Expressed)',0),
                    'collaboration': sub_pct.get('Collaboration',0)}},
            'behavioral_quotient': {'score': bq_s, 'interpretation': bq_i,
                'breakdown': {
                    'conflict_resolution': sub_pct.get('Conflict Resolution',0),
                    'time_management': sub_pct.get('Time Management',0),
                    'initiative': sub_pct.get('Initiative',0),
                    'accountability': sub_pct.get('Accountability',0),
                    'decision_making': sub_pct.get('Decision Making',0)}},
            'metadata': {
                'total_questions': len(self.QUESTIONS),
                'questions_answered': len(self.responses),
                'completion_rate': round((len(self.responses)/len(self.QUESTIONS))*100, 1),
                'assessment_date': datetime.now().isoformat()}
        }

    def get_recommendations(self, quotients: Dict) -> Dict:
        """Strengths (>=70), Development (<55), Role fit based on overall"""
        r = {'strengths': [], 'development_areas': [], 'role_fit': []}
        eq = quotients['emotional_quotient']['score']
        aq = quotients['adaptability_quotient']['score']
        sq = quotients['social_quotient']['score']
        bq = quotients['behavioral_quotient']['score']
        if eq >= 70: r['strengths'].append("Strong emotional intelligence")
        if aq >= 70: r['strengths'].append("High adaptability")
        if sq >= 70: r['strengths'].append("Excellent social skills")
        if bq >= 70: r['strengths'].append("Strong behavioral competencies")
        if eq < 55: r['development_areas'].append("EQ: Practice active listening & self-reflection")
        if aq < 55: r['development_areas'].append("AQ: Seek diverse challenges")
        if sq < 55: r['development_areas'].append("SQ: Engage in more team activities")
        if bq < 55: r['development_areas'].append("BQ: Focus on proactive communication")
        overall = quotients['overall_psychometric_score']
        if overall >= 75:
            r['role_fit'] = ["Leadership", "Client-facing", "Cross-functional lead"]
        elif overall >= 60:
            r['role_fit'] = ["Team contributor", "Specialist", "Project member"]
        else:
            r['role_fit'] = ["Individual contributor", "Structured environments"]
        return r

    def export_to_json(self, quotients: Dict, recommendations: Dict) -> str:
        return json.dumps({
            'assessment_type': 'Hybrid Psychometric Assessment', 'version': '1.0',
            'responses': self.responses, 'quotients': quotients,
            'recommendations': recommendations,
            'export_timestamp': datetime.now().isoformat()
        }, indent=2)
```

---

## Tool 9 — `tools/interview_storage.py`

JSON file persistence for interview results.

```python
"""
Interview Results Storage — JSON file persistence
"""
import json, os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class InterviewStorage:
    """Manage JSON storage of interview results"""

    def __init__(self, base_dir: str = "interview_results"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def save_interview_result(self, candidate_id: str, interview_data: Dict,
                              scoring_data: Optional[Dict] = None) -> str:
        candidate_dir = self.base_dir / candidate_id
        candidate_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = candidate_dir / f"interview_{timestamp}.json"
        record = {
            'metadata': {'candidate_id': candidate_id, 'timestamp': timestamp,
                         'date': datetime.now().isoformat()},
            'interview_data': interview_data,
            'scoring': scoring_data or {},
            'psychometric_assessment': (scoring_data or {}).get('psychometric_results', {}),
            'psychometric_recommendations': (scoring_data or {}).get('psychometric_recommendations', {})
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        return str(filepath)

    def load_candidate_interviews(self, candidate_id: str) -> List[Dict]:
        candidate_dir = self.base_dir / candidate_id
        if not candidate_dir.exists(): return []
        interviews = []
        for jf in candidate_dir.glob("interview_*.json"):
            try:
                with open(jf, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['_filepath'] = str(jf)
                    interviews.append(data)
            except Exception:
                pass
        interviews.sort(key=lambda x: x['metadata']['timestamp'], reverse=True)
        return interviews

    def load_latest_interview(self, candidate_id: str) -> Optional[Dict]:
        interviews = self.load_candidate_interviews(candidate_id)
        return interviews[0] if interviews else None

    def get_all_candidates(self) -> List[str]:
        return sorted(
            item.name for item in self.base_dir.iterdir()
            if item.is_dir() and list(item.glob("interview_*.json"))
        )

    def get_candidate_summary(self, candidate_id: str) -> Dict:
        interviews = self.load_candidate_interviews(candidate_id)
        if not interviews:
            return {'candidate_id': candidate_id, 'total_interviews': 0,
                    'average_score': 0, 'highest_score': 0, 'latest_interview': None}
        scores = [i.get('scoring', {}).get('final_score', 0) for i in interviews if i.get('scoring', {}).get('final_score')]
        return {
            'candidate_id': candidate_id,
            'total_interviews': len(interviews),
            'average_score': sum(scores)/len(scores) if scores else 0,
            'highest_score': max(scores) if scores else 0,
            'latest_interview': interviews[0]['metadata']['date'],
            'problems_attempted': len({i['interview_data'].get('problem','Unknown') for i in interviews})
        }

    def export_all_results(self, output_file: str = "all_interviews.json") -> str:
        all_data = {cid: self.load_candidate_interviews(cid) for cid in self.get_all_candidates()}
        path = self.base_dir / output_file
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        return str(path)
```

---

## `tools/__init__.py`

```python
"""Tools layer — all reusable services and utilities"""
from tools.email_service import EmailService
from tools.code_executor import CodeExecutor
from tools.local_executor import LocalPythonExecutor
from tools.ai_code_analyzer import AICodeAnalyzer
from tools.technical_interview_chat import TechnicalInterviewChat
from tools.psychometric_assessment import PsychometricAssessment
from tools.interview_storage import InterviewStorage

# Optional heavy-dependency tools (video analysis)
try:
    from tools.video_analyzer import VideoConfidenceAnalyzer, analyze_candidate_video
    from tools.video_analyzer_hybrid import HybridVideoAnalyzer, analyze_candidate_video_ai
except ImportError:
    VideoConfidenceAnalyzer = None
    HybridVideoAnalyzer = None
    analyze_candidate_video = None
    analyze_candidate_video_ai = None
```

---

## ✅ Done Checklist

- [ ] `tools/__init__.py` created with all imports
- [ ] `tools/email_service.py` — `send_email()`, `send_leave_email()`, `send_test_result_email()`
- [ ] `tools/local_executor.py` — `execute_python()` with subprocess + timeout
- [ ] `tools/code_executor.py` — Judge0 API + local fallback + `run_test_cases()`
- [ ] `tools/ai_code_analyzer.py` — `analyze_code()`, `ask_followup_question()`, `evaluate_explanation()`
- [ ] `tools/video_analyzer.py` — copied verbatim from existing file (593 lines, optional deps)
- [ ] `tools/video_analyzer_hybrid.py` — Whisper transcription + LLM + 60/40 weighting
- [ ] `tools/technical_interview_chat.py` — 6 stages, dual-model, Socratic hints
- [ ] `tools/psychometric_assessment.py` — 20 questions, weighted scoring, recommendations
- [ ] `tools/interview_storage.py` — JSON file persistence, candidate summaries
- [ ] All imports updated to use `tools.` prefix and `core.config` constants
