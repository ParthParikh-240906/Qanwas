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
    python agent.py qsearch "what is langchain"
    python agent.py qresearch "fastapi vs flask"

Config (model name, host, temperature, etc.) lives in config.py.
"""

import sys
import json
import time
import threading
import argparse
from pathlib import Path
from groq_client import GroqClient

import requests
import web_tools

from config import (
    OLLAMA_HOST,
    MODEL_NAME,
    DEFAULT_TEMPERATURE,
    MAX_FILE_CHARS,
    PROMPTS_DIR,
)


# --------------------------------------------------------------------------
# Progress animation
# --------------------------------------------------------------------------

BAR_WIDTH = 40


def _progress_animation(stop_event: threading.Event, label: str = "thinking"):
    i = 0
    while not stop_event.is_set():
        filled = i % (BAR_WIDTH + 1)
        bar = "=" * filled + (">" if filled < BAR_WIDTH else "")
        sys.stdout.write(f"\r{label} [{bar:<{BAR_WIDTH + 1}}]")
        sys.stdout.flush()
        i += 1
        time.sleep(0.12)
    # clear the line once stopped
    sys.stdout.write("\r" + " " * (len(label) + BAR_WIDTH + 4) + "\r")
    sys.stdout.flush()


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

    stop_event = threading.Event()
    spinner = threading.Thread(target=_progress_animation, args=(stop_event,), daemon=True)
    spinner.start()

    try:
        resp = requests.post(url, json=payload, stream=stream, timeout=300)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        stop_event.set()
        spinner.join()
        print(f"[error] Couldn't reach Ollama at {OLLAMA_HOST}.")
        print("        Is it running? Try: ollama serve")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        stop_event.set()
        spinner.join()
        print(f"[error] Ollama returned an error: {e}")
        print(f"        Is '{MODEL_NAME}' pulled? Try: ollama pull {MODEL_NAME}")
        sys.exit(1)

    full_text = []
    first_token = True
    if stream:
        for line in resp.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            token = chunk.get("response", "")
            if first_token and token:
                stop_event.set()
                spinner.join()
                first_token = False
            print(token, end="", flush=True)
            full_text.append(token)
            if chunk.get("done"):
                print()  # trailing newline
        if not stop_event.is_set():
            stop_event.set()
            spinner.join()
        return "".join(full_text)
    else:
        data = resp.json()
        stop_event.set()
        spinner.join()
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
    total_lines = code.count("\n") + 1
    print(f"[read {filepath}: {total_lines} lines, {len(code)} chars]")

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
    """Summarize file using GPT-OSS-20B"""
    code = read_file_safely(args.file)
    
    try:
        groq = GroqClient(model="openai/gpt-oss-20b")
    except ValueError as e:
        print(f"[error] {e}")
        return
    
    prompt = f"""Summarize the following code file:

File: {args.file}

CODE START:
{code}
CODE END

Provide a concise summary:
1. What the code does (2-3 sentences)
2. Key functions/classes
3. Dependencies
4. Any notable patterns

Be terse and factual."""
    
    print(f"--- summarizing {args.file} with GPT-OSS-20B ---\n")
    response = groq.generate(prompt, max_tokens=2000, temperature=0.2)
    print(response)

def cmd_explain(args):
    """Explain file using GPT-OSS-20B"""
    code = read_file_safely(args.file)
    
    try:
        groq = GroqClient(model="openai/gpt-oss-20b")
    except ValueError as e:
        print(f"[error] {e}")
        return
    
    prompt = f"""Explain the following code file in detail:

File: {args.file}

CODE START:
{code}
CODE END

Explain:
1. Overall purpose
2. Each function/class in detail
3. How components interact
4. Any complex logic or algorithms
5. Potential improvements

Use bullet points and code references where helpful."""
    
    print(f"--- explaining {args.file} with GPT-OSS-20B ---\n")
    response = groq.generate(prompt, max_tokens=3000, temperature=0.2)
    print(response)

def cmd_generate(args):
    description = " ".join(args.description)
    
    # Validate input
    if not description.strip():
        print("[error] Description cannot be empty.")
        return
        
    prompt = build_prompt("generate", description=description)
    print(f"--- generating: {description} ---\n")
    call_ollama(prompt)


def cmd_web_search(args):
    """Search web and answer question with grounding"""
    question = " ".join(args.question) if isinstance(args.question, list) else args.question
    
    # Validate input
    if not question.strip():
        print("[error] Question cannot be empty.")
        return
    
    # Search and fetch
    results = web_tools.search_and_fetch(question)
    
    if not results:
        print("[no results found]")
        return
    
    # Build context
    context = web_tools.build_context_from_results(results)
    
    # Build prompt
    prompt = build_prompt("web_search", question=question, context=context)
    
    print(f"\n--- answering: {question} ---\n")
    answer = call_ollama(prompt)
    
    # Add clickable sources
    print(f"\n\n{'='*50}")
    print("SOURCES:")
    for i, result in enumerate(results, 1):
        link = result.get('link', '')
        title = result.get('title', 'N/A')
        if link:
            print(f"[{i}] {title}")
            print(f"    {link}")
        else:
            print(f"[{i}] {title}")
    
    return answer


def cmd_web_research(args):
    """Deep research mode - fetch more sources and analyze"""
    question = " ".join(args.question) if isinstance(args.question, list) else args.question
    
    # Validate input
    if not question.strip():
        print("[error] Research topic cannot be empty.")
        return
    
    print(f"[researching: {question}]")
    
    # Get results for research
    results = web_tools.search_and_fetch(question)
    
    if not results:
        print("[no results found]")
        return
    
    # Build detailed context
    context = web_tools.build_context_from_results(results)
    
    # Research prompt
    research_prompt = f"""Research Task: {question}

Available Information:
{context}

Provide a comprehensive analysis:
1. Summary of key findings
2. Different perspectives/approaches
3. Code examples if relevant
4. Best practices
5. Common pitfalls
6. Recommended resources

Important: Do NOT include a "Sources" section - sources will be displayed separately.
You may reference sources inline as [1], [2], etc.
"""
    
    print("\n--- research findings ---\n")
    answer = call_ollama(research_prompt)
    
    # Add clickable sources
    print(f"\n\n{'='*50}")
    print("SOURCES:")
    for i, result in enumerate(results, 1):
        link = result.get('link', '')
        title = result.get('title', 'N/A')
        if link:
            print(f"[{i}] {title}")
            print(f"    {link}")
        else:
            print(f"[{i}] {title}")
    
    return answer

def cmd_build(args):
    """V5: Autonomous project builder"""
    from project_builder import ProjectBuilder
    
    user_request = " ".join(args.prompt)
    
    if not user_request.strip():
        print("[error] Request cannot be empty.")
        return
    
    builder = ProjectBuilder(output_dir=".")
    builder.build_project(user_request)

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

    p_gen = sub.add_parser("generate", help="Generate code")
    p_gen.add_argument("description", nargs="+")
    p_gen.set_defaults(func=cmd_generate)

    p_search = sub.add_parser("qsearch", help="Search web and answer question")
    p_search.add_argument("question", nargs="+", help="Question to search and answer")
    p_search.set_defaults(func=cmd_web_search)

    p_research = sub.add_parser("qresearch", help="Deep research on a topic")
    p_research.add_argument("question", nargs="+", help="Topic to research")
    p_research.set_defaults(func=cmd_web_research)
    
    p_build = sub.add_parser("qbuild", help="Multi-agent orchestration for complex tasks")
    p_build.add_argument("prompt", nargs="+")
    p_build.set_defaults(func=cmd_build)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
