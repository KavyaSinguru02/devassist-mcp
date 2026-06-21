# DevAssist MCP

DevAssist is a beginner-friendly developer assistant.

It helps you:
- Understand unfamiliar code quickly
- Generate test prompts in multiple frameworks
- Review git changes before commit
- Find TODO/FIXME technical debt markers
- Suggest commit messages
- Diagnose errors from traceback/log text

You can run it in two ways:
1. As a Streamlit web app (easy UI)
2. As an MCP server for Claude Desktop (tool-calling workflow)

## Who This Is For

- Beginners who need plain-English code explanations
- Developers who want faster day-to-day code review and debugging
- Teams that want copy-paste-ready outputs for docs and PR comments

## Main Features

### 1) Explain Code
- Default behavior is overview-first (file or repository level)
- Optional deeper modes:
  - Repository: file-by-file overview
  - Specific file: line-by-line explanation

### 2) Generate Tests
- Builds a concise, practical test-generation prompt
- Supports frameworks like pytest, unittest, jest, mocha, junit, rspec, and more

### 3) Analyze Git Diff
- Reviews uncommitted changes with focus modes (general, security, performance, style, bugs)

### 4) Diagnose Error
- Paste traceback/log text
- Gets likely root cause, where to check first, and quick verification steps

### 5) Find TODOs
- Scans repository for TODO/FIXME/HACK/BUG style markers

### 6) Suggest Commit Message
- Suggests commit messages from current changes

## Email Validation Behavior

Signup uses email syntax + deliverability checks to reduce dummy inputs.

Note:
- DNS/deliverability checks improve quality but cannot guarantee a mailbox is owned by a real person.
- If you want strict enterprise-level verification, integrate an external email verification provider API.

## Quick Start (Local)

1. Clone repository

```bash
git clone https://github.com/<your-username>/devassist-mcp.git
cd devassist-mcp
```

2. Create and activate virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Run Streamlit app

```bash
streamlit run app.py
```

5. Open browser

```text
http://localhost:8501
```

## Claude Desktop MCP Setup

Add this to Claude Desktop config:

```json
{
  "mcpServers": {
    "devassist": {
      "command": "python",
      "args": ["<absolute-path-to>/devassist-mcp/src/server.py"]
    }
  }
}
```

Replace `<absolute-path-to>` with your machine path, then restart Claude Desktop.

## Deployment (Streamlit Community Cloud)

1. Push this repo to GitHub
2. Open https://share.streamlit.io
3. Click New app
4. Select repository and branch
5. Set main file to `app.py`
6. Deploy

## Project Structure

```text
devassist-mcp/
|- app.py
|- requirements.txt
|- README.md
|- src/
|  |- __init__.py
|  |- server.py
|  |- client.py
|  |- tools/
|  |  |- __init__.py
|  |  |- code_explainer.py
|  |  |- commit_helper.py
|  |  |- error_diagnoser.py
|  |  |- git_analyzer.py
|  |  |- test_generator.py
|  |  |- todo_finder.py
|  |- utils/
|     |- __init__.py
|     |- repo_cloner.py
|     |- usage_store.py
|- examples/
|- tests/
```

## File-by-File Usage Guide

### Root Files

- `app.py`
  - Main Streamlit UI entry point
  - Handles email gate, navigation, tool execution, and feedback capture

- `requirements.txt`
  - Pinned dependencies for reproducible installs

- `README.md`
  - User and contributor documentation

- `LICENSE`
  - Project license terms

### src Core

- `src/server.py`
  - MCP server
  - Registers available tools and dispatches tool calls

- `src/client.py`
  - Optional CLI client prototype for interacting with MCP server

- `src/__init__.py`
  - Package marker for Python imports

### src/tools Modules

- `src/tools/code_explainer.py`
  - File and repository explanation engine
  - Supports overview and deeper detail levels

- `src/tools/test_generator.py`
  - Builds concise test-generation prompts
  - Supports multiple test frameworks and coverage levels

- `src/tools/git_analyzer.py`
  - Parses and summarizes git diff changes with review focus

- `src/tools/todo_finder.py`
  - Finds TODO/FIXME/HACK/BUG markers in source tree

- `src/tools/commit_helper.py`
  - Suggests commit messages from current repository changes

- `src/tools/error_diagnoser.py`
  - Analyzes traceback/log text
  - Returns likely root cause, important frames, and debugging steps

- `src/tools/__init__.py`
  - Tools package marker

### src/utils Modules

- `src/utils/repo_cloner.py`
  - Validates GitHub URLs
  - Clones repositories safely into temporary folders for analysis

- `src/utils/usage_store.py`
  - Utility storage helpers for usage/subscriber/feedback stats
  - Kept for persistence workflows and data helper reuse

- `src/utils/__init__.py`
  - Utils package marker

### Other Folders

- `examples/`
  - Sample usage inputs or example workflows

- `tests/`
  - Automated tests (unit/integration)

## Troubleshooting

### Error: Module not found

Use the same Python environment for install and run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

If using venv on Windows:

```bash
.\venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### App runs but imports fail in VS Code

- Select the correct interpreter in VS Code
- Ensure it points to the same environment used for runtime

## Requirements

- Python 3.10 or newer
- Dependencies from `requirements.txt`

## License

MIT

