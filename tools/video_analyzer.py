"""
Video Confidence Analyzer — DeepFace + SpeechBrain + OpenCV + librosa
Optional heavy-dependency tool for video interview confidence analysis.

Dependencies (install separately if needed):
    pip install opencv-python numpy librosa moviepy deepface speechbrain torchaudio
"""
import os
from typing import Dict

# Attempt to import heavy dependencies
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False


class VideoConfidenceAnalyzer:
    """
    Analyzes candidate video interviews for confidence indicators:
    - Facial emotion detection (DeepFace)
    - Eye contact estimation (OpenCV)
    - Head stability tracking
    - Audio analysis (pitch, energy, speech rate)
    - Nervousness detection
    """

    def __init__(self):
        self.available = OPENCV_AVAILABLE and DEEPFACE_AVAILABLE

    def analyze(self, video_path: str) -> Dict:
        """Full video analysis pipeline."""
        if not self.available:
            return {
                'status': 'error',
                'error': 'Video analysis dependencies not installed. '
                         'Install: pip install opencv-python deepface librosa moviepy',
                'overall_confidence_score': 0
            }

        if not os.path.exists(video_path):
            return {'status': 'error', 'error': f'Video not found: {video_path}',
                    'overall_confidence_score': 0}

        try:
            visual = self._analyze_visual(video_path)
            audio = self._analyze_audio(video_path)

            # Weighted scoring
            visual_score = self._calculate_visual_score(visual)
            audio_score = self._calculate_audio_score(audio)
            overall = visual_score * 0.6 + audio_score * 0.4

            return {
                'status': 'success',
                'overall_confidence_score': round(overall, 1),
                'confidence_score': round(overall, 1),
                'visual_analysis': visual,
                'audio_analysis': audio,
                'video_path': video_path
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'overall_confidence_score': 0}

    def _analyze_visual(self, video_path: str) -> Dict:
        """Analyze video frames for facial expressions and body language."""
        if not OPENCV_AVAILABLE:
            return self._default_visual()

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return self._default_visual()

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            sample_interval = max(1, int(fps))  # Sample ~1 frame per second

            emotions_detected = []
            eye_contact_frames = 0
            face_detected_frames = 0
            head_positions = []
            smile_frames = 0
            analyzed_frames = 0

            frame_idx = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % sample_interval == 0:
                    analyzed_frames += 1
                    try:
                        # DeepFace emotion analysis
                        if DEEPFACE_AVAILABLE:
                            results = DeepFace.analyze(frame, actions=['emotion'],
                                                       enforce_detection=False, silent=True)
                            if results:
                                result = results[0] if isinstance(results, list) else results
                                dominant = result.get('dominant_emotion', 'neutral')
                                emotions_detected.append(dominant)
                                face_detected_frames += 1

                                if dominant in ('happy', 'surprise'):
                                    smile_frames += 1

                                # Simple eye contact proxy: face detected and centered
                                region = result.get('region', {})
                                if region:
                                    face_center_x = region.get('x', 0) + region.get('w', 0) / 2
                                    frame_center_x = frame.shape[1] / 2
                                    if abs(face_center_x - frame_center_x) < frame.shape[1] * 0.25:
                                        eye_contact_frames += 1

                                    head_positions.append((region.get('x', 0), region.get('y', 0)))
                    except Exception:
                        pass

                frame_idx += 1

            cap.release()

            # Calculate metrics
            eye_contact_rate = (eye_contact_frames / max(analyzed_frames, 1)) * 100
            smile_rate = (smile_frames / max(analyzed_frames, 1)) * 100

            # Head stability (lower variance = more stable)
            head_stability = 100
            if len(head_positions) > 1:
                x_positions = [p[0] for p in head_positions]
                y_positions = [p[1] for p in head_positions]
                x_var = np.var(x_positions) if x_positions else 0
                y_var = np.var(y_positions) if y_positions else 0
                total_var = x_var + y_var
                head_stability = max(0, 100 - min(total_var / 10, 100))

            # Emotion distribution
            emotion_counts = {}
            for e in emotions_detected:
                emotion_counts[e] = emotion_counts.get(e, 0) + 1

            positive_emotions = sum(emotion_counts.get(e, 0) for e in ['happy', 'surprise', 'neutral'])
            emotional_positivity = (positive_emotions / max(len(emotions_detected), 1)) * 100

            # Nervousness indicators
            negative_emotions = sum(emotion_counts.get(e, 0) for e in ['fear', 'sad', 'angry', 'disgust'])
            nervousness = (negative_emotions / max(len(emotions_detected), 1)) * 100

            return {
                'frames_analyzed': analyzed_frames,
                'face_detection_rate': (face_detected_frames / max(analyzed_frames, 1)) * 100,
                'eye_contact_rate': round(eye_contact_rate, 1),
                'smile_rate': round(smile_rate, 1),
                'head_stability': round(head_stability, 1),
                'emotional_positivity': round(emotional_positivity, 1),
                'nervousness_indicators': round(nervousness, 1),
                'emotion_distribution': emotion_counts,
            }
        except Exception as e:
            print(f"Visual analysis error: {e}")
            return self._default_visual()

    def _analyze_audio(self, video_path: str) -> Dict:
        """Extract and analyze audio features."""
        if not LIBROSA_AVAILABLE or not MOVIEPY_AVAILABLE:
            return self._default_audio()

        try:
            # Extract audio
            video = VideoFileClip(video_path)
            audio_path = video_path.rsplit('.', 1)[0] + '_temp.wav'
            video.audio.write_audiofile(audio_path, verbose=False, logger=None)
            video.close()

            # Load with librosa
            y, sr = librosa.load(audio_path, sr=None)

            # Pitch analysis
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)

            pitch_mean = float(np.mean(pitch_values)) if pitch_values else 0
            pitch_var = float(np.var(pitch_values)) if pitch_values else 0

            # Energy / RMS
            rms = librosa.feature.rms(y=y)[0]
            energy_mean = float(np.mean(rms))

            # Speech rate (zero crossings as proxy)
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            speech_rate = float(np.mean(zcr)) * 100

            # Confidence score from audio
            pitch_score = min(pitch_var / 1000, 100) if pitch_var else 50
            energy_score = min(energy_mean * 1000, 100)
            audio_confidence = (pitch_score * 0.4 + energy_score * 0.4 + min(speech_rate, 100) * 0.2)

            # Cleanup
            try:
                os.remove(audio_path)
            except Exception:
                pass

            return {
                'pitch_mean': round(pitch_mean, 2),
                'pitch_variation': round(pitch_var, 2),
                'energy': round(energy_mean, 4),
                'speech_rate': round(speech_rate, 2),
                'confidence_score': round(audio_confidence, 1),
            }
        except Exception as e:
            print(f"Audio analysis error: {e}")
            return self._default_audio()

    def _calculate_visual_score(self, visual: Dict) -> float:
        """Weighted visual confidence score (0-10)."""
        eye = visual.get('eye_contact_rate', 50) / 100 * 10
        smile = visual.get('smile_rate', 20) / 100 * 10
        stability = visual.get('head_stability', 70) / 100 * 10
        positivity = visual.get('emotional_positivity', 60) / 100 * 10
        nervousness_penalty = visual.get('nervousness_indicators', 20) / 100 * 3
        return (eye * 0.3 + smile * 0.15 + stability * 0.2 + positivity * 0.35) - nervousness_penalty

    def _calculate_audio_score(self, audio: Dict) -> float:
        """Audio confidence score (0-10)."""
        return min(audio.get('confidence_score', 50) / 10, 10)

    def _default_visual(self) -> Dict:
        return {
            'frames_analyzed': 0, 'face_detection_rate': 0,
            'eye_contact_rate': 50, 'smile_rate': 20,
            'head_stability': 70, 'emotional_positivity': 60,
            'nervousness_indicators': 20, 'emotion_distribution': {},
        }

    def _default_audio(self) -> Dict:
        return {
            'pitch_mean': 0, 'pitch_variation': 0,
            'energy': 0, 'speech_rate': 0, 'confidence_score': 50,
        }


def analyze_candidate_video(video_path: str) -> Dict:
    """Convenience function for video analysis."""
    try:
        analyzer = VideoConfidenceAnalyzer()
        return analyzer.analyze(video_path)
    except Exception as e:
        return {'status': 'error', 'error': str(e),
                'overall_confidence_score': 0, 'confidence_score': 0}
