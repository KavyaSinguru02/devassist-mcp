from __future__ import annotations

import os
from collections import Counter
from typing import Any

try:
    from supabase import create_client
except Exception:  # pragma: no cover
    create_client = None


def _supabase_configured() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY") and create_client)


def get_supabase_client():
    if not _supabase_configured():
        raise RuntimeError("Supabase is not configured.")
    return create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))


def record_tool_usage(tool_name: str) -> None:
    try:
        get_supabase_client().table("tool_usage").insert(
            {"tool_name": tool_name}
        ).execute()
    except Exception:
        # Tracking should never block users from using DevAssist.
        pass


def get_tool_usage_stats() -> dict[str, int]:
    try:
        result = get_supabase_client().table("tool_usage").select("tool_name").execute()
        counter = Counter(item.get("tool_name", "Unknown") for item in (result.data or []))
        return dict(counter)
    except Exception:
        return {}


def save_tool_feedback(tool_name: str, vote: str) -> None:
    try:
        get_supabase_client().table("feedback").insert(
            {
                "tool_name": tool_name,
                "vote": vote,
            }
        ).execute()
    except Exception:
        # Feedback should never block users from continuing their task.
        pass


def get_feedback_summary() -> dict[str, dict[str, int]]:
    try:
        result = get_supabase_client().table("feedback").select("tool_name,vote").execute()
        summary: dict[str, dict[str, int]] = {}

        for item in result.data or []:
            tool = item.get("tool_name", "Unknown")
            vote = item.get("vote", "down")

            summary.setdefault(tool, {"up": 0, "down": 0})

            if vote == "up":
                summary[tool]["up"] += 1
            else:
                summary[tool]["down"] += 1

        return summary
    except Exception:
        return {}


def get_visitor_stats() -> dict[str, Any]:
    try:
        client = get_supabase_client()
        response = client.table("visitors").select("email", count="exact").execute()
        unique_visitors = int(response.count or 0)
    except Exception:
        unique_visitors = 0

    try:
        tool_response = get_supabase_client().table("tool_usage").select("id", count="exact").execute()
        total_tool_sessions = int(tool_response.count or 0)
    except Exception:
        total_tool_sessions = 0

    return {
        "unique_visitors": unique_visitors,
        "total_visits": total_tool_sessions,
    }
