"""
Tool: Analyze uncommitted git changes for pre-commit code review.

Reads staged, unstaged, and untracked changes in a git repository and returns a summary
formatted as a prompt for Claude to review before commit.
"""
from pathlib import Path
from git import Repo, InvalidGitRepositoryError, NoSuchPathError  # type: ignore[import]


def analyze_git_diff(repo_path: str = ".", review_focus: str = "general") -> str:
    """
    Analyze uncommitted git changes in a repository and prepare a code review prompt for Claude.

    Args:
        repo_path (str): The path to the git repository. Defaults to the current directory.
        review_focus (str): The focus of the code review. Can be "general", "security",
            "performance", "bugs", or "style". Defaults to "general".

    Returns:
        str: A formatted string containing the git diff and review instructions, ready for analysis.
    """
    path = Path(repo_path).expanduser().resolve()

    try:
        repo = Repo(path, search_parent_directories=True)  # type: ignore[assignment]
    except NoSuchPathError:
        return f"The provided path '{repo_path}' does not exist."
    except InvalidGitRepositoryError:
        return f"The provided path '{repo_path}' is not a valid git repository."

    if repo.bare:  # type: ignore
        return (
            f"The provided path '{repo_path}' is a git repository but it is bare "
            "(has no working directory). Please provide a valid git repository with "
            "a working directory for analysis."
        )

    review_focus = review_focus.strip().lower()
    valid_focus = {"general", "security", "performance", "style", "bugs"}
    if review_focus not in valid_focus:
        return (
            f"Invalid review focus: '{review_focus}'\n\n"
            f"Valid options: {', '.join(sorted(valid_focus))}"
        )

    try:
        branch = repo.active_branch.name  # type: ignore[attr-defined]
    except Exception:
        branch = "DETACHED HEAD"

    staged_diff = repo.git.diff("--cached")  # type: ignore[attr-defined]
    unstaged_diff = repo.git.diff()  # type: ignore[attr-defined]
    untracked = repo.untracked_files  # type: ignore[attr-defined]

    if not staged_diff and not unstaged_diff and not untracked:
        return (
            f"Working tree clean on branch {branch}\n\n"
            "Nothing to review: no staged, unstaged, or untracked changes."
        )

    output = (
        f"Git Repository Analysis\n"
        f"Repo: {repo.working_dir}\n"  # type: ignore[attr-defined]
        f"Branch: {branch}\n"
        f"Review focus: {review_focus}\n"
    )

    if untracked:
        output += f"\nUntracked files ({len(untracked)}):\n" # type: ignore
        for file_path in untracked[:20]: # type: ignore
            output += f"  + {file_path}\n"
        if len(untracked) > 20: # type: ignore
            output += f"  and {len(untracked) - 20} more\n" # type: ignore

    if staged_diff:
        if len(staged_diff) > 15000: # type: ignore
            staged_diff = staged_diff[:15000] + "\n... (truncated diff too large)" # type: ignore
        output += f"\nSTAGED CHANGES (ready to commit):\n```diff\n{staged_diff}\n```\n"

    if unstaged_diff:
        if len(unstaged_diff) > 15000: # type: ignore
            unstaged_diff = unstaged_diff[:15000] + "\n... (truncated diff too large)" # type: ignore
        output += f"\nUNSTAGED CHANGES (modifications not yet staged):\n```diff\n{unstaged_diff}\n```\n"

    focus_instructions = {
        "general": (
            "Provide a holistic code review covering code quality, readability, "
            "potential bugs, design patterns, and overall improvements."
        ),
        "security": (
            "Focus PRIMARILY on security: hardcoded secrets/keys/passwords, "
            "SQL injection risks, XSS vulnerabilities, insecure deserialization, "
            "missing input validation, exposed sensitive data, weak cryptography. "
            "Be paranoid and flag anything suspicious."
        ),
        "performance": (
            "Focus PRIMARILY on performance: O(n²) loops, N+1 queries, "
            "unnecessary I/O, missing caching opportunities, memory leaks, "
            "blocking calls in async code, inefficient data structures."
        ),
        "style": (
            "Focus PRIMARILY on style and conventions: naming consistency, "
            "code formatting, comment quality, function length, "
            "PEP 8/language-specific style guide adherence."
        ),
        "bugs": (
            "Focus PRIMARILY on bugs: logic errors, off-by-one mistakes, "
            "null/None handling, race conditions, edge cases not handled, "
            "exception handling issues, type mismatches."
        ),
    }

    output += (
        "\n## Code Review Request\n"
        f"{focus_instructions[review_focus]}\n"
        "### Please provide:\n"
        "1. **Summary** What changed at a high level (2-3 sentences)\n"
        "2. **Strengths** - What's done well in these changes\n"
        "3. **Issues found** - Numbered list with severity (Critical / Medium / Minor)\n"
        "4. **Suggested fixes** - Concrete code suggestions for each issue\n"
        "5. **Ready to commit?** Your verdict: Yes / Fix issues first / Major rework needed\n"
        "Be honest and direct; better to catch issues now than after pushing!\n"
    )

    return output


if __name__ == "__main__":
    import sys

    target_repo = "."
    target_focus = "general"

    if len(sys.argv) > 1:
        target_repo = sys.argv[1]
    if len(sys.argv) > 2:
        target_focus = sys.argv[2]

    print(f"Testing git_analyzer on '{target_repo}' (focus: {target_focus})...\n")
    result = analyze_git_diff(target_repo, target_focus)
    print(result)


