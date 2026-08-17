import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent
PROMPTS_DIR = BASE_DIR / "prompts"

# Ollama Settings
MODEL_NAME = "qwen2.5-coder:7b"
OLLAMA_HOST = "http://localhost:11434"
DEFAULT_TEMPERATURE = 0.2
MAX_FILE_CHARS = 50000

# Web Search Settings
MAX_SEARCH_RESULTS = 5
MAX_PAGE_CHARS = 5000
SEARCH_TIMEOUT = 10
TRUSTED_DOMAINS = [
    "github.com",
    "stackoverflow.com",
    "python.org",
    "docs.python.org",
    "wikipedia.org",
    "medium.com",
    "dev.to",
    "realpython.com",
    "geeksforgeeks.org",
    "towardsdatascience.com"
]

# Groq Settings (from .env)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")  # Default to 20B for speed
GROQ_ORCHESTRATOR_MODEL = os.getenv("GROQ_ORCHESTRATOR_MODEL", "openai/gpt-oss-120b")  # 120B for orchestration
USE_GROQ_FOR_GENERATE = os.getenv("USE_GROQ_FOR_GENERATE", "true").lower() == "true"

# Optional: Print warning if no API key
if not GROQ_API_KEY:
    print("[warn] GROQ_API_KEY not found in .env - qbuild and qgenerate-fast will not work")