"""Explain code files and repositories in direct plain English."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

MAX_FILE_SIZE = 1 * 1024 * 1024
MAX_REPO_FILES = 250
EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs",
    ".cpp", ".c", ".cs", ".rb", ".php", ".swift", ".kt", ".scala", ".sh",
}
SKIP_DIRS = {
    ".git", "venv", ".venv", "node_modules", "dist", "build", "target",
    "__pycache__", ".pytest_cache", ".mypy_cache",
}


def _read_text(path: Path) -> tuple[bool, str]:
    try:
        return True, path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return False, str(exc)


def _clean_name(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").strip()


def _line_explanation(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return "Blank line used to separate logic and improve readability."
    if stripped.startswith(("#", "//", "/*", "*")):
        return "Comment that explains intent or gives context."
    if stripped.startswith(("import ", "from ", "package ")):
        return "Imports code or dependencies needed by this file."
    if stripped.startswith("class "):
        return "Defines a class, which groups related data and behavior."
    if stripped.startswith(("def ", "async def ", "function ", "func ")):
        return "Defines a function or method that performs a specific task."
    if stripped.startswith(("if ", "elif ", "else", "switch", "case")):
        return "Conditional branch that chooses behavior based on a condition."
    if stripped.startswith(("for ", "while ")):
        return "Loop that repeats work over data or until a condition changes."
    if stripped.startswith("return"):
        return "Returns a result from the current function or method."
    if stripped.startswith(("raise ", "throw ")):
        return "Stops normal execution and signals an error condition."
    if "=" in stripped and "==" not in stripped:
        return "Stores or updates a value in a variable."
    if "(" in stripped and ")" in stripped:
        return "Calls another function or method to perform work."
    return "General program statement that contributes to the file's behavior."


def _extract_symbols(content: str) -> dict[str, list[str]]:
    classes = re.findall(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)", content, flags=re.MULTILINE)
    functions = re.findall(r"^(?:async\s+def|def)\s+([A-Za-z_][A-Za-z0-9_]*)", content, flags=re.MULTILINE)
    imports = re.findall(r"^(?:from|import)\s+(.+)", content, flags=re.MULTILINE)
    return {
        "classes": classes[:8],
        "functions": functions[:12],
        "imports": imports[:8],
    }


def explain_code(file_path: str, language: str = "English", detail_level: str = "overview") -> str:
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        return f"The provided path '{file_path}' does not exist."
    if not path.is_file():
        return f"The provided path '{file_path}' is not a valid file."

    file_size = path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        return (
            f"The file '{file_path}' is too large ({file_size} bytes). "
            "Please provide a file smaller than 1MB for explanation."
        )

    ok, content = _read_text(path)
    if not ok:
        return f"Could not read the file '{file_path}': {content}"

    lines = content.splitlines()
    symbols = _extract_symbols(content)
    detail = (detail_level or "overview").strip().lower()

    if detail == "line-by-line":
        output = [
            f"File: {path.name}",
            f"Purpose: This file is written in {path.suffix.lstrip('.').upper() or 'text'} and contains {len(lines)} lines.",
            "",
            "Line-by-line explanation:",
        ]
        for index, line in enumerate(lines, start=1):
            preview = line.rstrip() if line.strip() else "(blank)"
            if len(preview) > 120:
                preview = preview[:117] + "..."
            output.append(f"- Line {index}: {preview}")
            output.append(f"  Meaning: {_line_explanation(line)}")
        return "\n".join(output)

    summary_bits: list[str] = []
    if symbols["classes"]:
        summary_bits.append(f"classes such as {', '.join(symbols['classes'][:3])}")
    if symbols["functions"]:
        summary_bits.append(f"functions such as {', '.join(symbols['functions'][:5])}")
    if symbols["imports"]:
        summary_bits.append("external dependencies or shared modules")

    likely_role = "general application logic"
    name_lower = path.name.lower()
    if "model" in name_lower:
        likely_role = "data modeling and persistence"
    elif "view" in name_lower or "controller" in name_lower:
        likely_role = "request handling and response generation"
    elif "form" in name_lower or "schema" in name_lower:
        likely_role = "input validation and data shaping"
    elif "test" in name_lower:
        likely_role = "automated testing"
    elif "util" in name_lower or "helper" in name_lower:
        likely_role = "shared helper logic"

    output = [
        f"File: {path.name}",
        f"What it does: This file mainly handles {likely_role}.",
        f"Size: {len(lines)} lines, {file_size} bytes.",
    ]

    if summary_bits:
        output.append(f"Main contents: It contains {', '.join(summary_bits)}.")
    if symbols["functions"]:
        output.append(f"Key functions: {', '.join(symbols['functions'][:8])}.")
    if symbols["classes"]:
        output.append(f"Key classes: {', '.join(symbols['classes'][:6])}.")

    output.extend(
        [
            "",
            "Plain-English overview:",
            "- Start by reading the function and class names. They show the main responsibilities of the file.",
            "- Then check the imports to understand which framework or helper modules this file depends on.",
            "- If you need deeper detail, use the line-by-line mode for this specific file.",
        ]
    )
    return "\n".join(output)


def _collect_repo_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for item in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in item.parts):
            continue
        if item.is_file() and item.suffix.lower() in EXTENSIONS:
            files.append(item)
        if len(files) >= MAX_REPO_FILES:
            break
    return files


def _detect_stack(files: list[Path], root: Path) -> list[str]:
    names = {file.name.lower() for file in files}
    rels = [str(file.relative_to(root)).lower().replace("\\", "/") for file in files]
    stack: list[str] = []
    if "manage.py" in names or any("django" in rel for rel in rels):
        stack.append("Django")
    if any(rel.endswith(".py") for rel in rels):
        stack.append("Python")
    if "requirements.txt" in names:
        stack.append("requirements.txt dependency management")
    if any(rel.endswith(".js") or rel.endswith(".ts") for rel in rels):
        stack.append("JavaScript or TypeScript")
    if any("templates/" in rel for rel in rels):
        stack.append("server-rendered HTML templates")
    return stack or ["general multi-module project"]


def _sample_blob(files: list[Path], root: Path) -> str:
    parts: list[str] = []
    for file in files[:80]:
        parts.append(str(file.relative_to(root)).lower())
        ok, content = _read_text(file)
        if ok:
            parts.append(content.lower()[:1800])
    return "\n".join(parts)


def _infer_domain(blob: str) -> str:
    if sum(1 for word in ("cart", "checkout", "order", "product", "payment", "coupon", "wishlist") if word in blob) >= 2:
        return "ecommerce website"
    if any(word in blob for word in ("blog", "article", "post", "comment")):
        return "content publishing site"
    if any(word in blob for word in ("course", "lesson", "student", "instructor")):
        return "learning platform"
    if any(word in blob for word in ("login", "signup", "auth", "token", "password reset")):
        return "user account or authentication system"
    return "software application"


def _find_django_apps(root: Path) -> list[str]:
    apps: list[str] = []
    src_dir = root / "src"
    base = src_dir if src_dir.is_dir() else root
    for child in sorted(base.iterdir(), key=lambda item: item.name.lower()):
        if not child.is_dir() or child.name in SKIP_DIRS or child.name.startswith("."):
            continue
        files = {item.name for item in child.iterdir() if item.is_file()}
        if {"apps.py", "models.py"} & files or {"views.py", "urls.py"} & files:
            apps.append(child.name)
    return apps[:12]


def _key_files(root: Path) -> list[str]:
    candidates = [
        "README.md", "requirements.txt", "manage.py", "app.py", "server.py",
        "package.json", "Dockerfile", "Procfile", "runtime.txt",
    ]
    found: list[str] = []
    for candidate in candidates:
        for path in root.rglob(candidate):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            found.append(str(path.relative_to(root)).replace("\\", "/"))
            break
    return found[:12]


def _read_readme(root: Path) -> str:
    for name in ("README.md", "README.txt", "README"):
        readme = root / name
        if readme.exists() and readme.is_file():
            ok, content = _read_text(readme)
            if ok:
                collapsed = " ".join(content.split())
                return collapsed[:400]
    return ""


def _flow_summary(apps: list[str], blob: str) -> list[str]:
    flow: list[str] = []
    if any(word in blob for word in ("urls.py", "path(", "urlpatterns", "re_path(")):
        flow.append("A browser request first reaches Django URL routing, which decides which view should handle it.")
    if any(word in blob for word in ("views.py", "render(", "redirect(", "form_valid", "get_context_data")):
        flow.append("The selected view prepares data, applies business rules, and decides which page or action to return.")
    if any(word in blob for word in ("forms.py", "modelform", "forms.form", "clean_")):
        flow.append("Forms validate user input before the application saves data or continues the workflow.")
    if any(word in blob for word in ("models.py", "objects.", "foreignkey", "queryset", "manager")):
        flow.append("Models handle database structure and queries, so products, carts, users, and orders can be stored and retrieved.")
    if any(word in blob for word in ("templates/", "base.html", "home_page.html", "render(")):
        flow.append("Templates turn the processed data into HTML pages the user can see in the browser.")
    if "checkout" in blob or "payment" in blob or "billing" in blob:
        flow.append("Checkout and billing modules complete the purchase flow by collecting payment-related information and turning carts into orders.")
    if not flow and apps:
        flow.append("Requests move through app-level modules, which validate data, apply business logic, store information, and return a page or response.")
    return flow[:6]


def _app_descriptions(apps: list[str]) -> list[str]:
    descriptions: list[str] = []
    known = {
        "accounts": "user registration, login, email activation, and account-related workflows",
        "addresses": "customer address capture and reuse during checkout",
        "analytics": "tracking, metrics, or behavior analysis",
        "billing": "payment-related records and billing workflows",
        "carts": "shopping cart creation, update, and checkout preparation",
        "marketing": "promotions, contact flows, or marketing pages",
        "orders": "order creation, status, and purchase history",
        "products": "product catalog, listing pages, and product detail data",
        "search": "searching and filtering products or site content",
        "tags": "grouping or labeling content or products",
    }
    for app in apps[:10]:
        detail = known.get(app, f"logic related to the {_clean_name(app)} area")
        descriptions.append(f"- {app}: handles {detail}.")
    return descriptions


def explain_repo(repo_path: str, language: str = "English", detail_level: str = "overview", max_files: int = 12) -> str:
    root = Path(repo_path).expanduser().resolve()
    if not root.exists():
        return f"The provided path '{repo_path}' does not exist."
    if not root.is_dir():
        return f"The provided path '{repo_path}' is not a valid directory."

    files = _collect_repo_files(root)
    if not files:
        return "No supported code files were found in this repository."

    detail = (detail_level or "overview").strip().lower()
    if detail == "file-by-file":
        lines = [
            f"Repository: {root.name}",
            "",
            "File-by-file overview:",
        ]
        for file in files[:max_files]:
            rel = str(file.relative_to(root)).replace("\\", "/")
            ok, content = _read_text(file)
            if not ok:
                lines.append(f"- {rel}: could not be read.")
                continue
            functions = re.findall(r"^(?:async\s+def|def)\s+([A-Za-z_][A-Za-z0-9_]*)", content, flags=re.MULTILINE)
            classes = re.findall(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)", content, flags=re.MULTILINE)
            detail_parts = []
            if functions:
                detail_parts.append(f"functions {', '.join(functions[:4])}")
            if classes:
                detail_parts.append(f"classes {', '.join(classes[:3])}")
            summary = "; ".join(detail_parts) if detail_parts else "general implementation code"
            lines.append(f"- {rel}: contains {summary}.")
        return "\n".join(lines)

    stack = _detect_stack(files, root)
    blob = _sample_blob(files, root)
    domain = _infer_domain(blob)
    apps = _find_django_apps(root)
    important_files = _key_files(root)
    readme_summary = _read_readme(root)
    flow = _flow_summary(apps, blob)
    ext_counts = Counter(file.suffix.lower() for file in files)

    purpose = "This repository looks like a web application."
    if domain == "ecommerce website":
        purpose = (
            "This repository is building an ecommerce website where users can browse products, manage carts, "
            "enter account and address details, and place orders."
        )
    elif domain == "user account or authentication system":
        purpose = "This repository mainly focuses on user accounts, authentication, and account-related workflows."

    lines = [
        f"Repository: {root.name}",
        "",
        "What this project is:",
        purpose,
    ]

    if readme_summary:
        lines.extend([
            "",
            "Simple context from the README:",
            readme_summary,
        ])

    lines.extend([
        "",
        "Technology stack:",
        f"- Main stack: {', '.join(stack)}.",
        f"- Most common file types: {', '.join(f'{suffix or '[no extension]'}:{count}' for suffix, count in ext_counts.most_common(5))}.",
    ])

    if important_files:
        lines.extend([
            "",
            "Important files a beginner should look at first:",
        ])
        lines.extend([f"- {path}" for path in important_files])

    if apps:
        lines.extend([
            "",
            "Main parts of the project:",
        ])
        lines.extend(_app_descriptions(apps))

    if flow:
        lines.extend([
            "",
            "How the application likely works from request to response:",
        ])
        lines.extend([f"- {step}" for step in flow])

    lines.extend([
        "",
        "Beginner-friendly reading order:",
        "- Start with README.md to understand the project goal.",
        "- Then open the main entry file such as manage.py or the central urls.py/settings files.",
        "- Next read one business area at a time, for example products, carts, and orders.",
        "- Inside each app, read urls.py, then views.py, then forms.py, then models.py.",
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "."
    if Path(target).is_dir():
        print(explain_repo(target))
    else:
        print(explain_code(target))

