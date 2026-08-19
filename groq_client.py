"""Groq client with multi-key support"""
from groq import Groq
import config
import json
import re
import time

class GroqClient:
    def __init__(self, model=None, use_backup=False):
        self.model = model or config.GROQ_MODEL
        self.use_backup = use_backup
        self.client = self._create_client()
        self.total_tokens = 0
    
    def _create_client(self):
        """Create Groq client with current key"""
        api_key = config.GROQ_API_KEY_2 if self.use_backup else config.GROQ_API_KEY
        
        if not api_key:
            raise ValueError("GROQ_API_KEY not found. Add it to .env file")
        
        return Groq(api_key=api_key)
    
    def switch_to_backup(self):
        """Switch to backup API key"""
        if config.GROQ_API_KEY_2:
            print(f"  🔄 Switching to backup API key...")
            self.use_backup = True
            self.client = self._create_client()
            return True
        return False
    
    def switch_to_primary(self):
        """Switch back to primary API key"""
        self.use_backup = False
        self.client = self._create_client()
    
    def generate(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.3) -> str:
        """Generate with automatic key switching on rate limit"""
        for attempt in range(5):
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
                error_str = str(e)
                
                if "429" in error_str or "Rate limit" in error_str or "rate_limit" in error_str:
                    if "TPM" in error_str or "tokens per minute" in error_str:
                        # Per-minute limit - wait
                        wait_time = 10
                        print(f"  ⏳ Per-minute limit, waiting {wait_time}s...")
                        time.sleep(wait_time)
                    elif "TPD" in error_str or "tokens per day" in error_str:
                        # Daily limit - switch to backup
                        print(f"  ⚠️ Daily limit reached on current key!")
                        if self.switch_to_backup():
                            print(f"  ✅ Switched to backup key!")
                            continue
                        else:
                            print(f"  ❌ No backup key available")
                            return ""
                else:
                    print(f"  [Groq error: {e}]")
                    time.sleep(2)
        
        return ""
    
    def generate_silent(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.3) -> str:
        """Generate without printing"""
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
                error_str = str(e)
                if "429" in error_str or "Rate limit" in error_str:
                    if self.switch_to_backup():
                        continue
                    else:
                        time.sleep(10)
                else:
                    time.sleep(2)
        return ""