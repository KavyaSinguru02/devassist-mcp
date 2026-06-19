"""
Tool: Find TODOs,FIXMEs and Hacks in a codebase.

Scans all code files in a directory and extract comment markers
that indicate technical debt or incomplete work.
"""

import re
from pathlib import Path


def find_todos(directory: str = ".", patterns: list[str] | None = None) -> str:
    """
    Scan a directory for TODO/FIXME/HACK comments in code files
    Args:
        directory (str): The directory to scan. Defaults to the current directory.
        patterns (list[str] | None): List of file patterns to include in the scan.
            If None, defaults to common code file extensions.

    Returns:
        str: A formatted string containing the found TODOs, FIXMEs, and HACKs.
        showing the file path, line number, and comment text.
    """
    # Default patterns to search for if none are provided
    if patterns is None:
        patterns = ["TODO", "FIXME", "HACK", "BUG", "XXX"]

    # Convert the directory to a Path object
    path = Path(directory).expanduser().resolve()

    # Validate directory existence
    if not path.is_dir():
        return f"The provided path '{directory}' is not a valid directory."

    if not path.exists():
        return f"The provided path '{directory}' does not exist."

    # code file extensions we care about

    extensions = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".cs",
        ".rb",
        ".go",
        ".php",
        ".swift",
        ".kt",
        ".m",
        ".scala",
        ".rs",
        ".sh",
        ".html",
        ".css",
        ".json",
        ".xml",
    }

    # Directories to skip (don't scan dependencies/buildartifacts)
    skip_dirs = {
        "node_modules",
        "venv",
        ".venv",
        ".git",
        ".next",
        "target",
        "build",
        "dist",
        "__pycache__",
    }

    # Build regex pattern that matches:
    #   # TODO:MESSAGES (python style)
    #   //FIXME:MESSAGES (C/JS style)
    #   /* HACK:MESSAGES */ (C/Java style)
    pattern = re.compile(
        r"(?:#|//|/\*|\*)\s*(" + "|".join(patterns) + r")\b[:\s]*(.*)", re.IGNORECASE
    )

    # Track all matches found
    matches = []
    files_scanned = 0

    # walk through the directory and scan files
    for file_path in path.rglob("*"):
        # Skip directories we don't want to scan
        if any(part in skip_dirs for part in file_path.parts):
            continue

        # Only scan files with the specified extensions
        if not file_path.is_file() or file_path.suffix not in extensions:
            continue

        files_scanned += 1

        # Read file and search for patterns
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, start=1):
                    match = pattern.search(line)
                    if match:
                        tag = match.group(1).upper()
                        message = match.group(2).strip()
                        rel_path = file_path.relative_to(path)
                        matches.append(
                            {
                                "file": str(rel_path),
                                "line": line_num,
                                "tag": tag,
                                "message": message or "(no message)",
                            }
                        )
        except (UnicodeDecodeError, PermissionError):
            # skip files that can't be read due to encoding issues or permission errors
            continue

    if not matches:
        return f"No TODO/FIXME/HACK markers found in the directory '{directory}'."

    # Group matches by tag for readability
    by_tag = {}
    for m in matches:
        by_tag.setdefault(m["tag"], []).append(m)

    # Build output string
    output = f"Found {len(matches)} marker(s) in {files_scanned} scanned file(s):\n"

    for tag in sorted(by_tag.keys()):
        items = by_tag[tag]
        output += f"\n{tag} ({len(items)}):\n"

        # show upto 50 items per tag to avoid overwhelming output
        for item in items[:50]:
            output += f"  {item['file']}:{item['line']} - {item['message']}\n"

        if len(items) > 50:
            output += f"  ...and {len(items)-50} more {tag} marker(s) not shown.\n"

        output += f"\n"
    output += f"Scanned {files_scanned} file(s) and found {len(matches)} marker(s).\n"

    return output


# Test :run this file directly to test it
if __name__ == "__main__":
    print("Testing find_todos function in the current directory...")
    result = find_todos(".")
    print(result)
