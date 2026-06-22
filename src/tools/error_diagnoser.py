from __future__ import annotations

import re
from pathlib import Path

FRAME_RE = re.compile(r'File "(?P<file>[^"]+)", line (?P<line>\d+), in (?P<func>.+)')
EXC_RE = re.compile(r'(?P<type>[A-Za-z_][\w.]*Error|Exception): (?P<msg>.+)')


def _extract_frames(text: str):
    frames = []
    for m in FRAME_RE.finditer(text):
        frames.append({"file": m.group("file"), "line": int(m.group("line")), "func": m.group("func")})
    return frames


def _extract_exception(text: str):
    matches = list(EXC_RE.finditer(text))
    if not matches:
        return "Unknown error", "Could not detect a specific exception message."
    m = matches[-1]
    return m.group("type"), m.group("msg")


def _hint(exc_type: str, msg: str) -> str:
    lower = (exc_type + " " + msg).lower()
    if "importerror" in lower or "modulenotfounderror" in lower:
        return "A required module/function could not be imported. Check the import name, installed package, and file path."
    if "attributeerror" in lower and "nonetype" in lower:
        return "A variable is None, but the code is trying to access an attribute on it. Check where that value is created or returned."
    if "keyerror" in lower:
        return "The code expected a dictionary key that was not present. Check input data and add safe defaults."
    if "filenotfounderror" in lower:
        return "The code is trying to read a file/path that does not exist from the current working directory."
    if "permission" in lower:
        return "The current user or API key does not have permission for this operation. Check roles, grants, and policies."
    if "timeout" in lower:
        return "An external operation took too long. Add retries, smaller inputs, or increase timeout safely."
    return "Start from the last file shown in the traceback. That is usually the closest place to the real failure."


def diagnose_error(error_text: str, repo_path: str = ".") -> str:
    if not error_text.strip():
        return "# No error text provided\n\nPaste the full traceback or log so DevAssist can explain what happened."
    frames = _extract_frames(error_text)
    exc_type, msg = _extract_exception(error_text)
    likely = frames[-1] if frames else None
    lines = [
        "# Error Diagnosis",
        "",
        "## What Happened",
        f"**{exc_type}** — {msg}",
        "",
        "## Likely Root Cause",
        _hint(exc_type, msg),
        "",
        "## Where To Look First",
    ]
    if likely:
        lines.append(f"- File: `{likely['file']}`")
        lines.append(f"- Line: `{likely['line']}`")
        lines.append(f"- Function: `{likely['func']}`")
    else:
        lines.append("- Could not detect a traceback frame. Look near the code that produced this log.")
    lines += ["", "## What You Can Do", "1. Open the file and line mentioned above.", "2. Check the values being passed into that function.", "3. Confirm required files, imports, environment variables, and permissions.", "4. Re-run after one small fix so you can verify the change.", "", "## Prevention Tip", "Add validation and friendly error messages near user input, file access, external APIs, and database calls."]
    return "\n".join(lines)
