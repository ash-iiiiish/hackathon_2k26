import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# App Settings
APP_NAME = "Adaptive AI Tutor"
APP_TAGLINE = "Your Personal Intelligent Study Companion"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CHROMA_PATH = os.path.join(DATA_DIR, "chroma_db")
DB_PATH = os.path.join(DATA_DIR, "tutor.db")

# Demo mode (works without API keys using rule-based fallbacks)
DEMO_MODE = not (OPENAI_API_KEY or GOOGLE_API_KEY)