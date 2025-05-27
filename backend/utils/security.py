"""
Security Utilities
Security-related functions for input sanitization, CSRF protection, and security headers.
"""

import secrets
import hashlib
import hmac
import logging
from typing import Dict, Any, Optional
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def sanitize_input(text: str, allow_html: bool = False) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.

    Args:
        text: Input text to sanitize
        allow_html: Whether to allow basic HTML tags

    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return str(text)

    # Remove null bytes
    text = text.replace("\x00", "")

    if not allow_html:
        # Remove all HTML tags
        text = re.sub(r"<[^>]*>", "", text)

        # Remove potentially dangerous characters
        text = re.sub(r'[<>"\']', "", text)
    else:
        # Allow only basic HTML tags
        allowed_tags = ["b", "i", "u", "em", "strong", "p", "br"]
        # This is a simplified approach - in production, use a proper HTML sanitizer
        pass

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Limit length to prevent DoS
    if len(text) > 10000:
        text = text[:10000]

    return text


def generate_csrf_token() -> str:
    """
    Generate a CSRF token.

    Returns:
        Random CSRF token
    """
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, expected_token: str) -> bool:
    """
    Verify CSRF token.

    Args:
        token: Token to verify
        expected_token: Expected token value

    Returns:
        True if tokens match, False otherwise
    """
    if not token or not expected_token:
        return False

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(token, expected_token)


def generate_api_key() -> str:
    """
    Generate a secure API key.

    Returns:
        Random API key
    """
    return secrets.token_urlsafe(48)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for storage.

    Args:
        api_key: API key to hash

    Returns:
        Hashed API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against its hash.

    Args:
        api_key: API key to verify
        hashed_key: Stored hash

    Returns:
        True if API key matches, False otherwise
    """
    if not api_key or not hashed_key:
        return False

    computed_hash = hash_api_key(api_key)
    return hmac.compare_digest(computed_hash, hashed_key)


def generate_secure_filename(filename: str) -> str:
    """
    Generate a secure filename to prevent directory traversal.

    Args:
        filename: Original filename

    Returns:
        Secure filename
    """
    if not filename:
        return "unnamed_file"

    # Remove directory separators and dangerous characters
    filename = re.sub(r'[/\\:*?"<>|]', "", filename)

    # Remove leading dots to prevent hidden files
    filename = filename.lstrip(".")

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:250] + ("." + ext if ext else "")

    # Ensure it's not empty
    if not filename:
        filename = "unnamed_file"

    return filename


def check_password_strength(password: str) -> Dict[str, Any]:
    """
    Check password strength and provide feedback.

    Args:
        password: Password to check

    Returns:
        Dictionary with strength analysis
    """
    result = {"score": 0, "strength": "very_weak", "feedback": []}

    if not password:
        result["feedback"].append("Password is required")
        return result

    # Length check
    if len(password) >= 8:
        result["score"] += 1
    else:
        result["feedback"].append("Use at least 8 characters")

    if len(password) >= 12:
        result["score"] += 1

    # Character variety checks
    if re.search(r"[a-z]", password):
        result["score"] += 1
    else:
        result["feedback"].append("Add lowercase letters")

    if re.search(r"[A-Z]", password):
        result["score"] += 1
    else:
        result["feedback"].append("Add uppercase letters")

    if re.search(r"\d", password):
        result["score"] += 1
    else:
        result["feedback"].append("Add numbers")

    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result["score"] += 1
    else:
        result["feedback"].append("Add special characters")

    # Common patterns check
    if re.search(r"(.)\1{2,}", password):  # Repeated characters
        result["score"] -= 1
        result["feedback"].append("Avoid repeated characters")

    if re.search(r"(012|123|234|345|456|567|678|789|890)", password):
        result["score"] -= 1
        result["feedback"].append("Avoid sequential numbers")

    # Determine strength
    if result["score"] >= 6:
        result["strength"] = "very_strong"
    elif result["score"] >= 5:
        result["strength"] = "strong"
    elif result["score"] >= 4:
        result["strength"] = "medium"
    elif result["score"] >= 2:
        result["strength"] = "weak"
    else:
        result["strength"] = "very_weak"

    return result


def get_security_headers() -> Dict[str, str]:
    """
    Get recommended security headers for HTTP responses.

    Returns:
        Dictionary of security headers
    """
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }


def validate_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Validate webhook signature using HMAC.

    Args:
        payload: Request payload
        signature: Provided signature
        secret: Webhook secret

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature or not secret:
        return False

    # Remove 'sha256=' prefix if present
    if signature.startswith("sha256="):
        signature = signature[7:]

    # Compute expected signature
    expected_signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    # Use constant-time comparison
    return hmac.compare_digest(signature, expected_signature)


def generate_nonce() -> str:
    """
    Generate a cryptographic nonce.

    Returns:
        Random nonce
    """
    return secrets.token_hex(16)


def is_safe_url(url: str, allowed_hosts: Optional[list] = None) -> bool:
    """
    Check if a URL is safe for redirects.

    Args:
        url: URL to check
        allowed_hosts: List of allowed hostnames

    Returns:
        True if URL is safe, False otherwise
    """
    if not url:
        return False

    # Check for absolute URLs
    if url.startswith(("http://", "https://")):
        if allowed_hosts:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return parsed.hostname in allowed_hosts
        return False

    # Check for protocol-relative URLs
    if url.startswith("//"):
        return False

    # Check for javascript: or data: URLs
    if url.lower().startswith(("javascript:", "data:", "vbscript:")):
        return False

    # Relative URLs are generally safe
    return True


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging.

    Args:
        data: Data to mask
        mask_char: Character to use for masking
        visible_chars: Number of characters to leave visible

    Returns:
        Masked data
    """
    if not data or len(data) <= visible_chars:
        return mask_char * len(data) if data else ""

    return data[:visible_chars] + mask_char * (len(data) - visible_chars)


def generate_session_id() -> str:
    """
    Generate a secure session ID.

    Returns:
        Random session ID
    """
    return secrets.token_urlsafe(32)


def check_rate_limit_security(
    identifier: str, max_attempts: int = 5, window_minutes: int = 15
) -> Dict[str, Any]:
    """
    Security-focused rate limiting for login attempts, etc.

    Args:
        identifier: Unique identifier (IP, user ID, etc.)
        max_attempts: Maximum attempts allowed
        window_minutes: Time window in minutes

    Returns:
        Dictionary with rate limit status
    """
    # This would need Redis implementation for production
    # Placeholder implementation

    return {
        "allowed": True,
        "remaining_attempts": max_attempts - 1,
        "reset_time": datetime.utcnow() + timedelta(minutes=window_minutes),
        "blocked_until": None,
    }
