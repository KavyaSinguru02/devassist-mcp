"""
DevAssist MCP Server

Wires tools to the MCP protocol so they can be used by:
- Claude Desktop (Anthropic's official client)
- Custom CLI client (your own client.py)
- Any other MCP-compatible app

Transport: stdio (clients spawn this as subprocess)
Protocol: JSON-RPC 2.0 over stdin/stdout
"""
# type: ignore
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path so imports work when spawned by clients
sys.path.insert(0, str(Path(__file__).parent))

from typing import Any, Dict, List

from mcp.server import Server  # type: ignore[import]
from mcp.server.stdio import stdio_server  # type: ignore[import]
from mcp.types import Tool, TextContent  # type: ignore[import]

# Import our tool functions
from tools.code_explainer import explain_code
from tools.architecture_diagram import (
    generate_architecture_diagram,
    generate_architecture_from_github_url,
)
from tools.test_generator import generate_tests
from tools.git_analyzer import analyze_git_diff
from tools.todo_finder import find_todos
from tools.commit_helper import suggest_commit_message

# CRITICAL: Logging MUST go to stderr, NEVER stdout!
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s - %(levelname)s %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("devassist-mcp")


# Initialize MCP server
app: Any = Server("devassist")  # type: ignore[assignment]


@app.list_tools()
async def list_tools() -> List[Any]:
    """Register all DevAssist tools with the MCP client."""
    return [
        Tool(
            name="explain_code",
            description=(
                "Explain a code file with overview by default, or line-by-line "
                "when requested. Supports many human languages."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute or relative path to the code file",
                    },
                    "language": {
                        "type": "string",
                        "description": "Human language (e.g., 'English')",
                        "default": "English",
                    },
                    "detail_level": {
                        "type": "string",
                        "description": "Explanation depth",
                        "default": "overview",
                        "enum": ["overview", "line-by-line"],
                    },
                },
                "required": ["file_path"],
            },
        ),

        Tool(
            name="generate_tests",
            description=(
                "Generate comprehensive unit tests. Supports multiple frameworks."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the source file",
                    },
                    "framework": {
                        "type": "string",
                        "description": "Testing framework",
                        "default": "pytest",
                        "enum": [
                            "pytest",
                            "unittest",
                            "jest",
                            "mocha",
                            "junit",
                            "rspec",
                            "gotest",
                        ],
                    },
                    "coverage_level": {
                        "type": "string",
                        "description": "How thorough: basic/thorough/exhaustive",
                        "default": "thorough",
                        "enum": ["basic", "thorough", "exhaustive"],
                    },
                },
                "required": ["file_path"],
            },
        ),

        Tool(
            name="analyze_git_diff",
            description=(
                "Review uncommitted git changes (staged + unstaged) for "
                "pre-commit code review. Focus modes: general, security, performance, style, bugs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "Path to the git repository",
                        "default": ".",
                    },
                    "review_focus": {
                        "type": "string",
                        "description": "What to focus the review on",
                        "default": "general",
                        "enum": ["general", "security", "performance", "style", "bugs"],
                    },
                },
            },
        ),

        Tool(
            name="find_todos",
            description=(
                "Scan a directory for TODO, FIXME, HACK, XXX, and BUG comments."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory to scan",
                        "default": ".",
                    },
                    "patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Custom patterns to search",
                    },
                },
            },
        ),

        Tool(
            name="suggest_commit_message",
            description=(
                "Generate a Conventional Commits message from staged changes. Returns options to choose from."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "Path to the git repository",
                        "default": ".",
                    },
                    "style": {
                        "type": "string",
                        "description": "Message style",
                        "default": "conventional",
                        "enum": ["conventional", "simple", "detailed"],
                    },
                    "include_body": {
                        "type": "boolean",
                        "description": "Include 'why' body section",
                        "default": True,
                    },
                },
            },
        ),

        Tool(
            name="architecture_diagram",
            description=(
                "Generate a Mermaid architecture diagram from a local repository path "
                "or from a public GitHub repository URL."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "Local repository path",
                        "default": ".",
                    },
                    "github_url": {
                        "type": "string",
                        "description": "Public GitHub repository URL",
                    },
                    "max_dirs": {
                        "type": "integer",
                        "description": "Maximum top-level entries to include",
                        "default": 20,
                    },
                    "mode": {
                        "type": "string",
                        "description": "Diagram depth",
                        "default": "overview",
                        "enum": ["overview", "detailed"],
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[Any]:
    """Dispatch tool calls to the correct function."""
    logger.info(f"Tool called: {name} with args: {arguments}")

    try:
        if name == "explain_code":
            result = explain_code(
                file_path=arguments["file_path"],
                language=arguments.get("language", "English"),
                detail_level=arguments.get("detail_level", "overview"),
            )
        elif name == "generate_tests":
            result = generate_tests(
                file_path=arguments["file_path"],
                framework=arguments.get("framework", "pytest"),
                coverage_level=arguments.get("coverage_level", "thorough"),
            )
        elif name == "analyze_git_diff":
            result = analyze_git_diff(
                repo_path=arguments.get("repo_path", "."),
                review_focus=arguments.get("review_focus", "general"),
            )
        elif name == "find_todos":
            result = find_todos(
                directory=arguments.get("directory", "."),
                patterns=arguments.get("patterns"),
            )
        elif name == "suggest_commit_message":
            result = suggest_commit_message(
                repo_path=arguments.get("repo_path", "."),
                style=arguments.get("style", "conventional"),
                include_body=arguments.get("include_body", True),
            )
        elif name == "architecture_diagram":
            github_url = arguments.get("github_url")
            max_dirs = int(arguments.get("max_dirs", 20))
            mode = arguments.get("mode", "overview")
            if github_url:
                result = generate_architecture_from_github_url(
                    github_url=github_url,
                    max_dirs=max_dirs,
                    mode=mode,
                )
            else:
                result = generate_architecture_diagram(
                    repo_path=arguments.get("repo_path", "."),
                    max_dirs=max_dirs,
                    mode=mode,
                )
        else:
            result = f"Unknown tool: {name}"
            logger.warning(f"Unknown tool requested: {name}")

    except KeyError as e:
        result = f"Missing required argument: {e}"
        logger.error(f"Missing argument for {name}: {e}")

    except Exception as e:
        result = f"Error executing {name}: {str(e)}"
        logger.exception(f"Tool {name} failed unexpectedly")

    return [TextContent(type="text", text=result)]


async def main():
    """Run the MCP server using stdio transport."""
    logger.info("DevAssist MCP Server starting...")
    logger.info("Transport: stdio")
    logger.info("Tools registered: 6")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(  # type: ignore[attr-defined]
            read_stream,
            write_stream,
            app.create_initialization_options(),  # type: ignore[attr-defined]
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Server crashed: {e}")
        sys.exit(1)
