from __future__ import annotations

# DevAssist MCP server placeholder/compatibility module.
# Keep your existing MCP server if you already customized it.
# Streamlit production deployment uses app.py directly.

from tools.code_explainer import explain_code, explain_repo
from tools.error_diagnoser import diagnose_error
from tools.repository_overview import generate_repository_overview
from tools.code_builder import build_code_from_requirement

__all__ = ["explain_code", "explain_repo", "diagnose_error", "generate_repository_overview", "build_code_from_requirement"]
