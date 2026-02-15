"""
Configuration for the What If life-path simulator.
Centralized settings for LLM providers, rate limiting, caching, and security.
"""

# OpenRouter LLM Configuration
# Uses OpenRouter as a unified gateway to multiple model providers.
LLM_CONFIG = {
    "base_url": "https://openrouter.ai/api/v1",
    "models": {
        "primary": "anthropic/claude-sonnet-4-5-20250929",
        "fallback_1": "openai/gpt-4o",
        "fallback_2": "google/gemini-2.0-flash",
    },
    "max_tokens": 1024,
    "temperature": 0.7,
    "timeout": 30,
}

# Rate Limiting — token bucket algorithm
RATE_LIMIT_CONFIG = {
    "max_tokens": 10,
    "refill_rate": 0.5,       # tokens per second (1 every 2s)
    "burst_limit": 5,
}

# Response Cache — avoids duplicate LLM calls
CACHE_CONFIG = {
    "max_size": 100,
    "ttl_minutes": 15,
}

# Security
SECURITY_CONFIG = {
    "max_input_length": 500,
    "enable_content_filtering": True,
    "sanitize_outputs": True,
}

# Monitoring
MONITORING_CONFIG = {
    "enable_metrics": True,
    "log_api_calls": True,
    "track_costs": True,
}

# Cost estimates (per 1K tokens, USD)
COST_ESTIMATES = {
    "anthropic/claude-sonnet-4-5-20250929": 0.003,
    "openai/gpt-4o": 0.005,
    "google/gemini-2.0-flash": 0.0001,
}
