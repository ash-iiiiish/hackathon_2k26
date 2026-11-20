# Adaptive AI Tutor

**Your Personal Intelligent Study Companion**

A priority-driven AI tutoring system that plans, teaches, tracks mastery, and adapts daily according to each student’s needs.

---

## What It Does

- Builds a **dynamic daily study plan** based on mastery gaps, exam weightage, and spaced repetition
- Serves the right content format (Explanation → Summary → Quiz → Flashcards)
- Continuously tracks **topic-wise mastery (0–100)**
- Shows clear **progress charts** and weak-area analysis
- Works in **Demo Mode** without any API keys (rule-based fallbacks)
- Switches to live LLM generation when you add OpenAI or Gemini keys

---

## Tech Stack

| Layer            | Technology                          |
|------------------|-------------------------------------|
| Frontend         | Streamlit (dark professional UI)    |
| Backend Logic    | Pure Python                         |
| AI Orchestration | LangChain / LangGraph ready         |
| RAG              | LlamaIndex compatible               |
| Vector Store     | ChromaDB (ready)                    |
| Charts           | Plotly                              |
| Data             | JSON persistence (easy to swap for Postgres) |

Main language: **Python**

---

## Quick Start

```bash
# 1. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Add API keys for live AI
cp .env.example .env
# Edit .env and add OPENAI_API_KEY or GOOGLE_API_KEY

# 4. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## Demo Mode vs Live Mode

- **No API keys** → Demo Mode (pre-written high-quality explanations, quizzes, flashcards)
- **With API keys** → Live LLM generation using GPT-4o-mini or Gemini

This makes the project demoable even offline or without keys.

---

## Project Structure

```
adaptive_ai_tutor/
├── app.py                  # Main Streamlit application
├── requirements.txt
├── .env.example
├── README.md
├── src/
│   ├── config.py           # Settings & feature flags
│   ├── models.py           # Pydantic data models
│   ├── database.py         # Persistence layer
│   ├── priority_engine.py  # Daily plan + priority scoring
│   ├── mastery.py          # Mastery update & progress analytics
│   ├── content_generator.py# LLM + demo content generation
│   └── sample_data.py      # Realistic sample curriculum
└── data/                   # Auto-created (profile, topics, sessions)
```

---

## Core Features Implemented

✅ User profile (name, exam date, available hours)  
✅ Sample Computer Science curriculum (OS, DBMS, Networks, Algorithms)  
✅ Priority engine (mastery + weightage + spaced repetition + urgency)  
✅ Today’s Focus (ranked daily plan)  
✅ Study Session (Explanation / Summary / Quiz / Flashcards)  
✅ Mastery tracking with live updates  
✅ Progress dashboard with charts  
✅ Weak-area highlighting  
✅ Clean dark professional UI  

---

## How the Priority Engine Works

```
Priority Score =
  (100 - mastery) * 0.45
  + weightage * 12
  + difficulty * 5
  + spaced_repetition_bonus
  × urgency_multiplier (based on days left to exam)
```

Content type is chosen automatically:
- Mastery < 25% → Explanation
- 25–50% → Summary
- 50–75% → Quiz
- > 75% → Flashcards

---

## Future Extensions (Easy to Add)

- Real RAG over uploaded PDF notes (LlamaIndex already in requirements)
- LangGraph multi-agent tutor (Planner + Teacher + Evaluator)
- Google Calendar sync for study blocks
- Voice mode
- Mobile-responsive PWA
- Teacher / parent dashboard

---

## For Hackathon Judges

This is **not** a ChatGPT wrapper.  

It is a closed-loop adaptive system:

**Plan → Teach → Assess → Update Mastery → Re-Plan**

The student no longer has to decide *what* to study.  
The system decides, teaches, measures, and improves continuously.

---

Built with ❤️ for students who want a real tutor, not just another chatbot.
