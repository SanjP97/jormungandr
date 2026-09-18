"""Rate Limiter - Token bucket algorithm"""

import time
import asyncio
from typing import Dict, Any
from jormungandr.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate_config: Dict[str, Any]):
        self.requests_per_minute = rate_config.get("requests_per_minute", 60)
        self.requests_per_hour = rate_config.get("requests_per_hour", 1000)
        self.concurrent_requests = rate_config.get("concurrent_requests", 5)
        
        self.tokens_minute = self.requests_per_minute
        self.tokens_hour = self.requests_per_hour
        self.last_refill_minute = time.time()
        self.last_refill_hour = time.time()
        
        self.semaphore = asyncio.Semaphore(self.concurrent_requests)
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire token for request"""
        async with self.lock:
            await self._refill_tokens()
            
            while self.tokens_minute < 1 or self.tokens_hour < 1:
                await asyncio.sleep(0.1)
                await self._refill_tokens()
            
            self.tokens_minute -= 1
            self.tokens_hour -= 1
    
    async def _refill_tokens(self):
        """Refill token buckets"""
        now = time.time()
        
        # Refill per-minute bucket
        time_passed_minute = now - self.last_refill_minute
        if time_passed_minute >= 60:
            self.tokens_minute = self.requests_per_minute
            self.last_refill_minute = now
        
        # Refill per-hour bucket
        time_passed_hour = now - self.last_refill_hour
        if time_passed_hour >= 3600:
            self.tokens_hour = self.requests_per_hour
            self.last_refill_hour = now
