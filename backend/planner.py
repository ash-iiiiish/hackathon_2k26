"""Roadmap planning.

standard_plan  - spreads every topic across the days until the exam, highest
                 priority first, with spaced revision (+1 practice, +3 and +7 revise)
                 and a final full-revision day.
crisis_plan    - when time is short (e.g. exam tomorrow): picks the topics that
                 give the most marks per minute, compresses them into 25/5 sprints,
                 keeps a protected sleep cutoff, and ends with a rapid-recall block.
assess         - compares the time needed with the time left and decides whether
                 the student should switch to crisis mode.

All times are naive local datetimes (the calendar is shown in the student's timezone).
"""
import math
from datetime import date, datetime, time, timedelta

BLOCK = 50          # standard focus block (minutes)
BREAK = 10
SPRINT = 25         # crisis pomodoro
SPRINT_BREAK = 5
REVISION_MIN = 20
REVISION_OFFSETS = [(1, "practice"), (3, "revise"), (7, "revise")]


def round5(x):
    return int(5 * math.ceil(x / 5))


def need_minutes(t):
    """Minutes still needed to learn a topic properly, given current mastery."""
    if t["mastery"] >= 85:
        return 0
    gap = 1 - t["mastery"] / 100
    return max(15, round5(t["est_minutes"] * gap * (0.8 + 0.2 * t["difficulty"])))


def priority(t):
    gap = 1 - t["mastery"] / 100 + 0.15
    never = 1.2 if not t.get("times_studied") else 1.0
    return t["weightage"] * gap * (1 + (t["difficulty"] - 1) * 0.15) * never


def _to_time(v, default):
    if isinstance(v, time):
        return v
    try:
        return datetime.strptime(str(v)[:5], "%H:%M").time()
    except (TypeError, ValueError):
        return default


def _next_quarter(dt):
    dt = dt.replace(second=0, microsecond=0)
    extra = (15 - dt.minute % 15) % 15
    return dt + timedelta(minutes=extra)


def _day_window(student, day, now):
    """(start, end) of the study window on a given day."""
    start = datetime.combine(day, _to_time(student["study_start"], time(17)))
    sleep = datetime.combine(day, _to_time(student["sleep_time"], time(23)))
    if sleep <= start:
        sleep += timedelta(days=1)
    if day == now.date():
        start = max(start, _next_quarter(now + timedelta(minutes=5)))
    end = min(sleep, start + timedelta(minutes=student["daily_hours"] * 60))
    return start, end


# ------------------------------------------------------------------ assessment

def assess(student, topics, now=None):
    now = now or datetime.now()
    exam = student.get("exam_date")
    needed = sum(need_minutes(t) for t in topics) + REVISION_MIN * 2 * len(topics)
    if not exam:
        return {"days_left": None, "needed_minutes": needed, "available_minutes": None,
                "recommend_crisis": False, "reason": "Set your exam date to build a roadmap."}
    days_left = (exam - now.date()).days
    available = 0
    for i in range(max(0, days_left)):
        s, e = _day_window(student, now.date() + timedelta(days=i), now)
        available += max(0, (e - s).total_seconds() / 60) * BLOCK / (BLOCK + BREAK)
    available = int(available)
    crisis = days_left <= 1 or (topics and needed > available)
    if days_left < 0:
        reason = "Your exam date has passed. Update it in Settings."
    elif days_left <= 1:
        reason = "Exam is tomorrow or today. Switch to crisis mode for a focused, high-yield plan."
    elif crisis:
        reason = (f"You need ~{needed // 60}h but have ~{available // 60}h of study time left. "
                  "Crisis mode will prioritise the highest-scoring topics.")
    else:
        reason = f"On track: ~{needed // 60}h needed, ~{available // 60}h available."
    return {"days_left": days_left, "needed_minutes": needed, "available_minutes": available,
            "recommend_crisis": bool(crisis), "reason": reason}


# ------------------------------------------------------------------ standard roadmap

def standard_plan(student, topics, now=None, exam_time=time(9, 0)):
    now = now or datetime.now()
    exam = student["exam_date"]
    days = (exam - now.date()).days
    if days < 1:
        raise ValueError("Exam is today or past — use crisis mode instead.")

    study_days = [now.date() + timedelta(days=i) for i in range(days)]
    final_day = len(study_days) - 1 if days >= 3 else None
    learn_days = study_days[:final_day] if final_day is not None else study_days

    queue = [{"t": t, "left": need_minutes(t), "need": need_minutes(t)}
             for t in sorted(topics, key=priority, reverse=True) if need_minutes(t) > 0]
    # day index -> [(topic, kind)]; already-mastered topics only get a light revision on day 0
    revisions = {0: [(t, "revise") for t in topics if need_minutes(t) == 0]}

    events, daily_load = [], []
    for i, day in enumerate(learn_days):
        start, end = _day_window(student, day, now)
        cursor_ = start
        minutes_today = 0
        capacity = max(0, int((end - start).total_seconds() // 60))

        def place(title, kind, topic, minutes, phase):
            nonlocal cursor_, minutes_today
            s = cursor_
            e = s + timedelta(minutes=minutes)
            if e > end:
                return False
            events.append({"title": title, "kind": kind, "topic_id": topic["id"] if topic else None,
                           "start_at": s, "end_at": e, "phase": phase})
            cursor_ = e
            minutes_today += minutes
            # a break after every focus block, unless the day is over
            if kind != "break" and cursor_ + timedelta(minutes=BREAK + 15) <= end:
                events.append({"title": "Break — stretch, water, eyes off screen", "kind": "break",
                               "topic_id": None, "start_at": cursor_,
                               "end_at": cursor_ + timedelta(minutes=BREAK), "phase": phase})
                cursor_ += timedelta(minutes=BREAK)
            return True

        # 1) due revisions first (capped at 40% of the day, the rest rolls over)
        due = revisions.pop(i, [])
        rev_budget = capacity * 0.4
        rolled = []
        for topic, kind in due:
            label = "Practice quiz" if kind == "practice" else "Revise"
            if rev_budget >= REVISION_MIN and place(f"{label}: {topic['title']}", kind, topic, REVISION_MIN, "revision"):
                rev_budget -= REVISION_MIN + BREAK
            else:
                rolled.append((topic, kind))
        if rolled:
            revisions.setdefault(i + 1, []).extend(rolled)

        # 2) new learning
        while queue:
            q = queue[0]
            remaining = int((end - cursor_).total_seconds() // 60)
            if remaining < 20:
                break
            chunk = min(BLOCK, q["left"], remaining)
            part = "Learn" if q["left"] == q["need"] else "Continue"
            place(f"{part}: {q['t']['title']}", "study", q["t"], chunk, "learn")
            q["left"] -= chunk
            if q["left"] <= 0:
                queue.pop(0)
                for offset, kind in REVISION_OFFSETS:
                    if i + offset < len(learn_days):
                        revisions.setdefault(i + offset, []).append((q["t"], kind))
        daily_load.append({"date": day.isoformat(), "minutes": minutes_today})

    # 3) final day: rapid revision of everything, highest weightage first
    if final_day is not None:
        day = study_days[final_day]
        start, end = _day_window(student, day, now)
        cursor_ = start
        minutes_today = 0
        for t in sorted(topics, key=lambda t: -t["weightage"]):
            if cursor_ + timedelta(minutes=REVISION_MIN) > end:
                break
            events.append({"title": f"Final revision: {t['title']}", "kind": "revise", "topic_id": t["id"],
                           "start_at": cursor_, "end_at": cursor_ + timedelta(minutes=REVISION_MIN),
                           "phase": "final"})
            cursor_ += timedelta(minutes=REVISION_MIN + 5)
            minutes_today += REVISION_MIN
        daily_load.append({"date": day.isoformat(), "minutes": minutes_today})

    exam_at = datetime.combine(exam, exam_time)
    events.append({"title": f"{student.get('exam_name') or 'Exam'}", "kind": "exam", "topic_id": None,
                   "start_at": exam_at, "end_at": exam_at + timedelta(hours=3), "phase": "exam"})

    unfinished = [{"title": q["t"]["title"], "minutes_left": q["left"]} for q in queue]
    study_minutes = sum((e["end_at"] - e["start_at"]).seconds // 60 for e in events if e["kind"] not in ("break", "exam"))
    summary = {
        "days": days,
        "study_minutes": study_minutes,
        "topics": len(topics),
        "unfinished": unfinished,
        "feasible": not unfinished,
        "daily_load": daily_load,
        "message": ("Every topic fits before the exam, with spaced revision and a final revision day."
                    if not unfinished else
                    f"{len(unfinished)} topic(s) don't fit. Increase daily hours or switch to crisis mode."),
    }
    return events, summary


# ------------------------------------------------------------------ crisis roadmap

def crisis_minutes(t):
    if t["mastery"] >= 80:
        return 10
    gap = 1 - (t["mastery"] / 100) * 0.7
    return max(15, round5(t["est_minutes"] * 0.35 * gap * (0.8 + 0.2 * t["difficulty"])))


def crisis_plan(student, topics, hours, exam_at, now=None):
    now = now or datetime.now()
    start = _next_quarter(now + timedelta(minutes=5))

    # protect sleep: never plan past the student's sleep time (or 01:00 at the latest)
    sleep_t = _to_time(student["sleep_time"], time(23))
    if start.hour < 5:                       # already past midnight: one last hour, then sleep
        sleep_at = start + timedelta(hours=1)
    else:
        sleep_at = datetime.combine(start.date(), sleep_t)
        if sleep_at <= start:
            sleep_at = start + timedelta(minutes=45)
    if exam_at - start >= timedelta(hours=8):
        sleep_at = min(sleep_at, exam_at - timedelta(hours=7))
    else:                                    # exam in a few hours: no night left to protect
        sleep_at = exam_at - timedelta(minutes=30)
    requested_end = start + timedelta(hours=hours)
    end = max(start, min(requested_end, sleep_at))
    capped = requested_end > end

    total = max(0, int((end - start).total_seconds() // 60))
    recall = 15 if total >= 60 else 0
    focus_budget = int((total - recall) * SPRINT / (SPRINT + SPRINT_BREAK))

    scored = []
    for t in topics:
        m = crisis_minutes(t)
        value = t["weightage"] * (1 - t["mastery"] / 100 + 0.1)
        scored.append({"t": t, "minutes": m, "value": value, "ratio": value / m})
    scored.sort(key=lambda s: (s["ratio"], s["t"]["weightage"]), reverse=True)

    picked, used = [], 0
    for s in scored:
        if used + s["minutes"] <= focus_budget:
            picked.append(s)
            used += s["minutes"]
    picked_ids = {s["t"]["id"] for s in picked}

    def bucket(s):
        if s["t"]["id"] in picked_ids:
            return "must" if s["t"]["weightage"] >= 4 else "should"
        return "skim" if s["t"]["weightage"] >= 3 else "skip"

    triage = {"must": [], "should": [], "skim": [], "skip": []}
    for s in scored:
        triage[bucket(s)].append({"id": s["t"]["id"], "title": s["t"]["title"], "minutes": s["minutes"],
                                  "weightage": s["t"]["weightage"], "mastery": s["t"]["mastery"]})

    # hardest high-weightage topics while fresh, quick wins later
    order = sorted(picked, key=lambda s: (-s["t"]["weightage"], -s["t"]["difficulty"]))
    events, cursor_ = [], start
    sprint_left = SPRINT
    for s in order:
        left = s["minutes"]
        while left > 0:
            chunk = min(left, sprint_left)
            events.append({"title": f"Sprint: {s['t']['title']}", "kind": "study", "topic_id": s["t"]["id"],
                           "start_at": cursor_, "end_at": cursor_ + timedelta(minutes=chunk), "phase": "crisis"})
            cursor_ += timedelta(minutes=chunk)
            left -= chunk
            sprint_left -= chunk
            if sprint_left <= 0:
                events.append({"title": "5-min break — breathe, water", "kind": "break", "topic_id": None,
                               "start_at": cursor_, "end_at": cursor_ + timedelta(minutes=SPRINT_BREAK),
                               "phase": "crisis"})
                cursor_ += timedelta(minutes=SPRINT_BREAK)
                sprint_left = SPRINT
    if recall:
        events.append({"title": "Rapid recall: cheat sheet + skim topics", "kind": "revise", "topic_id": None,
                       "start_at": cursor_, "end_at": cursor_ + timedelta(minutes=recall), "phase": "crisis"})
        cursor_ += timedelta(minutes=recall)
    lights_out = max(cursor_, end)
    if exam_at - lights_out >= timedelta(hours=6):
        events.append({"title": "Lights out — sleep locks in what you studied", "kind": "reminder",
                       "topic_id": None, "start_at": lights_out, "end_at": lights_out + timedelta(minutes=15),
                       "phase": "crisis"})
    warmup = exam_at - timedelta(minutes=90)
    if warmup > end:
        events.append({"title": "Morning glance: cheat sheet only (no new topics)", "kind": "revise",
                       "topic_id": None, "start_at": warmup, "end_at": warmup + timedelta(minutes=20),
                       "phase": "crisis"})
    events.append({"title": student.get("exam_name") or "Exam", "kind": "exam", "topic_id": None,
                   "start_at": exam_at, "end_at": exam_at + timedelta(hours=3), "phase": "exam"})

    coverage = sum(s["t"]["weightage"] for s in picked) / max(1, sum(t["weightage"] for t in topics))
    summary = {
        "hours": round(total / 60, 1),
        "focus_minutes": used,
        "capped_for_sleep": capped,
        "weight_coverage": round(coverage * 100),
        "triage": triage,
        "message": (f"Covers ~{round(coverage * 100)}% of the exam weight in {round(total / 60, 1)}h."
                    + (" Plan stops at your sleep time — sleep improves recall more than another hour of cramming."
                       if capped else "")),
    }
    return events, summary
