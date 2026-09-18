"""Request Executor with Rate Limiting and Retry Logic"""

import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional, List
from jormungandr.utils.logger import get_logger

logger = get_logger(__name__)


class RequestExecutor:
    """Execute API requests with rate limiting and retry logic"""
    
    def __init__(self, auth_manager, endpoint_config, rate_limiter, response_handling_config):
        self.auth_manager = auth_manager
        self.endpoint_config = endpoint_config
        self.rate_limiter = rate_limiter
        self.response_handling_config = response_handling_config
        
        # Get custom headers from config
        self.custom_headers = endpoint_config.get("request", {}).get("headers", {})
        
        self.base_url = None
        self.retry_config = {}
        self.timeout_config = {}
        self.adaptive_timeout_config = {}
        
        self.response_times = []
    
    def set_base_url(self, base_url: str):
        """Set base URL"""
        self.base_url = base_url
    
    def set_retry_config(self, retry_config: Dict[str, Any]):
        """Set retry configuration"""
        self.retry_config = retry_config
    
    def set_timeout_config(self, timeout_config: Dict[str, Any]):
        """Set timeout configuration"""
        self.timeout_config = timeout_config
    
    def enable_adaptive_timeout(self, adaptive_config: Dict[str, Any]):
        """Enable adaptive timeout"""
        self.adaptive_timeout_config = adaptive_config
    
    async def execute_request(self, prompt: str, chatbot_id: Optional[str] = None) -> tuple:
        """Execute API request with retry logic"""
        
        await self.rate_limiter.acquire()
        
        start_time = time.time()
        
        # Build request
        url = f"{self.base_url}{self.endpoint_config['path']}"
        method = self.endpoint_config['method']
        body = self._build_request_body(prompt, chatbot_id)
        
        # Get auth headers
        headers = self.auth_manager.get_headers()
        
        # Add custom headers from config
        if self.custom_headers:
            headers.update(self.custom_headers)
        
        # Calculate timeout
        timeout = self._calculate_timeout()
        
        # Retry logic
        max_retries = self.retry_config.get("max_retries", 3)
        backoff_factor = self.retry_config.get("backoff_factor", 2)
        retry_statuses = self.retry_config.get("retry_on_status", [429, 500, 502, 503, 504])
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method,
                        url,
                        json=body,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        
                        # Check if should retry
                        if response.status in retry_statuses and attempt < max_retries:
                            wait_time = backoff_factor ** attempt
                            logger.warning(f"Request failed with status {response.status}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        
                        # Get response
                        response_data = await response.json()
                        duration = time.time() - start_time
                        
                        # Track response time for adaptive timeout
                        if self.adaptive_timeout_config.get("enabled"):
                            self.response_times.append(duration)
                        
                        # Check for errors
                        if response.status >= 400:
                            logger.error(f"Request failed: {response.status}, {response.reason}, url='{url}'")
                            return None, duration
                        
                        return response_data, duration
            
            except asyncio.TimeoutError:
                logger.error(f"Request timeout after {timeout}s (attempt {attempt + 1}/{max_retries})")
                last_exception = "Timeout"
                if attempt < max_retries:
                    wait_time = backoff_factor ** attempt
                    await asyncio.sleep(wait_time)
                    continue
            
            except Exception as e:
                logger.error(f"Request error: {e} (attempt {attempt + 1}/{max_retries})")
                last_exception = str(e)
                if attempt < max_retries:
                    wait_time = backoff_factor ** attempt
                    await asyncio.sleep(wait_time)
                    continue
        
        # All retries failed
        duration = time.time() - start_time
        logger.error(f"All retries failed. Last error: {last_exception}")
        return None, duration
    
    def _build_request_body(self, prompt: str, chatbot_id: Optional[str]) -> Dict[str, Any]:
        """Build request body from template"""
        
        request_config = self.endpoint_config.get("request", {})
        body_template = request_config.get("body_template", {})
        
        # Replace prompt placeholder
        body = {}
        for key, value in body_template.items():
            if isinstance(value, str) and "{prompt}" in value:
                body[key] = value.replace("{prompt}", prompt)
            elif isinstance(value, str) and "{chatbot_id}" in value and chatbot_id:
                body[key] = value.replace("{chatbot_id}", chatbot_id)
            else:
                body[key] = value
        
        return body
    
    def _calculate_timeout(self) -> float:
        """Calculate timeout based on adaptive configuration"""
        
        # Default timeout
        default_timeout = self.timeout_config.get("total_timeout", 60)
        
        # Check if adaptive timeout is enabled
        if not self.adaptive_timeout_config.get("enabled"):
            return default_timeout
        
        # Need minimum samples
        min_samples = self.adaptive_timeout_config.get("min_samples", 10)
        if len(self.response_times) < min_samples:
            return default_timeout
        
        # Calculate percentile-based timeout
        percentile = self.adaptive_timeout_config.get("percentile", 95)
        multiplier = self.adaptive_timeout_config.get("multiplier", 1.5)
        
        sorted_times = sorted(self.response_times[-100:])  # Use last 100 samples
        index = int(len(sorted_times) * (percentile / 100))
        percentile_time = sorted_times[min(index, len(sorted_times) - 1)]
        
        adaptive_timeout = percentile_time * multiplier
        
        # Clamp to reasonable bounds
        min_timeout = self.timeout_config.get("read_timeout", 30)
        max_timeout = default_timeout * 2
        
        return max(min_timeout, min(adaptive_timeout, max_timeout))
