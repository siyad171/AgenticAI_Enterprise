"""
Video Interview UI — WebRTC live recording + Groq AI evaluation

Flow: Camera preview → Record (~30s) → AI Analysis → Results
Add more entries to VIDEO_QUESTIONS to scale to multiple questions.

Dependencies (required):
    pip install streamlit-webrtc numpy opencv-python
Optional (emotion analysis):
    pip install deepface
"""

import streamlit as st
import streamlit.components.v1 as components
import os, json, wave, time, threading
import numpy as np
from datetime import datetime
from typing import List, Dict

# ── Optional imports (graceful fallback) ──────────────────────
try:
    from streamlit_webrtc import webrtc_streamer, WebRtcMode
    import av
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False

from groq import Groq
from core.config import GROQ_API_KEY, LLM_WHISPER_MODEL, LLM_ANALYSIS_MODEL
from tools.interview_storage import InterviewStorage


# ═══════════════════════════════════════════════════════════════
# QUESTIONS — add more entries here to scale the interview
# ═══════════════════════════════════════════════════════════════
VIDEO_QUESTIONS = [
    {
        "id": "VQ_01",
        "type": "behavioral",
        "question": (
            "Tell us about yourself and explain why you're "
            "interested in this role."
        ),
        "time_limit": 30,  # seconds (recommendation shown to candidate)
        "criteria": ["communication", "enthusiasm", "relevance", "clarity"],
    },
    # ── Uncomment / add more entries to scale ────────────
    # {
    #     "id": "VQ_02",
    #     "type": "behavioral",
    #     "question": "Describe a challenging situation you faced and how you handled it.",
    #     "time_limit": 30,
    #     "criteria": ["problem_solving", "communication", "resilience"],
    # },
    # {
    #     "id": "VQ_03",
    #     "type": "behavioral",
    #     "question": "What are your greatest strengths and how would they benefit our team?",
    #     "time_limit": 30,
    #     "criteria": ["self_awareness", "relevance", "confidence"],
    # },
]


# ═══════════════════════════════════════════════════════════════
# Thread-safe Frame Recorder
# ═══════════════════════════════════════════════════════════════
class FrameRecorder:
    """Buffers audio (numpy) and video (numpy) from WebRTC callbacks.
    All data is stored as self-contained numpy arrays so it survives
    even after the WebRTC component unmounts."""

    def __init__(self):
        self._lock = threading.Lock()
        self.audio_chunks: List[np.ndarray] = []
        self.sampled_frames: List[np.ndarray] = []   # ~1 fps for emotion analysis
        self.all_frames: List[np.ndarray] = []        # every frame for video file
        self.recording = False
        self.sample_rate = 48000
        self._vcount = 0

    def start(self):
        with self._lock:
            self.audio_chunks.clear()
            self.sampled_frames.clear()
            self.all_frames.clear()
            self._vcount = 0
            self.recording = True

    def stop(self):
        with self._lock:
            self.recording = False

    # ── Callbacks (run on WebRTC I/O thread) ──────────────
    def video_cb(self, frame):
        if self.recording:
            img = frame.to_ndarray(format="bgr24")
            with self._lock:
                self.all_frames.append(img)
                self._vcount += 1
                # Sample ~1 frame per second for emotion analysis
                if self._vcount % 30 == 0 and len(self.sampled_frames) < 120:
                    self.sampled_frames.append(img.copy())
        return frame

    def audio_cb(self, frame):
        if self.recording:
            nd = frame.to_ndarray().flatten()
            with self._lock:
                self.audio_chunks.append(nd)
                self.sample_rate = frame.sample_rate
        # Return silent frame so browser doesn't play audio back (no echo)
        silent = av.AudioFrame.from_ndarray(
            np.zeros_like(frame.to_ndarray()), layout=frame.layout.name
        )
        silent.sample_rate = frame.sample_rate
        return silent

    # ── Save helpers ──────────────────────────────────────
    def save_audio_wav(self, path: str) -> bool:
        """Write buffered audio as a mono 16-bit WAV file."""
        with self._lock:
            chunks = list(self.audio_chunks)
            sr = self.sample_rate
        if not chunks:
            return False
        try:
            raw = np.concatenate(chunks)
            # Convert float → int16 if needed
            if raw.dtype in (np.float32, np.float64):
                raw = np.clip(raw, -1.0, 1.0)
                raw = (raw * 32767).astype(np.int16)
            else:
                raw = raw.astype(np.int16)
            with wave.open(path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(raw.tobytes())
            return True
        except Exception as e:
            print(f"[VideoInterview] Audio save error: {e}")
            return False

    def save_video_file(self, path: str, duration: float) -> bool:
        """Write buffered frames as a MJPG AVI file."""
        if not OPENCV_AVAILABLE:
            return False
        with self._lock:
            frames = list(self.all_frames)
        if not frames:
            return False
        try:
            fps = max(1, int(len(frames) / max(duration, 1)))
            fps = min(fps, 30)
            h, w = frames[0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            writer = cv2.VideoWriter(path, fourcc, fps, (w, h))
            if not writer.isOpened():
                return False
            for f in frames:
                writer.write(f)
            writer.release()
            return True
        except Exception as e:
            print(f"[VideoInterview] Video save error: {e}")
            return False

    @property
    def has_audio(self):
        with self._lock:
            return len(self.audio_chunks) > 0

    @property
    def has_video(self):
        with self._lock:
            return len(self.all_frames) > 0


# ═══════════════════════════════════════════════════════════════
# Analysis helpers
# ═══════════════════════════════════════════════════════════════

def _transcribe(audio_path: str) -> str:
    """Transcribe audio using Groq Whisper (free)."""
    try:
        client = Groq(api_key=GROQ_API_KEY)
        with open(audio_path, "rb") as f:
            resp = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), f.read()),
                model=LLM_WHISPER_MODEL,
                response_format="json",
                language="en",
                temperature=0.0,
            )
        return resp.text.strip()
    except Exception as e:
        return f"[Transcription failed: {e}]"


def _emotion_analysis(frames: List[np.ndarray]) -> Dict:
    """Run DeepFace emotion detection on sampled frames (optional)."""
    if not DEEPFACE_AVAILABLE or not frames:
        return {"available": False}

    emotion_counts: Dict[str, int] = {}
    timeline = []
    for i, frame in enumerate(frames):
        try:
            res = DeepFace.analyze(
                frame, actions=["emotion"],
                enforce_detection=False, silent=True,
            )
            if res:
                r = res[0] if isinstance(res, list) else res
                dom = r.get("dominant_emotion", "neutral")
                emotion_counts[dom] = emotion_counts.get(dom, 0) + 1
                timeline.append({
                    "second": i + 1, "emotion": dom,
                    "scores": r.get("emotion", {}),
                })
        except Exception:
            pass

    total = max(len(timeline), 1)
    pos = sum(emotion_counts.get(e, 0) for e in ("happy", "surprise", "neutral"))
    neg = sum(emotion_counts.get(e, 0) for e in ("fear", "sad", "angry", "disgust"))
    return {
        "available": True,
        "timeline": timeline,
        "distribution": emotion_counts,
        "positivity": round(pos / total * 100, 1),
        "nervousness": round(neg / total * 100, 1),
        "confidence": round(pos / total * 100, 1),
        "frames_analyzed": len(timeline),
    }


def _llm_evaluate(question: str, transcript: str, criteria: List[str]) -> Dict:
    """Use Groq LLM to evaluate the candidate's spoken answer."""
    if not transcript or len(transcript.strip()) < 10:
        return {
            "overall_score": 0,
            "feedback": "No speech detected or response was too short.",
            "recommendation": "Retry",
            "criteria_scores": {c: 0 for c in criteria},
        }

    crit_json = ", ".join(f'"{c}": <0-100>' for c in criteria)
    prompt = (
        "You are an expert HR interviewer evaluating a candidate's video "
        "interview response.\n\n"
        f'Question: "{question}"\n'
        f'Candidate transcript: "{transcript}"\n\n'
        "Evaluate:\n"
        f"1. criteria_scores (JSON object): {{{crit_json}}}\n"
        "2. overall_score: integer 0-100\n"
        "3. feedback: 2-3 sentences of constructive feedback\n"
        '4. recommendation: one of "Strong Hire", "Hire", "Maybe", "No Hire"\n\n'
        "Respond with ONLY valid JSON, no extra text."
    )
    try:
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Expert HR interviewer. Return JSON only."},
                {"role": "user", "content": prompt},
            ],
            model=LLM_ANALYSIS_MODEL,
            temperature=0.3,
            max_tokens=500,
        )
        text = resp.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as e:
        return {
            "overall_score": 50,
            "feedback": f"AI evaluation error: {e}",
            "recommendation": "Manual Review",
            "criteria_scores": {c: 50 for c in criteria},
        }


# ═══════════════════════════════════════════════════════════════
# File helpers
# ═══════════════════════════════════════════════════════════════

def _save_dir(candidate_id: str) -> str:
    """Ensure data/video_interviews/{candidate_id}/ exists and return path."""
    base = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data", "video_interviews",
    )
    d = os.path.join(base, candidate_id or "unknown")
    os.makedirs(d, exist_ok=True)
    return d


# ═══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def show_video_interview():
    st.subheader("🎥 Video Interview")

    # ── WebRTC not installed fallback ─────────────────────
    if not WEBRTC_AVAILABLE:
        st.warning(
            "⚠️ Video interview requires additional packages.\n\n"
            "Run: `pip install streamlit-webrtc numpy opencv-python`"
        )
        _show_text_fallback()
        return

    cand_id = st.session_state.get("current_candidate_id", "unknown")
    total_q = len(VIDEO_QUESTIONS)

    # ── Session state defaults ────────────────────────────
    defaults = {
        "vi_step": "interview",    # interview → processing → results → done
        "vi_q_idx": 0,
        "vi_results": [],
        "vi_rec_start": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    if "frame_recorder" not in st.session_state:
        st.session_state.frame_recorder = FrameRecorder()

    recorder = st.session_state.frame_recorder
    q_idx = st.session_state.vi_q_idx
    step = st.session_state.vi_step

    # ── All questions answered ────────────────────────────
    if step == "done" or q_idx >= total_q:
        _show_final_summary(cand_id)
        return

    q = VIDEO_QUESTIONS[q_idx]
    st.progress(q_idx / total_q, text=f"Question {q_idx + 1} / {total_q}")

    if step == "interview":
        _show_interview_room(q, recorder)
    elif step == "processing":
        _show_processing(q, recorder, cand_id)
    elif step == "results":
        _show_question_results()


# ═══════════════════════════════════════════════════════════════
# Interview Room (camera preview + recording)
# ═══════════════════════════════════════════════════════════════

def _show_interview_room(q, recorder):
    is_recording = recorder.recording

    st.markdown(f"### 🎤 Question {st.session_state.vi_q_idx + 1}")
    st.info(f"**{q['question']}**")

    if not is_recording:
        st.caption(
            f"📷 Camera preview — position yourself in frame, "
            f"then click **Start Recording** (~{q['time_limit']}s recommended)"
        )
    else:
        # Real-time JavaScript timer (runs client-side, no reruns needed)
        components.html("""
        <div style="text-align:center; padding:8px 0;">
            <span id="vi-timer"
                  style="font-size:1.4em; font-weight:bold; color:#e74c3c;">
                &#128308; Recording: 0:00
            </span>
        </div>
        <script>
        var start = Date.now();
        setInterval(function(){
            var s = Math.floor((Date.now()-start)/1000);
            document.getElementById('vi-timer').innerText =
                '\\u{1F534} Recording: ' +
                Math.floor(s/60) + ':' + String(s%60).padStart(2,'0');
        }, 500);
        </script>
        """, height=55)

    # ── WebRTC component (SENDRECV shows video preview; audio muted via silent return)
    webrtc_streamer(
        key="vi_camera",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        },
        media_stream_constraints={"video": True, "audio": True},
        video_frame_callback=recorder.video_cb,
        audio_frame_callback=recorder.audio_cb,
    )

    # ── Controls ──────────────────────────────────────────
    c1, c2, c3 = st.columns(3)

    if not is_recording:
        with c1:
            if st.button("🔴 Start Recording", type="primary",
                         use_container_width=True):
                recorder.start()
                st.session_state.vi_rec_start = time.time()
                st.rerun()
        with c3:
            if st.button("⏭️ Skip Video Interview",
                         use_container_width=True):
                st.session_state.candidate_step = "complete"
                st.rerun()
    else:
        with c1:
            if st.button("⏹️ Stop & Submit", type="primary",
                         use_container_width=True):
                recorder.stop()
                st.session_state.vi_step = "processing"
                st.rerun()
        with c2:
            st.caption(f"Recommended: ~{q['time_limit']}s")


# ═══════════════════════════════════════════════════════════════
# Processing (save files → transcribe → analyze → evaluate)
# ═══════════════════════════════════════════════════════════════

def _show_processing(q, recorder, cand_id):
    if not recorder.has_audio and not recorder.has_video:
        st.warning("⚠️ No recording detected — camera/mic may not have "
                   "been allowed. Please try again.")
        if st.button("← Try Again"):
            st.session_state.vi_step = "interview"
            st.session_state.frame_recorder = FrameRecorder()
            st.rerun()
        return

    save_path = _save_dir(cand_id)
    q_num = st.session_state.vi_q_idx + 1
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rec_duration = time.time() - (st.session_state.vi_rec_start or time.time())

    progress = st.progress(0, text="Processing recording...")
    result: Dict = {"question": q["question"], "question_id": q["id"]}

    # 1 — Save audio WAV
    progress.progress(10, text="💾 Saving audio...")
    wav_path = os.path.join(save_path, f"q{q_num}_{ts}.wav")
    audio_saved = recorder.save_audio_wav(wav_path)
    result["audio_file"] = wav_path if audio_saved else None

    # 2 — Save video AVI
    progress.progress(25, text="💾 Saving video...")
    vid_path = os.path.join(save_path, f"q{q_num}_{ts}.avi")
    video_saved = recorder.save_video_file(vid_path, rec_duration)
    result["video_file"] = vid_path if video_saved else None
    result["duration_seconds"] = round(rec_duration, 1)

    # 3 — Transcribe with Groq Whisper
    progress.progress(40, text="🎙️ Transcribing audio (Groq Whisper)...")
    transcript = ""
    if audio_saved:
        transcript = _transcribe(wav_path)
    result["transcript"] = transcript

    # 4 — Emotion analysis (if DeepFace installed)
    progress.progress(60, text="🧠 Analyzing emotions...")
    with recorder._lock:
        sampled = list(recorder.sampled_frames)
    emotions = _emotion_analysis(sampled)
    result["emotions"] = emotions

    # 5 — LLM answer evaluation
    progress.progress(80, text="🤖 Evaluating response...")
    evaluation = _llm_evaluate(q["question"], transcript, q["criteria"])
    result["evaluation"] = evaluation

    # 6 — Compute final score (70% LLM + 30% emotion if available)
    llm_score = evaluation.get("overall_score", 0)
    emo_score = emotions.get("confidence") if emotions.get("available") else None
    if emo_score is not None:
        result["final_score"] = round(llm_score * 0.7 + emo_score * 0.3, 1)
    else:
        result["final_score"] = llm_score
    result["recommendation"] = evaluation.get("recommendation", "N/A")
    result["timestamp"] = datetime.now().isoformat()

    # 7 — Save JSON result
    progress.progress(90, text="💾 Saving results...")
    result_path = os.path.join(save_path, f"q{q_num}_{ts}_result.json")
    with open(result_path, "w", encoding="utf-8") as f:
        # Make numpy floats JSON-serializable
        serialisable = {k: v for k, v in result.items()}
        if "emotions" in serialisable and serialisable["emotions"].get("available"):
            tl = serialisable["emotions"].get("timeline", [])
            for item in tl:
                scores = item.get("scores", {})
                item["scores"] = {k: round(float(v), 2) for k, v in scores.items()}
        json.dump(serialisable, f, indent=2, default=str)
    result["result_file"] = result_path

    # Also persist via InterviewStorage
    try:
        storage = InterviewStorage()
        storage.save_video_analysis(cand_id, result)
    except Exception:
        pass

    progress.progress(100, text="✅ Analysis complete!")
    time.sleep(0.5)

    # Store and advance
    st.session_state.vi_results.append(result)
    st.session_state.vi_current_result = result
    st.session_state.vi_step = "results"
    st.session_state.frame_recorder = FrameRecorder()  # free memory
    st.rerun()


# ═══════════════════════════════════════════════════════════════
# Results display
# ═══════════════════════════════════════════════════════════════

def _show_question_results():
    result = st.session_state.get("vi_current_result", {})
    if not result:
        st.session_state.vi_step = "interview"
        st.rerun()
        return

    q_num = st.session_state.vi_q_idx + 1
    st.markdown(f"### 📊 Results — Question {q_num}")

    # ── Top-level metrics ─────────────────────────────────
    c1, c2, c3 = st.columns(3)
    c1.metric("Overall Score", f"{result.get('final_score', 0)}/100")
    c2.metric("Recommendation", result.get("recommendation", "N/A"))
    c3.metric("Duration", f"{result.get('duration_seconds', 0)}s")

    # ── Criteria breakdown ────────────────────────────────
    eval_data = result.get("evaluation", {})
    criteria_scores = eval_data.get("criteria_scores", {})
    if criteria_scores:
        st.markdown("#### Criteria Scores")
        cols = st.columns(min(len(criteria_scores), 4))
        for i, (crit, score) in enumerate(criteria_scores.items()):
            with cols[i % len(cols)]:
                label = crit.replace("_", " ").title()
                st.metric(label, f"{score}/100")
                st.progress(min(int(score), 100) / 100)

    # ── AI Feedback ───────────────────────────────────────
    feedback = eval_data.get("feedback", "")
    if feedback:
        st.markdown("#### 🤖 AI Feedback")
        st.success(feedback)

    # ── Transcript ────────────────────────────────────────
    transcript = result.get("transcript", "")
    if transcript:
        with st.expander("📝 Transcript", expanded=False):
            st.write(transcript)

    # ── Emotion analysis ──────────────────────────────────
    emotions = result.get("emotions", {})
    if emotions.get("available"):
        with st.expander("🧠 Emotion Analysis", expanded=False):
            ec1, ec2, ec3 = st.columns(3)
            ec1.metric("Positivity", f"{emotions.get('positivity', 0)}%")
            ec2.metric("Nervousness", f"{emotions.get('nervousness', 0)}%")
            ec3.metric("Frames Analyzed", emotions.get("frames_analyzed", 0))
            dist = emotions.get("distribution", {})
            if dist:
                st.markdown("**Emotion distribution:**")
                for emo, count in sorted(dist.items(), key=lambda x: -x[1]):
                    pct = count / max(emotions.get("frames_analyzed", 1), 1) * 100
                    st.write(f"- **{emo}**: {pct:.0f}%")
    elif not DEEPFACE_AVAILABLE:
        st.caption("💡 Install `deepface` for facial emotion analysis.")

    # ── Saved files ───────────────────────────────────────
    with st.expander("📁 Saved Files", expanded=False):
        for label, key in [("🔊 Audio", "audio_file"),
                           ("🎬 Video", "video_file"),
                           ("📄 Results", "result_file")]:
            path = result.get(key)
            if path and os.path.exists(path):
                st.write(f"{label}: `{path}`")

    st.divider()

    # ── Next question or continue ─────────────────────────
    total_q = len(VIDEO_QUESTIONS)
    next_idx = st.session_state.vi_q_idx + 1

    if next_idx < total_q:
        if st.button(f"➡️ Next Question ({next_idx + 1}/{total_q})",
                     type="primary", use_container_width=True):
            st.session_state.vi_q_idx = next_idx
            st.session_state.vi_step = "interview"
            st.rerun()
    else:
        if st.button("✅ Continue → Complete Application",
                     type="primary", use_container_width=True):
            st.session_state.vi_step = "done"
            st.rerun()


# ═══════════════════════════════════════════════════════════════
# Final summary (all questions answered)
# ═══════════════════════════════════════════════════════════════

def _show_final_summary(cand_id):
    results = st.session_state.get("vi_results", [])

    if not results:
        st.info("No video interview results recorded.")
    else:
        st.markdown("### 🎬 Video Interview — Summary")
        avg = sum(r.get("final_score", 0) for r in results) / len(results)
        st.metric("Average Score", f"{avg:.0f}/100")

        for i, r in enumerate(results):
            with st.expander(f"Q{i + 1}: {r.get('question', '')}", expanded=False):
                st.write(f"**Score:** {r.get('final_score', 0)}/100")
                st.write(f"**Recommendation:** {r.get('recommendation', 'N/A')}")
                st.write(f"**Duration:** {r.get('duration_seconds', 0)}s")
                if r.get("transcript"):
                    st.write(f"**Transcript:** {r['transcript']}")

    st.divider()
    if st.button("✅ Complete Application", type="primary",
                 use_container_width=True):
        st.session_state.candidate_step = "complete"
        st.rerun()


# ═══════════════════════════════════════════════════════════════
# Text fallback (when WebRTC is not available)
# ═══════════════════════════════════════════════════════════════

def _show_text_fallback():
    """Text-based interview when WebRTC / camera not available."""
    st.markdown("---")
    st.markdown("### 📝 Text-Based Alternative")

    q = VIDEO_QUESTIONS[0]
    st.info(f"**{q['question']}**")

    answer = st.text_area(
        "Type your response:",
        height=150,
        placeholder="Type your answer here...",
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Submit Answer", type="primary") and answer.strip():
            with st.spinner("Evaluating your response..."):
                evaluation = _llm_evaluate(q["question"], answer, q["criteria"])
                st.session_state.vi_results = [{
                    "question": q["question"],
                    "transcript": answer,
                    "evaluation": evaluation,
                    "final_score": evaluation.get("overall_score", 0),
                    "recommendation": evaluation.get("recommendation", "N/A"),
                    "duration_seconds": 0,
                    "emotions": {"available": False},
                    "timestamp": datetime.now().isoformat(),
                }]
                st.session_state.vi_step = "done"
                st.session_state.vi_q_idx = len(VIDEO_QUESTIONS)
                st.rerun()
    with c2:
        if st.button("⏭️ Skip Video Interview"):
            st.session_state.candidate_step = "complete"
            st.rerun()
