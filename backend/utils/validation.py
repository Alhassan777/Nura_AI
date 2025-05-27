"""
Validation Utilities
Input validation, sanitization, and data format checking.
"""

import re
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import html

logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid email format, False otherwise
    """
    if not email or not isinstance(email, str):
        return False

    # Basic email regex pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email.strip()) is not None


def validate_phone_number(phone: str, country_code: str = "US") -> bool:
    """
    Validate phone number format.

    Args:
        phone: Phone number to validate
        country_code: Country code for validation (default: US)

    Returns:
        True if valid phone format, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False

    # Remove all non-digit characters
    digits_only = re.sub(r"\D", "", phone)

    if country_code == "US":
        # US phone numbers: 10 digits
        return len(digits_only) == 10
    else:
        # International: 7-15 digits
        return 7 <= len(digits_only) <= 15


def validate_password(password: str, min_length: int = 8) -> Dict[str, Any]:
    """
    Validate password strength.

    Args:
        password: Password to validate
        min_length: Minimum password length

    Returns:
        Dictionary with validation results
    """
    result = {"valid": False, "errors": [], "strength": "weak"}

    if not password or not isinstance(password, str):
        result["errors"].append("Password is required")
        return result

    # Check length
    if len(password) < min_length:
        result["errors"].append(f"Password must be at least {min_length} characters")

    # Check for uppercase
    if not re.search(r"[A-Z]", password):
        result["errors"].append("Password must contain at least one uppercase letter")

    # Check for lowercase
    if not re.search(r"[a-z]", password):
        result["errors"].append("Password must contain at least one lowercase letter")

    # Check for digits
    if not re.search(r"\d", password):
        result["errors"].append("Password must contain at least one number")

    # Check for special characters
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result["errors"].append("Password must contain at least one special character")

    # Determine strength
    if len(result["errors"]) == 0:
        result["valid"] = True
        if len(password) >= 12:
            result["strength"] = "strong"
        elif len(password) >= 10:
            result["strength"] = "medium"
        else:
            result["strength"] = "weak"

    return result


def validate_user_input(
    data: Dict[str, Any], required_fields: List[str]
) -> Dict[str, Any]:
    """
    Validate user input data.

    Args:
        data: Input data to validate
        required_fields: List of required field names

    Returns:
        Dictionary with validation results
    """
    result = {"valid": True, "errors": {}, "sanitized_data": {}}

    # Check required fields
    for field in required_fields:
        if field not in data or not data[field]:
            result["valid"] = False
            result["errors"][field] = f"{field} is required"

    # Sanitize and validate specific fields
    for field, value in data.items():
        if value is None:
            continue

        # Sanitize string inputs
        if isinstance(value, str):
            sanitized_value = sanitize_input(value)
            result["sanitized_data"][field] = sanitized_value

            # Field-specific validation
            if field == "email":
                if not validate_email(sanitized_value):
                    result["valid"] = False
                    result["errors"][field] = "Invalid email format"

            elif field in ["phone", "phone_number", "phoneNumber"]:
                if not validate_phone_number(sanitized_value):
                    result["valid"] = False
                    result["errors"][field] = "Invalid phone number format"

            elif field == "password":
                password_validation = validate_password(
                    value
                )  # Don't sanitize passwords
                if not password_validation["valid"]:
                    result["valid"] = False
                    result["errors"][field] = password_validation["errors"]
                result["sanitized_data"][field] = value  # Keep original password

        else:
            result["sanitized_data"][field] = value

    return result


def validate_conversation_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate conversation/message data.

    Args:
        data: Conversation data to validate

    Returns:
        Dictionary with validation results
    """
    result = {"valid": True, "errors": {}, "sanitized_data": {}}

    # Required fields for conversation
    required_fields = ["content"]

    for field in required_fields:
        if field not in data or not data[field]:
            result["valid"] = False
            result["errors"][field] = f"{field} is required"

    # Validate content length
    if "content" in data and data["content"]:
        content = str(data["content"]).strip()
        if len(content) > 4000:  # Max message length
            result["valid"] = False
            result["errors"]["content"] = "Message too long (max 4000 characters)"
        elif len(content) < 1:
            result["valid"] = False
            result["errors"]["content"] = "Message cannot be empty"
        else:
            result["sanitized_data"]["content"] = sanitize_input(content)

    # Validate role if provided
    if "role" in data:
        valid_roles = ["user", "assistant", "system"]
        if data["role"] not in valid_roles:
            result["valid"] = False
            result["errors"]["role"] = f"Role must be one of: {', '.join(valid_roles)}"
        else:
            result["sanitized_data"]["role"] = data["role"]

    # Validate message type if provided
    if "message_type" in data:
        valid_types = ["text", "image", "audio", "system_alert"]
        if data["message_type"] not in valid_types:
            result["valid"] = False
            result["errors"][
                "message_type"
            ] = f"Message type must be one of: {', '.join(valid_types)}"
        else:
            result["sanitized_data"]["message_type"] = data["message_type"]

    return result


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS and other attacks.

    Args:
        text: Input text to sanitize

    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return str(text)

    # HTML escape
    sanitized = html.escape(text)

    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', "", sanitized)

    # Normalize whitespace
    sanitized = re.sub(r"\s+", " ", sanitized).strip()

    return sanitized


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID format.

    Args:
        uuid_string: UUID string to validate

    Returns:
        True if valid UUID format, False otherwise
    """
    if not uuid_string or not isinstance(uuid_string, str):
        return False

    # UUID pattern
    pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    return re.match(pattern, uuid_string.lower()) is not None


def validate_date_string(date_string: str, format_string: str = "%Y-%m-%d") -> bool:
    """
    Validate date string format.

    Args:
        date_string: Date string to validate
        format_string: Expected date format

    Returns:
        True if valid date format, False otherwise
    """
    if not date_string or not isinstance(date_string, str):
        return False

    try:
        datetime.strptime(date_string, format_string)
        return True
    except ValueError:
        return False


def validate_json_data(data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate JSON data against a simple schema.

    Args:
        data: Data to validate
        schema: Schema definition

    Returns:
        Dictionary with validation results
    """
    result = {"valid": True, "errors": []}

    # Simple schema validation
    if "type" in schema:
        expected_type = schema["type"]
        if expected_type == "string" and not isinstance(data, str):
            result["valid"] = False
            result["errors"].append(f"Expected string, got {type(data).__name__}")
        elif expected_type == "number" and not isinstance(data, (int, float)):
            result["valid"] = False
            result["errors"].append(f"Expected number, got {type(data).__name__}")
        elif expected_type == "boolean" and not isinstance(data, bool):
            result["valid"] = False
            result["errors"].append(f"Expected boolean, got {type(data).__name__}")
        elif expected_type == "array" and not isinstance(data, list):
            result["valid"] = False
            result["errors"].append(f"Expected array, got {type(data).__name__}")
        elif expected_type == "object" and not isinstance(data, dict):
            result["valid"] = False
            result["errors"].append(f"Expected object, got {type(data).__name__}")

    # Check required properties for objects
    if isinstance(data, dict) and "required" in schema:
        for prop in schema["required"]:
            if prop not in data:
                result["valid"] = False
                result["errors"].append(f"Missing required property: {prop}")

    return result


def check_rate_limit(
    identifier: str, max_requests: int = 100, window_minutes: int = 60
) -> Dict[str, Any]:
    """
    Simple rate limiting check (would need Redis implementation for production).

    Args:
        identifier: Unique identifier (user ID, IP, etc.)
        max_requests: Maximum requests allowed
        window_minutes: Time window in minutes

    Returns:
        Dictionary with rate limit status
    """
    # This is a placeholder implementation
    # In production, this would use Redis with sliding window or token bucket

    return {
        "allowed": True,
        "remaining": max_requests - 1,
        "reset_time": datetime.utcnow().timestamp() + (window_minutes * 60),
        "limit": max_requests,
    }
