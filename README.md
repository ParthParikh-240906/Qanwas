# qwen-code-agent

**V4.4**

A multi-agent AI coding assistant that orchestrates GPT-OSS models via Groq
to solve complex tasks. Built on V3's multi-agent architecture, V4 removes
the Ollama dependency entirely — all commands now run through Groq's free
tier with GPT-OSS-20B for fast generation and GPT-OSS-120B for intelligent
orchestration.

One-line install. Zero cost. Web-grounded. Multi-model. No local setup
required.

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

## Quick install

```bash
curl -sSL https://raw.githubusercontent.com/ParthParikh-240906/qwen-code-agent/main/install.sh | bash
```

Then add your Groq API key to `~/.qwen-code-agent/.env` and run `source ~/.zshrc`.

## Project structure

```
qwen-code-agent/
├── README.md
├── requirements.txt
├── config.py              # model settings, API keys, search config
├── agent.py                # CLI entrypoint
├── web_tools.py             # web search + content fetching
├── groq_client.py           # GPT-OSS integration via Groq
├── install.sh               # one-line installer
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

### One-line install (recommended)

```bash
curl -sSL https://raw.githubusercontent.com/ParthParikh-240906/qwen-code-agent/main/install.sh | bash
```

### Manual setup

1. Get a free Groq API key:
   - Go to https://console.groq.com
   - Sign up / login
   - Navigate to API Keys
   - Create a new key

2. Clone and install:
   ```bash
   git clone https://github.com/ParthParikh-240906/qwen-code-agent.git
   cd qwen-code-agent
   pip install -r requirements.txt
   ```

3. Create a `.env` file:
   ```env
   GROQ_API_KEY=gsk_your_actual_key_here
   GROQ_MODEL=openai/gpt-oss-20b
   GROQ_ORCHESTRATOR_MODEL=openai/gpt-oss-120b
   USE_GROQ_FOR_GENERATE=true
   ```

4. Add aliases (add to `~/.zshrc` or `~/.bashrc`):
   ```bash
   alias qsummarize="python3 ~/.qwen-code-agent/agent.py summarize"
   alias qexplain="python3 ~/.qwen-code-agent/agent.py explain"
   alias qgenerate="python3 ~/.qwen-code-agent/agent.py qgenerate-fast"
   alias qsearch="python3 ~/.qwen-code-agent/agent.py qsearch"
   alias qresearch="python3 ~/.qwen-code-agent/agent.py qresearch"
   alias qbuild="python3 ~/.qwen-code-agent/agent.py qbuild"
   ```

## Usage

### File operations (GPT-OSS-20B)

```bash
# Summarize a code file
qsummarize examples/main.py

# Explain a file in detail
qexplain examples/main.py

# Generate code from a description
qgenerate "a fastapi GET /health endpoint"
```

### Web search (DuckDuckGo + GPT-OSS-20B)

```bash
# Quick search - grounded in real web sources
qsearch "what is langchain"

# Deep research - comprehensive analysis
qresearch "compare FastAPI vs Flask"
```

### Multi-agent orchestration (GPT-OSS-120B + 20B)

```bash
# Complex task - breaks into subtasks, executes, combines
qbuild "Create a REST API with user authentication"

## How it works
### Multi-agent orchestration (`qbuild`)

1. **Orchestration** — GPT-OSS-120B breaks the request into 3 subtasks:
   - Search: find current best practices
   - Research: deep dive into technical details
   - Generate: create code informed by search/research

2. **Execution** — Each subtask runs with the appropriate tool.

3. **Combination** — GPT-OSS-20B synthesizes everything into a coherent
   response.

### Model routing

| Task | Model | Why |
|---|---|---|
| Orchestration | GPT-OSS-120B | Smart task decomposition |
| Code generation | GPT-OSS-20B | Fast, high-quality output |
| Result combination | GPT-OSS-20B | Quick synthesis |
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
  in argparse.
- **New model**: change `GROQ_MODEL` in `.env` to any Groq-supported model.
- **Better orchestration**: customize the task breakdown prompt in
  `groq_client.py`.
- **Parallel execution**: use `asyncio` to run subtasks concurrently.
- **More subtask types**: add "test", "refactor", "document" to the
  orchestrator.

## Known limitations

- **Rate limits** — Groq free tier: 8K tokens/min, 200K tokens/day.
- **Search quality** — DuckDuckGo results can be noisy.
- **Page fetching** — Some sites block scrapers (403 errors).
- **Orchestration variability** — 120B might occasionally create duplicate
  tasks.

## Changelog

**V4.4**
- Removed Ollama dependency — all commands use GPT-OSS-20B
- One-line installer with auto `.env` copying
- All file operations (`summarize`, `explain`) now use GPT-OSS-20B
- Simplified setup — no local model required
- Faster generation (1-2 seconds per request)

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

**V1**
- Initial release: `summarize`, `explain`, `review`, `generate` commands
- Templated prompts in `prompts/` for consistent, non-rambly 7B output
- Config-driven model/host/temperature settings