"""
Test suite for rate limiting, caching, and security modules.
"""

import pytest
import time
from unittest.mock import Mock, patch

from rate_limiter import RateLimiter, ResponseCache, APIMonitor
from security import InputValidator, ContentFilter
from backend import SimulationEngine


class TestRateLimiter:

    def test_allows_initial_requests(self):
        limiter = RateLimiter(max_tokens=5, refill_rate=1.0)
        for _ in range(5):
            ok, wait = limiter.can_make_request()
            assert ok is True
            assert wait == 0.0

    def test_blocks_excess_requests(self):
        limiter = RateLimiter(max_tokens=2, refill_rate=1.0)
        limiter.can_make_request()
        limiter.can_make_request()
        ok, wait = limiter.can_make_request()
        assert ok is False
        assert wait > 0

    def test_refills_tokens(self):
        limiter = RateLimiter(max_tokens=1, refill_rate=10.0)
        limiter.can_make_request()
        time.sleep(0.2)
        ok, _ = limiter.can_make_request()
        assert ok is True


class TestResponseCache:

    def test_store_and_retrieve(self):
        cache = ResponseCache(max_size=10, ttl_minutes=15)
        cache.set("prompt", "mode", {"result": "test"})
        assert cache.get("prompt", "mode") == {"result": "test"}

    def test_miss_on_different_key(self):
        cache = ResponseCache()
        cache.set("p1", "m1", {"r": "1"})
        assert cache.get("p2", "m1") is None
        assert cache.get("p1", "m2") is None

    def test_eviction(self):
        cache = ResponseCache(max_size=2, ttl_minutes=60)
        cache.set("p1", "m", {"r": "1"})
        cache.set("p2", "m", {"r": "2"})
        cache.set("p3", "m", {"r": "3"})
        assert cache.get("p1", "m") is None
        assert cache.get("p2", "m") == {"r": "2"}
        assert cache.get("p3", "m") == {"r": "3"}


class TestSecurity:

    def test_html_escaping(self):
        v = InputValidator()
        result = v.sanitize_decision("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_length_limit(self):
        v = InputValidator()
        result = v.sanitize_decision("x" * 1000)
        assert len(result) <= 503

    def test_content_filter_safe(self):
        f = ContentFilter()
        ok, reason = f.check_content_safety("What if I moved to Paris?")
        assert ok is True
        assert reason is None

    def test_content_filter_blocked(self):
        f = ContentFilter()
        ok, reason = f.check_content_safety("What about self-harm?")
        assert ok is False
        assert "self-harm" in reason

    def test_output_sanitization(self):
        f = ContentFilter()
        result = f.sanitize_output('<script>alert(1)</script> hello')
        assert "<script>" not in result
        assert "hello" in result


class TestAPIMonitor:

    def test_tracks_calls(self):
        mon = APIMonitor()
        mon.record_call("model-a", tokens=100, cost=0.001)
        mon.record_call("model-a", tokens=200, cost=0.002)
        mon.record_call("model-b", tokens=150, cost=0.003)

        stats = mon.get_stats()
        assert stats["total_calls"] == 3
        assert stats["total_tokens"] == 450
        assert abs(stats["total_cost"] - 0.006) < 1e-9
        assert stats["by_api"]["model-a"]["calls"] == 2


class TestIntegrationWithSecurity:

    @pytest.mark.asyncio
    async def test_xss_in_decision(self):
        engine = SimulationEngine()
        branches = await engine.generate_branches(
            "What if I <script>alert('xss')</script>", "realistic", 2
        )
        assert len(branches) == 2
        assert "<script>" not in branches[0].story

    @pytest.mark.asyncio
    async def test_openrouter_mock(self):
        """Verify the engine correctly parses an OpenRouter-style response."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content='{"title":"Test Path","story":"A test story.","timeline":[{"year":"Year 1","event":"Test"}],"key_events":["Test event"],"probability_score":0.5}'
                )
            )
        ]
        mock_response.usage = Mock(total_tokens=100)
        mock_client.chat.completions.create.return_value = mock_response

        engine = SimulationEngine(api_key="test-key")
        engine.client = mock_client

        branches = await engine.generate_branches("test decision", "realistic", 1)

        assert len(branches) == 1
        assert branches[0].title == "Test Path"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
