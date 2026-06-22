"""Stronger email validation with OTP verification support."""

from __future__ import annotations

import os
import re
import secrets
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from functools import lru_cache
from typing import Optional

import dns.resolver
from email_validator import EmailNotValidError, validate_email


DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com",
    "10minutemail.com",
    "guerrillamail.com",
    "temp-mail.org",
    "yopmail.com",
    "sharklasers.com",
    "dispostable.com",
    "throwawaymail.com",
    "tempmail.com",
    "fakeinbox.com",
    "trashmail.com",
    "getnada.com",
    "moakt.com",
}

BLOCKED_LOCAL_PARTS = {
    "test",
    "testing",
    "demo",
    "dummy",
    "fake",
    "admin",
    "support",
    "info",
    "contact",
    "noreply",
    "no-reply",
}

COMMON_DOMAIN_TYPOS = {
    "gamil.com": "gmail.com",
    "gmial.com": "gmail.com",
    "gnail.com": "gmail.com",
    "hotmial.com": "hotmail.com",
    "outlok.com": "outlook.com",
    "yaho.com": "yahoo.com",
}


@dataclass
class EmailValidationResult:
    is_valid: bool
    normalized_email: Optional[str]
    message: str


@lru_cache(maxsize=1024)
def get_mx_records(domain: str) -> list[str]:
    try:
        answers = dns.resolver.resolve(domain, "MX")
        records = sorted(
            [(int(r.preference), str(r.exchange).rstrip(".")) for r in answers],
            key=lambda item: item[0],
        )
        return [host for _, host in records]
    except Exception:
        return []


def validate_email_before_otp(raw_email: str) -> EmailValidationResult:
    raw_email = raw_email.strip()

    if not raw_email:
        return EmailValidationResult(False, None, "Email is required.")

    try:
        result = validate_email(raw_email, check_deliverability=True)
        normalized = result.normalized
    except EmailNotValidError as exc:
        return EmailValidationResult(False, None, str(exc))

    local_part, _, domain = normalized.partition("@")
    local_part = local_part.lower()
    domain = domain.lower()

    if domain in COMMON_DOMAIN_TYPOS:
        return EmailValidationResult(
            False,
            None,
            f"Did you mean {local_part}@{COMMON_DOMAIN_TYPOS[domain]}?",
        )

    if domain in DISPOSABLE_EMAIL_DOMAINS:
        return EmailValidationResult(False, None, "Temporary/disposable emails are not allowed.")

    if local_part in BLOCKED_LOCAL_PARTS:
        return EmailValidationResult(False, None, "Please enter your real personal email address.")

    if re.fullmatch(r"\d+", local_part):
        return EmailValidationResult(False, None, "Email username cannot be only numbers.")

    if not get_mx_records(domain):
        return EmailValidationResult(False, None, "This email domain cannot receive emails.")

    return EmailValidationResult(True, normalized, "Email looks valid. OTP verification required.")


def generate_otp() -> str:
    return str(secrets.randbelow(900000) + 100000)


def send_otp_email(to_email: str, otp: str) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL", smtp_user)

    if not smtp_host or not smtp_user or not smtp_password or not from_email:
        raise RuntimeError(
            "SMTP is not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, and FROM_EMAIL."
        )

    message = EmailMessage()
    message["Subject"] = "Your DevAssist verification code"
    message["From"] = from_email
    message["To"] = to_email
    message.set_content(
        f"""
Hi,

Your DevAssist verification code is:

{otp}

This code is valid for this session.

Thank you,
DevAssist
"""
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)
