"""
Central config. Tweak these instead of hunting through agent.py.
"""

from pathlib import Path

# Ollama server (default local install)
OLLAMA_HOST = "http://localhost:11434"

# Exact model tag as shown by `ollama list`
# e.g. "qwen2.5-coder:7b" or "qwen2.5-coder:7b-instruct-q4_K_M"
MODEL_NAME = "qwen2.5-coder:7b"

# Lower = more deterministic/precise (good for code), higher = more creative
DEFAULT_TEMPERATURE = 0.2

# Rough safety cap on how many characters of a file get pasted into a prompt.
# 7B models handle ~32k tokens of context; ~4 chars/token is a safe rule of
# thumb, so this stays well under that with room for the template + output.
MAX_FILE_CHARS = 60_000

PROMPTS_DIR = Path(__file__).parent / "prompts"
