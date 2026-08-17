# qwen-code-agent

**V5.3**

An autonomous AI project builder that orchestrates GPT-OSS models via Groq
to create complete full-stack applications. V5 transforms the agent from a
Q&A tool into a software engineer — it plans architectures, generates
multiple files with real-time streaming, writes them to disk, and can
modify existing projects.

One-line install. Zero cost. Real-time code generation. Autonomous project
building. No local setup required.

## What's new in V5

- **Autonomous project builder** — `qbuild` creates complete projects with
  frontend, backend, configs, and docs
- **Real-time code streaming** — watch code being written file-by-file
  like Cline/Devin
- **Project modification** — `qmodify` analyzes existing projects and
  makes targeted changes
- **Intelligent architecture** — GPT-OSS-120B plans the best structure for
  each project
- **Multi-file generation** — creates 5-10+ files per project automatically

## Architecture

```
User Request: "Build a PDF analysis tool"
    ↓
[GPT-OSS-120B Architect]
    Plans project structure:
    ├── backend/main.py
    ├── backend/requirements.txt
    ├── frontend/index.html
    ├── frontend/style.css
    ├── frontend/app.js
    └── README.md
    ↓
[GPT-OSS-20B Generator - streams each file]
    ├── [1/6] Generating backend/main.py... (real-time)
    ├── [2/6] Generating backend/requirements.txt...
    ├── [3/6] Generating frontend/index.html...
    └── ...
    ↓
[File Writer]
    Creates files in current directory
    ↓
[GPT-OSS-120B Reviewer]
    Validates project completeness
    ↓
✅ PROJECT COMPLETE!
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
├── groq_client.py           # GPT-OSS integration with streaming
├── project_builder.py       # V5: autonomous project builder
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
   alias qgenerate="python3 ~/.qwen-code-agent/agent.py generate"
   alias qsearch="python3 ~/.qwen-code-agent/agent.py qsearch"
   alias qresearch="python3 ~/.qwen-code-agent/agent.py qresearch"
   alias qbuild="python3 ~/.qwen-code-agent/agent.py qbuild"
   alias qmodify="python3 ~/.qwen-code-agent/agent.py qmodify"
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

### Autonomous project building (GPT-OSS-120B + 20B)

```bash
# Build complete project with real-time code streaming
qbuild "Create a full-stack PDF analysis tool with RAG"

# This will:
# 1. Plan architecture (GPT-OSS-120B)
# 2. Generate each file with real-time display (GPT-OSS-20B)
# 3. Write files to current directory
# 4. Review the complete project
```

### Project modification

```bash
# Modify existing project
cd my-project
qmodify "Add vector database support to the RAG pipeline"

# This will:
# 1. Scan current project files
# 2. Plan modifications (GPT-OSS-120B)
# 3. Execute changes with real-time streaming
```

## Example: building a full-stack app

```bash
mkdir my-app && cd my-app
qbuild "Create a real estate website with property listings"

# Output:
# 🤖 AUTONOMOUS PROJECT BUILDER
# Request: Create a real estate website...
#
# [1/4] 🧠 Architect planning...
#   Project: real-estate-website
#   Tech stack: React, FastAPI, SQLite
#   Files to create: 8
#
# [2/4] 📝 Generating files...
#   [1/8] Generating backend/main.py...
#   📄 backend/main.py
#   ──────────────────────────────────
#   from fastapi import FastAPI...
#   (streaming in real-time)
#   ✓ Generated 2341 chars
#   ...
#
# [3/4] 💾 Writing files...
#   ✓ Created backend/main.py
#   ✓ Created frontend/index.html
#   ...
#
# [4/4] ✅ Final review...
#   Review: Project is complete...
#
# 🎉 PROJECT COMPLETE!
# Location: /Users/username/my-app
```

## How it works

### Autonomous project builder (`qbuild`)

1. **Architecture planning** — GPT-OSS-120B analyzes the request and plans
   the best project structure
2. **Real-time generation** — GPT-OSS-20B generates each file with
   streaming display
3. **File writing** — creates directories and writes files to current
   location
4. **Validation** — GPT-OSS-120B reviews the complete project

### Project modification (`qmodify`)

1. **Project scan** — analyzes existing files in current directory
2. **Change planning** — GPT-OSS-120B determines what files need to change
3. **Execution** — generates new content with streaming and writes changes

### Model routing

| Task | Model | Why |
|---|---|---|
| Architecture planning | GPT-OSS-120B | Complex reasoning |
| Code generation | GPT-OSS-20B | Fast, streaming |
| Project modification planning | GPT-OSS-120B | Context understanding |
| Web search | DuckDuckGo | Free, no API key |
| File operations | Python | Direct file system access |

### Token economics

A typical `qbuild` (8 files):
- Architecture planning: ~2K tokens
- File generation: ~25K tokens (8 files × ~3K each)
- Review: ~1K tokens
- **Total: ~28K tokens** — well within daily free limit

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
- **Custom architectures**: modify the planning prompt in
  `project_builder.py`.
- **More file types**: extend `_create_placeholder` for new file
  extensions.
- **Git integration**: auto-initialize git after project creation.

## Known limitations

- **Rate limits** — Groq free tier: 8K tokens/min, 200K tokens/day.
- **Large projects** — projects with 20+ files may exceed context window.
- **Search quality** — DuckDuckGo results can be noisy.
- **Page fetching** — Some sites block scrapers (403 errors).
- **JSON parsing** — orchestrator might occasionally return malformed JSON.

## Changelog

**V5**
- Autonomous project builder (`qbuild`)
- Real-time code streaming display
- Project modification (`qmodify`)
- Intelligent architecture planning
- Multi-file generation (5-10+ files)
- File writing to disk
- Project review and validation

**V4**
- Removed Ollama dependency — all commands use GPT-OSS-20B
- One-line installer with auto `.env` copying
- Simplified setup — no local model required
- Faster generation (1-2 seconds per request)

**V3**
- Add GPT-OSS-120B orchestration via Groq
- Add GPT-OSS-20B for fast generation
- Multi-agent orchestration with web search
- Terminal-friendly output

**V2**
- Web search (`qsearch`) and deep research (`qresearch`)
- DuckDuckGo integration + BeautifulSoup page fetching
- Grounded Q&A with source citation

**V1.1**
- Real line/char count display
- Animated progress bar

**V1.0**
- Initial release: `summarize`, `explain`, `generate`
- Templated prompts for consistent output