import os
from dataclasses import dataclass
from typing import Optional

from supabase import create_client
from email_validator import EmailNotValidError, validate_email


@dataclass
class AuthResult:
    success: bool
    message: str
    email: Optional[str] = None


def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise RuntimeError("Supabase is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY.")

    return create_client(url, key)


def normalize_email(email: str) -> AuthResult:
    try:
        result = validate_email(email.strip(), check_deliverability=True)
        return AuthResult(True, "Valid email.", result.normalized)
    except EmailNotValidError as exc:
        return AuthResult(False, str(exc))


def send_login_otp(email: str) -> AuthResult:
    normalized = normalize_email(email)

    if not normalized.success:
        return normalized

    supabase = get_supabase_client()

    supabase.auth.sign_in_with_otp({
        "email": normalized.email,
        "options": {
            "email_redirect_to": "http://localhost:8501",
            "should_create_user": True,
        }
    })

    return AuthResult(True, "Magic link sent. Please check your email.", normalized.email)

def verify_login_otp(email: str, token: str) -> AuthResult:
    supabase = get_supabase_client()

    response = supabase.auth.verify_otp({
        "email": email,
        "token": token.strip(),
        "type": "email",
    })

    if response.user:
        return AuthResult(True, "Email verified successfully.", email)

    return AuthResult(False, "Invalid verification code.")