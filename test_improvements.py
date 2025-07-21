"""
Test suite for new improvements: rate limiting, caching, security
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch

from rate_limiter import RateLimiter, ResponseCache, APIMonitor
from security import InputValidator, APIKeyManager, ContentFilter
from backend import SimulationEngine

class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def test_rate_limiter_allows_initial_requests(self):
        """Test that initial requests are allowed"""
        limiter = RateLimiter(max_tokens=5, refill_rate=1.0)
        
        for _ in range(5):
            can_proceed, wait_time = limiter.can_make_request()
            assert can_proceed is True
            assert wait_time == 0.0
    
    def test_rate_limiter_blocks_excess_requests(self):
        """Test that excess requests are blocked"""
        limiter = RateLimiter(max_tokens=2, refill_rate=1.0)
        
        # Use up tokens
        limiter.can_make_request()
        limiter.can_make_request()
        
        # Next request should be blocked
        can_proceed, wait_time = limiter.can_make_request()
        assert can_proceed is False
        assert wait_time > 0
    
    def test_rate_limiter_refills_tokens(self):
        """Test token refill mechanism"""
        limiter = RateLimiter(max_tokens=1, refill_rate=10.0)  # Fast refill
        
        # Use token
        limiter.can_make_request()
        
        # Wait for refill
        time.sleep(0.2)
        
        # Should be able to request again
        can_proceed, wait_time = limiter.can_make_request()
        assert can_proceed is True

class TestResponseCache:
    """Test caching functionality"""
    
    def test_cache_stores_and_retrieves(self):
        """Test basic cache operations"""
        cache = ResponseCache(max_size=10, ttl_minutes=15)
        
        # Store response
        cache.set("test prompt", "realistic", {"result": "test"})
        
        # Retrieve response
        result = cache.get("test prompt", "realistic")
        assert result == {"result": "test"}
    
    def test_cache_misses_different_keys(self):
        """Test cache misses for different keys"""
        cache = ResponseCache()
        
        cache.set("prompt1", "mode1", {"result": "1"})
        
        # Different prompt should miss
        result = cache.get("prompt2", "mode1")
        assert result is None
        
        # Different mode should miss
        result = cache.get("prompt1", "mode2")
        assert result is None
    
    def test_cache_eviction(self):
        """Test LRU eviction"""
        cache = ResponseCache(max_size=2, ttl_minutes=60)
        
        cache.set("prompt1", "mode", {"result": "1"})
        cache.set("prompt2", "mode", {"result": "2"})
        cache.set("prompt3", "mode", {"result": "3"})  # Should evict prompt1
        
        assert cache.get("prompt1", "mode") is None
        assert cache.get("prompt2", "mode") == {"result": "2"}
        assert cache.get("prompt3", "mode") == {"result": "3"}

class TestSecurity:
    """Test security features"""
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        validator = InputValidator()
        
        # Test HTML escape
        result = validator.sanitize_decision("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
        
        # Test length limit
        long_input = "x" * 1000
        result = validator.sanitize_decision(long_input)
        assert len(result) <= 503  # 500 + "..."
    
    def test_api_key_validation(self):
        """Test API key format validation"""
        validator = InputValidator()
        
        # Valid formats
        assert validator.validate_api_key("sk-ant-" + "x" * 40, "anthropic") is True
        assert validator.validate_api_key("sk-" + "x" * 40, "openai") is True
        
        # Invalid formats
        assert validator.validate_api_key("invalid", "anthropic") is False
        assert validator.validate_api_key("", "openai") is False
    
    def test_api_key_masking(self):
        """Test API key masking"""
        manager = APIKeyManager()
        
        masked = manager.mask_key("sk-ant-secretkey123456")
        assert masked == "sk-a...3456"
        
        # Short key
        masked = manager.mask_key("short")
        assert masked == "****"
    
    def test_content_filtering(self):
        """Test content safety checking"""
        filter = ContentFilter()
        
        # Safe content
        is_safe, reason = filter.check_content_safety("What if I moved to Paris?")
        assert is_safe is True
        assert reason is None
        
        # Unsafe content
        is_safe, reason = filter.check_content_safety("What if I commit a crime?")
        assert is_safe is False
        assert "illegal content" in reason

class TestAPIMonitor:
    """Test API monitoring"""
    
    def test_api_monitoring_tracks_calls(self):
        """Test API call tracking"""
        monitor = APIMonitor()
        
        monitor.record_call("grok", tokens=100, cost=0.001)
        monitor.record_call("grok", tokens=200, cost=0.002)
        monitor.record_call("anthropic", tokens=150, cost=0.003)
        
        stats = monitor.get_stats()
        assert stats["total_calls"] == 3
        assert stats["total_tokens"] == 450
        assert stats["total_cost"] == 0.006
        assert stats["by_api"]["grok"]["calls"] == 2
        assert stats["by_api"]["anthropic"]["calls"] == 1

class TestIntegrationWithSecurity:
    """Test integration of security features with main app"""
    
    @pytest.mark.asyncio
    async def test_simulation_with_unsafe_content(self):
        """Test that unsafe content is handled properly"""
        engine = SimulationEngine()
        
        # Test with potentially unsafe content
        branches = await engine.generate_branches(
            "What if I <script>alert('xss')</script>", 
            "realistic", 
            2
        )
        
        # Should return safe fallback branches
        assert len(branches) == 2
        assert all(b.title.startswith("Path") for b in branches)
        assert "<script>" not in branches[0].story
    
    @pytest.mark.asyncio
    async def test_grok_api_integration(self):
        """Test Grok API integration"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock Grok response
            mock_response = Mock()
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": '''{
                            "title": "Grok Test Path",
                            "story": "Test story from Grok",
                            "timeline": [{"year": "Year 1", "event": "Test"}],
                            "key_events": ["Test event"],
                            "probability_score": 0.5
                        }'''
                    }
                }],
                "usage": {"total_tokens": 100}
            }
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response
            
            engine = SimulationEngine(
                api_key="test-grok-key",
                api_type="grok"
            )
            
            branches = await engine.generate_branches("test decision", "realistic", 1)
            
            assert len(branches) == 1
            assert branches[0].title == "Grok Test Path"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])