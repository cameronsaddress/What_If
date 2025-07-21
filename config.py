"""
Configuration settings for optimization and performance
"""

# Rate Limiting Configuration
RATE_LIMIT_CONFIG = {
    "max_tokens": 10,           # Maximum requests in bucket
    "refill_rate": 0.5,         # Tokens per second (1 token every 2 seconds)
    "burst_limit": 5,           # Max burst requests
}

# Cache Configuration
CACHE_CONFIG = {
    "max_size": 100,            # Maximum cached responses
    "ttl_minutes": 15,          # Time to live
    "enable_compression": True,  # Compress cached data
}

# API Configuration
API_CONFIG = {
    "grok": {
        "model": "grok-beta",
        "max_tokens": 1000,
        "temperature": 0.7,
        "timeout": 30,
        "base_url": "https://api.x.ai/v1"
    },
    "anthropic": {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1000,
        "temperature": 0.7,
        "timeout": 30
    },
    "openai": {
        "model": "gpt-4",
        "max_tokens": 1000,
        "temperature": 0.7,
        "timeout": 30
    }
}

# Performance Optimization
PERFORMANCE_CONFIG = {
    "enable_async": True,
    "max_concurrent_branches": 4,
    "batch_size": 2,
    "connection_pool_size": 10,
    "enable_response_streaming": False,
}

# Security Configuration
SECURITY_CONFIG = {
    "max_input_length": 500,
    "enable_content_filtering": True,
    "log_suspicious_activity": True,
    "api_key_validation": True,
    "sanitize_outputs": True,
}

# Monitoring Configuration
MONITORING_CONFIG = {
    "enable_metrics": True,
    "log_api_calls": True,
    "track_costs": True,
    "alert_on_errors": True,
    "metrics_retention_days": 30,
}

# Cost Optimization
COST_CONFIG = {
    "enable_caching": True,
    "prefer_cached_responses": True,
    "fallback_on_rate_limit": True,
    "batch_similar_requests": True,
    "estimated_costs": {
        "grok": 0.00001,      # Per token
        "anthropic": 0.00002,
        "openai": 0.00003
    }
}

# Development/Testing Configuration
DEV_CONFIG = {
    "enable_debug": False,
    "mock_api_calls": False,
    "always_use_fallback": False,
    "detailed_logging": True,
}