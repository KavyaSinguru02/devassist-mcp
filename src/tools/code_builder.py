from __future__ import annotations

from pathlib import Path
from textwrap import dedent


def _safe_read(path: str, limit: int = 40_000) -> str:
    if not path:
        return ""
    p = Path(path)
    if not p.exists() or not p.is_file():
        return ""
    try:
        return p.read_text(encoding="utf-8", errors="ignore")[:limit]
    except Exception:
        return ""


def _detect_stack_from_path(path: str) -> str:
    p = Path(path) if path else Path(".")
    if not p.exists():
        return "Unknown"
    root = p if p.is_dir() else p.parent
    markers = {
        "requirements.txt": "Python",
        "pyproject.toml": "Python",
        "package.json": "JavaScript/TypeScript",
        "pom.xml": "Java/Spring",
        "build.gradle": "Java/Gradle",
        "go.mod": "Go",
        "Cargo.toml": "Rust",
        "composer.json": "PHP",
        "Gemfile": "Ruby",
        "pubspec.yaml": "Dart/Flutter",
        "mix.exs": "Elixir",
        "Package.swift": "Swift",
        "*.csproj": "C#/.NET",
    }
    found: list[str] = []
    for marker, name in markers.items():
        if "*" in marker:
            if list(root.glob(marker)):
                found.append(name)
        elif (root / marker).exists():
            found.append(name)
    return ", ".join(dict.fromkeys(found)) if found else "Unknown"


def _safe_identifier(value: str, fallback: str = "GeneratedFeature") -> str:
    cleaned = "".join(ch if ch.isalnum() else " " for ch in value).title().replace(" ", "")
    return cleaned[:60] or fallback


def _feature_name(requirement: str) -> str:
    return requirement.split(".")[0].split(",")[0].strip()[:80] or "Generated Feature"


def _generic_code_template(language: str, framework: str, feature_name: str) -> str:
    language_key = language.lower()
    framework_key = framework.lower()
    class_name = _safe_identifier(feature_name)
    function_name = "_".join(feature_name.lower().replace("-", " ").split())[:60] or "generated_feature"

    if "python" in language_key and "streamlit" in framework_key:
        return dedent(f'''
        from __future__ import annotations

        import streamlit as st


        def {function_name}_page() -> None:
            st.subheader("{feature_name}")
            user_input = st.text_area("Input", placeholder="Enter the required data")

            if st.button("Run", type="primary"):
                if not user_input.strip():
                    st.error("Please provide input.")
                    return

                st.success("Completed successfully.")
                st.write(user_input)
        ''').strip()

    if "python" in language_key and "fastapi" in framework_key:
        return dedent(f'''
        from __future__ import annotations

        from fastapi import APIRouter, HTTPException
        from pydantic import BaseModel

        router = APIRouter(prefix="/{function_name}", tags=["{feature_name}"])


        class {class_name}Request(BaseModel):
            value: str


        class {class_name}Response(BaseModel):
            success: bool
            message: str


        @router.post("/", response_model={class_name}Response)
        def handle_{function_name}(request: {class_name}Request) -> {class_name}Response:
            if not request.value.strip():
                raise HTTPException(status_code=400, detail="value is required")
            return {class_name}Response(success=True, message="Completed successfully")
        ''').strip()

    if "java" in language_key or "spring" in framework_key:
        return dedent(f'''
        @RestController
        @RequestMapping("/api/{function_name.replace('_', '-')}")
        public class {class_name}Controller {{

            private final {class_name}Service service;

            public {class_name}Controller({class_name}Service service) {{
                this.service = service;
            }}

            @PostMapping
            public ResponseEntity<{class_name}Response> handle(@RequestBody {class_name}Request request) {{
                return ResponseEntity.ok(service.handle(request));
            }}
        }}
        ''').strip()

    if any(x in language_key for x in ["javascript", "typescript"]) or "react" in framework_key:
        return dedent(f'''
        export function {class_name}() {{
          async function handleSubmit(input) {{
            if (!input || !input.trim()) {{
              throw new Error("Input is required");
            }}
            return {{ success: true, message: "Completed successfully" }};
          }}

          return {{ handleSubmit }};
        }}
        ''').strip()

    return dedent(f'''
    // Language: {language}
    // Framework/Style: {framework}
    // Feature: {feature_name}

    // Implementation outline:
    // 1. Create an input/request model for the required data.
    // 2. Validate required fields early.
    // 3. Put business logic in a service/module function.
    // 4. Return a clear success/error response.
    // 5. Add tests for success, invalid input, and edge cases.

    // Ask DevAssist to refine this for your exact project structure if needed.
    ''').strip()


def build_code_from_requirement(
    requirement: str,
    language: str = "Any",
    framework: str = "Any",
    target_file: str = "",
    repo_path: str = "",
    audience: str = "Developer",
) -> str:
    req = requirement.strip()
    if not req:
        return "# Code Builder\n\nPlease enter a clear requirement before generating code."

    existing = _safe_read(target_file)
    stack = _detect_stack_from_path(repo_path or target_file)
    feature_name = _feature_name(req).title()
    code = _generic_code_template(language, framework, feature_name)

    lines = [
        "# Code Builder Result",
        "",
        "## Requirement",
        req,
        "",
        "## Requested Stack",
        f"- Language: **{language or 'Any'}**",
        f"- Framework/Style: **{framework or 'Any'}**",
        f"- Repository stack detected: **{stack}**",
        f"- Output style: **{audience}**",
        "",
        "## Implementation Plan",
        "1. Identify the closest existing module or feature folder.",
        "2. Add a small, focused function/class/component for the new requirement.",
        "3. Validate user input before processing.",
        "4. Keep business logic separate from UI/router/controller code when possible.",
        "5. Add tests for success, validation failure, and edge cases.",
        "",
        "## Suggested Files",
        f"- `{target_file or 'Create a new file near related feature code'}`",
        "- Add or update a matching test file near your test folder.",
        "- Update README or usage docs only if the feature changes user behavior.",
        "",
        "## Starter Code",
        "```",
        code,
        "```",
        "",
        "## Test Guidance",
        f"Generate tests using the framework used by this project. If unsure, use the common test framework for **{language or stack or 'the detected language'}**.",
        "Cover these cases:",
        "- Valid input / happy path",
        "- Missing or invalid input",
        "- Boundary or edge cases",
        "- Failure path for external dependencies",
        "",
        "## Placement Guidance",
    ]

    if target_file:
        lines.append(f"Update `{target_file}` only if this feature belongs there. Otherwise create a separate file to keep the code clean.")
    elif repo_path:
        lines.append("Create the implementation near the most related feature folder in the repository.")
    else:
        lines.append("Create a small standalone module first, then integrate it into your app/router/UI after testing.")

    if existing:
        lines += [
            "",
            "## Existing File Context Used",
            f"`{target_file}` was read. Use the starter code as a safe draft and adapt it to the existing style.",
        ]

    return "\n".join(lines)
