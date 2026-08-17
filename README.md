# qwen-code-agent

**V3.0**

A multi-agent AI coding assistant that orchestrates multiple models to solve
complex tasks. Built on the foundation of V2 (local Qwen + web search), V3
adds GPT-OSS models via Groq for intelligent task decomposition, fast code
generation, and context-aware synthesis.

The agent now has three tiers of intelligence:
- **GPT-OSS-120B** — The Brain: breaks complex requests into subtasks
- **GPT-OSS-20B** — The Worker: fast code generation and result combination
- **Qwen2.5-Coder-7B** — The Local: file operations, basic tasks, zero cost

No RAG, no framework, no vector DB — just smart prompt engineering,
multi-model orchestration, and web grounding. This hits the sweet spot
between capability and simplicity.

## Architecture

```
User Request
    ↓
[GPT-OSS-120B Orchestrator]
    ↓
Breaks into: Search + Research + Generate
    ↓
┌─────────────┬──────────────┬─────────────┐
│  Web Search │  Web Research│  GPT-OSS-20B│
│  (DuckDuckGo)│ (DuckDuckGo) │  (Generate) │
└─────────────┴──────────────┴─────────────┘
    ↓              ↓              ↓
[GPT-OSS-20B Combiner - uses all context]
    ↓
Final Response with Code + Sources
```

## Project structure

```
qwen-code-agent/
├── README.md
├── requirements.txt
├── config.py              # model settings, API keys, search config
├── agent.py                # CLI entrypoint (the actual agent)
├── web_tools.py             # web search + content fetching
├── groq_client.py           # GPT-OSS integration via Groq
├── .env                    # API keys (NOT committed to git)
├── .gitignore
├── prompts/
│   ├── summarize.txt
│   ├── explain.txt
│   ├── generate.txt
│   └── web_search.txt
└── examples/
    └── main.py
```

## Setup

1. Make sure Ollama is installed and the model is pulled:
   ```bash
   ollama pull qwen2.5-coder:7b
   ollama serve   # if not already running
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Get a free Groq API key:
   - Go to https://console.groq.com
   - Sign up / login
   - Navigate to API Keys
   - Create a new key

4. Create a `.env` file:
   ```bash
   touch .env
   ```
   Add your key:
   ```env
   GROQ_API_KEY=gsk_your_actual_key_here
   GROQ_MODEL=openai/gpt-oss-20b
   GROQ_ORCHESTRATOR_MODEL=openai/gpt-oss-120b
   USE_GROQ_FOR_GENERATE=true
   ```

5. Set up shell aliases (add to `~/.zshrc` or `~/.bashrc`):
   ```bash
   # Local Qwen commands
   alias qsummarize='python3 ~/projects/qwen-code-agent/agent.py summarize'
   alias qexplain='python3 ~/projects/qwen-code-agent/agent.py explain'
   alias qgenerate='python3 ~/projects/qwen-code-agent/agent.py generate'

   # Web search commands
   alias qsearch='python3 ~/projects/qwen-code-agent/agent.py qsearch'
   alias qresearch='python3 ~/projects/qwen-code-agent/agent.py qresearch'

   # GPT-OSS commands
   alias qgenerate-fast='python3 ~/projects/qwen-code-agent/agent.py qgenerate-fast'
   alias qbuild='python3 ~/projects/qwen-code-agent/agent.py qbuild'
   ```
   Then reload: `source ~/.zshrc`

## Usage

### Local Qwen 7B (free, always available)

```bash
# Summarize a file
qsummarize examples/main.py

# Explain a file in more depth
qexplain examples/main.py

# Generate code from a description
qgenerate "a fastapi GET /health endpoint"
```

### Web search (DuckDuckGo, free)

```bash
# Quick search - grounded in real web sources
qsearch "what is langchain"

# Deep research - comprehensive analysis
qresearch "compare FastAPI vs Flask"
```

### GPT-OSS via Groq (free tier, 200K tokens/day)

```bash
# Fast generation with GPT-OSS-20B
qgenerate-fast "a FastAPI endpoint with rate limiting"

# Multi-agent orchestration
qbuild "Create a REST API with user authentication"
```

## How it works

### Multi-agent orchestration (`qbuild`)

The flagship V3 command that combines all models:

1. **Orchestration** — GPT-OSS-120B breaks the request into 3 subtasks:
   - Search: find current best practices
   - Research: deep dive into technical details
   - Generate: create code informed by search/research

2. **Execution** — Each subtask runs with the appropriate tool:
   - Web search fetches current information
   - Research digs deeper into specific aspects
   - Generation uses context from search/research

3. **Combination** — GPT-OSS-20B synthesizes everything into a coherent
   response with code examples, sources, and alternatives.

### Model routing

| Task | Model | Why |
|---|---|---|
| Orchestration | GPT-OSS-120B | Smart task decomposition |
| Code generation | GPT-OSS-20B | Fast, high-quality output |
| Result combination | GPT-OSS-20B | Quick synthesis |
| File operations | Qwen 7B | Local, free, sufficient |
| Web search | DuckDuckGo | Free, no API key needed |

### Token economics

A typical `qbuild` uses ~6K tokens:
- Orchestration: ~1K tokens
- Generation: ~3K tokens
- Combination: ~2K tokens

With Groq's free tier (200K tokens/day), you can run **~33 `qbuild`
operations per day** at zero cost.

## Config

In `config.py`:

- `MODEL_NAME` — Ollama model (default: `qwen2.5-coder:7b`)
- `OLLAMA_HOST` — Ollama server URL
- `DEFAULT_TEMPERATURE` — local model temperature
- `MAX_FILE_CHARS` — max file size before truncation
- `MAX_SEARCH_RESULTS` — web search results (default: `5`)
- `MAX_PAGE_CHARS` — max chars per page fetch
- `SEARCH_TIMEOUT` — page fetch timeout
- `TRUSTED_DOMAINS` — prioritized domains in search

In `.env`:

- `GROQ_API_KEY` — your Groq API key
- `GROQ_MODEL` — fast model (default: `openai/gpt-oss-20b`)
- `GROQ_ORCHESTRATOR_MODEL` — smart model (default: `openai/gpt-oss-120b`)

## Extending it

- **New command**: add a `cmd_yourcommand` function in `agent.py`, register
  in the `argparse` subparsers block.
- **New model**: add to `config.py` and create a client wrapper.
- **Better orchestration**: customize the task breakdown prompt in
  `groq_client.py`.
- **Parallel execution**: use `asyncio` to run subtasks concurrently.
- **More subtask types**: add "test", "refactor", "document" to the
  orchestrator.

## Known limitations

- **Rate limits** — Groq free tier: 8K tokens/min, 200K tokens/day.
- **7B context window** — Long files get truncated.
- **Search quality** — DuckDuckGo results can be noisy.
- **Page fetching** — Some sites block scrapers (403 errors).
- **Orchestration variability** — 120B might occasionally create duplicate
  tasks.

## Changelog

**V3.0**
- Add GPT-OSS-120B orchestration via Groq
- Add GPT-OSS-20B for fast generation
- Add `qbuild` multi-agent command
- Add `qgenerate-fast` for quick GPT-OSS generation
- Context-aware generation (search/research inform code)
- Multi-model routing (120B for planning, 20B for execution)
- Terminal-friendly output (no tables)
- `.env` support for API keys

**V2.0**
- Add web search (`qsearch`) and deep research (`qresearch`) commands
- Add `web_tools.py` with DuckDuckGo search + page fetching via BeautifulSoup
- Add grounded Q&A prompt template that forces answer-from-context behavior
- Display clickable source URLs below answers
- Trusted domain filtering for higher-quality results
- Graceful fallback to search snippets when full page content isn't available

**V1.1**
- Print real line/char count when a file is read (e.g. `[read main.py: 87 lines, 2103 chars]`)
- Add animated `====>` progress bar while waiting on the model's first token; clears automatically once streaming output begins
- Note: the bar is cosmetic ("still working" signal), not true progress — Ollama's API doesn't expose prefill/prompt-processing progress

**V1.0**
- Initial release: `summarize`, `explain`, `review`, `generate` commands
- Templated prompts in `prompts/` for consistent, non-rambly 7B output
- Config-driven model/host/temperature settings