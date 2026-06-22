from __future__ import annotations

from pathlib import Path


SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "target",
}

ALLOWED_EXTENSIONS = {
    ".py",
    ".java",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".json",
    ".xml",
    ".properties",
    ".toml",
}


def _should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def _read_file(path: Path, max_chars: int = 8000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except Exception:
        return ""


def build_repository_index(repo_path: str) -> list[dict]:
    root = Path(repo_path)
    chunks = []

    if not root.exists():
        return chunks

    for file in root.rglob("*"):
        if not file.is_file():
            continue

        if _should_skip(file):
            continue

        if file.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        content = _read_file(file)

        if not content.strip():
            continue

        relative_path = str(file.relative_to(root))

        chunks.append(
            {
                "path": relative_path,
                "content": content,
            }
        )

    return chunks


def search_repository(chunks: list[dict], question: str, limit: int = 5) -> list[dict]:
    terms = [
        word.lower()
        for word in question.replace("_", " ").replace("-", " ").split()
        if len(word) > 2
    ]

    scored = []

    for chunk in chunks:
        content = chunk["content"].lower()
        path = chunk["path"].lower()

        score = 0

        for term in terms:
            if term in path:
                score += 5
            if term in content:
                score += content.count(term)

        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)

    return [chunk for _, chunk in scored[:limit]]


def chat_with_repository(
    repo_path: str,
    question: str,
    audience: str = "Beginner",
    language: str = "English",
) -> str:
    if not question.strip():
        return "Please enter a question about the repository."

    chunks = build_repository_index(repo_path)

    if not chunks:
        return (
            "I could not read this repository.\n\n"
            "Possible reasons:\n"
            "- The path is incorrect\n"
            "- The repository has unsupported file types\n"
            "- The repository is empty\n\n"
            "Try using a valid local repository path or GitHub repository."
        )

    matches = search_repository(chunks, question)

    if not matches:
        return (
            "# Repository Chat Answer\n\n"
            "I could not find a direct match in the repository files.\n\n"
            "Try asking with more specific words, such as:\n\n"
            "- Which file starts the application?\n"
            "- Where is authentication implemented?\n"
            "- Explain the database layer\n"
            "- Which file handles errors?\n"
        )

    lines = []

    lines.append("# Repository Chat Answer")
    lines.append("")
    lines.append(f"**Question:** {question}")
    lines.append(f"**Audience:** {audience}")
    lines.append(f"**Language requested:** {language}")
    lines.append("")
    lines.append("## Short Answer")
    lines.append(
        "Based on matching files in the repository, these are the most relevant places to inspect."
    )
    lines.append("")
    lines.append("## Relevant Files")

    for match in matches:
        lines.append(f"- `{match['path']}`")

    lines.append("")
    lines.append("## Explanation")

    for match in matches:
        content_preview = match["content"][:1200].strip()

        lines.append(f"### `{match['path']}`")
        lines.append("")
        lines.append(
            "This file appears relevant to your question because it contains matching terms or related code."
        )
        lines.append("")
        lines.append("```text")
        lines.append(content_preview)
        lines.append("```")
        lines.append("")

    lines.append("## What To Read Next")
    lines.append("1. Start with the first relevant file above.")
    lines.append("2. Look at its imports to understand dependencies.")
    lines.append("3. Search for the main classes or function names in the repository.")
    lines.append("4. Use Explain Code on the most important file.")

    return "\n".join(lines)