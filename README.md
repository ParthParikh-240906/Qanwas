# qwen-code-agent

**V2.0**
A minimal local agent that wraps `qwen2.5-coder:7b` running in Ollama. It solves
the "you have to paste the whole file for the model to do anything useful"
problem by reading files and building precise, templated prompts for you.

Now with web search capabilities — the agent can search DuckDuckGo, fetch
web pages, and ground answers in real sources. This solves the knowledge
cutoff problem: your local 7B model might not know about new frameworks,
but it can search for current information and synthesize grounded answers.

No RAG, no framework, no vector DB — just file I/O + prompt templates + an
HTTP call to your local Ollama server + web search. This is the right scope for
single-file / few-file usage. If you later work across a whole multi-file
repo where everything can't fit in context, that's when a hybrid
(vector + keyword) RAG pipeline starts to earn its keep.

## Project structure

```
qwen-code-agent/
├── README.md
├── requirements.txt
├── config.py
├── agent.py
├── web_tools.py
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

3. Check `config.py` — confirm `MODEL_NAME` matches exactly what `ollama list`
   shows (tags matter, e.g. `qwen2.5-coder:7b` vs `qwen2.5-coder:7b-instruct-q4_K_M`).

4. Set up shell aliases (add to `~/.zshrc` or `~/.bashrc`):
   ```bash
   alias qsummarize='python agent.py summarize'
   alias qexplain='python agent.py explain'
   alias qgenerate='python agent.py generate'
   alias qsearch='python agent.py qsearch'
   alias qresearch='python agent.py qresearch'
   alias qchat='python agent.py chat'
   ```
   Then reload: `source ~/.zshrc`

## Usage

```bash
# Summarize a file
qsummarize examples/main.py

# Explain a file in more depth
qexplain examples/main.py

# Generate code from a description
qgenerate "a fastapi GET /health endpoint that also checks db connectivity"

# Quick search - answers grounded in real web sources
qsearch "what is langchain"

# Deep research - comprehensive analysis on a topic
qresearch "compare FastAPI vs Flask for microservices"
```

## How it works

### File-based commands (`summarize`, `explain`)

Each command maps to a `.txt` template in `prompts/`. The agent reads your
target file, drops its contents into the template via `str.format`, and POSTs
the result to Ollama's `/api/generate` endpoint, streaming tokens back to
your terminal as they arrive.

This is exactly the "paste the whole file into the prompt" workflow you were
already doing manually — just automated and with prompt wording that's been
shaped to get consistent, non-rambly output from a 7B instruct model.

### Web search commands (`qsearch`, `qresearch`)

The search flow is:

1. **Search** — Query DuckDuckGo (free, no API key) for relevant results
2. **Fetch** — Download top pages and extract readable text with BeautifulSoup
3. **Ground** — Build a prompt containing the original question + fetched content
4. **Answer** — Qwen synthesizes an answer using ONLY the provided web content
5. **Cite** — Display clickable source URLs below the answer

This solves the "knowledge cutoff" problem: Qwen2.5-Coder-7B doesn't know
about post-2024 tools, but `qsearch` can fetch current information and
ground the answer in real sources instead of hallucinating.

When you run a file-based command, you'll see output like:

```
[read main.py: 87 lines, 2103 chars]
--- explaining main.py ---

thinking [=========================>              ]
```

The `====>` bar animates while Ollama processes the prompt, then clears and
the real streamed output takes over as soon as the first token arrives.
This is a cosmetic "still working, not frozen" indicator — Ollama's API
doesn't expose real progress during prompt processing, so there's no way
to show a genuine "line 23 of 50" style counter. The line/char count printed
right after reading the file, however, is real, and reflects your actual file.

For web search, you'll see:

```
[searching web: what is langchain]
[fetching: https://en.wikipedia.org/wiki/LangChain]
[fetching: https://www.ibm.com/think/topics/langchain]

--- answering: what is langchain ---

LangChain is an open-source framework...

==================================================
SOURCES:
[1] LangChain - Wikipedia
    https://en.wikipedia.org/wiki/LangChain
[2] What Is LangChain? | IBM
    https://www.ibm.com/think/topics/langchain
```

## Config

In `config.py`:

- `MODEL_NAME` — Ollama model tag (default: `qwen2.5-coder:7b`)
- `OLLAMA_HOST` — Ollama server URL (default: `http://localhost:11434`)
- `DEFAULT_TEMPERATURE` — model temperature (default: `0.2`)
- `MAX_FILE_CHARS` — max file size before truncation
- `MAX_SEARCH_RESULTS` — max web search results (default: `5`)
- `MAX_PAGE_CHARS` — max characters to fetch per page (default: `5000`)
- `SEARCH_TIMEOUT` — HTTP timeout for page fetches (seconds)
- `TRUSTED_DOMAINS` — preferred domains to prioritize in search results

## Extending it

- **New command**: add a `prompts/yourcommand.txt` template, a `cmd_yourcommand`
  function in `agent.py`, and register it in the `argparse` subparsers block.
- **Bigger files / multi-file repos**: swap `read_file_safely` for a chunking +
  retrieval step (tree-sitter for AST-aware chunking, `rank_bm25` +
  a local embedding model for hybrid retrieval) before building the prompt.
- **Different model**: just change `MODEL_NAME` in `config.py` — nothing else
  needs to change, since it's a generic Ollama call.
- **Better search**: swap DuckDuckGo for Brave Search API or Tavily if you
  need higher-quality results or want to avoid rate limits.

## Notes on prompt design

Qwen2.5-Coder-7B (and small local models generally) respond much better to:
- Explicit output format instructions ("output ONLY code", "bullet list, one
  line each") rather than open-ended asks.
- Low temperature (0.1–0.3) for code tasks — keeps output deterministic and
  reduces rambling/hallucinated APIs.
- Not being asked to "go read a file" — always paste the content in, which is
  what this agent automates.
- Being told to ground answers in provided context rather than relying on
  training data — critical for web search to avoid hallucination.

## Known limitations

- **7B model context window** — Long web pages get truncated. Consider
  chunking + retrieval for multi-page research.
- **Search quality** — DuckDuckGo results can be noisy. Trusted domain
  filtering helps but isn't perfect.
- **Page fetching** — Some sites block scrapers. The agent gracefully
  falls back to using the search snippet when full content isn't available.
- **Rate limits** — The agent sleeps 0.3s between page fetches to be
  polite to servers. Don't remove this.

## Changelog

**V2.0**
- Add web search (`qsearch`) and deep research (`qresearch`) commands
- Add `web_tools.py` with DuckDuckGo search + page fetching via BeautifulSoup
- Add grounded Q&A prompt template that forces answer-from-context behavior
- Display clickable source URLs below answers
- Trusted domain filtering for higher-quality results
- Graceful fallback to search snippets when full page content isn't available
- Removed review, kept hallucinating 

**V1.1**
- Print real line/char count when a file is read (e.g. `[read main.py: 87 lines, 2103 chars]`)
- Add animated `====>` progress bar while waiting on the model's first token; clears automatically once streaming output begins
- Note: the bar is cosmetic ("still working" signal), not true progress — Ollama's API doesn't expose prefill/prompt-processing progress

**V1.0**
- Initial release: `summarize`, `explain`, `review`, `generate` commands
- Templated prompts in `prompts/` for consistent, non-rambly 7B output
- Config-driven model/host/temperature settings