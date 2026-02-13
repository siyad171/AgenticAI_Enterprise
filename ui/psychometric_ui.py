"""Psychometric Assessment UI — 20 questions with results visualization"""
import streamlit as st
from tools.psychometric_assessment import PsychometricAssessment
from tools.interview_storage import InterviewStorage


def show_psychometric_assessment():
    st.subheader("🧠 Psychometric Assessment")
    st.write("Answer 20 scenario-based questions. Choose the response that best reflects "
             "how you would actually behave, not what you think is the 'right' answer.")

    cand_id = st.session_state.get('current_candidate_id')

    # Initialize assessment
    if 'psychometric' not in st.session_state:
        st.session_state.psychometric = PsychometricAssessment()

    assessment = st.session_state.psychometric
    questions = assessment.get_questions()

    # Dimension descriptions
    with st.expander("ℹ️ What are we measuring?"):
        for dim, desc in assessment.get_dimension_descriptions().items():
            st.write(f"**{dim}:** {desc}")

    # Question form
    with st.form("psychometric_form"):
        for q in questions:
            st.markdown(f"---\n**Q{q['id']}.** _{q['category']}_ — {q['scenario']}")
            option_texts = [opt['text'] for opt in q['options']]
            selected = st.radio("Choose:", option_texts,
                                key=f"psych_{q['id']}", index=None)
            if selected:
                idx = option_texts.index(selected)
                assessment.submit_answer(q['id'], idx)

        submit = st.form_submit_button("Submit Assessment", type="primary")

        if submit:
            results = assessment.calculate_results()
            if results['status'] == 'incomplete':
                st.error(f"Please answer all questions ({results['answered']}/{results['total']})")
            else:
                st.session_state.psychometric_results = results
                st.rerun()

    # Show results
    if 'psychometric_results' in st.session_state:
        results = st.session_state.psychometric_results
        _show_results(results)

        # Save and proceed
        if st.button("Continue →", type="primary"):
            storage = InterviewStorage()
            storage.save_psychometric_results(cand_id or "unknown", results)

            st.session_state.candidate_step = "video_interview"
            st.session_state.pop('psychometric', None)
            st.session_state.pop('psychometric_results', None)
            st.rerun()


def _show_results(results):
    st.divider()
    st.subheader("📊 Your Results")

    # Overall score
    overall = results.get('overall_score', 0)
    st.metric("Overall Score", f"{overall:.1f}/100")

    # Dimension scores
    dims = results.get('dimensions', {})
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        eq = dims.get('emotional_quotient', {})
        st.markdown(f"""
        <div class="metric-card metric-card-blue">
            <h3>{eq.get('percentage', 0):.0f}%</h3>
            <p>Emotional (EQ)</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        aq = dims.get('adaptability_quotient', {})
        st.markdown(f"""
        <div class="metric-card metric-card-green">
            <h3>{aq.get('percentage', 0):.0f}%</h3>
            <p>Adaptability (AQ)</p>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        bq = dims.get('behavioral_quotient', {})
        st.markdown(f"""
        <div class="metric-card metric-card-orange">
            <h3>{bq.get('percentage', 0):.0f}%</h3>
            <p>Behavioral (BQ)</p>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        sq = dims.get('social_quotient', {})
        st.markdown(f"""
        <div class="metric-card metric-card-purple">
            <h3>{sq.get('percentage', 0):.0f}%</h3>
            <p>Social (SQ)</p>
        </div>
        """, unsafe_allow_html=True)

    # AI Feedback
    feedback = results.get('ai_feedback', {})
    if feedback:
        st.subheader("🤖 AI Insights")
        st.write(feedback.get('summary', ''))

        c1, c2 = st.columns(2)
        with c1:
            st.write("**Strengths:**")
            for s in feedback.get('strengths', []):
                st.write(f"  ✅ {s}")
        with c2:
            st.write("**Development Areas:**")
            for d in feedback.get('development_areas', []):
                st.write(f"  📈 {d}")

        st.write(f"**Team Fit:** {feedback.get('team_fit', 'N/A')}")
        st.write(f"**Leadership Potential:** {feedback.get('leadership_potential', 'N/A')}")
