"""Test tools layer"""
import os

def test_local_executor():
    from tools.local_executor import LocalPythonExecutor
    executor = LocalPythonExecutor()
    result = executor.execute_python("print('hello')")
    assert result["status"] == "success"
    assert "hello" in result["output"]

def test_local_executor_timeout():
    from tools.local_executor import LocalPythonExecutor
    executor = LocalPythonExecutor()
    result = executor.execute_python("import time; time.sleep(10)", timeout=2.0)
    assert result["status"] == "error" or "Time Limit" in result.get("output", "")

def test_psychometric_scoring():
    from tools.psychometric_assessment import PsychometricAssessment
    pa = PsychometricAssessment()
    # Answer all 20 questions with option index 2
    questions = pa.get_questions()
    for q in questions:
        pa.submit_answer(q['id'], 2)
    results = pa.calculate_results()
    assert results['status'] == 'complete'
    assert 'overall_score' in results
    dims = results['dimensions']
    assert 'emotional_quotient' in dims
    assert 'adaptability_quotient' in dims
    assert 'social_quotient' in dims
    assert 'behavioral_quotient' in dims
    assert 0 <= results['overall_score'] <= 100

def test_interview_storage():
    from tools.interview_storage import InterviewStorage
    storage = InterviewStorage()
    cand_id = "TEST_CAND_001"
    # Save a code submission
    result = storage.save_code_submission(
        candidate_id=cand_id, problem_id="PROB001",
        code="print('hello')", language="python",
        test_results=[{"test": "test1", "status": "passed"}, {"test": "test2", "status": "passed"}]
    )
    assert "submission_id" in result
    # Check candidate summary
    summary = storage.get_candidate_summary(cand_id)
    assert summary.get("code_submissions", 0) >= 1
    # Cleanup
    import shutil, pathlib
    from core.config import INTERVIEW_RESULTS_DIR
    path = pathlib.Path(INTERVIEW_RESULTS_DIR) / cand_id
    if path.exists():
        shutil.rmtree(path)
