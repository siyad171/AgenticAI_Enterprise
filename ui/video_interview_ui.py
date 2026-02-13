"""Video Interview UI — Video upload + hybrid analysis display"""
import streamlit as st
import os, tempfile
from tools.interview_storage import InterviewStorage
from tools import HYBRID_VIDEO_AVAILABLE


def show_video_interview():
    st.subheader("🎥 Video Interview")
    cand_id = st.session_state.get('current_candidate_id')

    if not HYBRID_VIDEO_AVAILABLE:
        st.warning("Video analysis requires additional dependencies. "
                   "Install: pip install opencv-python deepface librosa moviepy")
        st.info("You can skip this step.")
        if st.button("Skip → Complete Application", type="primary"):
            st.session_state.candidate_step = "complete"
            st.rerun()
        return

    st.write("Upload a short video (1-3 minutes) introducing yourself and "
             "explaining why you're interested in this role.")

    uploaded = st.file_uploader("Upload Video", type=["mp4", "avi", "mov", "webm"])

    if uploaded:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as f:
            f.write(uploaded.read())
            video_path = f.name

        st.video(uploaded)

        if st.button("🔍 Analyze Video", type="primary"):
            with st.spinner("Analyzing video... This may take a few minutes."):
                try:
                    from tools.video_analyzer_hybrid import HybridVideoAnalyzer
                    analyzer = HybridVideoAnalyzer()
                    result = analyzer.analyze(video_path)

                    if result.get('status') == 'success':
                        _show_video_results(result)

                        # Save results
                        storage = InterviewStorage()
                        storage.save_video_analysis(cand_id or "unknown", result)
                    else:
                        st.error(f"Analysis failed: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                finally:
                    try:
                        os.unlink(video_path)
                    except Exception:
                        pass

    st.divider()
    if st.button("Continue → Complete Application", type="primary"):
        st.session_state.candidate_step = "complete"
        st.rerun()


def _show_video_results(result):
    st.subheader("📊 Video Analysis Results")

    # Overall score
    overall = result.get('overall_confidence_score', 0)
    st.metric("Confidence Score", f"{overall:.1f}/10")

    # Score breakdown
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Heuristic Score:** {result.get('heuristic_score', 0):.1f}/10")
    with c2:
        st.write(f"**AI Communication:** {result.get('ai_communication_score', 0)}/100")

    # Breakdown
    breakdown = result.get('breakdown', {})
    if breakdown:
        st.subheader("Detailed Breakdown")
        cols = st.columns(2)
        metrics = [
            ("Eye Contact", breakdown.get('eye_contact_score', 0)),
            ("Smile Rate", breakdown.get('smile_score', 0)),
            ("Head Stability", breakdown.get('head_stability', 0)),
            ("Emotional Positivity", breakdown.get('emotional_positivity', 0)),
            ("Audio Confidence", breakdown.get('audio_score', 0)),
            ("Nervousness", breakdown.get('nervousness_score', 0)),
        ]
        for i, (label, val) in enumerate(metrics):
            with cols[i % 2]:
                st.write(f"**{label}:** {val:.1f}%")
                st.progress(min(val / 100, 1.0))

    # AI Feedback
    if result.get('ai_feedback'):
        st.subheader("🤖 AI Feedback")
        st.write(result['ai_feedback'])

    # Transcript
    if result.get('transcript'):
        with st.expander("📝 Transcript"):
            st.write(result['transcript'])
