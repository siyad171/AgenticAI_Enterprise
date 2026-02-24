"""Chat Interview UI — AI interviewer chat + integrated code editor"""
import streamlit as st
from tools.technical_interview_chat import TechnicalInterviewChat
from tools.interview_storage import InterviewStorage
from tools.code_executor import CodeExecutor
from tools.ai_code_analyzer import AICodeAnalyzer


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

    # ── Problem selection ─────────────────────────────────────────
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

    # ── Sidebar controls ─────────────────────────────────────────
    st.sidebar.subheader("Interview Controls")
    _stage_label = {
        'introduction': '1️⃣ Introduction',
        'clarification': '2️⃣ Clarification',
        'approach': '3️⃣ Approach',
        'coding': '4️⃣ Coding',
        'review': '5️⃣ Review',
        'complete': '✅ Complete',
    }
    st.sidebar.info(f"**Current Stage:** {_stage_label.get(chat.current_stage, chat.current_stage)}")

    if chat.current_stage in ('introduction', 'clarification'):
        if st.sidebar.button("➡️ Move to Approach"):
            chat.current_stage = 'approach'
            st.session_state.interview_messages.append(
                {"role": "assistant", "content": "Great! Let's discuss your approach. Walk me through how you'd solve this problem step by step.", "stage": "approach"})
            st.rerun()

    if chat.current_stage in ('introduction', 'clarification', 'approach'):
        if st.sidebar.button("➡️ Move to Coding"):
            chat.current_stage = 'coding'
            st.session_state.interview_messages.append(
                {"role": "assistant", "content": "Time to code! Use the editor below to write your solution. You can run it, test against test cases, and submit when ready.", "stage": "coding"})
            st.rerun()

    if st.sidebar.button(f"💡 Get Hint ({chat.hint_count}/{chat.max_hints})"):
        hint = chat.get_context_aware_hint(st.session_state.get('candidate_code', ''))
        st.session_state.interview_messages.append(
            {"role": "assistant", "content": f"💡 {hint}", "stage": "hint"})
        st.rerun()

    if st.sidebar.button("✅ Complete Interview"):
        _complete_interview(chat, cand_id)

    # ── Chat history ─────────────────────────────────────────────
    for msg in st.session_state.interview_messages:
        with st.chat_message(msg['role']):
            st.write(msg['content'])
            if msg.get('stage'):
                st.caption(f"Stage: {msg['stage']}")

    # ── CODING STAGE: show code editor ───────────────────────────
    if chat.current_stage == 'coding':
        _show_coding_panel(chat, db, cand_id)

    # ── Chat input (always available) ────────────────────────────
    if prompt := st.chat_input("Type your response..."):
        st.session_state.interview_messages.append(
            {"role": "user", "content": prompt, "stage": chat.current_stage})

        stage = chat.current_stage
        if stage in ('introduction', 'clarification'):
            response = chat.handle_clarification(prompt)
        elif stage == 'approach':
            result = chat.discuss_approach(prompt)
            response = result.get('feedback_message', str(result))
        elif stage == 'coding':
            code = st.session_state.get('candidate_code', '')
            test_results = st.session_state.get('test_results', [])
            response = chat.debug_conversation(prompt, code, test_results)
        else:
            response = chat.handle_clarification(prompt)

        st.session_state.interview_messages.append(
            {"role": "assistant", "content": response, "stage": chat.current_stage})
        st.rerun()


# ══════════════════════════════════════════════════════════════════
#  Coding Panel — editor, run, test, AI review, submit
# ══════════════════════════════════════════════════════════════════
def _show_coding_panel(chat, db, cand_id):
    st.divider()
    st.subheader("💻 Code Editor")

    prob_id = st.session_state.get('current_problem_id')
    prob = db.technical_problems.get(prob_id)
    if not prob:
        st.error("Problem not found")
        return

    # Problem reference
    with st.expander("📋 Problem Description", expanded=False):
        st.markdown(f"**{prob.title}** ({prob.difficulty})")
        st.write(prob.description)
        if prob.examples:
            for i, ex in enumerate(prob.examples, 1):
                st.code(f"Input:  {ex.get('input', '')}\nOutput: {ex.get('output', '')}")

    # Language selector
    language = st.selectbox("Language", ["python", "javascript", "java"], key="code_lang")

    # Starter code
    starter = ""
    if hasattr(prob, 'starter_code') and prob.starter_code:
        starter = prob.starter_code.get(language, "")

    # Try to use Ace editor, fall back to text_area
    try:
        from streamlit_ace import st_ace
        code = st_ace(
            value=st.session_state.get('candidate_code') or starter or f"# Write your {language} solution here\n",
            language=language,
            theme="monokai",
            height=350,
            key=f"ace_chat_{prob_id}_{language}"
        )
    except ImportError:
        code = st.text_area(
            "Write your code:",
            value=st.session_state.get('candidate_code') or starter or f"# Write your {language} solution here\n",
            height=350,
            key=f"ta_chat_{prob_id}_{language}"
        )

    st.session_state.candidate_code = code

    # ── Action buttons ────────────────────────────────────────
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("▶️ Run Code", type="primary"):
            with st.spinner("Executing..."):
                executor = CodeExecutor()
                # Use first example input as default stdin so code doesn't hit EOFError
                default_stdin = ""
                if prob.examples:
                    default_stdin = prob.examples[0].get('input', '')
                result = executor.execute_code(code, language, stdin=default_stdin)
                if result.get('status') == 'success':
                    st.success("Output:")
                    st.code(result.get('output', 'No output'))
                    if prob.examples:
                        st.caption(f"Expected: {prob.examples[0].get('output', '')}")
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")

    with c2:
        if st.button("🧪 Run Tests"):
            with st.spinner("Running test cases..."):
                executor = CodeExecutor()
                test_cases = prob.test_cases if hasattr(prob, 'test_cases') else []
                if test_cases:
                    raw_results = executor.run_test_cases(code, language, test_cases)
                    # run_test_cases returns a dict with 'test_results' list
                    test_result_list = raw_results.get('test_results', []) if isinstance(raw_results, dict) else raw_results
                    passed = sum(1 for r in test_result_list if isinstance(r, dict) and r.get('status') == 'passed')
                    total = len(test_result_list)

                    if passed == total:
                        st.success(f"✅ All {total} tests passed!")
                    else:
                        st.warning(f"⚠️ {passed}/{total} tests passed")

                    for i, r in enumerate(test_result_list, 1):
                        if not isinstance(r, dict):
                            continue
                        icon = "✅" if r.get('status') == 'passed' else "❌"
                        with st.expander(f"{icon} Test {i}"):
                            # Show all test details (no hidden tests in interview context)
                            actual_input = r.get('input', 'N/A')
                            actual_expected = r.get('expected', 'N/A')
                            actual_output = r.get('actual', r.get('output', 'N/A'))
                            # If hidden, look up from original test cases
                            if actual_input == 'Hidden' and hasattr(prob, 'test_cases') and i <= len(prob.test_cases):
                                tc = prob.test_cases[i - 1]
                                actual_input = tc.get('input', 'N/A')
                                actual_expected = tc.get('expected', 'N/A')
                            st.write(f"**Input:** {actual_input}")
                            st.write(f"**Expected:** {actual_expected}")
                            st.write(f"**Got:** {actual_output}")
                            if r.get('time'):
                                st.write(f"**Time:** {r.get('time', 0):.3f}s")

                    st.session_state.test_results = test_result_list
                else:
                    st.info("No test cases available for this problem")

    with c3:
        if st.button("📤 Submit Code"):
            storage = InterviewStorage()
            test_results = st.session_state.get('test_results', [])
            storage.save_code_submission(
                cand_id or "unknown", prob_id,
                code, language, test_results
            )

            # Also feed back into the chat interview for final report
            review = chat.analyze_code_submission(code, test_results)
            passed = sum(1 for r in test_results if r.get('status') == 'passed')
            total = len(test_results) if test_results else 0

            st.session_state.interview_messages.append({
                "role": "assistant",
                "content": (
                    f"✅ Code submitted!\n\n"
                    f"**Tests passed:** {passed}/{total}\n"
                    f"**Code Quality:** {review.get('code_quality_score', 'N/A')}/100\n"
                    f"**Feedback:** {review.get('overall_feedback', 'Good effort!')}"
                ),
                "stage": "review"
            })
            chat.current_stage = 'review'
            st.rerun()


# ══════════════════════════════════════════════════════════════════
#  Complete Interview
# ══════════════════════════════════════════════════════════════════
def _complete_interview(chat, cand_id):
    report = chat.get_final_report()

    storage = InterviewStorage()
    storage.save_interview_chat(
        cand_id or "unknown",
        st.session_state.get('current_problem_id', ''),
        chat.get_conversation_for_display(),
        report
    )

    st.session_state.interview_messages.append({
        "role": "assistant",
        "content": (
            f"🎉 Interview complete!\n\n"
            f"- **Approach Quality:** {report['approach_quality']}/100\n"
            f"- **Communication:** {report['communication_score']}/100\n"
            f"- **Hints Used:** {report['hints_used']}/{chat.max_hints}\n"
            f"- **Total Messages:** {report['total_messages']}"
        ),
        "stage": "complete"
    })

    st.session_state.candidate_step = "psychometric"
    st.rerun()
