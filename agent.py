#!/usr/bin/env python3
"""
qwen-code-agent
A thin CLI wrapper around a local Ollama-served Qwen2.5-Coder-7B model.

Why this exists:
    Small local coder models don't have filesystem/tool access. If you ask
    them to "read main.py and summarize it", there's nothing that actually
    reads the file - the model just free-associates on the raw instruction.
    This script does the "tool call" for you: it reads the file, wraps it
    in a template the model responds well to, and streams the result back.

Usage:
    python agent.py summarize path/to/file.py
    python agent.py explain path/to/file.py
    python agent.py generate "a fastapi GET /health endpoint"
    python agent.py review path/to/file.py
    python agent.py chat                     # freeform REPL, no file context
    python agent.py chat path/to/file.py      # freeform REPL, with file loaded as context

Config (model name, host, temperature, etc.) lives in config.py.
"""

import sys
import json
import argparse
from pathlib import Path

import requests

from config import (
    OLLAMA_HOST,
    MODEL_NAME,
    DEFAULT_TEMPERATURE,
    MAX_FILE_CHARS,
    PROMPTS_DIR,
)


# --------------------------------------------------------------------------
# Core model call
# --------------------------------------------------------------------------

def call_ollama(prompt: str, temperature: float = DEFAULT_TEMPERATURE, stream: bool = True) -> str:
    """Send a prompt to the local Ollama server and stream the response."""
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": stream,
        "options": {"temperature": temperature},
    }

    try:
        resp = requests.post(url, json=payload, stream=stream, timeout=300)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(f"\n[error] Couldn't reach Ollama at {OLLAMA_HOST}.")
        print("        Is it running? Try: ollama serve")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"\n[error] Ollama returned an error: {e}")
        print(f"        Is '{MODEL_NAME}' pulled? Try: ollama pull {MODEL_NAME}")
        sys.exit(1)

    full_text = []
    if stream:
        for line in resp.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            token = chunk.get("response", "")
            print(token, end="", flush=True)
            full_text.append(token)
            if chunk.get("done"):
                print()  # trailing newline
        return "".join(full_text)
    else:
        data = resp.json()
        print(data.get("response", ""))
        return data.get("response", "")


# --------------------------------------------------------------------------
# Prompt building
# --------------------------------------------------------------------------

def load_template(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        print(f"[error] Missing prompt template: {path}")
        sys.exit(1)
    return path.read_text()


def read_file_safely(filepath: str) -> str:
    path = Path(filepath)
    if not path.exists():
        print(f"[error] File not found: {filepath}")
        sys.exit(1)

    code = path.read_text(errors="replace")

    if len(code) > MAX_FILE_CHARS:
        print(
            f"[warn] {filepath} is {len(code)} chars, truncating to "
            f"{MAX_FILE_CHARS} (edit MAX_FILE_CHARS in config.py to change this).\n"
            f"       For files this large, consider a RAG/chunking pipeline instead."
        )
        code = code[:MAX_FILE_CHARS]

    return code


def build_prompt(template_name: str, **kwargs) -> str:
    template = load_template(template_name)
    return template.format(**kwargs)


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

def cmd_summarize(args):
    code = read_file_safely(args.file)
    prompt = build_prompt("summarize", filename=args.file, code=code)
    print(f"--- summarizing {args.file} ---\n")
    call_ollama(prompt)


def cmd_explain(args):
    code = read_file_safely(args.file)
    prompt = build_prompt("explain", filename=args.file, code=code)
    print(f"--- explaining {args.file} ---\n")
    call_ollama(prompt)


def cmd_review(args):
    code = read_file_safely(args.file)
    prompt = build_prompt("review", filename=args.file, code=code)
    print(f"--- reviewing {args.file} ---\n")
    call_ollama(prompt)


def cmd_generate(args):
    description = " ".join(args.description)
    prompt = build_prompt("generate", description=description)
    print(f"--- generating: {description} ---\n")
    call_ollama(prompt)


def cmd_chat(args):
    context = ""
    if args.file:
        code = read_file_safely(args.file)
        context = f"You are working with the following file ({args.file}):\n\n```\n{code}\n```\n\n"
        print(f"[loaded {args.file} as context, {len(code)} chars]\n")

    print("Freeform chat. Type 'exit' or Ctrl+C to quit.\n")
    history = context
    try:
        while True:
            user_input = input(">>> ")
            if user_input.strip().lower() in ("exit", "quit"):
                break
            prompt = f"{history}\n\nUser: {user_input}\nAssistant:"
            print()
            reply = call_ollama(prompt)
            print()
            # keep a rolling window so context doesn't grow unbounded
            history += f"\n\nUser: {user_input}\nAssistant: {reply}"
            if len(history) > MAX_FILE_CHARS * 2:
                history = context + history[-MAX_FILE_CHARS:]
    except KeyboardInterrupt:
        print("\nbye")


# --------------------------------------------------------------------------
# CLI wiring
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Local agent that runs precise, templated prompts against Qwen2.5-Coder-7B via Ollama."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_sum = sub.add_parser("summarize", help="Summarize a code file")
    p_sum.add_argument("file")
    p_sum.set_defaults(func=cmd_summarize)

    p_exp = sub.add_parser("explain", help="Explain a code file in detail")
    p_exp.add_argument("file")
    p_exp.set_defaults(func=cmd_explain)

    p_rev = sub.add_parser("review", help="Code review a file (bugs, style, suggestions)")
    p_rev.add_argument("file")
    p_rev.set_defaults(func=cmd_review)

    p_gen = sub.add_parser("generate", help="Generate code from a description")
    p_gen.add_argument("description", nargs="+")
    p_gen.set_defaults(func=cmd_generate)

    p_chat = sub.add_parser("chat", help="Freeform REPL, optionally with a file loaded as context")
    p_chat.add_argument("file", nargs="?", default=None)
    p_chat.set_defaults(func=cmd_chat)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
