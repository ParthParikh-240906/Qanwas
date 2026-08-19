"""Groq client for GPT-OSS models"""
from groq import Groq
import config
import json
import re
import time

class GroqClient:
    def __init__(self, model=None):
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found. Add it to .env file")
        
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = model or config.GROQ_MODEL
        self.total_tokens_used = 0
    
    def generate(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.3) -> str:
        """Generate response from Groq model with retry"""
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                content = response.choices[0].message.content
                if content and len(content.strip()) > 0:
                    self.total_tokens_used += max_tokens
                    return content
            except Exception as e:
                if "429" in str(e) or "Rate limit" in str(e):
                    wait_time = min(30, 5 * (attempt + 1))
                    print(f"  ⏳ Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"  [Groq error (attempt {attempt+1}): {e}]")
                    time.sleep(2)
        
        return ""
    
    def generate_silent(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.3) -> str:
        """Generate without printing - for parallel execution"""
        import time
        
        for attempt in range(3):
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
                if "429" in str(e) or "Rate limit" in str(e):
                    time.sleep(10)
                else:
                    time.sleep(2)
        return ""