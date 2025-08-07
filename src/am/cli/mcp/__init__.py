from .__main__ import mcp_app
from .development import register_mcp_development
from .install import register_mcp_install

_ = register_mcp_development(mcp_app)
_ = register_mcp_install(mcp_app)

__all__ = ["mcp_app"]


