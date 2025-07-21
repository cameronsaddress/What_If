"""
Security utilities for input validation and sanitization
"""

import re
import html
from typing import Optional, List
import hashlib
import secrets

class InputValidator:
    """Validate and sanitize user inputs"""
    
    @staticmethod
    def sanitize_decision(decision: str) -> str:
        """Sanitize user decision input"""
        # Remove any HTML/script tags
        decision = html.escape(decision)
        
        # Limit length
        max_length = 500
        if len(decision) > max_length:
            decision = decision[:max_length] + "..."
        
        # Remove multiple spaces/newlines
        decision = ' '.join(decision.split())
        
        # Basic profanity filter (expandable)
        profanity_patterns = [
            r'\b(hate|kill|die)\b',  # Add more as needed
        ]
        
        for pattern in profanity_patterns:
            if re.search(pattern, decision, re.IGNORECASE):
                # Replace with asterisks
                decision = re.sub(pattern, '***', decision, flags=re.IGNORECASE)
        
        return decision
    
    @staticmethod
    def validate_api_key(api_key: str, api_type: str) -> bool:
        """Validate API key format"""
        if not api_key or not isinstance(api_key, str):
            return False
        
        # Basic format validation
        patterns = {
            "grok": r'^[a-zA-Z0-9\-_]{20,}$',  # Adjust based on actual format
            "anthropic": r'^sk-ant-[a-zA-Z0-9\-_]{40,}$',
            "openai": r'^sk-[a-zA-Z0-9]{40,}$'
        }
        
        pattern = patterns.get(api_type)
        if pattern and not re.match(pattern, api_key):
            return False
        
        return True
    
    @staticmethod
    def validate_mode(mode: str) -> str:
        """Validate simulation mode"""
        valid_modes = ["realistic", "50/50", "random"]
        if mode not in valid_modes:
            return "realistic"
        return mode

class APIKeyManager:
    """Secure API key management"""
    
    @staticmethod
    def hash_key(api_key: str) -> str:
        """Create a hash of API key for logging (never log actual keys)"""
        if not api_key:
            return "no_key"
        return hashlib.sha256(api_key.encode()).hexdigest()[:8]
    
    @staticmethod
    def mask_key(api_key: str) -> str:
        """Mask API key for display"""
        if not api_key or len(api_key) < 8:
            return "****"
        return f"{api_key[:4]}...{api_key[-4:]}"

class SecurityMonitor:
    """Monitor for suspicious activity"""
    
    def __init__(self):
        self.failed_attempts = {}
        self.request_patterns = {}
    
    def check_rate_abuse(self, user_id: str, max_requests_per_minute: int = 20) -> bool:
        """Check if user is abusing rate limits"""
        # Implementation would track requests per user
        # For now, return False (not abusing)
        return False
    
    def log_suspicious_activity(self, activity_type: str, details: dict):
        """Log suspicious activities for monitoring"""
        # In production, this would log to a security monitoring system
        print(f"Security Alert: {activity_type} - {details}")

class ContentFilter:
    """Filter inappropriate content"""
    
    @staticmethod
    def check_content_safety(text: str) -> tuple[bool, Optional[str]]:
        """
        Check if content is safe
        Returns: (is_safe, reason_if_not)
        """
        # Check for various inappropriate content
        checks = [
            (r'\b(suicide|self-harm)\b', "self-harm content"),
            (r'\b(violence|murder|assault)\b', "violent content"),
            (r'\b(illegal|crime|fraud)\b', "potentially illegal content"),
        ]
        
        for pattern, reason in checks:
            if re.search(pattern, text, re.IGNORECASE):
                return False, reason
        
        return True, None
    
    @staticmethod
    def sanitize_output(text: str) -> str:
        """Sanitize LLM output before displaying"""
        # Remove any potential prompt injections
        text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        
        # Escape HTML
        text = html.escape(text)
        
        return text

# Global instances
input_validator = InputValidator()
api_key_manager = APIKeyManager()
security_monitor = SecurityMonitor()
content_filter = ContentFilter()