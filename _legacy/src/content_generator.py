import os
from typing import List, Dict, Optional
from src.models import Topic, ContentType
from src.config import (
    DEMO_MODE, LLM_PROVIDER,
    GROQ_API_KEY, GROQ_MODEL,
    OPENAI_API_KEY, GOOGLE_API_KEY, LLM_MODEL
)


def _get_llm():
    """
    Return an LLM instance.
    Priority: Groq (free) → OpenAI → Gemini → None (demo mode)
    """
    if DEMO_MODE:
        return None

    try:
        # 1. Groq (FREE & FAST) - recommended
        if LLM_PROVIDER == "groq" and GROQ_API_KEY:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model=GROQ_MODEL,
                api_key=GROQ_API_KEY,
                temperature=0.4,
                max_tokens=1024,
            )

        # 2. OpenAI (optional)
        if LLM_PROVIDER == "openai" and OPENAI_API_KEY:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=LLM_MODEL,
                api_key=OPENAI_API_KEY,
                temperature=0.4
            )

        # 3. Gemini (optional)
        if LLM_PROVIDER == "gemini" and GOOGLE_API_KEY:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=GOOGLE_API_KEY,
                temperature=0.4
            )

        # Fallback: try Groq if key exists even if provider setting is different
        if GROQ_API_KEY:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model=GROQ_MODEL,
                api_key=GROQ_API_KEY,
                temperature=0.4,
                max_tokens=1024,
            )

    except Exception as e:
        print(f"[LLM Init Error] {e}")
        return None

    return None


def generate_explanation(topic: Topic, context: str = "") -> str:
    llm = _get_llm()
    if llm is None:
        return _demo_explanation(topic)

    prompt = f"""You are an excellent, clear tutor for college students.
Explain the topic below in a structured, easy-to-understand way.
Use simple language, short paragraphs, bullet points, and one practical example.
Keep it under 350 words.

Topic: {topic.title}
Subject: {topic.subject}
Extra context from notes: {context[:1500] if context else "None"}

Structure:
1. Simple definition
2. Key points (3-5 bullets)
3. One concrete example
4. Why it matters / common mistakes
"""
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return _demo_explanation(topic) + f"\n\n*(Fell back to demo content: {str(e)[:80]})*"


def generate_summary(topic: Topic, context: str = "") -> str:
    llm = _get_llm()
    if llm is None:
        return _demo_summary(topic)

    prompt = f"""Create a concise revision summary for a student.
Topic: {topic.title} ({topic.subject})
Context: {context[:1000] if context else "None"}

Output format:
- 5-7 crisp bullet points
- One key formula or definition if relevant
- 1 common exam trap
Keep under 180 words.
"""
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception:
        return _demo_summary(topic)


def generate_quiz(topic: Topic, num_questions: int = 4) -> List[Dict]:
    llm = _get_llm()
    if llm is None:
        return _demo_quiz(topic)

    prompt = f"""Generate {num_questions} multiple-choice questions to test understanding of:
Topic: {topic.title}
Subject: {topic.subject}

Return ONLY valid JSON list like this:
[
  {{
    "question": "...",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "answer": "B",
    "explanation": "Short reason"
  }}
]
No markdown, no extra text.
"""
    try:
        response = llm.invoke(prompt)
        import json
        text = response.content.strip()
        # Clean possible markdown fences
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception:
        return _demo_quiz(topic)


def generate_flashcards(topic: Topic, num: int = 5) -> List[Dict]:
    llm = _get_llm()
    if llm is None:
        return _demo_flashcards(topic)

    prompt = f"""Create {num} high-quality flashcards for revision.
Topic: {topic.title} ({topic.subject})

Return ONLY JSON list:
[
  {{"front": "Question or term", "back": "Clear concise answer"}}
]
"""
    try:
        response = llm.invoke(prompt)
        import json
        text = response.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception:
        return _demo_flashcards(topic)


# -------------------- Demo Fallbacks (no API key needed) --------------------

def _demo_explanation(topic: Topic) -> str:
    return f"""### {topic.title}

**Simple Definition**  
{topic.title} is a core concept in {topic.subject}. It forms the foundation for many advanced ideas you will encounter later.

**Key Points**
- Understand the basic definition and purpose first
- Focus on the relationships between related concepts
- Practice with small examples before moving to complex problems
- Pay attention to edge cases and assumptions
- Connect this topic to what you already know

**Practical Example**  
Imagine a simple real-world scenario related to {topic.title}. Breaking it into smaller parts makes the concept much clearer and easier to remember.

**Why it matters**  
This topic frequently appears in exams and interviews. Mastering it early reduces stress later and improves your overall performance in {topic.subject}.

*Tip: After reading, try explaining it out loud in your own words.*
"""


def _demo_summary(topic: Topic) -> str:
    return f"""**Quick Revision – {topic.title}**

• Core idea: Fundamental building block of {topic.subject}
• Remember the main definition and 2-3 supporting points
• Common pattern questions test application, not just theory
• Link this topic to previous chapters for better retention
• Watch out for similar-sounding terms that confuse students

**Exam Trap**: Students often mix this concept with a closely related one. Always double-check the exact definition asked.
"""


def _demo_quiz(topic: Topic) -> List[Dict]:
    return [
        {
            "question": f"What is the primary purpose of studying {topic.title}?",
            "options": [
                "A) Memorize definitions only",
                "B) Build foundational understanding for advanced topics",
                "C) Skip difficult parts",
                "D) Focus only on formulas"
            ],
            "answer": "B",
            "explanation": "Strong foundations make advanced topics much easier."
        },
        {
            "question": f"Which approach helps most when learning {topic.title}?",
            "options": [
                "A) Reading once quickly",
                "B) Active recall + practice questions",
                "C) Highlighting everything",
                "D) Watching videos passively"
            ],
            "answer": "B",
            "explanation": "Active recall is proven to be far more effective."
        },
        {
            "question": f"In {topic.subject}, {topic.title} is best described as:",
            "options": [
                "A) An optional advanced topic",
                "B) A core concept with high exam relevance",
                "C) Only useful for research",
                "D) Outdated material"
            ],
            "answer": "B",
            "explanation": "Core concepts usually carry significant weightage."
        },
        {
            "question": "What should you do after finishing a concept explanation?",
            "options": [
                "A) Move to the next topic immediately",
                "B) Test yourself with questions or teach it to someone",
                "C) Close the book and rest",
                "D) Re-read the same text 5 times"
            ],
            "answer": "B",
            "explanation": "Testing and teaching reveal gaps in understanding."
        }
    ]


def _demo_flashcards(topic: Topic) -> List[Dict]:
    return [
        {"front": f"Define {topic.title} in one sentence", "back": f"A fundamental concept in {topic.subject} that helps build deeper understanding."},
        {"front": f"Why is {topic.title} important?", "back": "It appears frequently in exams and forms the base for advanced topics."},
        {"front": "Best way to revise this topic?", "back": "Active recall + short practice questions + spaced repetition."},
        {"front": f"Common mistake students make with {topic.title}", "back": "Memorizing without understanding relationships to other concepts."},
        {"front": "When should you revisit this topic?", "back": "After 2-3 days, then after a week (spaced repetition)."}
    ]
