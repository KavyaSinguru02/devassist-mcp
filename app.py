"""DevAssist production Streamlit app: open access, optional email capture, privacy-safe analytics, and developer tools."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Add src to path so we can import tools directly.
sys.path.insert(0, str(Path(__file__).parent / "src"))
load_dotenv()

from tools.code_explainer import explain_code, explain_repo
from tools.commit_helper import suggest_commit_message
from tools.error_diagnoser import diagnose_error
from tools.git_analyzer import analyze_git_diff
from tools.test_generator import SUPPORTED_FRAMEWORKS, generate_tests
from tools.todo_finder import find_todos
from utils.repo_cloner import POPULAR_REPOS, clone_temp_repo, get_repo_info, validate_github_url
from utils.supabase_visitors import save_visitor_email
from utils.supabase_tracking import (
    get_feedback_summary,
    get_tool_usage_stats,
    get_visitor_stats,
    record_tool_usage,
    save_tool_feedback,
)
from tools.repository_overview import generate_repository_overview
from tools.code_builder import build_code_from_requirement
from utils.repository_cache import get_cached_repo, save_repo_cache
from tools.repository_chat import chat_with_repository


SAMPLE_REPOSITORIES = {
    "DevAssist": "https://github.com/KavyaSinguru02/devassist-mcp",
    "Spring PetClinic": "https://github.com/spring-projects/spring-petclinic",
    "FastAPI": "https://github.com/fastapi/fastapi",
    "React": "https://github.com/facebook/react",
} 

st.set_page_config(
    page_title="DevAssist",
    page_icon="DA",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp {
        background: radial-gradient(circle at top right, #e8f3ff 0%, #f6f7fb 45%, #f4f6f8 100%);
        color: #111111;
    }
    h1, h2, h3 {
        color: #111111 !important;
    }
    .small-subtitle {
        color: #3f3f46;
        margin-top: -0.2rem;
        font-size: 0.98rem;
    }
    .hero {
        border: 1px solid #d7dce3;
        background: linear-gradient(120deg, #ffffff 0%, #eef3ff 100%);
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
        margin-bottom: 1rem;
    }
    .hero-title {
        font-size: 1.95rem;
        font-weight: 800;
        letter-spacing: 0.2px;
        color: #0f172a;
        margin: 0;
    }
    .hero-sub {
        font-size: 0.96rem;
        color: #334155;
        margin: 0.2rem 0 0 0;
    }
    .card {
        background: #ffffff;
        border: 1px solid #dddddd;
        border-radius: 12px;
        padding: 1rem;
    }
    .tool-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.7rem;
        margin-top: 0.3rem;
    }
    .tool-item {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.65rem 0.75rem;
    }
    .simple-footer {
        margin-top: 2rem;
        padding: 1rem;
        text-align: center;
        border-top: 1px solid #d0d0d0;
        color: #222222;
        background: #ffffff;
        border-radius: 12px;
    }
    .social-row {
        display: flex;
        justify-content: center;
        gap: 16px;
        margin-top: 0.6rem;
        flex-wrap: wrap;
    }
    .social-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border: 1px solid #d1d5db;
        border-radius: 999px;
        padding: 0.5rem 0.8rem;
        text-decoration: none;
        color: #0f172a;
        background: #ffffff;
        font-weight: 600;
    }
    .social-pill img {
        width: 20px;
        height: 20px;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=1800, show_spinner=False)
def _cached_repo_info(url: str) -> dict:
    return get_repo_info(url)



# -------------------------
# Visitor and analytics
# -------------------------
def visitor_stats() -> dict:
    return get_visitor_stats()


def render_feedback(tool_name: str) -> None:
    st.write("Was this result useful?")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Thumbs Up", key=f"up_{tool_name}"):
            save_tool_feedback(tool_name, "up")
            stats = get_feedback_summary().get(tool_name, {"up": 0, "down": 0})
            st.success(f"Saved. Up: {stats['up']} | Down: {stats['down']}")

    with col2:
        if st.button("Thumbs Down", key=f"down_{tool_name}"):
            save_tool_feedback(tool_name, "down")
            stats = get_feedback_summary().get(tool_name, {"up": 0, "down": 0})
            st.success(f"Saved. Up: {stats['up']} | Down: {stats['down']}")

# -------------------------
# Shared UI helpers
# -------------------------
def render_source_selector(tool_key: str, allow_file_path: bool = True):
    options = ["Local Path", "GitHub Repository"]
    if not allow_file_path:
        options[0] = "Local Directory"

    source = st.radio("Source", options, horizontal=True, key=f"source_{tool_key}")

    if source in {"Local Path", "Local Directory"}:
        value = st.text_input(
            "Path",
            placeholder="src/tools/code_explainer.py" if allow_file_path else ".",
            key=f"path_{tool_key}",
        )
        return "local", value

    st.caption("Popular repositories")
    cols = st.columns(len(POPULAR_REPOS))
    for i, (name, url) in enumerate(POPULAR_REPOS.items()):
        with cols[i]:
            if st.button(name, key=f"popular_{tool_key}_{i}", use_container_width=True):
                st.session_state[f"github_{tool_key}"] = url
                st.rerun()

    value = st.text_input(
        "GitHub URL",
        value=st.session_state.get(f"github_{tool_key}", ""),
        placeholder="https://github.com/psf/requests",
        key=f"github_url_{tool_key}",
    )

    if value:
        info = _cached_repo_info(value)
        if info.get("valid"):
            st.info(f"Repository: {info['display_name']}")

    return "github", value


def render_branding_bottom() -> None:
    st.markdown(
        """
<div class="simple-footer">
    <h3 style="margin:0; color:#111111;">Dev Assist</h3>
    <p class="small-subtitle" style="margin-top:0.25rem;">Developer-focused tools for explanation, testing, review, and debugging.</p>
    <div class="social-row">
        <a class="social-pill" href="https://github.com/KavyaSinguru02/devassist-mcp" target="_blank">
            <img src="https://cdn.simpleicons.org/github/111111" alt="GitHub" />
            GitHub
        </a>
        <a class="social-pill" href="https://www.linkedin.com/in/kavya-singuru" target="_blank">
            <img src="https://cdn.simpleicons.org/linkedin/0A66C2" alt="LinkedIn" />
            LinkedIn
        </a>
    </div>
    <p class="small-subtitle" style="margin-top:0.7rem;">Use any tool from the sidebar and share instant feedback after each result.</p>
</div>
""",
        unsafe_allow_html=True,
    )


# -------------------------
# Session init
# -------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(datetime.now().timestamp())
if "user_email" not in st.session_state:
    st.session_state.user_email = "anonymous"
if "email_captured" not in st.session_state:
    st.session_state.email_captured = False
if "just_captured_email" not in st.session_state:
    st.session_state.just_captured_email = False


def render_optional_email_capture(location: str = "home") -> None:
    """Collect email without blocking access to tools.

    This is intentionally optional for production UX. Users can use DevAssist
    without creating an account or waiting for OTP/magic links.
    """
    if st.session_state.email_captured:
        st.success("Thanks for joining the DevAssist community.")
        return

    with st.form(f"optional_email_capture_{location}", clear_on_submit=False):
        email = st.text_input(
            "Optional email",
            placeholder="your.email@example.com",
            help="Optional. We only use this to understand interest and improve DevAssist. Tools work without it.",
        )
        submitted = st.form_submit_button("Join community")

    if submitted:
        if not email.strip():
            st.info("Email is optional. You can continue using DevAssist without joining.")
            return
        try:
            result = save_visitor_email(email, st.session_state.session_id)
            if result.success:
                st.session_state.user_email = result.email or "anonymous"
                st.session_state.email_captured = True
                st.session_state.just_captured_email = True
                st.success("Thanks! You can continue using DevAssist.")
                st.rerun()
            else:
                st.error("Please enter a valid email address.")
                st.caption(result.message)
        except Exception as exc:
            st.warning("DevAssist is still available. We could not save the email right now.")
            st.caption(str(exc))

# -------------------------
# Page 2: Main app
# -------------------------
st.sidebar.title("Tools")
st.sidebar.caption("Open access • No subscription required")

pages = [
    "Home",
    "Repository Overview",
    "Explain Code",
    "Build Code",
    "Generate Tests",
    "Analyze Git Diff",
    "Diagnose Error",
    "Find TODOs",
    "Suggest Commit",
    "Repository Chat",
    "Stats",
]

selected = st.sidebar.radio("Navigate", pages, index=0)

st.markdown(
    """
<div class="hero">
    <p class="hero-title">Dev Assist Workspace</p>
    <p class="hero-sub">Open developer tools for repository understanding, code explanation, testing, debugging, git review, and architecture visualization.</p>
</div>
""",
    unsafe_allow_html=True,
)
if selected == "Home":
    st.subheader("Home")
    if st.session_state.just_captured_email:
        st.success("Thanks for joining the DevAssist community.")
        st.session_state.just_captured_email = False

    stats = visitor_stats()

    left, right = st.columns([1.35, 1])
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Overview")
        st.write("Dev Assist is built to speed up day-to-day coding tasks for developers.")
        st.markdown(
            """
<div class="tool-grid">
    <div class="tool-item"><b>Repository Overview</b><br/>Beginner-friendly project purpose, stack, architecture, and learning path.</div>
    <div class="tool-item"><b>Explain Code</b><br/>Line-by-line explanation in your language.</div>
    <div class="tool-item"><b>Build Code</b><br/>Turn requirements into implementation-ready code.</div>
    <div class="tool-item"><b>Generate Tests</b><br/>Framework-specific test prompt with coverage options.</div>
    <div class="tool-item"><b>Analyze Git Diff</b><br/>Review uncommitted changes by focus area.</div>
    <div class="tool-item"><b>Diagnose Error</b><br/>Paste traceback and get root cause + where to check.</div>
    <div class="tool-item"><b>Find TODOs</b><br/>Scan technical debt markers across repo files.</div>
    <div class="tool-item"><b>Suggest Commit</b><br/>Generate clean conventional commit messages.</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.info("Tip: Start from Explain Code or Analyze Git Diff for immediate productivity.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Usage")
        st.write("DevAssist is open access. No subscription is required.")
        st.write(f"Community members: {stats['unique_visitors']}")
        st.write(f"Total tool sessions: {stats['total_visits']}")
        st.write("Feedback is collected without showing personal emails in the UI.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Join Community (Optional)")
        render_optional_email_capture("home")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### How To Use")
    st.write("1. Pick a tool from the left sidebar.")
    st.write("2. Provide local path or GitHub URL input.")
    st.write("3. Run the tool and review actionable output.")
    st.write("4. Submit thumbs up/down to improve quality.")
    st.markdown("</div>", unsafe_allow_html=True)

elif selected == "Repository Overview":
    st.subheader("Repository Overview")
    st.caption("Beginner-friendly repository tour with purpose, stack, architecture, important files, and learning path.")

    source_type, source_value = render_source_selector("repo_overview", allow_file_path=False)
    if st.session_state.get("github_repo_overview"):
        source_value = st.session_state["github_repo_overview"]

    audience = st.selectbox(
        "Explain for",
        ["Beginner", "Non-technical", "Developer", "Architect", "Interview Preparation"],
        index=0,
    )
    language = st.text_input(
        "Output language",
        value="English",
        placeholder="Example: English, Telugu, Hindi, Polish, German, Spanish",
        help="DevAssist will use this language for repository guidance when supported. Technical terms are kept readable.",
    )
    include_diagram = st.checkbox("Include Mermaid architecture diagram", value=True)

    if st.button("Teach Me This Repository", type="primary"):
        result = ""
        with st.spinner("Building beginner-friendly repository overview..."):
            if source_type == "local":
                if not source_value:
                    st.error("Please provide a local repository path.")
                else:
                    result = generate_repository_overview(
                        source_value,
                        audience=audience,
                        language=language,
                        include_diagram=include_diagram,
                    )
            else:
                if not source_value:
                    st.error("Please enter a GitHub URL.")
                else:
                    valid, err = validate_github_url(source_value)
                    if not valid:
                        st.error(err)
                    else:
                        try:
                            cached = get_cached_repo(
                                source_value,
                                audience=audience,
                                language=language,
                                include_diagram=include_diagram,
                            )
                            if cached.found and cached.overview:
                                st.success("Loaded from cache.")
                                result = cached.overview
                            else:
                                with clone_temp_repo(source_value) as repo_path:
                                    result = generate_repository_overview(
                                        str(repo_path),
                                        audience=audience,
                                        language=language,
                                        include_diagram=include_diagram,
                                    )
                                    save_repo_cache(
                                        repo_url=source_value,
                                        repo_name=repo_path.name,
                                        overview=result,
                                        frameworks=[],
                                        architecture="Detected",
                                        last_commit=None,
                                        audience=audience,
                                        language=language,
                                        include_diagram=include_diagram,
                                    )
                        except (RuntimeError, ValueError, TimeoutError) as ex:
                            st.error(str(ex))

        if result:
            st.success("Repository guide ready.")
            st.markdown(result)
            record_tool_usage("Repository Overview")
            render_feedback("Repository Overview")

elif selected == "Explain Code":
    st.subheader("Explain Code")
    scope = st.radio("Analyze", ["Entire Repository", "Specific File"], horizontal=True)
    detail_level = "overview"

    if scope == "Entire Repository":
        detail_choice = st.selectbox(
            "Explanation depth",
            ["Overview (recommended)", "File-by-file overview"],
            index=0,
        )
        detail_level = "file-by-file" if detail_choice.startswith("File-by-file") else "overview"
    else:
        detail_choice = st.selectbox(
            "Explanation depth",
            ["Overview (recommended)", "Line-by-line (specific file)"],
            index=0,
        )
        detail_level = "line-by-line" if detail_choice.startswith("Line-by-line") else "overview"

    source_type, source_value = render_source_selector("explain", allow_file_path=(scope == "Specific File"))

    relative_path = ""
    if source_type == "github" and scope == "Specific File":
        relative_path = st.text_input("File path inside repository", placeholder="src/main.py")

    language = st.selectbox(
        "Explanation language",
        ["English", "Telugu", "Hindi", "Tamil", "Spanish", "French", "German"],
        index=0,
    )

    if st.button("Analyze and Explain", type="primary"):
        result = ""
        if source_type == "local":
            if not source_value:
                st.error("Please provide a valid path.")
            else:
                with st.spinner("Analyzing..."):
                    if scope == "Entire Repository":
                        result = explain_repo(source_value, language, detail_level=detail_level)
                    else:
                        result = explain_code(source_value, language, detail_level=detail_level)
        else:
            if not source_value:
                st.error("Please enter a GitHub URL.")
            elif scope == "Specific File" and not relative_path:
                st.error("Please provide file path inside repository.")
            else:
                valid, err = validate_github_url(source_value)
                if not valid:
                    st.error(err)
                else:
                    with st.spinner("Cloning repository..."):
                        try:
                            with clone_temp_repo(source_value) as repo_path:
                                if scope == "Entire Repository":
                                    result = explain_repo(str(repo_path), language, detail_level=detail_level)
                                else:
                                    result = explain_code(str(repo_path / relative_path), language, detail_level=detail_level)
                        except (RuntimeError, ValueError, TimeoutError) as ex:
                            st.error(str(ex))

        if result:
            st.success("Explanation generated.")
            st.code(result, language="markdown")
            record_tool_usage("Explain Code")
            render_feedback("Explain Code")


elif selected == "Build Code":
    st.subheader("Build Code")
    st.caption("Describe what you want to build. DevAssist will generate implementation-ready code and placement guidance for any language/framework.")

    requirement = st.text_area(
        "Requirement",
        height=180,
        placeholder="Example: Add login API with JWT, validation, service layer, tests, and Swagger docs.",
    )

    col1, col2 = st.columns(2)
    with col1:
        language = st.text_input(
            "Language",
            value="Any",
            placeholder="Example: Python, Java, Go, Rust, C#, Kotlin, PHP, Ruby, Dart",
        )
        framework = st.text_input(
            "Framework / Style",
            value="Any",
            placeholder="Example: Spring Boot, FastAPI, React, Django, Laravel, .NET, Flutter",
        )
    with col2:
        audience = st.selectbox(
            "Output style",
            ["Developer", "Beginner", "Senior Engineer", "Architect"],
            index=0,
        )
        repo_path = st.text_input("Repository path for context (optional)", value="")

    target_file = st.text_input(
        "Target file to update (optional)",
        placeholder="Example: src/services/user_service.py or app/controllers/UserController.java",
    )

    if st.button("Generate Code", type="primary"):
        with st.spinner("Generating implementation-ready code..."):
            result = build_code_from_requirement(
                requirement=requirement,
                language=language,
                framework=framework,
                target_file=target_file,
                repo_path=repo_path,
                audience=audience,
            )
        st.success("Code draft ready.")
        st.markdown(result)
        record_tool_usage("Build Code")
        render_feedback("Build Code")

elif selected == "Generate Tests":
    st.subheader("Generate Tests")
    st.caption("Generate tests for any language or framework. Use a known framework or type your own.")

    source_type, source_value = render_source_selector("tests", allow_file_path=True)
    relative_path = ""
    if source_type == "github":
        relative_path = st.text_input("File path inside repository", placeholder="src/module.py")

    framework = st.text_input(
        "Testing framework",
        value="pytest",
        placeholder="Example: pytest, JUnit, Jest, Vitest, Go test, RSpec, PHPUnit, xUnit, Flutter test",
    )
    coverage = st.select_slider("Coverage", ["basic", "thorough", "exhaustive"], value="thorough")
    explanation_language = st.text_input(
        "Comment/explanation language",
        value="English",
        placeholder="Example: English, Telugu, Hindi, Polish",
    )

    if st.button("Generate Tests", type="primary"):
        result = ""
        with st.spinner("Generating tests..."):
            if source_type == "local":
                result = (
                    generate_tests(source_value, framework, coverage, explanation_language)
                    if source_value
                    else "Please provide a file path."
                )
            else:
                if not source_value or not relative_path:
                    result = "Please provide both GitHub URL and file path."
                else:
                    valid, err = validate_github_url(source_value)
                    if not valid:
                        result = err
                    else:
                        try:
                            with clone_temp_repo(source_value) as repo_path:
                                result = generate_tests(
                                    str(repo_path / relative_path),
                                    framework,
                                    coverage,
                                    explanation_language,
                                )
                        except (RuntimeError, ValueError, TimeoutError) as ex:
                            result = str(ex)

        if result.startswith("Please") or result.startswith("Invalid"):
            st.error(result)
        else:
            st.success("Test prompt generated.")
            st.code(result, language="markdown")
            record_tool_usage("Generate Tests")
            render_feedback("Generate Tests")

elif selected == "Analyze Git Diff":
    st.subheader("Analyze Git Diff")
    repo_path = st.text_input("Repository path", value=".")
    focus = st.radio("Focus", ["general", "security", "performance", "style", "bugs"], horizontal=True)

    if st.button("Analyze Changes", type="primary"):
        with st.spinner("Reviewing changes..."):
            result = analyze_git_diff(repo_path, focus)
        st.code(result, language="markdown")
        record_tool_usage("Analyze Git Diff")
        render_feedback("Analyze Git Diff")

elif selected == "Diagnose Error":
    st.subheader("Diagnose Error")
    st.caption("Paste traceback/log text. This tool points to likely root cause and exact files/lines to inspect.")

    error_text = st.text_area(
        "Error / Traceback",
        height=260,
        placeholder="Paste full traceback here...",
    )
    repo_path = st.text_input("Repository path (optional)", value=".")

    if st.button("Diagnose", type="primary"):
        if not error_text.strip():
            st.error("Please paste traceback or log text.")
        else:
            with st.spinner("Diagnosing error..."):
                result = diagnose_error(error_text=error_text, repo_path=repo_path or ".")
            st.success("Diagnosis ready.")
            st.code(result, language="markdown")
            record_tool_usage("Diagnose Error")
            render_feedback("Diagnose Error")

elif selected == "Find TODOs":
    st.subheader("Find TODOs")
    source_type, source_value = render_source_selector("todos", allow_file_path=False)
    patterns = st.multiselect(
        "Patterns",
        ["TODO", "FIXME", "HACK", "XXX", "BUG", "NOTE", "REVIEW", "OPTIMIZE", "DEPRECATED"],
        default=["TODO", "FIXME", "HACK", "XXX", "BUG"],
    )

    if st.button("Scan TODOs", type="primary"):
        if not patterns:
            st.error("Select at least one pattern.")
        else:
            result = ""
            with st.spinner("Scanning repository..."):
                if source_type == "local":
                    result = find_todos(source_value or ".", patterns)
                else:
                    valid, err = validate_github_url(source_value)
                    if not valid:
                        result = err
                    else:
                        try:
                            with clone_temp_repo(source_value) as repo_path:
                                result = find_todos(str(repo_path), patterns)
                        except (RuntimeError, ValueError, TimeoutError) as ex:
                            result = str(ex)
            st.code(result, language="markdown")
            record_tool_usage("Find TODOs")
            render_feedback("Find TODOs")

elif selected == "Suggest Commit":
    st.subheader("Suggest Commit")
    repo_path = st.text_input("Repository path", value=".")
    style = st.selectbox("Style", ["conventional", "simple", "detailed"], index=0)
    include_body = st.checkbox("Include body", value=True)

    if st.button("Suggest Commit Message", type="primary"):
        with st.spinner("Preparing commit suggestions..."):
            result = suggest_commit_message(repo_path, style, include_body)
        st.code(result, language="markdown")
        record_tool_usage("Suggest Commit")
        render_feedback("Suggest Commit")
elif selected == "Repository Chat":
    st.subheader("Repository Chat")
    st.caption("Ask questions about a repository, such as where authentication happens or what file starts the app.")

    source_type, source_value = render_source_selector("repo_chat", allow_file_path=False)

    question = st.text_area(
        "Question",
        height=120,
        placeholder="Example: Which file starts the application? Where is authentication implemented?",
    )

    audience = st.selectbox(
        "Explain for",
        ["Beginner", "Developer", "Architect", "Interview Preparation"],
        index=0,
        key="repo_chat_audience",
    )

    language = st.selectbox(
        "Language",
        ["English", "Telugu", "Hindi", "Tamil", "Spanish", "French", "German", "Polish"],
        index=0,
        key="repo_chat_language",
    )

    if st.button("Ask Repository", type="primary"):
        result = ""

        if source_type == "local":
            if not source_value:
                st.error("Please provide a local repository path.")
            else:
                with st.spinner("Reading repository and searching relevant files..."):
                    result = chat_with_repository(
                        source_value,
                        question,
                        audience=audience,
                        language=language,
                    )

        else:
            if not source_value:
                st.error("Please enter a GitHub URL.")
            else:
                valid, err = validate_github_url(source_value)

                if not valid:
                    st.error(err)
                else:
                    try:
                        with st.spinner("Cloning repository and searching relevant files..."):
                            with clone_temp_repo(source_value) as repo_path:
                                result = chat_with_repository(
                                    str(repo_path),
                                    question,
                                    audience=audience,
                                    language=language,
                                )
                    except (RuntimeError, ValueError, TimeoutError) as ex:
                        st.error(str(ex))

        if result:
            st.success("Repository answer ready.")
            st.markdown(result)
            record_tool_usage("Repository Chat")
            render_feedback("Repository Chat")

elif selected == "Stats":
    st.subheader("Stats")
    st.caption("Privacy-safe metrics only. Individual emails and sessions are not displayed.")
    vstats = visitor_stats()
    usage = get_tool_usage_stats()
    feedback = get_feedback_summary()

    file_created = datetime.fromtimestamp(Path(__file__).stat().st_ctime).strftime("%Y-%m-%d")

    c1, c2, c3 = st.columns(3)
    c1.metric("Unique Visitors", vstats["unique_visitors"])
    c2.metric("Total Visits", vstats["total_visits"])
    c3.metric("Page Created On", file_created)

    st.write("Service usage")
    st.json(usage)

    st.write("Feedback summary")
    st.json(feedback)

    st.info("Privacy note: individual email addresses are never displayed in the Stats page.")

render_branding_bottom()
