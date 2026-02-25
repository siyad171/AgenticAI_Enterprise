"""
Candidate Report Generator — Consolidates all interview data into a comprehensive report.

Weights:
  Resume / Application : 15%
  MCQ Test             : 15%
  Technical Interview  : 25%
  Psychometric         : 20%
  Video Interview      : 25%
"""
from typing import Dict, Optional
from tools.interview_storage import InterviewStorage
from core.config import LLM_ANALYSIS_MODEL


# ─── Score weights ────────────────────────────────────────────────
WEIGHTS = {
    "resume":      0.15,
    "mcq":         0.15,
    "technical":   0.25,
    "psychometric": 0.20,
    "video":       0.25,
}


def _safe(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default


def _clamp(val, lo=0.0, hi=100.0):
    """Clamp a score to [lo, hi] range."""
    return max(lo, min(hi, float(val)))


# ═══════════════════════════════════════════════════════════════════
# SECTION SCORE CALCULATORS
# ═══════════════════════════════════════════════════════════════════

def _resume_score(candidate) -> Dict:
    """Evaluate resume quality from DB candidate object."""
    score = 0.0
    details = {}

    # Skill match
    skills = candidate.extracted_skills if candidate.extracted_skills else []
    skill_count = len(skills)
    skill_score = min(skill_count / 8 * 100, 100)  # 8 skills = full marks
    details["skills_found"] = skill_count
    details["skill_score"] = round(skill_score, 1)
    score += skill_score * 0.40

    # Experience
    exp = candidate.experience_years or 0
    exp_score = min(exp / 5 * 100, 100)  # 5 years = full marks
    details["experience_years"] = exp
    details["experience_score"] = round(exp_score, 1)
    score += exp_score * 0.30

    # Education
    edu = (candidate.education or "").lower()
    edu_map = {"phd": 100, "master": 90, "bachelor": 75, "diploma": 50, "high school": 30}
    edu_score = 0
    for key, val in edu_map.items():
        if key in edu:
            edu_score = val
            break
    details["education"] = candidate.education
    details["education_score"] = edu_score
    score += edu_score * 0.20

    # Evaluation result from HR agent
    eval_result = candidate.evaluation_result or {}
    eval_score = _clamp(_safe(eval_result.get("score"), 50))
    details["hr_evaluation_score"] = eval_score
    score += eval_score * 0.10

    final = round(_clamp(score), 1)
    return {"score": final, "details": details}


def _mcq_score(candidate) -> Dict:
    """MCQ test score from DB."""
    if not candidate.test_taken:
        return {"score": None, "details": {"status": "Not taken"}}

    score = _clamp(_safe(candidate.test_score, 0))
    return {
        "score": round(score, 1),
        "details": {
            "test_taken": True,
            "raw_score": score,
            "passed": score >= 60,
        },
    }


def _technical_score(candidate_id: str, storage: InterviewStorage) -> Dict:
    """Combine chat interview + code submission scores."""
    chats = storage.get_interview_chats(candidate_id)
    submissions = storage.get_code_submissions(candidate_id)

    chat_score = 0
    code_score = 0
    details = {"chats": len(chats), "submissions": len(submissions)}

    # Chat interview quality
    if chats:
        last_chat = chats[-1]
        report = last_chat.get("report", {})
        approach_raw = _safe(report.get("approach_quality"), 0)
        communication_raw = _safe(report.get("communication_score"), 0)
        hints = int(report.get("hints_used", 0))
        stages = report.get("stages_completed", [])
        stage_progress = len(stages) / 5 * 100 if stages else 0

        # Normalize: if values look like 0-10 scale, multiply by 10
        # to get 0-100; if already 0-100 scale, use as-is.
        approach = _clamp(approach_raw * 10 if approach_raw <= 10 else approach_raw)
        communication = _clamp(communication_raw * 10 if communication_raw <= 10 else communication_raw)

        # Combine sub-scores (each component is 0-100, weights sum to 1.0)
        chat_score = (approach * 0.35 +
                      communication * 0.25 +
                      stage_progress * 0.25 +
                      max(0, 100 - hints * 15) * 0.15)
        chat_score = _clamp(chat_score)
        details["approach_quality"] = approach
        details["communication_score"] = communication
        details["hints_used"] = hints
        details["stages_completed"] = stages

    # Code submission quality
    if submissions:
        best = max(submissions, key=lambda s: s.get("passed", 0))
        passed = best.get("passed", 0)
        total = best.get("total", 1) or 1
        code_score = (passed / total) * 100
        details["tests_passed"] = passed
        details["tests_total"] = total

    # Weight: 60% chat interview, 40% code
    final = _clamp(chat_score * 0.6 + code_score * 0.4)
    if not chats and not submissions:
        return {"score": None, "details": {"status": "Not attempted"}}
    return {"score": round(final, 1), "details": details}


def _psychometric_score(candidate_id: str, storage: InterviewStorage) -> Dict:
    """Psychometric assessment scores."""
    results = storage.get_psychometric_results(candidate_id)
    if not results:
        return {"score": None, "details": {"status": "Not attempted"}}

    latest = results[-1]
    overall = _safe(latest.get("overall_score"), 0)
    dims = latest.get("dimensions", {})
    ai_fb = latest.get("ai_feedback", {})

    dimension_scores = {}
    for dim_key, dim_data in dims.items():
        dimension_scores[dim_key] = round(_safe(dim_data.get("percentage"), 0), 1)

    return {
        "score": round(overall, 1),
        "details": {
            "dimensions": dimension_scores,
            "strengths": ai_fb.get("strengths", []),
            "development_areas": ai_fb.get("development_areas", []),
            "team_fit": ai_fb.get("team_fit", ""),
            "leadership_potential": ai_fb.get("leadership_potential", ""),
            "total_questions": latest.get("total_questions", 0),
        },
    }


def _video_score(candidate_id: str, storage: InterviewStorage) -> Dict:
    """Video interview scores with emotion data."""
    analyses = storage.get_video_analyses(candidate_id)
    if not analyses:
        return {"score": None, "details": {"status": "Not attempted"}}

    latest = analyses[-1]
    eval_data = latest.get("evaluation", {})
    emotions = latest.get("emotions", {})
    criteria = eval_data.get("criteria_scores", {})

    criteria_scores = {k: _safe(v, 0) for k, v in criteria.items()}
    overall_eval = _safe(eval_data.get("overall_score"), 0)
    confidence = _safe(emotions.get("confidence"), 50)
    positivity = _safe(emotions.get("positivity"), 50)

    # Combine: 60% evaluation criteria, 20% confidence, 20% positivity
    final = _clamp(overall_eval * 0.6 + confidence * 0.2 + positivity * 0.2)

    emotion_dist = emotions.get("distribution", {})

    return {
        "score": round(final, 1),
        "details": {
            "criteria_scores": criteria_scores,
            "evaluation_score": overall_eval,
            "confidence": confidence,
            "positivity": positivity,
            "nervousness": _safe(emotions.get("nervousness"), 0),
            "emotion_distribution": emotion_dist,
            "recommendation": eval_data.get("recommendation", "N/A"),
            "feedback": eval_data.get("feedback", ""),
            "transcript": latest.get("transcript", ""),
            "duration": latest.get("duration_seconds", 0),
        },
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════

def generate_candidate_report(candidate, llm_service=None) -> Dict:
    """
    Build a comprehensive candidate report.

    Parameters
    ----------
    candidate : database.Candidate
        The candidate DB object.
    llm_service : LLMService, optional
        If provided, an AI executive summary is generated.

    Returns
    -------
    dict  — structured report with per-section scores, overall weighted
            score, radar data, emotion data, and AI summary.
    """
    storage = InterviewStorage()
    cid = candidate.candidate_id

    # ── Collect section scores ───────────────────────────────
    resume  = _resume_score(candidate)
    mcq     = _mcq_score(candidate)
    tech    = _technical_score(cid, storage)
    psych   = _psychometric_score(cid, storage)
    video   = _video_score(cid, storage)

    sections = {
        "resume":       resume,
        "mcq":          mcq,
        "technical":    tech,
        "psychometric": psych,
        "video":        video,
    }

    # ── Overall weighted score (only count completed sections) ──
    total_weight = 0
    weighted_sum = 0
    for key, data in sections.items():
        if data["score"] is not None:
            weighted_sum += data["score"] * WEIGHTS[key]
            total_weight += WEIGHTS[key]

    overall = round(_clamp(weighted_sum / total_weight), 1) if total_weight > 0 else 0

    # ── Completion status ────────────────────────────────────
    stages_completed = sum(1 for s in sections.values() if s["score"] is not None)
    stages_total = len(sections)

    # ── Radar chart data ─────────────────────────────────────
    radar_labels = ["Resume", "MCQ", "Technical", "Psychometric", "Video"]
    radar_values = [
        sections[k]["score"] if sections[k]["score"] is not None else 0
        for k in ["resume", "mcq", "technical", "psychometric", "video"]
    ]

    # ── Recommendation ───────────────────────────────────────
    if overall >= 75:
        recommendation = "Strong Hire"
    elif overall >= 60:
        recommendation = "Hire"
    elif overall >= 45:
        recommendation = "On Hold"
    else:
        recommendation = "No Hire"

    # ── AI Executive Summary ─────────────────────────────────
    ai_summary = ""
    if llm_service:
        try:
            summary_prompt = f"""You are an expert HR analyst. Generate a concise executive summary
for this candidate's interview report. Be professional and insightful.

Candidate: {candidate.name}
Position: {candidate.applied_position}
Experience: {candidate.experience_years} years
Education: {candidate.education}
Skills: {', '.join(candidate.extracted_skills or [])}

Section Scores:
- Resume/Application: {resume['score']}/100
- MCQ Test: {mcq['score']}/100
- Technical Interview: {tech['score']}/100
- Psychometric Assessment: {psych['score']}/100
- Video Interview: {video['score']}/100
- Overall Weighted Score: {overall}/100

Psychometric Details: {psych['details']}
Video Feedback: {video['details'].get('feedback', 'N/A')}
Video Recommendation: {video['details'].get('recommendation', 'N/A')}
Overall Recommendation: {recommendation}

Write 3-4 sentences summarizing the candidate's performance, key strengths,
areas of concern, and a clear hiring recommendation."""
            ai_summary = llm_service.generate_response(
                summary_prompt,
                system_prompt="You are an expert HR analyst providing candidate evaluation summaries.",
                model=LLM_ANALYSIS_MODEL,
            )
        except Exception as e:
            ai_summary = f"Summary generation failed: {e}"

    report = {
        "candidate_id":     cid,
        "candidate_name":   candidate.name,
        "position":         candidate.applied_position,
        "sections":         sections,
        "weights":          WEIGHTS,
        "overall_score":    overall,
        "recommendation":   recommendation,
        "stages_completed": stages_completed,
        "stages_total":     stages_total,
        "radar_labels":     radar_labels,
        "radar_values":     radar_values,
        "ai_summary":       ai_summary,
    }

    # Persist
    storage.save_final_report(cid, report)
    return report


# ═══════════════════════════════════════════════════════════════════
# DUMMY / BENCHMARK CANDIDATE
# ═══════════════════════════════════════════════════════════════════

def get_benchmark_data() -> Dict:
    """Return benchmark (ideal) candidate data for comparison charts."""
    return {
        "candidate_name": "Benchmark (Ideal)",
        "overall_score": 85,
        "radar_labels": ["Resume", "MCQ", "Technical", "Psychometric", "Video"],
        "radar_values": [88, 82, 90, 80, 85],
        "sections": {
            "resume":       {"score": 88},
            "mcq":          {"score": 82},
            "technical":    {"score": 90},
            "psychometric": {"score": 80},
            "video":        {"score": 85},
        },
    }
