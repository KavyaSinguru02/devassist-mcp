"""Analyze traceback or log text and return actionable debugging guidance."""

from __future__ import annotations

import re
from pathlib import Path


FILE_FRAME_RE = re.compile(r'File "([^"]+)", line (\d+), in ([^\n]+)')
EXCEPTION_RE = re.compile(r"^([\w.]+(?:Error|Exception|Warning)):\s*(.*)$")


def _is_user_file(path_str: str) -> bool:
    normalized = path_str.replace("\\", "/").lower()
    blocked = [
        "site-packages/",
        "/lib/python",
        "\\lib\\python",
        "python314",
        "python313",
        "python312",
        "python311",
    ]
    return not any(token in normalized for token in blocked)


def _extract_exception_line(lines: list[str]) -> tuple[str, str]:
    for line in reversed(lines):
        stripped = line.strip()
        match = EXCEPTION_RE.match(stripped)
        if match:
            return match.group(1), match.group(2).strip()

    for line in reversed(lines):
        stripped = line.strip()
        if stripped:
            return "UnknownError", stripped

    return "UnknownError", "No error details were provided."


def _root_cause_hint(exc_type: str, exc_message: str) -> str:
    msg_lower = exc_message.lower()

    if exc_type == "ModuleNotFoundError":
        missing = re.search(r"No module named ['\"]([^'\"]+)['\"]", exc_message)
        module_name = missing.group(1) if missing else "<module>"
        return (
            f"Missing dependency: '{module_name}' is not installed in the Python environment running this app. "
            "Install it in the same interpreter/venv used by the process."
        )

    if exc_type in {"ImportError", "NameError"}:
        return "Import/name mismatch: symbol is missing, misspelled, or not exported from the expected module."

    if exc_type == "FileNotFoundError":
        return "A required file/path does not exist at runtime. Verify working directory and input paths."

    if exc_type == "PermissionError":
        return "The process does not have file/system permission for the attempted operation."

    if exc_type in {"KeyError", "AttributeError", "TypeError", "ValueError"}:
        return "Data shape/type mismatch: inspect inputs just before the failing line and validate assumptions."

    if "timed out" in msg_lower or exc_type == "TimeoutError":
        return "Operation timeout: external dependency, network, or long task exceeded allowed time."

    return "Inspect the final app frame and evaluate variable values/inputs around that line."


def diagnose_error(error_text: str, repo_path: str = ".") -> str:
    """Parse traceback/log text and produce targeted debugging guidance.

    Args:
        error_text: Raw traceback or error log text.
        repo_path: Optional project root to resolve relative references.

    Returns:
        Human-readable debugging report.
    """
    raw = (error_text or "").strip()
    if not raw:
        return "Please paste traceback or error log text."

    lines = raw.splitlines()
    frames = FILE_FRAME_RE.findall(raw)
    exc_type, exc_message = _extract_exception_line(lines)

    app_frames = [(p, ln, fn) for p, ln, fn in frames if _is_user_file(p)]
    focus_frames = app_frames if app_frames else frames

    where_lines: list[str] = []
    for p, ln, fn in focus_frames[-5:]:
        where_lines.append(f"- {p}:{ln} (in {fn})")

    top_focus = focus_frames[-1] if focus_frames else None
    top_focus_text = (
        f"{top_focus[0]}:{top_focus[1]}" if top_focus else "Could not determine failing source line."
    )

    root_hint = _root_cause_hint(exc_type, exc_message)

    verify_steps: list[str] = []
    if exc_type == "ModuleNotFoundError":
        mod = re.search(r"No module named ['\"]([^'\"]+)['\"]", exc_message)
        module_name = mod.group(1) if mod else "<module>"
        verify_steps.extend(
            [
                "- Check interpreter in VS Code (Python: Select Interpreter).",
                f"- Run: python -m pip install {module_name}",
                f"- Verify: python -c \"import {module_name}; print('ok')\"",
            ]
        )
    else:
        verify_steps.extend(
            [
                "- Re-run command and capture full traceback.",
                f"- Add temporary prints/logs around: {top_focus_text}",
                "- Validate input values before the failing call.",
            ]
        )

    repo_root = Path(repo_path).expanduser().resolve()

    report = [
        "Error Diagnosis Report",
        "",
        f"Error type: {exc_type}",
        f"Error message: {exc_message or '(none)'}",
        "",
        f"Most likely root cause: {root_hint}",
        "",
        "Where to check first:",
    ]

    if where_lines:
        report.extend(where_lines)
    else:
        report.append("- No Python stack frames detected. Paste full traceback including 'File ... line ...'.")

    report.extend(
        [
            "",
            f"Repository context: {repo_root}",
            "",
            "Quick verification steps:",
            *verify_steps,
            "",
            "If it still fails: paste the complete traceback (including first and last lines).",
        ]
    )

    return "\n".join(report)
