"""Candidate Portal — Application, tests, interviews"""
import streamlit as st
import datetime
from ui.utils import parse_pdf_resume


def show_candidate_portal():
    st.title("📝 Candidate Application Portal")
    agent = st.session_state.agents['hr']
    db = st.session_state.db

    # Step tracking
    if 'candidate_step' not in st.session_state:
        st.session_state.candidate_step = "application"

    step = st.session_state.candidate_step

    if step == "application":
        _show_application_form(agent, db)
    elif step == "application_result":
        _show_application_result(agent, db)
    elif step == "mcq_test":
        _show_mcq_test(agent, db)
    elif step == "mcq_result":
        _show_mcq_result(agent, db)
    elif step in ("technical_interview", "chat_interview"):
        from ui.chat_interview_ui import show_chat_interview
        show_chat_interview()
    elif step == "psychometric":
        from ui.psychometric_ui import show_psychometric_assessment
        show_psychometric_assessment()
    elif step == "video_interview":
        from ui.video_interview_ui import show_video_interview
        show_video_interview()
    elif step == "complete":
        st.success("🎉 Application complete! You will be notified by email.")
        if st.button("← Back to Login"):
            st.session_state.show_application_form = False
            st.session_state.candidate_step = "application"
            st.rerun()


def _show_application_form(agent, db):
    """Application form with resume upload and position selection"""
    st.subheader("Step 1: Personal Information")

    # Back button
    if st.button("← Back to Login"):
        st.session_state.show_application_form = False
        st.rerun()

    # Position selection (outside form so job details update live)
    active_jobs = {jid: j for jid, j in db.job_positions.items()
                   if j.status == "Active"}
    job_titles = [j.title for j in active_jobs.values()]
    selected_position = st.selectbox("Position *", job_titles)

    # ── Show Job Requirements ──────────────────────────────
    if selected_position:
        job_id = db.get_job_id_by_title(selected_position)
        job = db.get_job_position(job_id) if job_id else None
        if job:
            with st.expander("📋 View Job Requirements", expanded=True):
                st.markdown(f"**Position:** {job.title}")
                st.markdown(f"**Department:** {job.department}")
                st.markdown(f"**Description:** {job.description}")
                st.markdown(f"**Required Skills:** {', '.join(job.required_skills)}")
                st.markdown(f"**Minimum Experience:** {job.min_experience} years")
                st.markdown(f"**Minimum Education:** {job.min_education}")

    with st.form("application_form"):
        name = st.text_input("Full Name *")
        email = st.text_input("Email *")
        phone = st.text_input("Phone Number")

        # Resume upload
        st.subheader("Resume")
        resume_file = st.file_uploader("Upload PDF Resume", type=["pdf"])
        resume_text = st.text_area("Or paste resume text", height=150)

        submitted = st.form_submit_button("Submit Application", type="primary")

        if submitted and name and email and selected_position:
            # Parse resume
            final_resume_text = ""
            if resume_file:
                final_resume_text = parse_pdf_resume(resume_file)
            if not final_resume_text and resume_text:
                final_resume_text = resume_text.strip()
            if not final_resume_text:
                st.error("Please provide a resume (upload PDF or paste text)")
                return

            # Extract skills via LLM
            parsed = agent.parse_resume_text(final_resume_text)

            # Generate candidate ID
            cand_id = f"CAND{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

            from core.database import Candidate
            candidate = Candidate(
                candidate_id=cand_id, name=name, email=email, phone=phone,
                applied_position=selected_position,
                resume_text=final_resume_text,
                extracted_skills=parsed['skills'],
                experience_years=parsed['experience_years'],
                education=parsed['education'],
                application_date=datetime.datetime.now().isoformat(),
                status="Pending"
            )
            db.add_candidate(candidate)

            # Evaluate
            job_id = db.get_job_id_by_title(selected_position)
            job = db.get_job_position(job_id)
            result = agent.evaluate_candidate(candidate, job)

            # Store results in session so we can display them on next page
            st.session_state.current_candidate_id = cand_id
            st.session_state.application_result = {
                "candidate_id": cand_id,
                "name": name,
                "position": selected_position,
                "skills": parsed['skills'],
                "experience_years": parsed['experience_years'],
                "education": parsed['education'],
                "evaluation": result['evaluation'],
            }
            st.session_state.candidate_step = "application_result"
            st.rerun()


def _show_application_result(agent, db):
    """Show application submission results before proceeding"""
    st.subheader("📄 Application Results")

    result = st.session_state.get('application_result')
    if not result:
        st.error("No application data found")
        st.session_state.candidate_step = "application"
        st.rerun()
        return

    evaluation = result['evaluation']

    # ── Success banner ──
    st.success(f"✅ Application submitted successfully! — Candidate ID: **{result['candidate_id']}**")

    # ── Candidate Info ──
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Name:** {result['name']}")
        st.markdown(f"**Position:** {result['position']}")
        st.markdown(f"**Education:** {result['education']}")
        st.markdown(f"**Experience:** {result['experience_years']} years")
    with col2:
        st.markdown(f"**Extracted Skills:** {', '.join(result['skills']) if result['skills'] else 'None detected'}")
        st.markdown(f"**Matched Skills:** {', '.join(evaluation.get('matched_skills', []))}")

    # ── Evaluation Metrics ──
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Overall Score", f"{evaluation['score']}%")
    m2.metric("Skill Match", f"{evaluation['skill_match_percentage']}%")
    m3.metric("Experience Met", "✅ Yes" if evaluation['experience_met'] else "❌ No")
    m4.metric("Education Met", "✅ Yes" if evaluation['education_met'] else "❌ No")

    # ── Decision ──
    st.divider()
    decision = evaluation['decision']
    if decision == "Accepted":
        st.success(f"🎉 Decision: **{decision}** — {evaluation['message']}")
        st.info("You are eligible to proceed to the MCQ Knowledge Assessment.")
        if st.button("▶ Proceed to MCQ Test", type="primary"):
            st.session_state.candidate_step = "mcq_test"
            st.rerun()
    elif decision == "Pending Review":
        st.warning(f"⏳ Decision: **{decision}** — {evaluation['message']}")
        st.info("Your application is under review. You may still proceed to the MCQ test.")
        if st.button("▶ Proceed to MCQ Test", type="primary"):
            st.session_state.candidate_step = "mcq_test"
            st.rerun()
    else:
        st.error(f"❌ Decision: **{decision}** — {evaluation['message']}")
        st.warning("Unfortunately you don't meet the minimum requirements for this position.")
        if st.button("← Back to Application"):
            st.session_state.candidate_step = "application"
            st.rerun()


def _show_mcq_test(agent, db):
    """MCQ test for accepted candidates"""
    st.subheader("Step 2: Knowledge Assessment")
    cand_id = st.session_state.get('current_candidate_id')
    candidate = db.get_candidate(cand_id)
    if not candidate:
        st.error("Candidate not found"); return

    job_id = db.get_job_id_by_title(candidate.applied_position)
    job = db.get_job_position(job_id)
    if not job or not job.test_questions:
        st.error("No test available"); return

    questions = job.test_questions
    with st.form("mcq_test"):
        answers = {}
        for i, q in enumerate(questions):
            answers[i] = st.radio(f"Q{i+1}: {q['question']}",
                                  q['options'], key=f"mcq_{i}")
        submit = st.form_submit_button("Submit Answers", type="primary")

        if submit:
            correct = sum(1 for i, q in enumerate(questions)
                          if answers[i] == q['correct_answer'])
            score = (correct / len(questions)) * 100
            passing = score >= 60

            # Save score to candidate record
            candidate.test_score = score
            candidate.test_taken = True

            # Store MCQ results in session for display
            st.session_state.mcq_result = {
                "correct": correct,
                "total": len(questions),
                "score": score,
                "passing": passing,
            }
            st.session_state.candidate_step = "mcq_result"
            st.rerun()


def _show_mcq_result(agent, db):
    """Show MCQ test results before proceeding"""
    st.subheader("📊 MCQ Test Results")

    result = st.session_state.get('mcq_result')
    if not result:
        st.error("No MCQ result found")
        st.session_state.candidate_step = "mcq_test"
        st.rerun()
        return

    # ── Score Display ──
    col1, col2, col3 = st.columns(3)
    col1.metric("Score", f"{result['score']:.0f}%")
    col2.metric("Correct Answers", f"{result['correct']} / {result['total']}")
    col3.metric("Status", "✅ PASS" if result['passing'] else "❌ FAIL")

    st.divider()

    if result['passing']:
        st.success(f"🎉 Congratulations! You scored **{result['score']:.0f}%** ({result['correct']}/{result['total']} correct)")
        st.info("You have passed the knowledge assessment. Proceed to the Technical Interview.")
        if st.button("▶ Proceed to Technical Interview", type="primary"):
            st.session_state.candidate_step = "technical_interview"
            st.rerun()
    else:
        st.error(f"You scored **{result['score']:.0f}%** ({result['correct']}/{result['total']} correct). Minimum required: 60%")
        st.warning("You did not meet the passing threshold for this assessment.")
        if st.button("← Back to Application"):
            st.session_state.candidate_step = "application"
            st.rerun()


# _show_technical_choice removed — candidates go directly to AI chat interview
