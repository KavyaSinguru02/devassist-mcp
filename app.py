"""DevAssist Streamlit app with email gate, sidebar tools, and feedback tracking."""

from __future__ import annotations

import json
import smtplib
import sys
from functools import lru_cache
from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st
import dns.resolver
from email_validator import EmailNotValidError, validate_email

# Add src to path so we can import tools directly.
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tools.code_explainer import explain_code, explain_repo
from tools.commit_helper import suggest_commit_message
from tools.error_diagnoser import diagnose_error
from tools.git_analyzer import analyze_git_diff
from tools.test_generator import SUPPORTED_FRAMEWORKS, generate_tests
from tools.todo_finder import find_todos
from utils.repo_cloner import POPULAR_REPOS, clone_temp_repo, get_repo_info, validate_github_url

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


# -------------------------
# JSON storage helpers
# -------------------------
def _json_path(name: str) -> Path:
    return Path(__file__).parent / name


def _load_json(name: str, default: dict) -> dict:
    path = _json_path(name)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(name: str, data: dict) -> None:
    path = _json_path(name)
    try:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com",
    "10minutemail.com",
    "guerrillamail.com",
    "temp-mail.org",
    "yopmail.com",
    "sharklasers.com",
    "dispostable.com",
    "throwawaymail.com",
}

ROLE_LOCALPARTS = {
    "admin",
    "support",
    "help",
    "info",
    "contact",
    "noreply",
    "no-reply",
    "test",
    "testing",
    "demo",
}

# Major providers often block RCPT probing, making mailbox checks indeterminate.
SMTP_INDETERMINATE_OK_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "yahoo.com",
    "icloud.com",
    "me.com",
    "aol.com",
}

SMTP_TIMEOUT_SECONDS = 3


@lru_cache(maxsize=512)
def _mx_records(domain: str) -> list[str]:
    try:
        answers = dns.resolver.resolve(domain, "MX")
    except Exception:
        return []
    records: list[tuple[int, str]] = []
    for r in answers:
        try:
            records.append((int(r.preference), str(r.exchange).rstrip(".")))
        except Exception:
            continue
    records.sort(key=lambda x: x[0])
    return [host for _, host in records]


def _smtp_mailbox_probe(email: str, mx_hosts: list[str]) -> tuple[Optional[bool], str]:
    """Try RCPT TO probe. Returns True/False/None (indeterminate)."""
    for host in mx_hosts[:2]:
        try:
            with smtplib.SMTP(host, 25, timeout=SMTP_TIMEOUT_SECONDS) as smtp:
                smtp.ehlo_or_helo_if_needed()
                smtp.mail("<>")
                code, msg = smtp.rcpt(email)
                text = (msg.decode(errors="ignore") if isinstance(msg, bytes) else str(msg)).strip()
                if code in (250, 251):
                    return True, f"Mailbox accepted by {host}"
                if code in (550, 551, 553):
                    return False, f"Mailbox rejected by {host}: {text}"
                return None, f"Mailbox could not be verified via {host}: {code} {text}"
        except Exception:
            continue
    return None, "Mailbox verification server did not allow probe"


def validate_real_email(raw_email: str) -> tuple[bool, str]:
    """Validate email syntax, domain quality, and mailbox plausibility."""
    try:
        validated = validate_email(raw_email, check_deliverability=True)
        normalized = validated.normalized
        local, _, domain = normalized.partition("@")
        local_l = local.lower()
        domain_l = domain.lower()

        if domain_l in DISPOSABLE_EMAIL_DOMAINS:
            return False, "Disposable email domains are not allowed."

        if local_l in ROLE_LOCALPARTS:
            return False, "Role-based email addresses are not allowed. Use your personal mailbox."

        mx_hosts = _mx_records(domain_l)
        if not mx_hosts:
            return False, "Domain has no reachable MX records."

        # Strict mode: accept only when mailbox probe is explicitly accepted.
        probe_ok, probe_msg = _smtp_mailbox_probe(normalized, mx_hosts)
        if probe_ok is False:
            return False, f"Mailbox could not be validated: {probe_msg}"
        if probe_ok is None:
            if domain_l in SMTP_INDETERMINATE_OK_DOMAINS:
                return True, normalized
            return False, f"Mailbox could not be verified: {probe_msg}"

        return True, normalized
    except EmailNotValidError as exc:
        return False, str(exc)


@st.cache_data(ttl=1800, show_spinner=False)
def _cached_repo_info(url: str) -> dict:
    return get_repo_info(url)


# -------------------------
# Visitor and analytics
# -------------------------
def add_or_update_visitor(email: str, session_id: str) -> tuple[bool, str]:
    data = _load_json(".visitors.json", {"created_on": datetime.now().isoformat(), "visitors": []})
    visitors = data.get("visitors", [])

    now = datetime.now().isoformat()
    for visitor in visitors:
        if visitor.get("email", "").lower() == email.lower():
            visitor["last_seen"] = now
            visitor["visits"] = int(visitor.get("visits", 1)) + 1
            visitor["session_id"] = session_id
            _save_json(".visitors.json", data)
            return False, "existing"

    visitors.append(
        {
            "email": email,
            "session_id": session_id,
            "first_seen": now,
            "last_seen": now,
            "visits": 1,
        }
    )
    data["visitors"] = visitors
    _save_json(".visitors.json", data)
    return True, "new"


def visitor_stats() -> dict:
    data = _load_json(".visitors.json", {"created_on": datetime.now().isoformat(), "visitors": []})
    visitors = data.get("visitors", [])
    total_visits = sum(int(v.get("visits", 1)) for v in visitors)
    created_on = data.get("created_on", datetime.now().isoformat())
    return {
        "created_on": created_on,
        "unique_visitors": len(visitors),
        "total_visits": total_visits,
        "recent": visitors[-10:],
    }


def record_service_use(tool_name: str, email: str, session_id: str) -> None:
    data = _load_json(".analytics.json", {"service_usage": {}, "page_views": []})
    data.setdefault("service_usage", {})
    data["service_usage"][tool_name] = int(data["service_usage"].get(tool_name, 0)) + 1
    data.setdefault("page_views", []).append(
        {
            "tool": tool_name,
            "email": email,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
        }
    )
    _save_json(".analytics.json", data)


def get_usage_stats() -> dict:
    return _load_json(".analytics.json", {"service_usage": {}, "page_views": []})


def save_feedback(tool_name: str, vote: str, email: str, session_id: str) -> None:
    data = _load_json(".feedback.json", {"feedback": []})
    data.setdefault("feedback", []).append(
        {
            "tool": tool_name,
            "vote": vote,
            "email": email,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
        }
    )
    _save_json(".feedback.json", data)


def get_feedback_stats() -> dict:
    data = _load_json(".feedback.json", {"feedback": []})
    counts = {}
    for item in data.get("feedback", []):
        tool = item.get("tool", "Unknown")
        vote = item.get("vote", "down")
        counts.setdefault(tool, {"up": 0, "down": 0})
        if vote == "up":
            counts[tool]["up"] += 1
        else:
            counts[tool]["down"] += 1
    return counts


def render_feedback(tool_name: str) -> None:
    st.write("Was this result useful?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Thumbs Up", key=f"up_{tool_name}"):
            save_feedback(tool_name, "up", st.session_state.user_email, st.session_state.session_id)
            stats = get_feedback_stats().get(tool_name, {"up": 0, "down": 0})
            st.success(f"Saved instantly. Up: {stats['up']} | Down: {stats['down']}")
    with col2:
        if st.button("Thumbs Down", key=f"down_{tool_name}"):
            save_feedback(tool_name, "down", st.session_state.user_email, st.session_state.session_id)
            stats = get_feedback_stats().get(tool_name, {"up": 0, "down": 0})
            st.success(f"Saved instantly. Up: {stats['up']} | Down: {stats['down']}")


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
if "subscribed" not in st.session_state:
    st.session_state.subscribed = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "just_subscribed" not in st.session_state:
    st.session_state.just_subscribed = False


# -------------------------
# Page 1: Email gate
# -------------------------
if not st.session_state.subscribed:
    st.title("Dev Assist")
    st.markdown('<p class="small-subtitle">Join with your email to continue.</p>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Join Our Community")
    with st.form("email_form", clear_on_submit=False):
        email = st.text_input("Email", placeholder="your.email@example.com")
        submit = st.form_submit_button("Subscribe")

    if submit:
        is_valid_email, email_result = validate_real_email(email.strip())
        if not is_valid_email:
            st.error("Enter valid email address.")
            st.caption(email_result)
        else:
            _, state = add_or_update_visitor(email_result, st.session_state.session_id)
            st.session_state.user_email = email_result
            st.session_state.subscribed = True
            st.session_state.just_subscribed = True
            if state == "new":
                st.success("Thank you for joining our community.")
            else:
                st.success("Welcome back. Your email is already registered.")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.stop()


# -------------------------
# Page 2: Main app
# -------------------------
st.sidebar.title("Tools")
st.sidebar.caption(f"Signed in as: {st.session_state.user_email}")

pages = [
    "Home",
    "Explain Code",
    "Generate Tests",
    "Analyze Git Diff",
    "Diagnose Error",
    "Find TODOs",
    "Suggest Commit",
    "Stats",
]

selected = st.sidebar.radio("Navigate", pages, index=0)

st.markdown(
    """
<div class="hero">
    <p class="hero-title">Dev Assist Workspace</p>
    <p class="hero-sub">Practical developer tools for code understanding, test generation, git review, TODO detection, commit quality, and architecture visualization.</p>
</div>
""",
    unsafe_allow_html=True,
)
if selected == "Home":
    st.subheader("Home")
    if st.session_state.just_subscribed:
        st.success("Thank you for subscribing.")
        st.session_state.just_subscribed = False

    stats = visitor_stats()

    left, right = st.columns([1.35, 1])
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Overview")
        st.write("Dev Assist is built to speed up day-to-day coding tasks for developers.")
        st.markdown(
            """
<div class="tool-grid">
    <div class="tool-item"><b>Explain Code</b><br/>Line-by-line explanation in your language.</div>
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
        st.markdown("### Account & Usage")
        st.write(f"Email: {st.session_state.user_email}")
        st.write(f"Unique visitors: {stats['unique_visitors']}")
        st.write(f"Total visits: {stats['total_visits']}")
        st.write("Feedback is collected instantly after each tool result.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### How To Use")
    st.write("1. Pick a tool from the left sidebar.")
    st.write("2. Provide local path or GitHub URL input.")
    st.write("3. Run the tool and review actionable output.")
    st.write("4. Submit thumbs up/down to improve quality.")
    st.markdown("</div>", unsafe_allow_html=True)

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
            record_service_use("Explain Code", st.session_state.user_email, st.session_state.session_id)
            render_feedback("Explain Code")

elif selected == "Generate Tests":
    st.subheader("Generate Tests")
    source_type, source_value = render_source_selector("tests", allow_file_path=True)
    relative_path = ""
    if source_type == "github":
        relative_path = st.text_input("File path inside repository", placeholder="src/module.py")

    framework = st.selectbox("Framework", list(SUPPORTED_FRAMEWORKS.keys()), index=0)
    coverage = st.select_slider("Coverage", ["basic", "thorough", "exhaustive"], value="thorough")

    if st.button("Generate Tests", type="primary"):
        result = ""
        with st.spinner("Generating tests..."):
            if source_type == "local":
                result = generate_tests(source_value, framework, coverage) if source_value else "Please provide a file path."
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
                                result = generate_tests(str(repo_path / relative_path), framework, coverage)
                        except (RuntimeError, ValueError, TimeoutError) as ex:
                            result = str(ex)

        if result.startswith("Please") or result.startswith("Unsupported") or result.startswith("Invalid"):
            st.error(result)
        else:
            st.success("Test prompt generated.")
            st.code(result, language="markdown")
            record_service_use("Generate Tests", st.session_state.user_email, st.session_state.session_id)
            render_feedback("Generate Tests")

elif selected == "Analyze Git Diff":
    st.subheader("Analyze Git Diff")
    repo_path = st.text_input("Repository path", value=".")
    focus = st.radio("Focus", ["general", "security", "performance", "style", "bugs"], horizontal=True)

    if st.button("Analyze Changes", type="primary"):
        with st.spinner("Reviewing changes..."):
            result = analyze_git_diff(repo_path, focus)
        st.code(result, language="markdown")
        record_service_use("Analyze Git Diff", st.session_state.user_email, st.session_state.session_id)
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
            record_service_use("Diagnose Error", st.session_state.user_email, st.session_state.session_id)
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
            record_service_use("Find TODOs", st.session_state.user_email, st.session_state.session_id)
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
        record_service_use("Suggest Commit", st.session_state.user_email, st.session_state.session_id)
        render_feedback("Suggest Commit")

elif selected == "Stats":
    st.subheader("Stats")
    vstats = visitor_stats()
    usage = get_usage_stats()
    feedback = get_feedback_stats()

    file_created = datetime.fromtimestamp(Path(__file__).stat().st_ctime).strftime("%Y-%m-%d")

    c1, c2, c3 = st.columns(3)
    c1.metric("Unique Visitors", vstats["unique_visitors"])
    c2.metric("Total Visits", vstats["total_visits"])
    c3.metric("Page Created On", file_created)

    st.write("Service usage")
    st.json(usage.get("service_usage", {}))

    st.write("Feedback summary")
    st.json(feedback)

    st.write("Recent emails")
    for item in vstats["recent"]:
        st.write(f"- {item.get('email', '')} | first seen: {item.get('first_seen', '')}")

render_branding_bottom()
