# DevAssist MCP

DevAssist is a beginner-friendly coding assistant.

It helps you understand code, generate tests, review git changes, find TODO comments, suggest commit messages, and create architecture diagrams.

You can use it in two ways:
1. As a normal web app (Streamlit).
2. As an MCP server inside Claude Desktop.

## What It Does

1. Explain Code:
By default, it gives a clear overview of a file or repository.
You can optionally choose deeper detail:
- Repository: file-by-file overview
- Specific file: line-by-line explanation

2. Generate Tests:
Creates a clean, practical test-generation prompt for your selected framework.

3. Analyze Git Diff:
Reviews your local git changes by focus area (general, bugs, security, etc.).

4. Find TODOs:
Finds TODO/FIXME/HACK-like comments in your codebase.

5. Suggest Commit Message:
Suggests commit messages based on your staged changes.

6. Architecture Diagram:
Builds a clean Mermaid architecture diagram from a local folder or GitHub repo.
Default is overview mode (module-level, easy to understand).
Optional detailed mode adds important internal folders (src/service/dao/webcontent, etc.).
Output is copy-paste ready for docs, PR comments, and Mermaid Live Editor.

## Important Validation

The app now checks email format and deliverability (DNS check) during signup.
This blocks most dummy or unreachable emails.

## Quick Start (Local)

1. Clone the repository:

```bash
git clone https://github.com/<your-username>/devassist-mcp.git
cd devassist-mcp
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the app:

```bash
streamlit run app.py
```

5. Open in browser:

http://localhost:8501

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to https://share.streamlit.io
3. Click New app.
4. Select your repo and branch.
5. Set main file path to app.py.
6. Click Deploy.

## MCP Server Setup (Claude Desktop)

Add this to your Claude Desktop config file:

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

Replace <absolute-path-to> with your real folder path, then restart Claude Desktop.

## Project Structure

```text
devassist-mcp/
|-- app.py
|-- requirements.txt
|-- src/
|   |-- server.py
|   |-- client.py
|   |-- tools/
|   |   |-- architecture_diagram.py
|   |   |-- code_explainer.py
|   |   |-- commit_helper.py
|   |   |-- git_analyzer.py
|   |   |-- test_generator.py
|   |   |-- todo_finder.py
|   |-- utils/
|       |-- repo_cloner.py
|       |-- usage_store.py
|-- tests/
|-- examples/
```

## Requirements

1. Python 3.10+
2. Dependencies from requirements.txt

## License

MIT

