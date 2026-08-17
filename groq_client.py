"""Groq client for GPT-OSS models"""
from groq import Groq
import config
import json
import re

class GroqClient:
    def __init__(self, model=None):
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found. Add it to .env file")
        
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = model or config.GROQ_MODEL
    
    def generate(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.3) -> str:
        """Generate response from Groq model with retry"""
        import time
        
        for attempt in range(3):  # Try 3 times
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                content = response.choices[0].message.content
                if content and len(content.strip()) > 0:
                    return content
            except Exception as e:
                print(f"[Groq error (attempt {attempt+1}): {e}]")
                time.sleep(2)  # Wait before retry
        
        print("[error] Failed to generate after 3 attempts")
        return ""
    
    def orchestrate(self, user_prompt: str) -> list:
        """Break down user prompt into subtasks with forced variety"""
        prompt = f"""Given this user request: "{user_prompt}"

Break this down into EXACTLY 3 subtasks:
1. ONE "search" task - Search the web for current information/best practices
2. ONE "research" task - Deep research on a specific aspect
3. ONE "generate" task - Generate code or content


Rules:
- Each task must be DIFFERENT
- At least one task MUST be "generate" type
- At least one task MUST be "search" type
- Make tasks specific and actionable

Return a JSON array in this exact format:
[
    {{"type": "search", "query": "specific search query"}},
    {{"type": "research", "query": "specific topic to research deeply"}},
    {{"type": "generate", "query": "specific code/content to generate"}}
]

Return ONLY the JSON array, no other text."""
        
        response = self.generate(prompt, max_tokens=1000, temperature=0.2)
        
        # Parse JSON
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            try:
                tasks = json.loads(json_match.group())
                # Ensure we have at least one generate task
                if not any(t['type'] == 'generate' for t in tasks):
                    tasks[1]['type'] = 'generate'
                    tasks[1]['query'] = user_prompt
                return tasks
            except:
                pass
        
        # Fallback
        print(f"[orchestration failed, using default]")
        return [
            {"type": "search", "query": f"{user_prompt} best practices"},
            {"type": "generate", "query": f"Implement {user_prompt}"},
            {"type": "research", "query": f"Compare approaches for {user_prompt}"}
        ]
    
    def combine_results(self, user_prompt: str, results: list) -> str:
        """Combine all sub-agent outputs into final answer (no tables!)"""
        # Format results for prompt
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(f"[Result {i} - {result['task']['type']}]")
            formatted_results.append(result['output'][:2000])
            formatted_results.append("---")
        
        results_text = "\n".join(formatted_results)
        
        prompt = f"""User request: {user_prompt}

Sub-agent outputs:
{results_text}

Combine these into a comprehensive, coherent response.

FORMATTING RULES:
- Use paragraphs and bullet points ONLY
- NO tables, NO markdown tables, NO ASCII tables
- Use code blocks for any code examples
- Use bold for important terms
- Keep it readable in a terminal

Include:
1. Main answer/solution
2. Code examples if relevant
3. Sources if available
4. Any important caveats or alternatives"""
        
        return self.generate(prompt, max_tokens=4000, temperature=0.3)
    
    def generate_stream(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.3) -> str:
        """Generate response with streaming display"""
        full_text = []
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    print(token, end="", flush=True)
                    full_text.append(token)
            
            print()  # New line after streaming
            return "".join(full_text)
            
        except Exception as e:
            print(f"[Groq streaming error: {e}]")
            # Fallback to non-streaming
            return self.generate(prompt, max_tokens, temperature)

    def generate_stream_indented(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.3, indent: str = "") -> str:
        """Stream with indentation for file display"""
        full_text = []
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    # Print with indentation
                    lines = token.split('\n')
                    for j, line in enumerate(lines):
                        if j == 0:
                            print(f"{indent}{line}", end="", flush=True)
                        else:
                            print(f"\n{indent}{line}", end="", flush=True)
                    full_text.append(token)
            
            print()
            return "".join(full_text)
            
        except Exception as e:
            print(f"[Streaming error: {e}]")
            return self.generate(prompt, max_tokens, temperature)