import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
PROMPTS_DIR = BASE_DIR / "prompts"

DEFAULT_TEMPERATURE = 0.2
MAX_FILE_CHARS = 50000

MAX_SEARCH_RESULTS = 5
MAX_PAGE_CHARS = 5000
SEARCH_TIMEOUT = 10
TRUSTED_DOMAINS = ["github.com", "stackoverflow.com", "python.org", "wikipedia.org"]

# Groq Settings - Primary
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Groq Settings - Backup
GROQ_API_KEY_2 = os.getenv("GROQ_API_KEY_2", None)

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_ORCHESTRATOR_MODEL = os.getenv("GROQ_ORCHESTRATOR_MODEL", "openai/gpt-oss-120b")