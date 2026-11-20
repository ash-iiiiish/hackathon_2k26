from datetime import date, datetime, timedelta
from typing import List, Optional
from src.models import Topic, DailyPlanItem, ContentType, UserProfile


def days_until(exam_date: Optional[date]) -> int:
    if not exam_date:
        return 30  # default horizon
    delta = (exam_date - date.today()).days
    return max(1, delta)


def calculate_priority(topic: Topic, exam_date: Optional[date], available_hours: float) -> float:
    """
    Priority Score (higher = study sooner)
    Factors:
    - Low mastery → higher priority
    - High weightage → higher priority
    - Days until exam → urgency multiplier
    - Time since last study (spaced repetition)
    - Difficulty
    """
    days_left = days_until(exam_date)

    # Mastery gap (0-100 scale inverted)
    mastery_gap = 100 - topic.mastery

    # Urgency based on remaining days
    urgency = 1.0 + (30 / max(days_left, 1)) * 0.5

    # Spaced repetition bonus
    spaced_bonus = 0.0
    if topic.last_studied:
        days_since = (datetime.now() - topic.last_studied).days
        if days_since >= 3 and topic.mastery < 80:
            spaced_bonus = min(25, days_since * 4)
        elif days_since >= 7:
            spaced_bonus = 15
    else:
        spaced_bonus = 20  # never studied

    # Weightage & difficulty
    weight_factor = topic.weightage * 12
    difficulty_factor = topic.difficulty * 5

    score = (mastery_gap * 0.45) + weight_factor + difficulty_factor + spaced_bonus
    score *= urgency

    return round(score, 2)


def recommend_content_type(topic: Topic) -> ContentType:
    """Decide the best content format based on current mastery."""
    if topic.mastery < 25:
        return ContentType.EXPLANATION
    elif topic.mastery < 50:
        return ContentType.SUMMARY
    elif topic.mastery < 75:
        return ContentType.QUIZ
    else:
        return ContentType.FLASHCARDS


def generate_daily_plan(
    topics: List[Topic],
    profile: UserProfile,
    max_items: int = 5
) -> List[DailyPlanItem]:
    """Create a prioritized daily study plan."""
    if not topics:
        return []

    scored = []
    for t in topics:
        p_score = calculate_priority(t, profile.exam_date, profile.daily_available_hours)
        content = recommend_content_type(t)
        reason = _build_reason(t, p_score, content)
        scored.append(
            DailyPlanItem(
                topic=t,
                priority_score=p_score,
                recommended_content=content,
                reason=reason,
                estimated_minutes=t.estimated_minutes
            )
        )

    # Sort by priority descending
    scored.sort(key=lambda x: x.priority_score, reverse=True)

    # Respect available time roughly
    available_minutes = int(profile.daily_available_hours * 60)
    plan = []
    used = 0
    for item in scored:
        if len(plan) >= max_items:
            break
        if used + item.estimated_minutes <= available_minutes + 20:  # small buffer
            plan.append(item)
            used += item.estimated_minutes
        elif not plan:  # always include at least one
            plan.append(item)
            break

    return plan


def _build_reason(topic: Topic, score: float, content: ContentType) -> str:
    reasons = []
    if topic.mastery < 30:
        reasons.append("Low mastery – needs foundational work")
    elif topic.mastery < 60:
        reasons.append("Medium mastery – practice required")
    else:
        reasons.append("Good mastery – revision recommended")

    if topic.weightage >= 3:
        reasons.append("High exam weightage")
    if topic.last_studied is None:
        reasons.append("Not studied yet")
    elif (datetime.now() - topic.last_studied).days >= 5:
        reasons.append("Due for spaced revision")

    content_map = {
        ContentType.EXPLANATION: "Start with clear explanation",
        ContentType.SUMMARY: "Review condensed summary",
        ContentType.QUIZ: "Test understanding with quiz",
        ContentType.FLASHCARDS: "Quick flashcard revision",
        ContentType.DRILL: "Targeted weak-area drill"
    }
    reasons.append(content_map.get(content, ""))

    return " • ".join(reasons)