from fastapi import Request, Response
from fastapi.responses import JSONResponse
import re
from typing import Dict, Any
import html

# Security headers middleware
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    return response

# Input validation and sanitization
class InputValidator:
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Basic HTML sanitization"""
        if not isinstance(text, str):
            return text

        # Remove script tags and other dangerous elements
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',
        ]

        sanitized = text
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)

        return html.escape(sanitized)

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))

    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format"""
        # Only allow alphanumeric characters, underscores, and hyphens
        username_pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(username_pattern, username)) and 3 <= len(username) <= 50

    @staticmethod
    def sanitize_input(data: Any) -> Any:
        """Recursively sanitize input data"""
        if isinstance(data, str):
            return InputValidator.sanitize_html(data)
        elif isinstance(data, dict):
            return {key: InputValidator.sanitize_input(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [InputValidator.sanitize_input(item) for item in data]
        else:
            return data

# SQL Injection prevention (additional layer)
class SQLInjectionProtector:
    @staticmethod
    def check_for_sql_injection(text: str) -> bool:
        """Check for potential SQL injection patterns"""
        if not isinstance(text, str):
            return False

        # Common SQL injection patterns
        sql_patterns = [
            r';\s*(drop|delete|update|insert|alter|create|truncate)\s',
            r'union\s+select',
            r'--',
            r'/\*.*\*/',
            r'xp_cmdshell',
            r'exec\s*\(',
            r'1=1',
            r'or\s+1=1',
            r'\'\s*or\s*\'',
        ]

        text_lower = text.lower()
        for pattern in sql_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        return False

# CSRF protection helper
def generate_csrf_token() -> str:
    """Generate CSRF token"""
    import secrets
    return secrets.token_urlsafe(32)

def validate_csrf_token(session_token: str, request_token: str) -> bool:
    """Validate CSRF token"""
    import hmac
    import hashlib

    if not session_token or not request_token:
        return False

    return hmac.compare_digest(session_token, request_token)

# Password strength validation
class PasswordValidator:
    @staticmethod
    def validate_strength(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        result = {
            "valid": True,
            "score": 0,
            "errors": []
        }

        if len(password) < 8:
            result["errors"].append("Password must be at least 8 characters long")
            result["valid"] = False

        if not re.search(r'[A-Z]', password):
            result["errors"].append("Password must contain at least one uppercase letter")
            result["valid"] = False

        if not re.search(r'[a-z]', password):
            result["errors"].append("Password must contain at least one lowercase letter")
            result["valid"] = False

        if not re.search(r'\d', password):
            result["errors"].append("Password must contain at least one digit")
            result["valid"] = False

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result["errors"].append("Password must contain at least one special character")
            result["valid"] = False

        # Calculate score
        score = 0
        if len(password) >= 8:
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        if len(password) >= 12:
            score += 1

        result["score"] = score

        return result

# Request validation middleware
async def request_validation_middleware(request: Request, call_next):
    """Validate and sanitize incoming requests"""
    # Skip validation for certain content types
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("application/json"):
        return await call_next(request)

    try:
        # Get request body
        body = await request.body()

        if body:
            import json
            data = json.loads(body.decode())

            # Sanitize input
            sanitized_data = InputValidator.sanitize_input(data)

            # Check for SQL injection
            def check_data_for_sql_injection(obj):
                if isinstance(obj, str):
                    if SQLInjectionProtector.check_for_sql_injection(obj):
                        raise HTTPException(
                            status_code=400,
                            detail="Potential SQL injection detected"
                        )
                elif isinstance(obj, dict):
                    for value in obj.values():
                        check_data_for_sql_injection(value)
                elif isinstance(obj, list):
                    for item in obj:
                        check_data_for_sql_injection(item)

            check_data_for_sql_injection(sanitized_data)

            # Replace request body with sanitized data
            sanitized_body = json.dumps(sanitized_data).encode()
            request._body = sanitized_body

    except json.JSONDecodeError:
        pass  # Not JSON, skip
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid request data", "detail": str(e)}
        )

    return await call_next(request)