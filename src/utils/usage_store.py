"""Simple persistent storage for emails, visits, and feedback stats."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
STATS_FILE = DATA_DIR / "usage_stats.json"
EMAILS_FILE = DATA_DIR / "subscribers.csv"


def _ensure_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not STATS_FILE.exists():
        STATS_FILE.write_text(
            json.dumps(
                {
                    "created_at": _now_iso(),
                    "total_visits": 0,
                    "unique_visitors": [],
                    "feedback": {},
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    if not EMAILS_FILE.exists():
        with EMAILS_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["email", "subscribed_at"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_stats() -> dict[str, Any]:
    _ensure_files()
    try:
        return json.loads(STATS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "created_at": _now_iso(),
            "total_visits": 0,
            "unique_visitors": [],
            "feedback": {},
        }


def save_stats(stats: dict[str, Any]) -> None:
    _ensure_files()
    STATS_FILE.write_text(json.dumps(stats, indent=2), encoding="utf-8")


def register_visit(visitor_id: str) -> dict[str, Any]:
    stats = load_stats()
    stats["total_visits"] = int(stats.get("total_visits", 0)) + 1

    visitors = set(stats.get("unique_visitors", []))
    visitors.add(visitor_id)
    stats["unique_visitors"] = sorted(visitors)

    save_stats(stats)
    return stats


def get_visit_counts() -> tuple[int, int, str]:
    stats = load_stats()
    total = int(stats.get("total_visits", 0))
    unique = len(stats.get("unique_visitors", []))
    created_at = str(stats.get("created_at", _now_iso()))
    return total, unique, created_at


def subscribe_email(email: str) -> bool:
    _ensure_files()
    email = email.strip().lower()
    if not email:
        return False

    existing = set()
    with EMAILS_FILE.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing.add(str(row.get("email", "")).strip().lower())

    if email in existing:
        return False

    with EMAILS_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([email, _now_iso()])
    return True


def subscriber_count() -> int:
    _ensure_files()
    with EMAILS_FILE.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return sum(1 for _ in reader)


def add_feedback(service: str, vote: str) -> dict[str, Any]:
    stats = load_stats()
    feedback = stats.setdefault("feedback", {})
    service_stats = feedback.setdefault(service, {"up": 0, "down": 0})

    if vote == "up":
        service_stats["up"] = int(service_stats.get("up", 0)) + 1
    elif vote == "down":
        service_stats["down"] = int(service_stats.get("down", 0)) + 1

    save_stats(stats)
    return service_stats


def get_feedback(service: str) -> tuple[int, int]:
    stats = load_stats()
    service_stats = stats.get("feedback", {}).get(service, {"up": 0, "down": 0})
    return int(service_stats.get("up", 0)), int(service_stats.get("down", 0))
