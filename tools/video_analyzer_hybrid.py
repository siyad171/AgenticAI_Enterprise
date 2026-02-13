"""
Hybrid Video Analyzer — Heuristic + Groq AI transcript analysis
60% visual/audio heuristics + 40% AI communication scoring
"""
import os, json, re
from typing import Dict
from tools.video_analyzer import analyze_candidate_video

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class HybridVideoAnalyzer:
    """Combines heuristic video analysis with AI transcript analysis"""

    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

    def _extract_audio(self, video_path: str) -> str:
        if not MOVIEPY_AVAILABLE:
            return None
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
