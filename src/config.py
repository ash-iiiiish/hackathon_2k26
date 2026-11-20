import os
from dotenv import load_dotenv

load_dotenv()

# ---------- LLM Configuration ----------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

# Free provider (recommended)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Optional paid providers
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")  # only used if openai is selected

# ---------- App Settings ----------
APP_NAME = "Adaptive AI Tutor"
APP_TAGLINE = "Your Personal Intelligent Study Companion"

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CHROMA_PATH = os.path.join(DATA_DIR, "chroma_db")
DB_PATH = os.path.join(DATA_DIR, "tutor.db")

# Demo mode = no API key available
DEMO_MODE = not (GROQ_API_KEY or OPENAI_API_KEY or GOOGLE_API_KEY)
