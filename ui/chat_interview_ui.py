"""Chat Interview UI — 6-stage AI interviewer chat interface"""
import streamlit as st
from tools.technical_interview_chat import TechnicalInterviewChat
from tools.interview_storage import InterviewStorage


def show_chat_interview():
    st.subheader("💬 AI Technical Interview")
    db = st.session_state.db
    cand_id = st.session_state.get('current_candidate_id')

    # Initialize chat interviewer
    if 'interview_chat' not in st.session_state:
        st.session_state.interview_chat = TechnicalInterviewChat()
        st.session_state.interview_started = False
        st.session_state.interview_messages = []

    chat = st.session_state.interview_chat

    # Problem selection
    if not st.session_state.interview_started:
        st.write("Select a problem to begin your technical interview:")
        problems = db.technical_problems
        for pid, prob in problems.items():
            if st.button(f"🧩 {prob.title} ({prob.difficulty})", key=f"prob_{pid}"):
                problem_data = {
                    'title': prob.title,
                    'difficulty': prob.difficulty,
                    'description': prob.description,
                    'examples': prob.examples,
                }
                intro = chat.start_interview(problem_data)
                st.session_state.interview_started = True
                st.session_state.current_problem_id = pid
                st.session_state.interview_messages.append(
                    {"role": "assistant", "content": intro, "stage": "introduction"})
                st.rerun()
        return

    # Display chat history
    for msg in st.session_state.interview_messages:
        with st.chat_message(msg['role']):
            st.write(msg['content'])
            if msg.get('stage'):
                st.caption(f"Stage: {msg['stage']}")

    # Chat input
    if prompt := st.chat_input("Type your response..."):
        st.session_state.interview_messages.append(
            {"role": "user", "content": prompt, "stage": chat.current_stage})

        # Route based on current stage
        stage = chat.current_stage
        if stage in ('introduction', 'clarification'):
            response = chat.handle_clarification(prompt)
        elif stage == 'approach':
            result = chat.discuss_approach(prompt)
            response = result.get('feedback_message', str(result))
        elif stage == 'coding':
            response = chat.debug_conversation(prompt, "", [])
        else:
            response = chat.handle_clarification(prompt)

        st.session_state.interview_messages.append(
            {"role": "assistant", "content": response, "stage": chat.current_stage})
        st.rerun()

    # Sidebar controls
    st.sidebar.subheader("Interview Controls")

    # Stage progression
    if st.sidebar.button("➡️ Move to Approach"):
        chat.current_stage = 'approach'
        st.rerun()
    if st.sidebar.button("➡️ Move to Coding"):
        chat.current_stage = 'coding'
        st.rerun()

    # Hints
    if st.sidebar.button(f"💡 Get Hint ({chat.hint_count}/{chat.max_hints})"):
        hint = chat.get_context_aware_hint(st.session_state.get('candidate_code', ''))
        st.session_state.interview_messages.append(
            {"role": "assistant", "content": f"💡 {hint}", "stage": "hint"})
        st.rerun()

    # Complete interview
    if st.sidebar.button("✅ Complete Interview"):
        report = chat.get_final_report()

        # Save to storage
        storage = InterviewStorage()
        storage.save_interview_chat(
            cand_id or "unknown",
            st.session_state.get('current_problem_id', ''),
            chat.get_conversation_for_display(),
            report
        )

        st.session_state.interview_messages.append({
            "role": "assistant",
            "content": f"Interview complete!\n"
                       f"- Approach Quality: {report['approach_quality']}/100\n"
                       f"- Communication: {report['communication_score']}/100\n"
                       f"- Hints Used: {report['hints_used']}/{chat.max_hints}\n"
                       f"- Total Messages: {report['total_messages']}",
            "stage": "complete"
        })

        st.session_state.candidate_step = "psychometric"
        st.rerun()
