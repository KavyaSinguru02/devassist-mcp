from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from email_validator import EmailNotValidError, validate_email

try:
    from supabase import create_client
except Exception:  # pragma: no cover
    create_client = None


@dataclass
class VisitorResult:
    success: bool
    message: str
    email: Optional[str] = None


def _supabase_configured() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY") and create_client)


def normalize_email(email: str) -> VisitorResult:
    try:
        result = validate_email(email.strip(), check_deliverability=True)
        return VisitorResult(True, "Valid email.", result.normalized)
    except EmailNotValidError as exc:
        return VisitorResult(False, str(exc))


def save_visitor_email(email: str, session_id: str) -> VisitorResult:
    normalized = normalize_email(email)
    if not normalized.success:
        return normalized

    if not _supabase_configured():
        return VisitorResult(True, "Email accepted locally. Supabase is not configured.", normalized.email)

    client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
    client.table("visitors").upsert(
        {"email": normalized.email, "session_id": session_id},
        on_conflict="email",
    ).execute()
    return VisitorResult(True, "Email saved.", normalized.email)
