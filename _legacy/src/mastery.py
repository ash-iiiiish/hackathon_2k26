from typing import List, Optional
from src.models import Topic, StudySession, ProgressSummary, UserProfile
from src.database import load_topics, load_sessions, update_topic_mastery


def update_mastery_after_session(
    topic_id: str,
    content_type: str,
    quiz_score: Optional[float] = None,
    time_spent: int = 20
) -> float:
    """
    Update mastery score after a study session.
    Returns the new mastery value.
    """
    topics = load_topics()
    topic = next((t for t in topics if t.id == topic_id), None)
    if not topic:
        return 0.0

    current = topic.mastery

    if quiz_score is not None:
        # Quiz has strongest signal
        if quiz_score >= 85:
            delta = 18
        elif quiz_score >= 70:
            delta = 12
        elif quiz_score >= 50:
            delta = 6
        else:
            delta = -8  # penalty for poor performance
        new_mastery = current + delta
    else:
        # Passive study (explanation / summary / flashcards)
        if content_type == "explanation":
            delta = 10
        elif content_type == "summary":
            delta = 7
        elif content_type == "flashcards":
            delta = 5
        else:
            delta = 4
        new_mastery = current + delta

    # Small bonus for consistent study
    if topic.times_studied > 0:
        new_mastery += 2

    new_mastery = max(0.0, min(100.0, new_mastery))
    update_topic_mastery(topic_id, new_mastery, quiz_score)
    return new_mastery


def compute_progress(topics: List[Topic], sessions: List[StudySession]) -> ProgressSummary:
    if not topics:
        return ProgressSummary(
            overall_mastery=0.0,
            topics_completed=0,
            total_topics=0,
            subjects_progress={},
            weak_topics=[],
            strong_topics=[],
            study_streak_days=0,
            total_study_minutes=0
        )

    overall = sum(t.mastery for t in topics) / len(topics)
    completed = sum(1 for t in topics if t.mastery >= 70)

    # Subject-wise
    subjects = {}
    for t in topics:
        if t.subject not in subjects:
            subjects[t.subject] = []
        subjects[t.subject].append(t.mastery)
    subjects_progress = {k: round(sum(v) / len(v), 1) for k, v in subjects.items()}

    weak = sorted([t for t in topics if t.mastery < 50], key=lambda x: x.mastery)[:6]
    strong = sorted([t for t in topics if t.mastery >= 75], key=lambda x: x.mastery, reverse=True)[:6]

    total_minutes = sum(s.duration_minutes for s in sessions)

    return ProgressSummary(
        overall_mastery=round(overall, 1),
        topics_completed=completed,
        total_topics=len(topics),
        subjects_progress=subjects_progress,
        weak_topics=weak,
        strong_topics=strong,
        study_streak_days=_estimate_streak(sessions),
        total_study_minutes=total_minutes
    )


def _estimate_streak(sessions: List[StudySession]) -> int:
    if not sessions:
        return 0
    # Simple approximation: unique days studied in last 14 days
    days = set()
    for s in sessions:
        days.add(s.completed_at.date())
    return min(len(days), 14)