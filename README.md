# qwen-code-agent

**V1.1**

A minimal local agent that wraps `qwen2.5-coder:7b` running in Ollama. It solves
the "you have to paste the whole file for the model to do anything useful"
problem by reading files and building precise, templated prompts for you.

No RAG, no framework, no vector DB — just file I/O + prompt templates + an
HTTP call to your local Ollama server. This is the right scope for
single-file / few-file usage. If you later work across a whole multi-file
repo where everything can't fit in context, that's when a hybrid
(vector + keyword) RAG pipeline starts to earn its keep.

## Project structure

```
qwen-code-agent/
├── README.md
├── requirements.txt
├── config.py              # model name, Ollama host, temperature, file size cap
├── agent.py                # CLI entrypoint (the actual agent)
├── prompts/
│   ├── summarize.txt
│   ├── explain.txt
│   ├── review.txt
│   └── generate.txt
└── examples/
    └── main.py             # toy file to test summarize/explain/review against
```

## Setup

1. Make sure Ollama is installed and the model is pulled:
   ```bash
   ollama pull qwen2.5-coder:7b
   ollama serve   # if not already running
   ```

2. Install the one Python dependency:
   ```bash
   pip install -r requirements.txt
   ```

3. Check `config.py` — confirm `MODEL_NAME` matches exactly what `ollama list`
   shows (tags matter, e.g. `qwen2.5-coder:7b` vs `qwen2.5-coder:7b-instruct-q4_K_M`).

## Usage

```bash
# Summarize a file
qsummarize examples/main.py

# Explain a file in more depth
qexplain examples/main.py

# Code review a file (bugs, style, security, edge cases)
qreview examples/main.py

# Generate code from a description
qgenerate "a fastapi GET /health endpoint that also checks db connectivity"
```

## How it works

Each command (`summarize`, `explain`, `review`, `generate`) maps to a
`.txt` template in `prompts/`. The agent reads your target file, drops its
contents into the template via `str.format`, and POSTs the result to
Ollama's `/api/generate` endpoint, streaming tokens back to your terminal
as they arrive.

This is exactly the "paste the whole file into the prompt" workflow you were
already doing manually — just automated and with prompt wording that's been
shaped to get consistent, non-rambly output from a 7B instruct model.

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

## Extending it

- **New command**: add a `prompts/yourcommand.txt` template, a `cmd_yourcommand`
  function in `agent.py`, and register it in the `argparse` subparsers block.
- **Bigger files / multi-file repos**: swap `read_file_safely` for a chunking +
  retrieval step (tree-sitter for AST-aware chunking, `rank_bm25` +
  a local embedding model for hybrid retrieval) before building the prompt.
- **Different model**: just change `MODEL_NAME` in `config.py` — nothing else
  needs to change, since it's a generic Ollama call.

## Notes on prompt design

Qwen2.5-Coder-7B (and small local models generally) respond much better to:
- Explicit output format instructions ("output ONLY code", "bullet list, one
  line each") rather than open-ended asks.
- Low temperature (0.1–0.3) for code tasks — keeps output deterministic and
  reduces rambling/hallucinated APIs.
- Not being asked to "go read a file" — always paste the content in, which is
  what this agent automates.

## Changelog

**V1.1**
- Print real line/char count when a file is read (e.g. `[read main.py: 87 lines, 2103 chars]`)
- Add animated `====>` progress bar while waiting on the model's first token; clears automatically once streaming output begins
- Note: the bar is cosmetic ("still working" signal), not true progress — Ollama's API doesn't expose prefill/prompt-processing progress

**V1**
- Initial release: `summarize`, `explain`, `review`, `generate`, `chat` commands
- Templated prompts in `prompts/` for consistent, non-rambly 7B output
- Config-driven model/host/temperature settings

