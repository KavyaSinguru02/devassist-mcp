from __future__ import annotations

import ast
from pathlib import Path
from analyzers.repository_analyzer import analyze_repository

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "target", "build", "dist"}


def _safe_read(path: Path, limit: int = 80_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except Exception as exc:
        return f""


def _friendly_missing(path: str) -> str:
    return f"""# I couldn't open this path

Path: `{path}`

Possible reasons:
- The file or folder does not exist.
- The path is relative to a different working directory.
- The repository is private or not cloned locally.

What you can try:
1. Use an absolute path.
2. Confirm the file exists.
3. For GitHub repositories, provide the file path inside the repository.
"""


def _python_symbols(content: str) -> tuple[list[str], list[str]]:
    try:
        tree = ast.parse(content)
    except Exception:
        return [], []
    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    funcs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return classes, funcs


def explain_code(file_path: str, language: str = "English", detail_level: str = "overview") -> str:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return _friendly_missing(file_path)
    content = _safe_read(path)
    classes, funcs = _python_symbols(content) if path.suffix == ".py" else ([], [])
    imports = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            imports.append(stripped)
        if len(imports) >= 12:
            break

    lines = [
        f"# File Guide: `{path.name}`",
        "",
        f"**Language requested:** {language}",
        "",
        "## What This File Is About",
        "This file is part of the project implementation. The explanation below is designed to help a developer understand purpose, structure, and flow before reading every line.",
        "",
        "## Why This File Exists",
        "It groups related logic in one place so the project stays easier to maintain and understand.",
        "",
        "## Key Building Blocks",
    ]
    if classes:
        lines.append("**Classes:** " + ", ".join(f"`{c}`" for c in classes[:20]))
    if funcs:
        lines.append("**Functions:** " + ", ".join(f"`{f}`" for f in funcs[:25]))
    if not classes and not funcs:
        lines.append("No Python classes/functions were detected, or this is not a Python source file.")
    lines += ["", "## Dependencies / Imports"]
    lines += [f"- `{i}`" for i in imports] if imports else ["- No imports detected in the first part of the file."]
    lines += ["", "## Beginner Explanation", "Read this file from top to bottom: imports first, constants/configuration next, then functions/classes. Focus on function names first because they usually describe the responsibility of the file."]
    if detail_level == "line-by-line":
        lines += ["", "## Line-by-Line Reading Aid"]
        for idx, line in enumerate(content.splitlines()[:120], start=1):
            if line.strip():
                lines.append(f"- Line {idx}: `{line[:120]}`")
    else:
        preview = "\n".join(content.splitlines()[:40])
        lines += ["", "## First 40 Lines Preview", "```", preview, "```"]
    return "\n".join(lines)


def explain_repo(repo_path: str, language: str = "English", detail_level: str = "overview") -> str:
    try:
        a = analyze_repository(repo_path)
    except Exception as exc:
        return f"# I couldn't analyze this repository\n\nReason: {exc}\n\nTry using an absolute local path or a valid GitHub repository URL."
    lines = [
        f"# Repository Guide: {a.name}",
        "",
        f"**Language requested:** {language}",
        "",
        "## Purpose",
        "This is a beginner-friendly orientation of the repository structure and important files.",
        "",
        "## Stack",
    ]
    lines += [f"- {s}" for s in a.stack]
    lines += ["", "## Architecture", a.architecture, "", "## Learning Path"]
    lines += [f"{x['step']}. `{x['path']}` — {x['reason']}" for x in a.learning_path] or ["1. Start with README or the main entry point."]
    if detail_level == "file-by-file":
        lines += ["", "## File-by-file overview"]
        lines += [f"- `{f}` — important project file/folder to inspect." for f in a.important_files[:40]]
    return "\n".join(lines)
