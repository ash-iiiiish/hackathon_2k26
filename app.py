"""
Adaptive AI Tutor
A priority-driven intelligent study companion.
"""

import streamlit as st
from datetime import date, datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import uuid
import os
import sys

# Ensure src is importable
sys.path.insert(0, os.path.dirname(__file__))

from hackathon_2k26.src.models import Topic, StudySession, ContentType, UserProfile
from hackathon_2k26.src.database import (
    load_profile, save_profile, load_topics, save_topics,
    load_sessions, add_session, update_topic_mastery
)
from hackathon_2k26.src.priority_engine import generate_daily_plan, recommend_content_type
from hackathon_2k26.src.mastery import update_mastery_after_session, compute_progress
from hackathon_2k26.src.content_generator import (
    generate_explanation, generate_summary,
    generate_quiz, generate_flashcards
)
from hackathon_2k26.src.sample_data import get_or_create_sample, create_sample_curriculum
from hackathon_2k26.src.config import APP_NAME, APP_TAGLINE, DEMO_MODE

# -------------------- Page Config --------------------
st.set_page_config(
    page_title="Adaptive AI Tutor",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- Custom Dark Theme CSS --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-primary: #0a0e17;
    --bg-secondary: #111827;
    --bg-card: #1a2234;
    --bg-card-hover: #1f2a40;
    --accent: #22d3ee;
    --accent-dim: #0891b2;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --border: #1e293b;
    --success: #34d399;
    --warning: #fbbf24;
    --danger: #f87171;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(180deg, #0a0e17 0%, #0f172a 100%);
    color: var(--text-primary);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0b1220 !important;
    border-right: 1px solid var(--border);
}

section[data-testid="stSidebar"] .stMarkdown {
    color: var(--text-secondary);
}

/* Headers */
h1, h2, h3 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em;
    color: var(--text-primary) !important;
}

/* Cards */
.tutor-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s ease;
}

.tutor-card:hover {
    border-color: #334155;
}

.priority-card {
    background: linear-gradient(135deg, #1a2234 0%, #0f172a 100%);
    border: 1px solid #1e293b;
    border-left: 3px solid var(--accent);
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.85rem;
}

.metric-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.2rem;
    text-align: center;
}

.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--accent);
    font-family: 'JetBrains Mono', monospace;
}

.metric-label {
    font-size: 0.8rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.25rem;
}

.tag {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 500;
    margin-right: 0.4rem;
}

.tag-cyan { background: rgba(34, 211, 238, 0.15); color: #22d3ee; }
.tag-green { background: rgba(52, 211, 153, 0.15); color: #34d399; }
.tag-amber { background: rgba(251, 191, 36, 0.15); color: #fbbf24; }
.tag-red { background: rgba(248, 113, 113, 0.15); color: #f87171; }

.stButton > button {
    background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 500;
    padding: 0.5rem 1.2rem;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
    box-shadow: 0 0 20px rgba(34, 211, 238, 0.25);
}

/* Progress bars */
.stProgress > div > div {
    background: linear-gradient(90deg, #0891b2, #22d3ee);
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Input fields */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    background: #1a2234 !important;
    border: 1px solid #1e293b !important;
    color: #f1f5f9 !important;
    border-radius: 8px;
}

/* Expander */
.streamlit-expanderHeader {
    background: var(--bg-card);
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)


# -------------------- Session State Init --------------------
def init_state():
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.page = "home"
        st.session_state.current_topic = None
        st.session_state.current_content = None
        st.session_state.quiz_data = None
        st.session_state.quiz_answers = {}
        st.session_state.flashcards = None
        st.session_state.fc_index = 0
        st.session_state.show_answer = False

        # Load or create sample data
        topics, profile = get_or_create_sample()
        st.session_state.topics = topics
        st.session_state.profile = profile
        st.session_state.sessions = load_sessions()


init_state()


# -------------------- Sidebar --------------------
with st.sidebar:
    st.markdown(f"""
    <div style="padding: 1rem 0 1.5rem 0;">
        <div style="font-size: 1.4rem; font-weight: 700; color: #22d3ee; letter-spacing: -0.03em;">
            ◈ {APP_NAME}
        </div>
        <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.2rem;">
            {APP_TAGLINE}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    nav = st.radio(
        "Navigation",
        ["🏠  Dashboard", "📋  Today's Focus", "📖  Study Session", "📊  Progress", "⚙️  Settings"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    profile = st.session_state.profile
    days_left = (profile.exam_date - date.today()).days if profile.exam_date else "—"
    st.markdown(f"""
    <div style="font-size: 0.85rem; color: #94a3b8;">
        <div style="margin-bottom: 0.4rem;">👤 <b style="color:#e2e8f0;">{profile.name}</b></div>
        <div style="margin-bottom: 0.4rem;">📅 Exam in <b style="color:#22d3ee;">{days_left}</b> days</div>
        <div>⏱️ {profile.daily_available_hours}h / day available</div>
    </div>
    """, unsafe_allow_html=True)

    if DEMO_MODE:
        st.markdown("""
        <div style="margin-top: 1.5rem; padding: 0.7rem; background: rgba(251,191,36,0.1);
                    border: 1px solid rgba(251,191,36,0.3); border-radius: 8px; font-size: 0.75rem; color: #fbbf24;">
            Demo Mode active<br>Add API keys in .env for live AI
        </div>
        """, unsafe_allow_html=True)


# -------------------- Helper: Mastery Color --------------------
def mastery_tag(m: float) -> str:
    if m >= 75:
        return f'<span class="tag tag-green">{m:.0f}%</span>'
    elif m >= 45:
        return f'<span class="tag tag-amber">{m:.0f}%</span>'
    else:
        return f'<span class="tag tag-red">{m:.0f}%</span>'


# -------------------- PAGE: DASHBOARD --------------------
if "Dashboard" in nav:
    st.markdown(f"""
    <h1 style="margin-bottom: 0.2rem;">Welcome back, {profile.name}</h1>
    <p style="color: #94a3b8; margin-bottom: 2rem;">Your adaptive study companion is ready.</p>
    """, unsafe_allow_html=True)

    topics = st.session_state.topics
    sessions = st.session_state.sessions
    progress = compute_progress(topics, sessions)

    # Metrics row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{progress.overall_mastery}%</div>
            <div class="metric-label">Overall Mastery</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{progress.topics_completed}/{progress.total_topics}</div>
            <div class="metric-label">Topics Ready</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{progress.total_study_minutes}</div>
            <div class="metric-label">Minutes Studied</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{days_left}</div>
            <div class="metric-label">Days to Exam</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Two columns: Subject progress + Weak areas
    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("#### Subject Mastery")
        if progress.subjects_progress:
            df = pd.DataFrame({
                "Subject": list(progress.subjects_progress.keys()),
                "Mastery": list(progress.subjects_progress.values())
            })
            fig = px.bar(
                df, x="Mastery", y="Subject", orientation="h",
                color="Mastery", color_continuous_scale=["#f87171", "#fbbf24", "#34d399"],
                range_color=[0, 100]
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#94a3b8",
                coloraxis_showscale=False,
                margin=dict(l=0, r=20, t=10, b=10),
                height=280,
                xaxis=dict(gridcolor="#1e293b", range=[0, 100]),
                yaxis=dict(gridcolor="#1e293b")
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No subjects yet.")

    with right:
        st.markdown("#### Focus Areas (Weak)")
        if progress.weak_topics:
            for t in progress.weak_topics[:5]:
                st.markdown(f"""
                <div class="tutor-card" style="padding: 0.8rem 1rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-weight:600; color:#e2e8f0;">{t.title}</div>
                            <div style="font-size:0.75rem; color:#64748b;">{t.subject}</div>
                        </div>
                        {mastery_tag(t.mastery)}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No critical weak areas. Great work!")

    # Quick action
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("→ Go to Today's Focus", use_container_width=False):
        st.session_state.page = "focus"
        st.rerun()


# -------------------- PAGE: TODAY'S FOCUS --------------------
elif "Today" in nav:
    st.markdown("""
    <h1 style="margin-bottom: 0.3rem;">Today's Focus</h1>
    <p style="color: #94a3b8; margin-bottom: 1.8rem;">
        Prioritized by mastery gap, exam weightage, and spaced repetition.
    </p>
    """, unsafe_allow_html=True)

    topics = st.session_state.topics
    profile = st.session_state.profile
    plan = generate_daily_plan(topics, profile, max_items=5)

    if not plan:
        st.warning("No topics available. Load sample data from Settings.")
    else:
        total_mins = sum(item.estimated_minutes for item in plan)
        st.markdown(f"""
        <div style="color:#64748b; font-size:0.85rem; margin-bottom:1.2rem;">
            {len(plan)} topics • ~{total_mins} minutes estimated
        </div>
        """, unsafe_allow_html=True)

        for i, item in enumerate(plan, 1):
            t = item.topic
            content_label = item.recommended_content.value.replace("_", " ").title()

            col_main, col_btn = st.columns([4, 1])
            with col_main:
                st.markdown(f"""
                <div class="priority-card">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <span style="color:#64748b; font-size:0.75rem; font-weight:600;">#{i}</span>
                            <span style="font-weight:600; color:#f1f5f9; margin-left:0.5rem;">{t.title}</span>
                        </div>
                        {mastery_tag(t.mastery)}
                    </div>
                    <div style="margin-top:0.5rem; font-size:0.8rem; color:#94a3b8;">
                        {t.subject} • {item.estimated_minutes} min • 
                        <span class="tag tag-cyan">{content_label}</span>
                    </div>
                    <div style="margin-top:0.45rem; font-size:0.78rem; color:#64748b;">
                        {item.reason}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_btn:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Study", key=f"study_{t.id}", use_container_width=True):
                    st.session_state.current_topic = t
                    st.session_state.current_content = item.recommended_content
                    st.session_state.quiz_data = None
                    st.session_state.flashcards = None
                    st.session_state.quiz_answers = {}
                    st.session_state.fc_index = 0
                    st.session_state.show_answer = False
                    # Force navigation feel
                    st.session_state.force_study = True
                    st.rerun()


# -------------------- PAGE: STUDY SESSION --------------------
elif "Study" in nav or st.session_state.get("force_study"):
    st.session_state.force_study = False
    topic = st.session_state.current_topic

    if topic is None:
        st.info("Select a topic from **Today's Focus** to begin a study session.")
        st.stop()

    content_type = st.session_state.current_content or recommend_content_type(topic)

    st.markdown(f"""
    <h1 style="margin-bottom: 0.2rem;">{topic.title}</h1>
    <p style="color: #94a3b8; margin-bottom: 1.5rem;">
        {topic.subject} • Current mastery {mastery_tag(topic.mastery)} • 
        Recommended: <span class="tag tag-cyan">{content_type.value.title()}</span>
    </p>
    """, unsafe_allow_html=True)

    # Content type selector
    ctype = st.radio(
        "Content format",
        ["Explanation", "Summary", "Quiz", "Flashcards"],
        horizontal=True,
        index=["explanation", "summary", "quiz", "flashcards"].index(content_type.value)
        if content_type.value in ["explanation", "summary", "quiz", "flashcards"] else 0
    )

    st.markdown("---")

    # ----- EXPLANATION -----
    if ctype == "Explanation":
        with st.spinner("Generating clear explanation..."):
            text = generate_explanation(topic)
        st.markdown(text)

        if st.button("Mark as Studied ✓", type="primary"):
            new_m = update_mastery_after_session(topic.id, "explanation", time_spent=25)
            add_session(StudySession(
                topic_id=topic.id,
                content_type=ContentType.EXPLANATION,
                duration_minutes=25
            ))
            # Refresh topics
            st.session_state.topics = load_topics()
            st.success(f"Mastery updated → {new_m:.0f}%")
            st.balloons()

    # ----- SUMMARY -----
    elif ctype == "Summary":
        with st.spinner("Creating revision summary..."):
            text = generate_summary(topic)
        st.markdown(text)

        if st.button("Mark as Reviewed ✓", type="primary"):
            new_m = update_mastery_after_session(topic.id, "summary", time_spent=15)
            add_session(StudySession(
                topic_id=topic.id,
                content_type=ContentType.SUMMARY,
                duration_minutes=15
            ))
            st.session_state.topics = load_topics()
            st.success(f"Mastery updated → {new_m:.0f}%")

    # ----- QUIZ -----
    elif ctype == "Quiz":
        if st.session_state.quiz_data is None:
            with st.spinner("Generating quiz questions..."):
                st.session_state.quiz_data = generate_quiz(topic, num_questions=4)

        quiz = st.session_state.quiz_data
        answers = st.session_state.quiz_answers

        for i, q in enumerate(quiz):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            choice = st.radio(
                f"q_{i}",
                q["options"],
                key=f"quiz_opt_{topic.id}_{i}",
                label_visibility="collapsed"
            )
            answers[i] = choice
            st.markdown("")

        if st.button("Submit Quiz", type="primary"):
            correct = 0
            results = []
            for i, q in enumerate(quiz):
                user_ans = answers.get(i, "")
                # Extract letter (A/B/C/D)
                user_letter = user_ans[0] if user_ans else ""
                is_correct = user_letter == q["answer"]
                if is_correct:
                    correct += 1
                results.append((is_correct, q))

            score = (correct / len(quiz)) * 100
            st.markdown(f"### Score: {correct}/{len(quiz)} ({score:.0f}%)")

            for i, (is_correct, q) in enumerate(results):
                icon = "✅" if is_correct else "❌"
                st.markdown(f"{icon} **Q{i+1}** — Correct answer: **{q['answer']}**")
                st.caption(q.get("explanation", ""))

            new_m = update_mastery_after_session(topic.id, "quiz", quiz_score=score, time_spent=20)
            add_session(StudySession(
                topic_id=topic.id,
                content_type=ContentType.QUIZ,
                duration_minutes=20,
                score=score
            ))
            st.session_state.topics = load_topics()
            st.session_state.current_topic = next(t for t in st.session_state.topics if t.id == topic.id)
            st.success(f"Mastery updated → {new_m:.0f}%")

    # ----- FLASHCARDS -----
    elif ctype == "Flashcards":
        if st.session_state.flashcards is None:
            with st.spinner("Creating flashcards..."):
                st.session_state.flashcards = generate_flashcards(topic)

        cards = st.session_state.flashcards
        idx = st.session_state.fc_index

        if cards:
            card = cards[idx % len(cards)]
            st.markdown(f"""
            <div class="tutor-card" style="min-height: 160px; display:flex; align-items:center; justify-content:center; text-align:center;">
                <div>
                    <div style="font-size:0.75rem; color:#64748b; margin-bottom:0.8rem;">
                        Card {idx % len(cards) + 1} / {len(cards)}
                    </div>
                    <div style="font-size:1.25rem; font-weight:600; color:#f1f5f9;">
                        {card['front']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.show_answer:
                st.info(f"**Answer:** {card['back']}")

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Show Answer"):
                    st.session_state.show_answer = True
                    st.rerun()
            with c2:
                if st.button("← Previous"):
                    st.session_state.fc_index = max(0, idx - 1)
                    st.session_state.show_answer = False
                    st.rerun()
            with c3:
                if st.button("Next →"):
                    st.session_state.fc_index = idx + 1
                    st.session_state.show_answer = False
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Finish Flashcard Session ✓", type="primary"):
                new_m = update_mastery_after_session(topic.id, "flashcards", time_spent=12)
                add_session(StudySession(
                    topic_id=topic.id,
                    content_type=ContentType.FLASHCARDS,
                    duration_minutes=12
                ))
                st.session_state.topics = load_topics()
                st.success(f"Mastery updated → {new_m:.0f}%")


# -------------------- PAGE: PROGRESS --------------------
elif "Progress" in nav:
    st.markdown("""
    <h1 style="margin-bottom: 0.3rem;">Progress Analytics</h1>
    <p style="color: #94a3b8; margin-bottom: 1.8rem;">
        Track mastery, identify weak areas, and measure consistency.
    </p>
    """, unsafe_allow_html=True)

    topics = st.session_state.topics
    sessions = load_sessions()
    progress = compute_progress(topics, sessions)

    # Overall ring-like metric
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Overall Mastery", f"{progress.overall_mastery}%")
    with c2:
        st.metric("Topics ≥ 70%", f"{progress.topics_completed} / {progress.total_topics}")
    with c3:
        st.metric("Total Study Time", f"{progress.total_study_minutes} min")

    st.markdown("---")

    # Subject radar / bars
    if progress.subjects_progress:
        st.markdown("#### Subject-wise Mastery")
        df = pd.DataFrame({
            "Subject": list(progress.subjects_progress.keys()),
            "Mastery %": list(progress.subjects_progress.values())
        })
        fig = go.Figure(go.Bar(
            x=df["Subject"],
            y=df["Mastery %"],
            marker_color=["#22d3ee" if v >= 60 else "#fbbf24" if v >= 35 else "#f87171" for v in df["Mastery %"]]
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8",
            yaxis=dict(range=[0, 100], gridcolor="#1e293b"),
            xaxis=dict(gridcolor="#1e293b"),
            height=320,
            margin=dict(t=20, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    # All topics table-like view
    st.markdown("#### All Topics")
    for t in sorted(topics, key=lambda x: x.mastery):
        color = "#34d399" if t.mastery >= 70 else "#fbbf24" if t.mastery >= 40 else "#f87171"
        st.markdown(f"""
        <div style="display:flex; align-items:center; margin-bottom:0.6rem;">
            <div style="width:220px; font-size:0.9rem; color:#e2e8f0;">{t.title}</div>
            <div style="flex:1; background:#1e293b; border-radius:4px; height:8px; margin:0 1rem;">
                <div style="width:{t.mastery}%; background:{color}; height:8px; border-radius:4px;"></div>
            </div>
            <div style="width:50px; text-align:right; font-family:'JetBrains Mono',monospace; color:{color};">
                {t.mastery:.0f}%
            </div>
        </div>
        """, unsafe_allow_html=True)


# -------------------- PAGE: SETTINGS --------------------
elif "Settings" in nav:
    st.markdown("""
    <h1 style="margin-bottom: 0.3rem;">Settings</h1>
    <p style="color: #94a3b8; margin-bottom: 1.8rem;">Profile and data management.</p>
    """, unsafe_allow_html=True)

    profile = st.session_state.profile

    with st.form("profile_form"):
        name = st.text_input("Your Name", value=profile.name)
        exam = st.date_input(
            "Exam Date",
            value=profile.exam_date or (date.today() + timedelta(days=21))
        )
        hours = st.slider("Daily Available Hours", 1.0, 8.0, float(profile.daily_available_hours), 0.5)

        if st.form_submit_button("Save Profile"):
            profile.name = name
            profile.exam_date = exam
            profile.daily_available_hours = hours
            save_profile(profile)
            st.session_state.profile = profile
            st.success("Profile updated.")

    st.markdown("---")
    st.markdown("#### Data")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Reload Sample Curriculum"):
            topics, profile = create_sample_curriculum()
            st.session_state.topics = topics
            st.session_state.profile = profile
            st.session_state.sessions = []
            st.success("Sample curriculum loaded.")
            st.rerun()

    with col_b:
        if st.button("Reset All Progress"):
            for t in st.session_state.topics:
                t.mastery = 0.0
                t.times_studied = 0
                t.last_studied = None
            save_topics(st.session_state.topics)
            st.session_state.sessions = []
            st.success("Progress reset.")
            st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.8rem; color:#64748b;">
        <b>Tech Stack</b><br>
        Python • Streamlit • LangChain / LangGraph ready • 
        LlamaIndex compatible • ChromaDB • Plotly<br><br>
        Add <code>OPENAI_API_KEY</code> or <code>GOOGLE_API_KEY</code> in <code>.env</code> 
        to enable live LLM generation. Demo mode works without keys.
    </div>
    """, unsafe_allow_html=True)