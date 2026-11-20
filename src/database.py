import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional
from src.models import Topic, StudySession, UserProfile, ContentType
from src.config import DATA_DIR

os.makedirs(DATA_DIR, exist_ok=True)

PROFILE_PATH = os.path.join(DATA_DIR, "profile.json")
TOPICS_PATH = os.path.join(DATA_DIR, "topics.json")
SESSIONS_PATH = os.path.join(DATA_DIR, "sessions.json")


def _serialize(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, ContentType):
        return obj.value
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def save_profile(profile: UserProfile):
    with open(PROFILE_PATH, "w") as f:
        json.dump(profile.model_dump(), f, default=_serialize, indent=2)


def load_profile() -> Optional[UserProfile]:
    if not os.path.exists(PROFILE_PATH):
        return None
    with open(PROFILE_PATH, "r") as f:
        data = json.load(f)
    if data.get("exam_date"):
        data["exam_date"] = date.fromisoformat(data["exam_date"])
    if data.get("created_at"):
        data["created_at"] = datetime.fromisoformat(data["created_at"])
    return UserProfile(**data)


def save_topics(topics: List[Topic]):
    data = [t.model_dump() for t in topics]
    with open(TOPICS_PATH, "w") as f:
        json.dump(data, f, default=_serialize, indent=2)


def load_topics() -> List[Topic]:
    if not os.path.exists(TOPICS_PATH):
        return []
    with open(TOPICS_PATH, "r") as f:
        data = json.load(f)
    topics = []
    for item in data:
        if item.get("last_studied"):
            item["last_studied"] = datetime.fromisoformat(item["last_studied"])
        topics.append(Topic(**item))
    return topics


def save_sessions(sessions: List[StudySession]):
    data = [s.model_dump() for s in sessions]
    with open(SESSIONS_PATH, "w") as f:
        json.dump(data, f, default=_serialize, indent=2)


def load_sessions() -> List[StudySession]:
    if not os.path.exists(SESSIONS_PATH):
        return []
    with open(SESSIONS_PATH, "r") as f:
        data = json.load(f)
    sessions = []
    for item in data:
        if item.get("completed_at"):
            item["completed_at"] = datetime.fromisoformat(item["completed_at"])
        if item.get("content_type"):
            item["content_type"] = ContentType(item["content_type"])
        sessions.append(StudySession(**item))
    return sessions


def add_session(session: StudySession):
    sessions = load_sessions()
    sessions.append(session)
    save_sessions(sessions)


def update_topic_mastery(topic_id: str, new_mastery: float, score: Optional[float] = None):
    topics = load_topics()
    for t in topics:
        if t.id == topic_id:
            t.mastery = max(0.0, min(100.0, new_mastery))
            t.last_studied = datetime.now()
            t.times_studied += 1
            if score is not None:
                t.total_attempts += 1
                if score >= 70:
                    t.correct_answers += 1
            break
    save_topics(topics)
    return topics