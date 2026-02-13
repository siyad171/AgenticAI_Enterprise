"""
Code Execution Service — Judge0 API Integration with Local Fallback
"""
import requests
import time
import base64
import os
from typing import Dict, List
from dotenv import load_dotenv
from tools.local_executor import LocalPythonExecutor

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
                    'input': tc.get('input', ''), 'expected': expected,
                    'actual': actual, 'error': result.get('error', ''),
                    'time': result.get('time', 0), 'memory': result.get('memory', 0)
                })
            else:
                results['test_results'].append({
                    'test_number': i+1, 'status': status,
                    'input': 'Hidden', 'expected': 'Hidden',
                    'actual': 'Hidden' if status != 'passed' else expected,
                    'error': result.get('error', '') if status == 'error' else '',
                    'time': result.get('time', 0), 'memory': result.get('memory', 0),
                    'hidden': True
                })
        results['all_passed'] = (results['passed'] == results['total'])
        return results

    @staticmethod
    def _compare_outputs(actual: str, expected: str) -> bool:
        if actual == expected:
            return True
        def normalize(s):
            s = s.replace('[', '').replace(']', '').replace('(', '').replace(')', '')
            s = s.replace(',', ' ').replace('\t', ' ')
            return ' '.join(s.split())
        return normalize(actual) == normalize(expected)
