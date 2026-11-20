# Adaptive AI Tutor

**Your Personal Intelligent Study Companion**

A priority-driven AI tutoring system that plans, teaches, tracks mastery, and adapts daily according to each student’s needs.

---

## What It Does

- Builds a **dynamic daily study plan** based on mastery gaps, exam weightage, and spaced repetition
- Serves the right content format (Explanation → Summary → Quiz → Flashcards)
- Continuously tracks **topic-wise mastery (0–100)**
- Shows clear **progress charts** and weak-area analysis
- Works in **Demo Mode** without any API keys
- Uses **free Groq API** (Llama 3.3 70B) when you add a free key

---

## Tech Stack

| Layer            | Technology                          | Cost      |
|------------------|-------------------------------------|-----------|
| Frontend         | Streamlit (dark professional UI)    | Free      |
| Backend Logic    | Pure Python                         | Free      |
| LLM (recommended)| **Groq** (Llama 3.3 / Mixtral)      | **Free tier** |
| Charts           | Plotly                              | Free      |

Main language: **Python**

---

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional but recommended) Add free Groq key
cp .env.example .env
# Get free key → https://console.groq.com/keys
# Paste it into .env as GROQ_API_KEY=gsk_...

# 4. Run the app
streamlit run app.py
```

---

## Free API Setup (Groq)

1. Go to [https://console.groq.com/keys](https://console.groq.com/keys)
2. Sign up (free)
3. Create an API key
4. Put it in `.env`:

```env
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
LLM_PROVIDER=groq
```

**Recommended free models on Groq:**
- `llama-3.3-70b-versatile` → best quality
- `llama-3.1-8b-instant` → fastest
- `gemma2-9b-it`
- `mixtral-8x7b-32768`

No credit card required for the free tier.

---

## Demo Mode vs Live Mode

| Mode       | Condition                  | Behavior                          |
|------------|----------------------------|-----------------------------------|
| Demo Mode  | No API key                 | High-quality rule-based content   |
| Live Mode  | GROQ_API_KEY present       | Real LLM generation via Groq      |

---

## Project Structure

```
adaptive_ai_tutor/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Only free / lightweight packages
├── .env.example
├── README.md
└── src/
    ├── config.py
    ├── models.py
    ├── database.py
    ├── priority_engine.py
    ├── mastery.py
    ├── content_generator.py   # Groq-first + demo fallbacks
    └── sample_data.py
```

---

## Core Features

✅ Priority-based daily plan  
✅ Adaptive content (Explanation / Summary / Quiz / Flashcards)  
✅ Mastery tracking (0–100)  
✅ Progress dashboard + charts  
✅ Weak area highlighting  
✅ Clean dark professional UI  
✅ Works fully offline in Demo Mode  
✅ Free Groq LLM support  

---

Built for students who want a real adaptive tutor — not just another chatbot.
