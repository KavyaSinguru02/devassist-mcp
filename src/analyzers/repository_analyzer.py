from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "target", "build", "dist", ".idea", ".vscode"}
IMPORTANT_NAMES = {"README.md", "readme.md", "app.py", "main.py", "server.py", "client.py", "requirements.txt", "package.json", "pom.xml", "build.gradle", "Dockerfile", "docker-compose.yml", "pyproject.toml"}


@dataclass
class RepoAnalysis:
    name: str
    root: str
    stack: list[str] = field(default_factory=list)
    frameworks: list[dict] = field(default_factory=list)
    architecture: str = "General application architecture"
    entry_points: list[str] = field(default_factory=list)
    important_files: list[str] = field(default_factory=list)
    important_folders: list[str] = field(default_factory=list)
    learning_path: list[dict] = field(default_factory=list)
    file_count: int = 0
    folder_count: int = 0


def _safe_read(path: Path, limit: int = 200_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except Exception:
        return ""


def _iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            yield path


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path)


def detect_stack(root: Path) -> list[str]:
    stack = []
    if (root / "requirements.txt").exists() or (root / "pyproject.toml").exists(): stack.append("Python")
    if (root / "package.json").exists(): stack.append("JavaScript / TypeScript")
    if (root / "pom.xml").exists() or (root / "build.gradle").exists(): stack.append("Java")
    if (root / "go.mod").exists(): stack.append("Go")
    if (root / "Cargo.toml").exists(): stack.append("Rust")
    if (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists(): stack.append("Docker")
    return stack or ["Stack not obvious from common manifest files"]


def detect_frameworks(root: Path) -> list[dict]:
    found: list[dict] = []
    req = _safe_read(root / "requirements.txt").lower()
    pyproject = _safe_read(root / "pyproject.toml").lower()
    pkg_raw = _safe_read(root / "package.json")
    pom = _safe_read(root / "pom.xml").lower()
    gradle = _safe_read(root / "build.gradle").lower()
    combined_py = req + "\n" + pyproject
    checks = [
        ("streamlit", "Streamlit", "Builds the interactive web UI quickly using Python."),
        ("fastapi", "FastAPI", "Creates fast Python APIs."),
        ("flask", "Flask", "Creates lightweight Python web apps/APIs."),
        ("django", "Django", "Creates full-featured Python web applications."),
        ("supabase", "Supabase", "Stores visitor/community data and can support auth later."),
        ("mcp", "MCP", "Exposes developer tools to AI clients through tool calls."),
    ]
    for key, name, why in checks:
        if key in combined_py:
            found.append({"name": name, "why": why, "detected_in": "requirements.txt/pyproject.toml"})
    if pkg_raw:
        try:
            pkg = json.loads(pkg_raw)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            for dep in deps:
                d=dep.lower()
                if d == "react": found.append({"name": "React", "why": "Builds reusable UI components.", "detected_in": "package.json"})
                if d == "next": found.append({"name": "Next.js", "why": "Builds React apps with routing and server-side features.", "detected_in": "package.json"})
                if d == "express": found.append({"name": "Express", "why": "Creates Node.js APIs and web servers.", "detected_in": "package.json"})
                if d == "@angular/core": found.append({"name": "Angular", "why": "Builds structured frontend applications.", "detected_in": "package.json"})
        except Exception:
            pass
    if "spring-boot" in pom + gradle:
        found.append({"name": "Spring Boot", "why": "Builds production-ready Java applications and APIs.", "detected_in": "pom.xml/build.gradle"})
    return found or [{"name": "No major framework detected", "why": "The project may be a library, script, or custom application.", "detected_in": "repository files"}]


def detect_architecture(root: Path) -> str:
    folders = {p.name.lower() for p in root.rglob("*") if p.is_dir() and not any(part in SKIP_DIRS for part in p.parts)}
    if {"controller", "controllers", "service", "services", "repository", "repositories"} & folders:
        return "Layered / MVC-style architecture"
    if (root / "app.py").exists() and (root / "src" / "tools").exists():
        return "Streamlit UI with modular tool architecture"
    if (root / "src" / "tools").exists():
        return "Modular tool-based architecture"
    if (root / "package.json").exists() and ((root / "pages").exists() or (root / "app").exists()):
        return "Frontend application architecture"
    return "General repository structure"


def analyze_repository(repo_path: str) -> RepoAnalysis:
    root = Path(repo_path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
    if root.is_file():
        root = root.parent

    files = list(_iter_files(root))
    dirs = [p for p in root.rglob("*") if p.is_dir() and not any(part in SKIP_DIRS for part in p.parts)]
    rel_files = [_rel(root, f) for f in files]

    important = [f for f in rel_files if Path(f).name in IMPORTANT_NAMES]
    important += [f for f in rel_files if any(part in f.lower().split("/") for part in ["tools", "utils", "controllers", "services", "repositories", "routes", "models", "config"])]
    important = list(dict.fromkeys(important))[:30]

    folders = []
    for candidate in ["src", "src/tools", "src/utils", "app", "pages", "controllers", "services", "repositories", "models", "tests", "config"]:
        if (root / candidate).exists():
            folders.append(candidate)

    entry_points = [f for f in rel_files if Path(f).name in {"app.py", "main.py", "server.py", "index.js", "main.ts", "Application.java"}]

    learning = []
    for idx, (file, reason) in enumerate([
        ("README.md", "Start here to understand the project goal."),
        ("app.py", "Main user interface entry point, if present."),
        ("server.py", "Backend or MCP server entry point, if present."),
        ("src/tools", "Core feature implementations usually live here."),
        ("src/utils", "Shared helper logic usually lives here."),
        ("tests", "Examples of expected behavior and edge cases."),
    ], start=1):
        if (root / file).exists():
            learning.append({"step": len(learning)+1, "path": file, "reason": reason})
    if not learning:
        for f in important[:5]:
            learning.append({"step": len(learning)+1, "path": f, "reason": "Important file detected from repository structure."})

    return RepoAnalysis(
        name=root.name,
        root=str(root),
        stack=detect_stack(root),
        frameworks=detect_frameworks(root),
        architecture=detect_architecture(root),
        entry_points=entry_points[:10],
        important_files=important,
        important_folders=folders,
        learning_path=learning,
        file_count=len(files),
        folder_count=len(dirs),
    )
