from __future__ import annotations

from pathlib import Path

SUPPORTED_FRAMEWORKS = {
    "pytest": {"language": "Python", "naming": "test_<module>.py", "style": "pytest fixtures and parameterize"},
    "unittest": {"language": "Python", "naming": "test_<module>.py", "style": "TestCase classes"},
    "jest": {"language": "JavaScript/TypeScript", "naming": "<module>.test.js/ts", "style": "describe/it blocks"},
    "vitest": {"language": "JavaScript/TypeScript", "naming": "<module>.test.ts", "style": "describe/it with expect"},
    "mocha": {"language": "JavaScript/TypeScript", "naming": "<module>.test.js", "style": "describe/it blocks"},
    "junit": {"language": "Java", "naming": "<Module>Test.java", "style": "@Test methods"},
    "testng": {"language": "Java", "naming": "<Module>Test.java", "style": "@Test methods"},
    "go test": {"language": "Go", "naming": "<module>_test.go", "style": "table-driven tests"},
    "rspec": {"language": "Ruby", "naming": "<module>_spec.rb", "style": "describe/context/it"},
    "phpunit": {"language": "PHP", "naming": "<Module>Test.php", "style": "PHPUnit TestCase"},
    "xunit": {"language": "C#/.NET", "naming": "<Module>Tests.cs", "style": "Fact/Theory tests"},
    "nunit": {"language": "C#/.NET", "naming": "<Module>Tests.cs", "style": "Test attributes"},
    "swift testing": {"language": "Swift", "naming": "<Module>Tests.swift", "style": "Swift Testing/XCTest"},
    "flutter test": {"language": "Dart/Flutter", "naming": "<module>_test.dart", "style": "testWidgets/test"},
}

SUPPORTED_LANGUAGES = [
    "English", "Telugu", "Hindi", "Tamil", "Spanish", "French", "German", "Polish",
    "Mandarin", "Japanese", "Korean", "Arabic", "Portuguese", "Russian", "Italian",
]

EXTENSION_LANGUAGE = {
    ".py": "Python",
    ".java": "Java",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript/React",
    ".jsx": "JavaScript/React",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".dart": "Dart",
    ".ex": "Elixir",
    ".scala": "Scala",
    ".cpp": "C++",
    ".c": "C",
}


def _framework_info(framework: str, detected_language: str) -> dict:
    key = framework.strip().lower()
    if key in SUPPORTED_FRAMEWORKS:
        return SUPPORTED_FRAMEWORKS[key]
    return {
        "language": detected_language or "Detected language",
        "naming": "Use the naming convention normally used by this framework/project.",
        "style": f"Use idiomatic {framework} tests with clear arrange/act/assert structure.",
    }


def _suggested_filename(stem: str, framework: str, suffix: str) -> str:
    key = framework.strip().lower()
    if key in {"pytest", "unittest"}:
        return f"test_{stem}.py"
    if key in {"jest", "vitest", "mocha"}:
        return f"{stem}.test.ts"
    if key in {"junit", "testng"}:
        return f"{stem}Test.java"
    if key == "go test":
        return f"{stem}_test.go"
    if key == "rspec":
        return f"{stem}_spec.rb"
    if key == "phpunit":
        return f"{stem}Test.php"
    if key in {"xunit", "nunit"}:
        return f"{stem}Tests.cs"
    if key == "flutter test":
        return f"{stem}_test.dart"
    return f"{stem}_test{suffix or '.txt'}"


def generate_tests(
    file_path: str,
    framework: str = "pytest",
    coverage_level: str = "thorough",
    explanation_language: str = "English",
) -> str:
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        return f"The provided path '{file_path}' does not exist."
    if not path.is_file():
        return f"The provided path '{file_path}' is not a valid file."

    max_file_size = 1 * 1024 * 1024
    file_size = path.stat().st_size
    if file_size > max_file_size:
        return f"The file '{file_path}' is too large ({file_size} bytes). Please provide a file smaller than 1MB for test generation."

    coverage_level = coverage_level.strip().lower()
    valid_coverage_levels = ["basic", "thorough", "exhaustive"]
    if coverage_level not in valid_coverage_levels:
        return f"Invalid coverage level '{coverage_level}'. Valid options are: {', '.join(valid_coverage_levels)}."

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except PermissionError:
        return f"Could not read the file '{file_path}' due to permission issues."

    detected_language = EXTENSION_LANGUAGE.get(path.suffix.lower(), path.suffix.lstrip(".").upper() or "Unknown")
    framework_info = _framework_info(framework, detected_language)
    suggested_test_filename = _suggested_filename(path.stem, framework, path.suffix)
    line_count = len(content.splitlines())

    coverage_instructions = {
        "basic": "Generate basic tests covering main happy paths and simple validation cases.",
        "thorough": "Generate thorough tests covering happy paths, edge cases, validation, and error handling.",
        "exhaustive": "Generate exhaustive tests covering success, failure, edge cases, boundary values, mocks, and integration-sensitive behavior.",
    }

    return f"""# Test Generation Request

Generate tests for the following code file.

Source File: {path.name}
Path: {path}
Size: {file_size:,} bytes | {line_count:,} lines
Detected Code Language: {detected_language}
Requested Test Framework: {framework}
Suggested Test Filename: {suggested_test_filename}
Coverage Level: {coverage_level}
Explanation/Comment Language: {explanation_language}

Framework Guidance:
- Language: {framework_info['language']}
- Naming: {framework_info['naming']}
- Style: {framework_info['style']}

Coverage Guidance:
- {coverage_instructions[coverage_level]}

Output requirements:
1. Return one complete runnable test file first.
2. Include only the setup/run commands required to execute the tests.
3. Include a short coverage summary.
4. Do not generate placeholder-only tests.
5. If external dependencies exist, mock them clearly.
6. Follow the conventions of the requested framework even if it is not in the predefined list.

--- SOURCE CODE ---
{content}
--- END SOURCE CODE ---
"""
