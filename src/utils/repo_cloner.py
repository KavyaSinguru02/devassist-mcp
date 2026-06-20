"""Utility to clone GitHub repos temporarily for analysis."""

import re
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

MAX_REPO_SIZE_MB = 200
CLONE_TIMEOUT = 60


def validate_github_url(url: str) -> tuple[bool, str]:
    """Validate that a URL is a public GitHub repo."""
    if not url:
        return False, "Please enter a GitHub URL"

    url = url.strip()
    pattern = r"^https?://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$"
    match = re.match(pattern, url)

    if not match:
        return False, (
            "Invalid format. Expected: https://github.com/owner/repo\n"
            "Example: https://github.com/psf/requests"
        )

    owner, repo = match.groups()
    if not owner or not repo:
        return False, "Owner and repo name cannot be empty"

    if owner.startswith(".") or repo.startswith("."):
        return False, "Owner/repo cannot start with a dot"

    normalized = f"https://github.com/{owner}/{repo}"
    return True, normalized


def get_repo_info(url: str) -> dict:
    """Extract owner and repo name from GitHub URL."""
    is_valid, normalized = validate_github_url(url)
    if not is_valid:
        return {"valid": False, "error": normalized}

    parts = normalized.replace("https://github.com/", "").split("/")
    return {
        "valid": True,
        "owner": parts[0],
        "repo": parts[1],
        "url": normalized,
        "display_name": f"{parts[0]}/{parts[1]}",
    }


@contextmanager
def clone_temp_repo(github_url: str):
    """Clone a GitHub repo to temp dir, yield path, auto-cleanup."""
    is_valid, result = validate_github_url(github_url)
    if not is_valid:
        raise ValueError(result)

    normalized_url = result
    temp_dir = tempfile.mkdtemp(prefix="devassist_clone_")
    temp_path = Path(temp_dir)

    try:
        result = subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--no-tags",
                "--single-branch",
                normalized_url,
                str(temp_path),
            ],
            capture_output=True,
            text=True,
            timeout=CLONE_TIMEOUT,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip()
            if "not found" in error_msg.lower():
                raise RuntimeError(
                    f"Repository not found or private: {normalized_url}"
                )
            else:
                raise RuntimeError(f"Clone failed: {error_msg}")

        size_mb = _get_dir_size_mb(temp_path)
        if size_mb > MAX_REPO_SIZE_MB:
            raise RuntimeError(
                f"Repository too large: {size_mb:.1f} MB (max: {MAX_REPO_SIZE_MB} MB)"
            )

        yield temp_path

    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Clone timed out after {CLONE_TIMEOUT}s.")

    finally:
        if temp_path.exists():
            shutil.rmtree(temp_path, ignore_errors=True)


def _get_dir_size_mb(path: Path) -> float:
    """Calculate total size of a directory in MB."""
    total_bytes = 0
    try:
        for item in path.rglob("*"):
            if item.is_file():
                try:
                    total_bytes += item.stat().st_size
                except (PermissionError, FileNotFoundError):
                    continue
    except (PermissionError, FileNotFoundError):
        pass

    return total_bytes / (1024 * 1024)


POPULAR_REPOS = {
    "Python Requests": "https://github.com/psf/requests",
    "React": "https://github.com/facebook/react",
    "LangChain": "https://github.com/langchain-ai/langchain",
    "FastAPI": "https://github.com/tiangolo/fastapi",
    "Streamlit": "https://github.com/streamlit/streamlit",
    "Flask": "https://github.com/pallets/flask",
}


if __name__ == "__main__":
    print("Test 1: Valid URL")
    is_valid, result = validate_github_url("https://github.com/psf/requests")
    print(f"Valid: {is_valid}, Result: {result}\n")

    print("Test 2: Invalid URL")
    is_valid, result = validate_github_url("not-a-url")
    print(f"Valid: {is_valid}, Result: {result}\n")

    print("Test 3: Clone test...")
    try:
        with clone_temp_repo("https://github.com/psf/requests") as path:
            py_files = list(path.rglob("*.py"))
            print(f"Cloned! Found {len(py_files)} Python files")
    except Exception as e:
        print(f"X Error: {e}")

    print("\nAll tests complete!")
