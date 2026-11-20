from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class ContentType(str, Enum):
    EXPLANATION = "explanation"
    SUMMARY = "summary"
    QUIZ = "quiz"
    FLASHCARDS = "flashcards"
    DRILL = "drill"


class Topic(BaseModel):
    id: str
    subject: str
    title: str
    description: str = ""
    weightage: float = 1.0          # relative importance (1-5)
    difficulty: float = 1.0         # 1=easy, 3=hard
    estimated_minutes: int = 30
    mastery: float = 0.0            # 0-100
    last_studied: Optional[datetime] = None
    times_studied: int = 0
    correct_answers: int = 0
    total_attempts: int = 0


class StudySession(BaseModel):
    topic_id: str
    content_type: ContentType
    duration_minutes: int = 0
    score: Optional[float] = None   # quiz accuracy 0-100
    completed_at: datetime = Field(default_factory=datetime.now)
    notes: str = ""


class UserProfile(BaseModel):
    name: str = "Student"
    exam_date: Optional[date] = None
    daily_available_hours: float = 3.0
    subjects: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)


class DailyPlanItem(BaseModel):
    topic: Topic
    priority_score: float
    recommended_content: ContentType
    reason: str
    estimated_minutes: int


class ProgressSummary(BaseModel):
    overall_mastery: float
    topics_completed: int
    total_topics: int
    subjects_progress: dict
    weak_topics: List[Topic]
    strong_topics: List[Topic]
    study_streak_days: int = 0
    total_study_minutes: int = 0