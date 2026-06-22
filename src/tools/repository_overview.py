from __future__ import annotations

from analyzers.repository_analyzer import analyze_repository


def _bullet(items):
    return "\n".join(f"- `{item}`" for item in items) if items else "- Not detected"


def _diagram(architecture: str) -> str:
    if "Streamlit" in architecture or "tool" in architecture.lower():
        return """```mermaid
graph TD
    User[Developer/User] --> UI[Streamlit UI]
    UI --> Router[Tool Selection]
    Router --> Repo[Repository Overview]
    Router --> Explain[Code Explainer]
    Router --> Debug[Error Diagnoser]
    Router --> Tests[Test Generator]
    Router --> Git[Git Analyzer]
    Repo --> Result[Beginner Friendly Output]
    Explain --> Result
    Debug --> Result
    Tests --> Result
    Git --> Result
```"""
    if "MVC" in architecture or "Layered" in architecture:
        return """```mermaid
graph TD
    User[User] --> Controller[Controller / Route]
    Controller --> Service[Service / Business Logic]
    Service --> Repository[Repository / Data Access]
    Repository --> Database[(Database)]
    Database --> Repository
    Repository --> Service
    Service --> Controller
    Controller --> User
```"""
    return """```mermaid
graph TD
    User[User] --> Entry[Entry Point]
    Entry --> Core[Core Modules]
    Core --> Helpers[Utilities / Helpers]
    Core --> Output[Result]
```"""


def generate_repository_overview(repo_path: str, audience: str = "Beginner", language: str = "English", include_diagram: bool = True) -> str:
    a = analyze_repository(repo_path)
    lines = []
    lines.append(f"# Repository Guide: {a.name}")
    lines.append("")
    lines.append(f"**Audience:** {audience}")
    lines.append(f"**Language requested:** {language}")
    lines.append("")
    lines.append("## What This Repository Is About")
    lines.append(f"This repository contains a software project named **{a.name}**. DevAssist inspected the files and created a beginner-friendly map so a developer can understand where to start and how the project is organized.")
    lines.append("")
    lines.append("## Technology Stack")
    for item in a.stack:
        lines.append(f"- **{item}**")
    lines.append("")
    lines.append("## Frameworks and Why They Are Used")
    for fw in a.frameworks:
        lines.append(f"- **{fw['name']}** — {fw['why']} Detected in `{fw['detected_in']}`.")
    lines.append("")
    lines.append("## Architecture in Simple Words")
    lines.append(f"**Detected style:** {a.architecture}")
    lines.append("Think of the repository as a set of organized rooms: entry files receive the request, feature modules do the main work, and utility files support repeated tasks.")
    lines.append("")
    if include_diagram:
        lines.append("## Architecture Diagram")
        lines.append(_diagram(a.architecture))
        lines.append("")
    lines.append("## Important Entry Points")
    lines.append(_bullet(a.entry_points))
    lines.append("")
    lines.append("## Important Folders")
    lines.append(_bullet(a.important_folders))
    lines.append("")
    lines.append("## Important Files To Read")
    lines.append(_bullet(a.important_files[:20]))
    lines.append("")
    lines.append("## Beginner Learning Path")
    if a.learning_path:
        for step in a.learning_path:
            lines.append(f"{step['step']}. `{step['path']}` — {step['reason']}")
    else:
        lines.append("1. Start with the README or the main entry point detected above.")
    lines.append("")
    lines.append("## Repository Journey")
    lines.append("1. A developer opens the repository.")
    lines.append("2. They read the README or main entry file to understand the purpose.")
    lines.append("3. They inspect important folders to see where features live.")
    lines.append("4. They open one feature file at a time and follow imports/dependencies.")
    lines.append("5. They use error diagnosis, tests, and git tools when they start changing code.")
    lines.append("")
    lines.append("## Quick Facts")
    lines.append(f"- Files scanned: **{a.file_count}**")
    lines.append(f"- Folders scanned: **{a.folder_count}**")
    lines.append("- This guide focuses on teaching and orientation, not criticism or code review.")
    return "\n".join(lines)
