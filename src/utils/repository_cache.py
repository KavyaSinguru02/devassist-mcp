# src/utils/repository_cache.py

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from supabase import create_client


CACHE_TTL_HOURS = 24


@dataclass
class RepositoryCacheResult:
    found: bool
    overview: Optional[str] = None
    repo_name: Optional[str] = None
    frameworks: Optional[list[str]] = None
    architecture: Optional[str] = None
    last_commit: Optional[str] = None
    message: str = ""


def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise RuntimeError("Supabase is not configured.")

    return create_client(url, key)


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def is_cache_valid(updated_at: Optional[str], ttl_hours: int = CACHE_TTL_HOURS) -> bool:
    cached_time = _parse_timestamp(updated_at)

    if not cached_time:
        return False

    now = datetime.now(timezone.utc)

    return now - cached_time <= timedelta(hours=ttl_hours)


def get_cached_repo(repo_url: str) -> RepositoryCacheResult:
    try:
        response = (
            get_supabase_client()
            .table("repository_cache")
            .select("*")
            .eq("repo_url", repo_url)
            .limit(1)
            .execute()
        )

        rows = response.data or []

        if not rows:
            return RepositoryCacheResult(
                found=False,
                message="No cache found.",
            )

        row = rows[0]

        if not is_cache_valid(row.get("updated_at")):
            return RepositoryCacheResult(
                found=False,
                message="Cache expired.",
            )

        return RepositoryCacheResult(
            found=True,
            overview=row.get("overview"),
            repo_name=row.get("repo_name"),
            frameworks=row.get("frameworks") or [],
            architecture=row.get("architecture"),
            last_commit=row.get("last_commit"),
            message="Cache found.",
        )

    except Exception as exc:
        return RepositoryCacheResult(
            found=False,
            message=f"Cache lookup skipped: {exc}",
        )


def save_repo_cache(
    repo_url: str,
    overview: str,
    repo_name: Optional[str] = None,
    frameworks: Optional[list[str]] = None,
    architecture: Optional[str] = None,
    last_commit: Optional[str] = None,
) -> None:
    try:
        payload: dict[str, Any] = {
            "repo_url": repo_url,
            "repo_name": repo_name,
            "overview": overview,
            "frameworks": frameworks or [],
            "architecture": architecture,
            "last_commit": last_commit,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        (
            get_supabase_client()
            .table("repository_cache")
            .upsert(payload, on_conflict="repo_url")
            .execute()
        )

    except Exception:
        pass


def clear_repo_cache(repo_url: str) -> bool:
    try:
        (
            get_supabase_client()
            .table("repository_cache")
            .delete()
            .eq("repo_url", repo_url)
            .execute()
        )

        return True

    except Exception:
        return False