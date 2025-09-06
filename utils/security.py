import os
import hmac
import hashlib
import base64
import logging
from typing import Optional
from flask import request, abort
from functools import wraps

logger = logging.getLogger(__name__)

class SecurityManager:
    """Security utilities for the application"""
    
    @staticmethod
    def verify_twilio_signature(request_url: str, post_params: dict, signature: str) -> bool:
        """
        Verify Twilio webhook signature to prevent spoofed requests
        
        Args:
            request_url: The full URL of the request
            post_params: POST parameters from the request
            signature: X-Twilio-Signature header value
            
        Returns:
            True if signature is valid, False otherwise
        """
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        if not auth_token:
            logger.warning("TWILIO_AUTH_TOKEN not set - cannot verify webhook signature")
            return False
        
        try:
            # Create the signature string
            signature_string = request_url
            
            # Sort parameters and append to signature string
            for key in sorted(post_params.keys()):
                signature_string += f"{key}{post_params[key]}"
            
            # Create HMAC-SHA1 hash
            mac = hmac.new(
                auth_token.encode('utf-8'),
                signature_string.encode('utf-8'),
                hashlib.sha1
            )
            
            # Base64 encode the hash
            expected_signature = base64.b64encode(mac.digest()).decode('utf-8')
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying Twilio signature: {e}")
            return False
    
    @staticmethod
    def require_twilio_signature(f):
        """
        Decorator to require valid Twilio signature on webhook endpoints
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip verification in development mode or if explicitly disabled
            if os.environ.get('FLASK_ENV') == 'development' or os.environ.get('SKIP_TWILIO_VERIFICATION') == '1':
                logger.info("Skipping Twilio signature verification (development mode)")
                return f(*args, **kwargs)
            
            # Get signature from headers
            signature = request.headers.get('X-Twilio-Signature')
            if not signature:
                logger.warning("Missing X-Twilio-Signature header")
                abort(403)
            
            # Verify signature
            request_url = request.url
            post_params = request.form.to_dict()
            
            if not SecurityManager.verify_twilio_signature(request_url, post_params, signature):
                logger.warning(f"Invalid Twilio signature for request to {request_url}")
                abort(403)
            
            logger.info("Twilio signature verified successfully")
            return f(*args, **kwargs)
        
        return decorated_function
    
    @staticmethod
    def sanitize_phone_number(phone: str) -> str:
        """
        Sanitize phone number input to prevent injection attacks
        
        Args:
            phone: Raw phone number input
            
        Returns:
            Sanitized phone number
        """
        if not phone:
            return ""
        
        # Remove all non-digit and non-plus characters
        sanitized = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Ensure it starts with + for E.164 format
        if sanitized and not sanitized.startswith('+'):
            sanitized = '+' + sanitized
        
        # Limit length to prevent abuse
        if len(sanitized) > 16:  # E.164 max length is 15 + 1 for +
            sanitized = sanitized[:16]
        
        return sanitized
    
    @staticmethod
    def sanitize_message_content(message: str) -> str:
        """
        Sanitize message content to prevent XSS and other attacks
        
        Args:
            message: Raw message content
            
        Returns:
            Sanitized message content
        """
        if not message:
            return ""
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r']
        sanitized = message
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        # Limit length to prevent abuse
        max_length = 1600  # SMS max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def is_safe_redirect_url(url: str) -> bool:
        """
        Check if a redirect URL is safe (prevents open redirect attacks)
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is safe for redirect, False otherwise
        """
        if not url:
            return False
        
        # Only allow relative URLs or URLs to the same domain
        if url.startswith('/'):
            return True
        
        # Block external redirects
        if url.startswith('http://') or url.startswith('https://'):
            return False
        
        return True
    
    @staticmethod
    def generate_csrf_token() -> str:
        """
        Generate a CSRF token for form protection
        
        Returns:
            CSRF token string
        """
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_admin_token(token: str) -> bool:
        """
        Validate admin authentication token
        
        Args:
            token: Token to validate
            
        Returns:
            True if token is valid, False otherwise
        """
        admin_token = os.environ.get('ADMIN_TOKEN')
        if not admin_token:
            logger.warning("ADMIN_TOKEN not configured")
            return False
        
        if not token:
            return False
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(admin_token, token)

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
        self.enabled = os.environ.get('RATE_LIMIT_ENABLED', '1') == '1'
        self.max_requests = int(os.environ.get('MAX_REQUESTS_PER_MINUTE', '60'))
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed based on rate limiting
        
        Args:
            identifier: Unique identifier for the client (IP, phone, etc.)
            
        Returns:
            True if request is allowed, False if rate limited
        """
        if not self.enabled:
            return True
        
        import time
        current_time = time.time()
        minute_window = int(current_time // 60)
        
        # Clean old entries
        self.requests = {k: v for k, v in self.requests.items() 
                        if k[1] >= minute_window - 1}
        
        # Count requests in current window
        key = (identifier, minute_window)
        current_count = self.requests.get(key, 0)
        
        if current_count >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {identifier}: {current_count} requests")
            return False
        
        # Increment counter
        self.requests[key] = current_count + 1
        return True
    
    def get_remaining_requests(self, identifier: str) -> int:
        """
        Get remaining requests for an identifier
        
        Args:
            identifier: Unique identifier for the client
            
        Returns:
            Number of remaining requests in current window
        """
        if not self.enabled:
            return self.max_requests
        
        import time
        current_time = time.time()
        minute_window = int(current_time // 60)
        
        key = (identifier, minute_window)
        current_count = self.requests.get(key, 0)
        
        return max(0, self.max_requests - current_count)

# Global rate limiter instance
rate_limiter = RateLimiter()

def require_rate_limit(identifier_func=None):
    """
    Decorator to apply rate limiting to endpoints
    
    Args:
        identifier_func: Function to get identifier from request (defaults to IP)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if identifier_func:
                identifier = identifier_func()
            else:
                identifier = request.remote_addr or 'unknown'
            
            if not rate_limiter.is_allowed(identifier):
                logger.warning(f"Rate limit exceeded for {identifier}")
                abort(429)  # Too Many Requests
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
