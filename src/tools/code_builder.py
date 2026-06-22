from __future__ import annotations

from pathlib import Path
from textwrap import dedent

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "target", "build", "dist"}


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
    }
    found = []
    for marker, name in markers.items():
        if (root / marker).exists():
            found.append(name)
    return ", ".join(found) if found else "Unknown"


def _python_streamlit_template(feature_name: str) -> str:
    function_name = feature_name.lower().replace(" ", "_").replace("-", "_")
    return dedent(f'''
    from __future__ import annotations

    import streamlit as st


    def {function_name}_page() -> None:
        st.subheader("{feature_name}")
        user_input = st.text_area("Requirement", placeholder="Describe what you want this feature to do")

        if st.button("Run {feature_name}", type="primary"):
            if not user_input.strip():
                st.error("Please enter a requirement.")
                return

            st.success("Feature executed successfully.")
            st.write(user_input)
    ''').strip()


def _python_service_template(feature_name: str) -> str:
    class_name = "".join(part.capitalize() for part in feature_name.replace("-", " ").split()) or "GeneratedFeature"
    return dedent(f'''
    from __future__ import annotations

    from dataclasses import dataclass


    @dataclass
    class {class_name}Request:
        value: str


    @dataclass
    class {class_name}Result:
        success: bool
        message: str
        data: dict | None = None


    def handle_{feature_name.lower().replace(" ", "_").replace("-", "_")}(request: {class_name}Request) -> {class_name}Result:
        if not request.value.strip():
            return {class_name}Result(False, "Input is required.")

        return {class_name}Result(
            success=True,
            message="Completed successfully.",
            data={{"value": request.value.strip()}},
        )
    ''').strip()


def _java_spring_template(feature_name: str) -> str:
    class_name = "".join(part.capitalize() for part in feature_name.replace("-", " ").split()) or "GeneratedFeature"
    return dedent(f'''
    package com.example.devassist;

    import org.springframework.http.ResponseEntity;
    import org.springframework.web.bind.annotation.PostMapping;
    import org.springframework.web.bind.annotation.RequestBody;
    import org.springframework.web.bind.annotation.RequestMapping;
    import org.springframework.web.bind.annotation.RestController;

    @RestController
    @RequestMapping("/api/{feature_name.lower().replace(' ', '-')}")
    public class {class_name}Controller {{

        private final {class_name}Service service;

        public {class_name}Controller({class_name}Service service) {{
            this.service = service;
        }}

        @PostMapping
        public ResponseEntity<{class_name}Response> create(@RequestBody {class_name}Request request) {{
            return ResponseEntity.ok(service.handle(request));
        }}
    }}
    ''').strip()


def _react_template(feature_name: str) -> str:
    component = "".join(part.capitalize() for part in feature_name.replace("-", " ").split()) or "GeneratedFeature"
    return dedent(f'''
    import {{ useState }} from "react";

    export default function {component}() {{
      const [value, setValue] = useState("");
      const [message, setMessage] = useState("");

      function handleSubmit(event) {{
        event.preventDefault();
        if (!value.trim()) {{
          setMessage("Please enter a value.");
          return;
        }}
        setMessage("Submitted successfully.");
      }}

      return (
        <form onSubmit={{handleSubmit}}>
          <h2>{feature_name}</h2>
          <input value={{value}} onChange={{event => setValue(event.target.value)}} />
          <button type="submit">Submit</button>
          {{message && <p>{{message}}</p>}}
        </form>
      );
    }}
    ''').strip()


def _pick_template(language: str, framework: str, feature_name: str) -> str:
    key = f"{language} {framework}".lower()
    if "spring" in key or "java" in key:
        return _java_spring_template(feature_name)
    if "react" in key or "javascript" in key or "typescript" in key:
        return _react_template(feature_name)
    if "streamlit" in key:
        return _python_streamlit_template(feature_name)
    return _python_service_template(feature_name)


def build_code_from_requirement(
    requirement: str,
    language: str = "Python",
    framework: str = "General",
    target_file: str = "",
    repo_path: str = "",
    audience: str = "Developer",
) -> str:
    req = requirement.strip()
    if not req:
        return "# Code Builder\n\nPlease enter a clear requirement before generating code."

    existing = _safe_read(target_file)
    stack = _detect_stack_from_path(repo_path or target_file)
    feature_name = req.split(".")[0].split(",")[0][:40].strip().title() or "Generated Feature"
    code = _pick_template(language, framework, feature_name)

    lines = [
        "# Code Builder",
        "",
        "## Requirement",
        req,
        "",
        "## Detected Context",
        f"- Target language: {language}",
        f"- Framework: {framework}",
        f"- Repository stack: {stack}",
        f"- Audience: {audience}",
        "",
        "## Implementation Plan",
        "1. Add the generated code in the target module or create a new file for the feature.",
        "2. Connect the function/component/controller to the existing app flow.",
        "3. Validate required inputs before processing.",
        "4. Return clear success and error messages.",
        "5. Add tests for success, empty input, and failure paths.",
        "",
        "## Suggested Code",
        "```" + ("java" if language.lower().startswith("java") else "javascript" if language.lower() in {"javascript", "typescript"} else "python"),
        code,
        "```",
        "",
        "## Where To Place It",
    ]

    if target_file:
        lines.append(f"Use or update `{target_file}`.")
    elif "streamlit" in framework.lower():
        lines.append("Create a page/helper module and call it from `app.py`.")
    elif "spring" in framework.lower():
        lines.append("Create controller, service, request, and response classes under your Java package.")
    elif "react" in framework.lower():
        lines.append("Create a component file and import it into the relevant page or route.")
    else:
        lines.append("Create a new module near related business logic.")

    if existing:
        lines += [
            "",
            "## Existing File Context Used",
            f"`{target_file}` was read and can be updated manually with the generated implementation.",
        ]

    return "\n".join(lines)
