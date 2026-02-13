"""Results Viewer UI — Browse all interview results"""
import streamlit as st
from tools.interview_storage import InterviewStorage


def show_candidate_results(candidate_id: str):
    """Show interview results for a specific candidate (inline in admin portal)"""
    storage = InterviewStorage()
    summary = storage.get_candidate_summary(candidate_id)

    if summary['code_submissions'] == 0 and summary['interview_chats'] == 0 and \
       summary['psychometric_assessments'] == 0 and summary['video_analyses'] == 0:
        st.caption("No interview data yet")
        return

    st.markdown("**Interview Results:**")

    # Code submissions
    if summary['code_submissions'] > 0:
        submissions = storage.get_code_submissions(candidate_id)
        with st.expander(f"💻 Code Submissions ({len(submissions)})"):
            for sub in submissions:
                st.write(f"**Problem:** {sub.get('problem_id', 'N/A')} | "
                         f"**Language:** {sub.get('language', 'N/A')} | "
                         f"**Passed:** {sub.get('passed', 0)}/{sub.get('total', 0)}")
                with st.expander("View Code"):
                    st.code(sub.get('code', ''), language=sub.get('language', 'python'))

    # Interview chats
    if summary['interview_chats'] > 0:
        chats = storage.get_interview_chats(candidate_id)
        with st.expander(f"💬 Interview Chats ({len(chats)})"):
            for chat in chats:
                report = chat.get('report', {})
                st.write(f"**Problem:** {chat.get('problem_id', 'N/A')} | "
                         f"**Messages:** {chat.get('message_count', 0)}")
                if report:
                    st.write(f"Approach: {report.get('approach_quality', 'N/A')}/100 | "
                             f"Communication: {report.get('communication_score', 'N/A')}/100")

    # Psychometric
    if summary['psychometric_assessments'] > 0:
        psych = storage.get_psychometric_results(candidate_id)
        with st.expander(f"🧠 Psychometric ({len(psych)})"):
            for p in psych:
                st.write(f"**Overall Score:** {p.get('overall_score', 'N/A')}/100")
                dims = p.get('dimensions', {})
                for dim_name, dim_data in dims.items():
                    if isinstance(dim_data, dict):
                        st.write(f"  • {dim_name}: {dim_data.get('percentage', 0):.0f}%")

    # Video analysis
    if summary['video_analyses'] > 0:
        videos = storage.get_video_analyses(candidate_id)
        with st.expander(f"🎥 Video Analysis ({len(videos)})"):
            for v in videos:
                st.write(f"**Confidence:** {v.get('overall_confidence_score', 'N/A')}/10")
                if v.get('ai_feedback'):
                    st.write(f"**Feedback:** {v['ai_feedback']}")


def show_results_browser():
    """Standalone results browser page"""
    st.header("📊 Interview Results Browser")
    storage = InterviewStorage()
    candidates = storage.list_all_candidates()

    if not candidates:
        st.info("No interview data yet")
        return

    selected = st.selectbox("Select Candidate", candidates)
    if selected:
        show_candidate_results(selected)

        # Final report
        report = storage.get_final_report(selected)
        if report:
            with st.expander("📋 Final Report"):
                st.json(report)
