"""Mock Target Client - Simulates target LLM using free API providers"""

import requests
import time
from typing import Dict, Any, Tuple, Optional
from jormungandr.utils.logger import get_logger

logger = get_logger(__name__)


class MockTargetClient:
    """
    Simulates the target LLM by calling a free model API.
    
    Supported providers:
      - "groq": Uses GroqCloud free tier (~30 RPM, fast, recommended)
      - "google": Uses Google AI Studio / Gemini free tier (~15 RPM)
      - "openrouter": Uses OpenRouter free models (strict rate limits)
    
    Used in --mock mode to test the full jormungandr pipeline
    without hitting the live target API.
    """
    
    def __init__(self, mock_config: Dict[str, Any]):
        self.provider = mock_config.get("provider", "groq")
        self.api_key = mock_config.get("api_key")
        self.model = mock_config.get("model")
        self.request_delay = mock_config.get("request_delay", 2)
        self.timeout = mock_config.get("timeout", 60)
        self.system_prompt = mock_config.get(
            "system_prompt",
            "You are a helpful AI assistant. Respond naturally to the user's message."
        )
        
        if not self.api_key:
            raise ValueError(
                "API key is required for mock target. "
                "Add 'api_key' to the 'mock' section of your config."
            )
        
        # Provider-specific setup
        if self.provider == "google":
            self.model = self.model or "gemini-2.0-flash"
            try:
                from google import genai
                self.google_client = genai.Client(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "google-genai package is required for Google mock target. "
                    "Install it with: pip install google-genai"
                )
        elif self.provider == "groq":
            self.model = self.model or "llama-3.3-70b-versatile"
            self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        elif self.provider == "openrouter":
            self.model = self.model or "nvidia/nemotron-3-nano-30b-a3b:free"
            self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        else:
            raise ValueError(
                f"Unsupported mock provider: '{self.provider}'. "
                f"Supported: 'groq', 'google', 'openrouter'"
            )
        
        logger.info(
            f"Mock target initialized: {self.provider} ({self.model}) "
            f"[delay={self.request_delay}s]"
        )
    
    async def execute_request(self, prompt: str, chatbot_id: Optional[str] = None) -> Tuple[Optional[Dict], float]:
        """
        Send prompt to the mock target and return the response
        in the same format that ResponseParser expects.
        
        Returns:
            Tuple of (response_data dict, duration in seconds)
        """
        # Rate limiting: wait between requests
        time.sleep(self.request_delay)
        
        if self.provider == "google":
            return self._call_google(prompt)
        else:
            # Both groq and openrouter use OpenAI-compatible API
            return self._call_openai_compatible(prompt)
    
    def _call_google(self, prompt: str) -> Tuple[Optional[Dict], float]:
        """Call Google AI Studio (Gemini) — free tier ~15 RPM"""
        from google import genai
        from google.genai import types
        
        start_time = time.time()
        
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries + 1):
            try:
                response = self.google_client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_prompt,
                        temperature=0.7,
                        max_output_tokens=1000,
                    )
                )
                
                output_text = response.text
                duration = time.time() - start_time
                
                logger.debug(f"Mock target response ({duration:.1f}s): {output_text[:100]}...")
                
                # Return in the format ResponseParser expects
                return {"response": output_text}, duration
            
            except Exception as e:
                error_str = str(e)
                if ("429" in error_str or "RESOURCE_EXHAUSTED" in error_str) and attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Mock target (Google) rate limited, "
                        f"retrying in {delay:.0f}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                    continue
                
                duration = time.time() - start_time
                logger.error(f"Mock target (Google) API call failed: {e}")
                return None, duration
        
        duration = time.time() - start_time
        return None, duration
    
    def _call_openai_compatible(self, prompt: str) -> Tuple[Optional[Dict], float]:
        """Call OpenAI-compatible API (Groq, OpenRouter)"""
        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        max_retries = 5
        base_delay = 2
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                output_text = result["choices"][0]["message"]["content"]
                
                duration = time.time() - start_time
                
                logger.debug(f"Mock target response ({duration:.1f}s): {output_text[:100]}...")
                return {"response": output_text}, duration
            
            except requests.exceptions.RequestException as e:
                status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
                
                # Log error body for debugging
                error_body = ""
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_body = e.response.text[:500]
                    except Exception:
                        pass
                
                # 403 = content moderation blocked the prompt
                # Return a synthetic refusal so the pipeline continues
                if status_code == 403:
                    duration = time.time() - start_time
                    logger.warning(
                        f"Mock target ({self.provider}): prompt blocked by content moderation "
                        f"(403). Returning synthetic refusal."
                    )
                    return {
                        "response": "I'm sorry, but I can't assist with that request. "
                                    "This content has been blocked by safety filters."
                    }, duration
                
                if status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                    retry_after = None
                    if hasattr(e, 'response') and e.response is not None:
                        retry_after = e.response.headers.get('Retry-After')
                    
                    if retry_after:
                        try:
                            delay = float(retry_after)
                        except (ValueError, TypeError):
                            delay = base_delay * (2 ** attempt)
                    else:
                        delay = base_delay * (2 ** attempt)
                    
                    logger.warning(
                        f"Mock target API returned {status_code}, "
                        f"retrying in {delay:.0f}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                    continue
                
                duration = time.time() - start_time
                logger.error(f"Mock target API call failed ({status_code}): {e} | Body: {error_body[:200]}")
                return None, duration
        
        duration = time.time() - start_time
        logger.error("Mock target: all retries exhausted")
        return None, duration
