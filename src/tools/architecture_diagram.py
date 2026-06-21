"""Generate understandable Mermaid architecture diagrams from repository structure."""

from __future__ import annotations

from pathlib import Path

from utils.repo_cloner import clone_temp_repo, get_repo_info


SKIP_DIRS = {
    ".git",
    "venv",
    ".venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
}


def _classify_module(path: Path) -> str:
    names = {p.name.lower() for p in path.iterdir()} if path.is_dir() else set()
    if "pom.xml" in names:
        return "Java module (Maven)"
    if "build.gradle" in names or "build.gradle.kts" in names:
        return "Java/Kotlin module (Gradle)"
    if "package.json" in names:
        return "Node module"
    if "requirements.txt" in names or "pyproject.toml" in names:
        return "Python module"
    if "webcontent" in names or "webroot" in names:
        return "Web module (Servlet/JSP)"
    if "src" in names:
        return "Source module"
    return "Module"


def _key_subdirs(path: Path) -> list[str]:
    if not path.is_dir():
        return []
    picks: list[str] = []
    priority = {
        "src",
        "main",
        "java",
        "resources",
        "webcontent",
        "webroot",
        "controller",
        "service",
        "dao",
        "model",
        "entity",
        "config",
    }
    for item in sorted(path.iterdir(), key=lambda p: p.name.lower()):
        if not item.is_dir() or item.name in SKIP_DIRS or item.name.startswith("."):
            continue
        if item.name.lower() in priority:
            picks.append(item.name)
    return picks[:4]


def generate_architecture_diagram(
    repo_path: str,
    max_dirs: int = 20,
    mode: str = "overview",
    root_label: str | None = None,
) -> str:
    """Create an understandable Mermaid architecture diagram.

    Args:
        repo_path: Path to repository root.
        max_dirs: Maximum number of directories/files to include.

    Returns:
        Mermaid diagram text with human summary.
    """
    root = Path(repo_path).expanduser().resolve()
    if not root.is_dir():
        return f"Invalid repository path: {repo_path}"

    children = []
    for item in sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        if item.name in SKIP_DIRS or item.name.startswith("."):
            continue
        children.append(item)
        if len(children) >= max_dirs:
            break

    if not children:
        return f"No visible modules/files found in: {root}"

    mode = (mode or "overview").strip().lower()
    detailed = mode == "detailed"

    root_name = (root_label or root.name).replace('"', "'")

    lines = [
        "```mermaid",
        "flowchart LR",
        f"  R[\"{root_name}\\nRepository\"]",
        "  classDef module fill:#E9F2FF,stroke:#2B6CB0,stroke-width:1.4px,color:#102A43;",
        "  classDef key fill:#E6FFFA,stroke:#2C7A7B,stroke-width:1.2px,color:#1D4044;",
        "  classDef file fill:#FFF9DB,stroke:#B7791F,stroke-width:1px,color:#5F370E;",
    ]

    module_nodes: list[tuple[str, str]] = []
    key_files: list[str] = []

    for idx, item in enumerate(children, start=1):
        node = f"N{idx}"
        label = item.name.replace('"', "'")
        if item.is_dir():
            module_type = _classify_module(item)
            shape = f"[\"{label}\\n{module_type}\"]"
            module_nodes.append((label, module_type))
        else:
            shape = f"(\"{label}\")"
            key_files.append(label)
        lines.append(f"  {node}{shape}")
        lines.append(f"  R --> {node}")
        lines.append(f"  class {node} {'module' if item.is_dir() else 'file'};")

        if item.is_dir() and detailed:
            sub_dirs = _key_subdirs(item)
            for jdx, sub_name in enumerate(sub_dirs, start=1):
                sub_node = f"{node}_{jdx}"
                sub_label = sub_name.replace('"', "'")
                lines.append(f"  {sub_node}[\"{sub_label}\"]")
                lines.append(f"  {node} --> {sub_node}")
                lines.append(f"  class {sub_node} key;")

    lines.append("```")

    lines.append("\nArchitecture Summary:")
    if module_nodes:
        for name, module_type in module_nodes[:12]:
            lines.append(f"- Module: {name} ({module_type})")
    if key_files:
        lines.append(f"- Root-level files: {', '.join(key_files[:8])}")
    lines.append(
        "- Diagram style: overview-first. Use mode='detailed' to include important internal folders "
        "(src, webcontent, controller, service, dao, etc.)."
    )
    lines.append(
        "- This output is copy-paste ready for Mermaid editors, PR comments, docs, and chat tools."
    )
    return "\n".join(lines)


def generate_architecture_from_github_url(
    github_url: str,
    max_dirs: int = 20,
    mode: str = "overview",
) -> str:
    """Clone a public GitHub repository and generate an architecture diagram."""
    info = get_repo_info(github_url)
    if not info.get("valid"):
        return str(info.get("error", "Invalid GitHub repository URL."))

    try:
        with clone_temp_repo(str(info["url"])) as repo_path:
            diagram = generate_architecture_diagram(
                str(repo_path),
                max_dirs=max_dirs,
                mode=mode,
                root_label=str(info["display_name"]),
            )
            return (
                f"Repository: {info['display_name']}\n"
                f"Source URL: {info['url']}\n\n"
                f"{diagram}"
            )
    except Exception as exc:
        return f"Could not generate architecture diagram: {exc}"
