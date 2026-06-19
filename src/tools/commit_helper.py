"""
Tool: Generate Conventional Commit messages from staged git changes.
"""
from pathlib import Path
from typing import Any
from git import Repo, InvalidGitRepositoryError, NoSuchPathError  # type: ignore[import]

COMMIT_TYPES = {
    "feat": "A new feature for the user",
    "fix": "A bug fix",
    "docs": "Documentation only changes",
    "style": "Formatting, missing semicolons (no logic change)",
    "refactor": "Code change that neither fixes a bug nor adds a feature",
    "perf": "Performance improvement",
    "test": "Adding or fixing tests",
    "chore": "Tooling, dependencies, build system",
    "ci": "CI/CD configuration changes",
    "build": "Build system or external dependency changes",
}


def suggest_commit_message(
    repo_path: str = ".",
    style: str = "conventional",
    include_body: bool = True,
) -> str:
    """Analyze staged changes and prepare a commit message generation prompt."""
    path = Path(repo_path).expanduser().resolve()

    try:
        repo: Any = Repo(path, search_parent_directories=True)  # type: ignore[assignment]
    except NoSuchPathError:
        return f"Error: Path does not exist: {path}"
    except InvalidGitRepositoryError:
        return f"Error: Not a git repository: {path}"

    if repo.bare:  # type: ignore[attr-defined]
        return "Error: Bare repository (no working tree)"

    style = style.strip().lower()
    valid_styles = {"conventional", "simple", "detailed"}
    if style not in valid_styles:
        return (
            f"Invalid style: '{style}'\n\n"
            f"Valid options: {', '.join(sorted(valid_styles))}"
        )

    staged_diff = str(repo.git.diff("--cached"))  # type: ignore[attr-defined]
    if not staged_diff:
        return (
            "No staged changes found.\n\n"
            "Stage your changes first:\n"
            "  git add <files>\n"
            "or stage everything:\n"
            "  git add .\n"
        )

    staged_files_raw = str(repo.git.diff("--cached", "--name-status"))  # type: ignore[attr-defined]
    staged_files = [line for line in staged_files_raw.splitlines() if line]

    try:
        branch = repo.active_branch.name  # type: ignore[attr-defined]
    except Exception:
        branch = "DETACHED HEAD"

    if len(staged_diff) > 12000:
        staged_diff = staged_diff[:12000] + "\n... (truncated)"

    files_summary = "\n".join(f"  {line}" for line in staged_files)
    style_instructions = {
        "conventional": _get_conventional_instructions(include_body),
        "simple": _get_simple_instructions(),
        "detailed": _get_detailed_instructions(),
    }
    instructions = style_instructions[style]

    return (
        f"Generate a {style} commit message\n\n"
        f"Branch: {branch}\n"
        f"Files changed ({len(staged_files)}):\n"
        f"{files_summary}\n\n"
        f"STAGED DIFF:\n```diff\n{staged_diff}\n```\n\n"
        f"{instructions}\n"
    )


def _get_conventional_instructions(include_body: bool) -> str:
    body_instruction = (
        "Include a detailed body describing what changed and why.\n"
        "Use bullet points for important details.\n"
    ) if include_body else ""

    return (
        "Write the commit message using Conventional Commit format:"
        "\n- type(scope): short description\n"
        "- include a longer description in the body if needed\n"
        "- reference any issue or ticket if applicable\n"
        f"{body_instruction}"
    )


def _get_simple_instructions() -> str:
    return (
        "Write a short, user-facing commit message that clearly explains the change.\n"
        "Keep it under 50 characters and avoid implementation details.\n"
    )


def _get_detailed_instructions() -> str:
    return (
        "Write a detailed commit message with a short summary and a body.\n"
        "Describe the problem, the fix, and any side effects.\n"
        "Keep the summary concise and the body easy to read.\n"
    )


if __name__ == "__main__":
    import sys

    target_repo = "."
    target_style = "conventional"
    include_body = True

    if len(sys.argv) > 1:
        target_repo = sys.argv[1]
    if len(sys.argv) > 2:
        target_style = sys.argv[2]
    if len(sys.argv) > 3:
        include_body = sys.argv[3].lower() in {"true", "1", "yes", "y"}

    print(suggest_commit_message(target_repo, target_style, include_body))
