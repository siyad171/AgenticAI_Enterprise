"""Technical Interview UI — Code editor, test cases, AI review"""
import streamlit as st
from streamlit_ace import st_ace
from tools.code_executor import CodeExecutor
from tools.ai_code_analyzer import AICodeAnalyzer
from tools.interview_storage import InterviewStorage


def show_technical_interview():
    st.subheader("⚡ Technical Code Assessment")
    db = st.session_state.db
    cand_id = st.session_state.get('current_candidate_id')

    # Problem selection
    if 'selected_problem' not in st.session_state:
        st.write("Select a coding problem:")
        problems = db.technical_problems
        for pid, prob in problems.items():
            if st.button(f"🧩 {prob.title} ({prob.difficulty})", key=f"tech_{pid}"):
                st.session_state.selected_problem = pid
                st.rerun()
        return

    prob_id = st.session_state.selected_problem
    prob = db.technical_problems.get(prob_id)
    if not prob:
        st.error("Problem not found")
        return

    # Problem description
    st.markdown(f"### {prob.title}")
    st.markdown(f"**Difficulty:** {prob.difficulty}")
    st.write(prob.description)

    if prob.examples:
        st.subheader("Examples")
        for i, ex in enumerate(prob.examples, 1):
            st.code(f"Input: {ex.get('input', '')}\nOutput: {ex.get('output', '')}")

    st.divider()

    # Language selection
    language = st.selectbox("Language", ["python", "javascript", "java"])

    # Get starter code
    starter = ""
    if hasattr(prob, 'starter_code') and prob.starter_code:
        starter = prob.starter_code.get(language, "")

    # Code editor
    st.subheader("Your Solution")
    code = st_ace(
        value=starter or f"# Write your {language} solution here\n",
        language=language,
        theme="monokai",
        height=350,
        key=f"ace_{prob_id}_{language}"
    )

    st.session_state.candidate_code = code

    # Action buttons
    c1, c2, c3 = st.columns(3)

    # Run code
    with c1:
        if st.button("▶️ Run Code", type="primary"):
            with st.spinner("Executing..."):
                executor = CodeExecutor()
                result = executor.execute_code(code, language)
                if result.get('status') == 'success':
                    st.success("Output:")
                    st.code(result.get('output', 'No output'))
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")

    # Run test cases
    with c2:
        if st.button("🧪 Run Tests"):
            with st.spinner("Running test cases..."):
                executor = CodeExecutor()
                test_cases = prob.test_cases if hasattr(prob, 'test_cases') else []
                if test_cases:
                    results = executor.run_test_cases(code, language, test_cases)
                    passed = sum(1 for r in results if r.get('status') == 'passed')
                    total = len(results)

                    if passed == total:
                        st.success(f"✅ All {total} tests passed!")
                    else:
                        st.warning(f"⚠️ {passed}/{total} tests passed")

                    for i, r in enumerate(results, 1):
                        icon = "✅" if r.get('status') == 'passed' else "❌"
                        with st.expander(f"{icon} Test {i}"):
                            st.write(f"**Input:** {r.get('input', 'N/A')}")
                            st.write(f"**Expected:** {r.get('expected', 'N/A')}")
                            st.write(f"**Got:** {r.get('output', 'N/A')}")

                    st.session_state.test_results = results
                else:
                    st.info("No test cases available for this problem")

    # AI Code Review
    with c3:
        if st.button("🤖 AI Review"):
            with st.spinner("Analyzing code..."):
                analyzer = AICodeAnalyzer()
                analysis = analyzer.analyze_code(code, prob.title, language)
                st.subheader("AI Code Review")
                st.write(f"**Quality Score:** {analysis.get('code_quality_score', 'N/A')}/100")
                if analysis.get('strengths'):
                    st.write("**Strengths:**")
                    for s in analysis['strengths']:
                        st.write(f"  ✅ {s}")
                if analysis.get('weaknesses'):
                    st.write("**Areas for Improvement:**")
                    for w in analysis['weaknesses']:
                        st.write(f"  ⚠️ {w}")
                if analysis.get('time_complexity'):
                    st.write(f"**Time Complexity:** {analysis['time_complexity']}")
                if analysis.get('space_complexity'):
                    st.write(f"**Space Complexity:** {analysis['space_complexity']}")

    st.divider()

    # Submit and proceed
    if st.button("📤 Submit & Continue", type="primary"):
        storage = InterviewStorage()
        test_results = st.session_state.get('test_results', [])
        storage.save_code_submission(
            cand_id or "unknown", prob_id,
            code, language, test_results
        )
        st.success("✅ Code submitted!")
        st.session_state.candidate_step = "psychometric"
        st.session_state.pop('selected_problem', None)
        st.rerun()
