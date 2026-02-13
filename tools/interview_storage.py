"""
Interview Storage — JSON-based persistence for interview sessions
Stores candidate code, test results, chat transcripts, and assessment data.
"""
import os, json
from datetime import datetime
from typing import Dict, List, Optional
from core.config import INTERVIEW_RESULTS_DIR


class InterviewStorage:
    """
    Persistent storage for interview data:
    - Code submissions & test results
    - Interview chat transcripts
    - Video analysis results
    - Psychometric assessment results
    - Final consolidated reports
    """

    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or INTERVIEW_RESULTS_DIR
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_candidate_dir(self, candidate_id: str) -> str:
        path = os.path.join(self.storage_dir, str(candidate_id))
        os.makedirs(path, exist_ok=True)
        return path

    def _save_json(self, filepath: str, data: dict):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

    def _load_json(self, filepath: str) -> dict:
        if not os.path.exists(filepath):
            return {}
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    # ── Code Submissions ──────────────────────────────────────────
    def save_code_submission(self, candidate_id: str, problem_id: str,
                             code: str, language: str, test_results: List[Dict]) -> Dict:
        cdir = self._get_candidate_dir(candidate_id)
        submissions_file = os.path.join(cdir, 'code_submissions.json')
        submissions = self._load_json(submissions_file)
        if 'submissions' not in submissions:
            submissions = {'candidate_id': candidate_id, 'submissions': []}

        entry = {
            'submission_id': f"SUB_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'problem_id': problem_id, 'language': language,
            'code': code, 'test_results': test_results,
            'passed': sum(1 for t in test_results if t.get('status') == 'passed'),
            'total': len(test_results),
            'timestamp': datetime.now().isoformat()
        }
        submissions['submissions'].append(entry)
        self._save_json(submissions_file, submissions)
        return entry

    def get_code_submissions(self, candidate_id: str) -> List[Dict]:
        cdir = self._get_candidate_dir(candidate_id)
        data = self._load_json(os.path.join(cdir, 'code_submissions.json'))
        return data.get('submissions', [])

    # ── Interview Chat ────────────────────────────────────────────
    def save_interview_chat(self, candidate_id: str, problem_id: str,
                            conversation: List[Dict], report: Dict) -> Dict:
        cdir = self._get_candidate_dir(candidate_id)
        chat_file = os.path.join(cdir, 'interview_chats.json')
        chats = self._load_json(chat_file)
        if 'chats' not in chats:
            chats = {'candidate_id': candidate_id, 'chats': []}

        entry = {
            'chat_id': f"CHAT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'problem_id': problem_id,
            'conversation': conversation, 'report': report,
            'message_count': len(conversation),
            'timestamp': datetime.now().isoformat()
        }
        chats['chats'].append(entry)
        self._save_json(chat_file, chats)
        return entry

    def get_interview_chats(self, candidate_id: str) -> List[Dict]:
        cdir = self._get_candidate_dir(candidate_id)
        data = self._load_json(os.path.join(cdir, 'interview_chats.json'))
        return data.get('chats', [])

    # ── Video Analysis ────────────────────────────────────────────
    def save_video_analysis(self, candidate_id: str, analysis_result: Dict) -> Dict:
        cdir = self._get_candidate_dir(candidate_id)
        video_file = os.path.join(cdir, 'video_analysis.json')
        data = self._load_json(video_file)
        if 'analyses' not in data:
            data = {'candidate_id': candidate_id, 'analyses': []}

        entry = {
            'analysis_id': f"VID_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            **analysis_result,
            'timestamp': datetime.now().isoformat()
        }
        data['analyses'].append(entry)
        self._save_json(video_file, data)
        return entry

    def get_video_analyses(self, candidate_id: str) -> List[Dict]:
        cdir = self._get_candidate_dir(candidate_id)
        data = self._load_json(os.path.join(cdir, 'video_analysis.json'))
        return data.get('analyses', [])

    # ── Psychometric Assessment ───────────────────────────────────
    def save_psychometric_results(self, candidate_id: str, results: Dict) -> Dict:
        cdir = self._get_candidate_dir(candidate_id)
        psych_file = os.path.join(cdir, 'psychometric_results.json')
        data = self._load_json(psych_file)
        if 'assessments' not in data:
            data = {'candidate_id': candidate_id, 'assessments': []}

        entry = {
            'assessment_id': f"PSY_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            **results,
            'timestamp': datetime.now().isoformat()
        }
        data['assessments'].append(entry)
        self._save_json(psych_file, data)
        return entry

    def get_psychometric_results(self, candidate_id: str) -> List[Dict]:
        cdir = self._get_candidate_dir(candidate_id)
        data = self._load_json(os.path.join(cdir, 'psychometric_results.json'))
        return data.get('assessments', [])

    # ── Final Report ──────────────────────────────────────────────
    def save_final_report(self, candidate_id: str, report: Dict) -> Dict:
        cdir = self._get_candidate_dir(candidate_id)
        report_file = os.path.join(cdir, 'final_report.json')
        report_data = {
            'candidate_id': candidate_id,
            'report_id': f"RPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            **report,
            'generated_at': datetime.now().isoformat()
        }
        self._save_json(report_file, report_data)
        return report_data

    def get_final_report(self, candidate_id: str) -> Dict:
        cdir = self._get_candidate_dir(candidate_id)
        return self._load_json(os.path.join(cdir, 'final_report.json'))

    # ── Candidate Summary ─────────────────────────────────────────
    def get_candidate_summary(self, candidate_id: str) -> Dict:
        return {
            'candidate_id': candidate_id,
            'code_submissions': len(self.get_code_submissions(candidate_id)),
            'interview_chats': len(self.get_interview_chats(candidate_id)),
            'video_analyses': len(self.get_video_analyses(candidate_id)),
            'psychometric_assessments': len(self.get_psychometric_results(candidate_id)),
            'has_final_report': bool(self.get_final_report(candidate_id)),
        }

    def list_all_candidates(self) -> List[str]:
        if not os.path.exists(self.storage_dir):
            return []
        return [d for d in os.listdir(self.storage_dir)
                if os.path.isdir(os.path.join(self.storage_dir, d))]
