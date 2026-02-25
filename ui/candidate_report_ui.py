"""
Candidate Report UI — Rich interactive report with Plotly charts.

Charts included:
  1. Overall score gauge
  2. Radar / spider chart (5 axes)
  3. Horizontal bar chart (section scores vs benchmark)
  4. Psychometric dimension grouped bar
  5. Video criteria bar chart
  6. Emotion distribution pie chart
  7. Emotion timeline area chart
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from tools.candidate_report import generate_candidate_report, get_benchmark_data, WEIGHTS
from tools.interview_storage import InterviewStorage


# ─── Color palette ────────────────────────────────────────────────
COLORS = {
    "primary":    "#4F46E5",   # Indigo
    "success":    "#10B981",   # Green
    "warning":    "#F59E0B",   # Amber
    "danger":     "#EF4444",   # Red
    "info":       "#3B82F6",   # Blue
    "purple":     "#8B5CF6",
    "pink":       "#EC4899",
    "cyan":       "#06B6D4",
    "bg_card":    "#1E1E2E",
    "bg_chart":   "rgba(0,0,0,0)",
    "text":       "#E2E8F0",
    "grid":       "#334155",
}

SECTION_COLORS = {
    "Resume":       COLORS["info"],
    "MCQ":          COLORS["purple"],
    "Technical":    COLORS["cyan"],
    "Psychometric": COLORS["pink"],
    "Video":        COLORS["warning"],
}

RECOMMENDATION_STYLES = {
    "Strong Hire": ("🟢", "success"),
    "Hire":        ("🟡", "info"),
    "On Hold":     ("🟠", "warning"),
    "No Hire":     ("🔴", "error"),
}

# ─── Chart layout defaults ────────────────────────────────────────
_LAYOUT = dict(
    paper_bgcolor=COLORS["bg_chart"],
    plot_bgcolor=COLORS["bg_chart"],
    font=dict(color=COLORS["text"], family="Inter, sans-serif"),
    margin=dict(l=20, r=20, t=40, b=20),
)


# ═══════════════════════════════════════════════════════════════════
# CHART BUILDERS
# ═══════════════════════════════════════════════════════════════════

def _gauge_chart(score: float, title: str = "Overall Score") -> go.Figure:
    if score >= 75:
        bar_color = COLORS["success"]
    elif score >= 60:
        bar_color = COLORS["info"]
    elif score >= 45:
        bar_color = COLORS["warning"]
    else:
        bar_color = COLORS["danger"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        title=dict(text=title, font=dict(size=18)),
        number=dict(suffix="/100", font=dict(size=32)),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor=COLORS["grid"]),
            bar=dict(color=bar_color, thickness=0.7),
            bgcolor=COLORS["bg_card"],
            bordercolor=COLORS["grid"],
            steps=[
                dict(range=[0, 45],  color="rgba(239,68,68,0.15)"),
                dict(range=[45, 60], color="rgba(245,158,11,0.15)"),
                dict(range=[60, 75], color="rgba(59,130,246,0.15)"),
                dict(range=[75, 100],color="rgba(16,185,129,0.15)"),
            ],
            threshold=dict(line=dict(color=COLORS["danger"], width=2), thickness=0.8, value=60),
        ),
    ))
    fig.update_layout(**_LAYOUT, height=300)
    return fig


def _radar_chart(labels, values, benchmark_values=None) -> go.Figure:
    fig = go.Figure()
    # Candidate
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=labels + [labels[0]],
        fill="toself",
        name="Candidate",
        line=dict(color=COLORS["primary"], width=2),
        fillcolor="rgba(79,70,229,0.25)",
    ))
    # Benchmark
    if benchmark_values:
        fig.add_trace(go.Scatterpolar(
            r=benchmark_values + [benchmark_values[0]],
            theta=labels + [labels[0]],
            fill="toself",
            name="Benchmark",
            line=dict(color=COLORS["success"], width=2, dash="dash"),
            fillcolor="rgba(16,185,129,0.12)",
        ))
    fig.update_layout(
        **_LAYOUT,
        polar=dict(
            bgcolor=COLORS["bg_chart"],
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=COLORS["grid"],
                            tickfont=dict(size=10)),
            angularaxis=dict(gridcolor=COLORS["grid"]),
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        title=dict(text="Performance Radar", font=dict(size=16)),
    )
    return fig


def _section_bars(report, benchmark) -> go.Figure:
    labels = report["radar_labels"]
    values = report["radar_values"]
    bench = benchmark["radar_values"]
    weight_pcts = [f"{WEIGHTS[k]*100:.0f}%" for k in
                   ["resume", "mcq", "technical", "psychometric", "video"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels, x=values, orientation="h", name="Candidate",
        marker=dict(color=[SECTION_COLORS.get(l, COLORS["primary"]) for l in labels]),
        text=[f"{v:.0f}" for v in values], textposition="auto",
    ))
    fig.add_trace(go.Bar(
        y=labels, x=bench, orientation="h", name="Benchmark",
        marker=dict(color="rgba(16,185,129,0.35)", line=dict(color=COLORS["success"], width=1.5)),
        text=[f"{v:.0f}" for v in bench], textposition="auto",
    ))
    # Weight annotations
    for i, w in enumerate(weight_pcts):
        fig.add_annotation(x=105, y=i, text=w, showarrow=False,
                           font=dict(size=11, color=COLORS["text"]))
    fig.update_layout(
        **_LAYOUT,
        barmode="group",
        xaxis=dict(range=[0, 115], title="Score", gridcolor=COLORS["grid"]),
        yaxis=dict(autorange="reversed"),
        title=dict(text="Section Scores vs Benchmark", font=dict(size=16)),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )
    return fig


def _psychometric_bars(dimensions: dict) -> go.Figure:
    labels = {
        "emotional_quotient":   "Emotional (EQ)",
        "adaptability_quotient":"Adaptability (AQ)",
        "behavioral_quotient":  "Behavioral (BQ)",
        "social_quotient":      "Social (SQ)",
    }
    names = [labels.get(k, k.replace("_", " ").title()) for k in dimensions]
    vals  = list(dimensions.values())
    colors = [COLORS["info"], COLORS["purple"], COLORS["pink"], COLORS["cyan"]]

    fig = go.Figure(go.Bar(
        x=names, y=vals,
        marker=dict(color=colors[:len(vals)]),
        text=[f"{v:.0f}%" for v in vals], textposition="auto",
    ))
    fig.update_layout(
        **_LAYOUT, height=320,
        yaxis=dict(range=[0, 100], title="Percentage", gridcolor=COLORS["grid"]),
        title=dict(text="Psychometric Dimensions", font=dict(size=16)),
    )
    return fig


def _video_criteria_bars(criteria: dict) -> go.Figure:
    names = [k.replace("_", " ").title() for k in criteria]
    vals  = list(criteria.values())
    colors = [COLORS["primary"], COLORS["success"], COLORS["warning"], COLORS["cyan"]]

    fig = go.Figure(go.Bar(
        x=names, y=vals,
        marker=dict(color=colors[:len(vals)]),
        text=[f"{v:.0f}" for v in vals], textposition="auto",
    ))
    fig.update_layout(
        **_LAYOUT, height=320,
        yaxis=dict(range=[0, 100], title="Score", gridcolor=COLORS["grid"]),
        title=dict(text="Video Interview Criteria", font=dict(size=16)),
    )
    return fig


def _emotion_pie(distribution: dict) -> go.Figure:
    emotion_colors = {
        "happy": "#10B981", "neutral": "#64748B", "sad": "#3B82F6",
        "fear": "#F59E0B", "angry": "#EF4444", "disgust": "#8B5CF6",
        "surprise": "#EC4899",
    }
    labels = [k.title() for k in distribution]
    values = list(distribution.values())
    colors = [emotion_colors.get(k, "#64748B") for k in distribution]

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker=dict(colors=colors),
        hole=0.45,
        textinfo="label+percent",
        textfont=dict(size=12),
    ))
    fig.update_layout(
        **_LAYOUT, height=320,
        title=dict(text="Emotion Distribution", font=dict(size=16)),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
    )
    return fig


def _emotion_timeline(candidate_id: str) -> go.Figure:
    """Build an emotion timeline area chart from raw video data."""
    storage = InterviewStorage()
    analyses = storage.get_video_analyses(candidate_id)
    if not analyses:
        return None

    latest = analyses[-1]
    timeline = latest.get("emotions", {}).get("timeline", [])
    if not timeline:
        return None

    emotion_keys = ["happy", "fear", "sad", "neutral", "angry", "surprise", "disgust"]
    emotion_colors = {
        "happy": "#10B981", "fear": "#F59E0B", "sad": "#3B82F6",
        "neutral": "#64748B", "angry": "#EF4444", "surprise": "#EC4899",
        "disgust": "#8B5CF6",
    }

    fig = go.Figure()
    seconds = [t["second"] for t in timeline]
    for emo in emotion_keys:
        vals = [t.get("scores", {}).get(emo, 0) for t in timeline]
        if max(vals) > 5:  # only show emotions that are meaningful
            fig.add_trace(go.Scatter(
                x=seconds, y=vals, name=emo.title(),
                mode="lines", stackgroup="one",
                line=dict(color=emotion_colors.get(emo, "#64748B"), width=0.5),
            ))

    fig.update_layout(
        **_LAYOUT, height=300,
        xaxis=dict(title="Time (seconds)", gridcolor=COLORS["grid"]),
        yaxis=dict(title="Confidence %", range=[0, 100], gridcolor=COLORS["grid"]),
        title=dict(text="Emotion Timeline", font=dict(size=16)),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    )
    return fig


# ═══════════════════════════════════════════════════════════════════
# MAIN DISPLAY
# ═══════════════════════════════════════════════════════════════════

def show_candidate_report(candidate, llm_service=None, compare: bool = True):
    """
    Render the full candidate report inside the admin portal.

    Parameters
    ----------
    candidate : database.Candidate
    llm_service : LLMService | None
    compare : bool — overlay benchmark on charts
    """

    # Generate the report
    with st.spinner("Generating comprehensive report..."):
        report = generate_candidate_report(candidate, llm_service)

    benchmark = get_benchmark_data() if compare else None

    # Header ─────────────────────────────────────────────────────
    rec = report["recommendation"]
    emoji, alert_type = RECOMMENDATION_STYLES.get(rec, ("⚪", "info"))

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1E1E2E 0%, #2D2B55 100%);
                padding: 24px; border-radius: 12px; margin-bottom: 20px;
                border: 1px solid #334155;">
        <h2 style="margin:0; color:#E2E8F0;">
            📊 Candidate Report — {candidate.name}
        </h2>
        <p style="color:#94A3B8; margin:4px 0 0 0; font-size:14px;">
            {candidate.applied_position} &nbsp;|&nbsp;
            {candidate.experience_years} yrs experience &nbsp;|&nbsp;
            {candidate.education or 'N/A'}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Top KPI row ───────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Overall Score", f"{report['overall_score']:.0f}/100")
    k2.metric("Recommendation", f"{emoji} {rec}")
    k3.metric("Stages Done", f"{report['stages_completed']}/{report['stages_total']}")
    k4.metric("Skills", f"{len(candidate.extracted_skills or [])}")

    # AI Summary ────────────────────────────────────────────────
    if report.get("ai_summary"):
        getattr(st, alert_type)(f"**AI Executive Summary:** {report['ai_summary']}")

    # ── Row 1: Gauge + Radar ──────────────────────────────────
    col_g, col_r = st.columns([1, 1.4])
    with col_g:
        st.plotly_chart(_gauge_chart(report["overall_score"]), use_container_width=True)
    with col_r:
        st.plotly_chart(
            _radar_chart(
                report["radar_labels"], report["radar_values"],
                benchmark["radar_values"] if benchmark else None,
            ),
            use_container_width=True,
        )

    # ── Row 2: Section bars ───────────────────────────────────
    if benchmark:
        st.plotly_chart(_section_bars(report, benchmark), use_container_width=True)

    st.divider()

    # ── Section Details (tabs) ────────────────────────────────
    tabs = st.tabs(["📄 Resume", "📝 MCQ", "💻 Technical", "🧠 Psychometric", "🎥 Video"])

    # ── TAB 0: Resume ─────────────────────────────────────────
    with tabs[0]:
        sec = report["sections"]["resume"]
        st.metric("Resume Score", f"{sec['score']:.0f}/100")
        det = sec["details"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Skills Found", det.get("skills_found", 0))
        c2.metric("Experience", f"{det.get('experience_years', 0)} yrs")
        c3.metric("Education Score", f"{det.get('education_score', 0)}")
        if candidate.extracted_skills:
            st.markdown("**Extracted Skills:** " + ", ".join(
                [f"`{s}`" for s in candidate.extracted_skills]))

    # ── TAB 1: MCQ ────────────────────────────────────────────
    with tabs[1]:
        sec = report["sections"]["mcq"]
        if sec["score"] is not None:
            st.metric("MCQ Score", f"{sec['score']:.0f}/100")
            st.write(f"**Passed:** {'✅ Yes' if sec['details'].get('passed') else '❌ No'}")
        else:
            st.info("MCQ test not taken yet.")

    # ── TAB 2: Technical ──────────────────────────────────────
    with tabs[2]:
        sec = report["sections"]["technical"]
        if sec["score"] is not None:
            st.metric("Technical Score", f"{sec['score']:.0f}/100")
            det = sec["details"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Chat Sessions", det.get("chats", 0))
            c2.metric("Code Submissions", det.get("submissions", 0))
            c3.metric("Hints Used", det.get("hints_used", 0))
            if det.get("tests_passed") is not None:
                st.progress(
                    det["tests_passed"] / max(det.get("tests_total", 1), 1),
                    text=f"Tests Passed: {det['tests_passed']}/{det['tests_total']}"
                )
            if det.get("stages_completed"):
                st.write("**Stages:** " + " → ".join(
                    [f"`{s}`" for s in det["stages_completed"]]))
        else:
            st.info("Technical interview not attempted yet.")

    # ── TAB 3: Psychometric ───────────────────────────────────
    with tabs[3]:
        sec = report["sections"]["psychometric"]
        if sec["score"] is not None:
            st.metric("Psychometric Score", f"{sec['score']:.0f}/100")
            det = sec["details"]
            dims = det.get("dimensions", {})
            if dims:
                st.plotly_chart(_psychometric_bars(dims), use_container_width=True)

            col_s, col_d = st.columns(2)
            with col_s:
                st.markdown("**✅ Strengths**")
                for s in det.get("strengths", []):
                    st.markdown(f"- {s}")
            with col_d:
                st.markdown("**📈 Development Areas**")
                for d in det.get("development_areas", []):
                    st.markdown(f"- {d}")

            if det.get("team_fit"):
                st.info(f"**Team Fit:** {det['team_fit']}")
            if det.get("leadership_potential"):
                st.info(f"**Leadership Potential:** {det['leadership_potential']}")
        else:
            st.info("Psychometric assessment not taken yet.")

    # ── TAB 4: Video ──────────────────────────────────────────
    with tabs[4]:
        sec = report["sections"]["video"]
        if sec["score"] is not None:
            det = sec["details"]
            st.metric("Video Interview Score", f"{sec['score']:.0f}/100")

            # Video criteria + emotion pie side by side
            v1, v2 = st.columns(2)
            with v1:
                criteria = det.get("criteria_scores", {})
                if criteria:
                    st.plotly_chart(_video_criteria_bars(criteria), use_container_width=True)
            with v2:
                emo_dist = det.get("emotion_distribution", {})
                if emo_dist:
                    st.plotly_chart(_emotion_pie(emo_dist), use_container_width=True)

            # Emotion timeline
            timeline_fig = _emotion_timeline(candidate.candidate_id)
            if timeline_fig:
                st.plotly_chart(timeline_fig, use_container_width=True)

            # Stats row
            s1, s2, s3 = st.columns(3)
            s1.metric("Confidence", f"{det.get('confidence', 0):.0f}%")
            s2.metric("Positivity", f"{det.get('positivity', 0):.0f}%")
            s3.metric("Duration", f"{det.get('duration', 0):.0f}s")

            if det.get("feedback"):
                st.warning(f"**AI Feedback:** {det['feedback']}")
            if det.get("recommendation"):
                st.write(f"**Recommendation:** {det['recommendation']}")
            if det.get("transcript"):
                with st.expander("📝 Transcript"):
                    st.write(det["transcript"])
        else:
            st.info("Video interview not conducted yet.")

    st.divider()

    # ── Score Breakdown Table ──────────────────────────────────
    with st.expander("📊 Detailed Score Breakdown"):
        import pandas as pd
        rows = []
        for key in ["resume", "mcq", "technical", "psychometric", "video"]:
            sec = report["sections"][key]
            rows.append({
                "Stage": key.replace("_", " ").title(),
                "Score": f"{sec['score']:.1f}" if sec["score"] is not None else "—",
                "Weight": f"{WEIGHTS[key]*100:.0f}%",
                "Weighted": f"{sec['score'] * WEIGHTS[key]:.1f}"
                            if sec["score"] is not None else "—",
                "Status": "✅" if sec["score"] is not None else "⏳",
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Raw JSON (debug) ──────────────────────────────────────
    with st.expander("🔧 Raw Report JSON"):
        st.json(report)
