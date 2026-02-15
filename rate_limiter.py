"""
Rate limiting and caching utilities for API calls.
Implements token bucket algorithm and LRU response caching.
"""

import time
import json
import hashlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import threading

class RateLimiter:
    """Token bucket rate limiter for API calls"""
    
    def __init__(self, max_tokens: int = 10, refill_rate: float = 1.0):
        """
        Initialize rate limiter
        
        Args:
            max_tokens: Maximum tokens in bucket
            refill_rate: Tokens added per second
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.tokens = max_tokens
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def can_make_request(self) -> Tuple[bool, float]:
        """
        Check if request can be made
        
        Returns:
            Tuple of (can_make_request, wait_time_if_not)
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True, 0.0
            else:
                # Calculate wait time
                wait_time = (1 - self.tokens) / self.refill_rate
                return False, wait_time
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status"""
        with self.lock:
            self._refill()
            return {
                "available_tokens": int(self.tokens),
                "max_tokens": self.max_tokens,
                "refill_rate": self.refill_rate,
                "percentage": (self.tokens / self.max_tokens) * 100
            }

class ResponseCache:
    """LRU cache for LLM responses with TTL"""
    
    def __init__(self, max_size: int = 100, ttl_minutes: int = 15):
        """
        Initialize response cache
        
        Args:
            max_size: Maximum number of cached responses
            ttl_minutes: Time to live in minutes
        """
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutes)
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self.access_order = []
        self.lock = threading.Lock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    def _generate_key(self, prompt: str, mode: str, **kwargs) -> str:
        """Generate cache key from prompt and parameters"""
        cache_data = {
            "prompt": prompt,
            "mode": mode,
            **kwargs
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def get(self, prompt: str, mode: str, **kwargs) -> Optional[Any]:
        """Get cached response if available and not expired"""
        key = self._generate_key(prompt, mode, **kwargs)
        
        with self.lock:
            if key in self.cache:
                response, timestamp = self.cache[key]
                
                # Check if expired
                if datetime.now(timezone.utc) - timestamp > self.ttl:
                    del self.cache[key]
                    self.stats["misses"] += 1
                    return None
                
                # Move to end (most recently used)
                self.access_order.remove(key)
                self.access_order.append(key)
                self.stats["hits"] += 1
                return response
            
            self.stats["misses"] += 1
            return None
    
    def set(self, prompt: str, mode: str, response: Any, **kwargs):
        """Cache a response"""
        key = self._generate_key(prompt, mode, **kwargs)
        
        with self.lock:
            # Remove oldest if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                oldest_key = self.access_order.pop(0)
                del self.cache[oldest_key]
                self.stats["evictions"] += 1
            
            # Add/update cache
            self.cache[key] = (response, datetime.now(timezone.utc))
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
    
    def clear(self):
        """Clear all cached responses"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "evictions": self.stats["evictions"],
                "hit_rate": f"{hit_rate:.1f}%",
                "ttl_minutes": self.ttl.total_seconds() / 60
            }

class APIMonitor:
    """Monitor API usage and costs"""
    
    def __init__(self):
        self.calls = defaultdict(int)
        self.tokens_used = defaultdict(int)
        self.errors = defaultdict(int)
        self.costs = defaultdict(float)
        self.lock = threading.Lock()
    
    def record_call(self, api_type: str, tokens: int = 0, cost: float = 0.0, error: bool = False):
        """Record an API call"""
        with self.lock:
            self.calls[api_type] += 1
            self.tokens_used[api_type] += tokens
            self.costs[api_type] += cost
            if error:
                self.errors[api_type] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        with self.lock:
            return {
                "total_calls": sum(self.calls.values()),
                "total_tokens": sum(self.tokens_used.values()),
                "total_cost": sum(self.costs.values()),
                "by_api": {
                    api: {
                        "calls": self.calls[api],
                        "tokens": self.tokens_used[api],
                        "cost": self.costs[api],
                        "errors": self.errors[api]
                    }
                    for api in self.calls
                }
            }

# Global instances
rate_limiter = RateLimiter(max_tokens=10, refill_rate=0.5)  # 10 requests, refill 1 every 2 seconds
response_cache = ResponseCache(max_size=100, ttl_minutes=15)
api_monitor = APIMonitor()