from .__main__ import mcp_app
from .development import register_mcp_development

_ = register_mcp_development(mcp_app)

__all__ = ["mcp_app"]


