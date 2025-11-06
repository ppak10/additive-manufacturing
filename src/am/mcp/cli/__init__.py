from .__main__ import app
from .development import register_mcp_development
from .install import register_mcp_install

_ = register_mcp_development(app)
_ = register_mcp_install(app)

__all__ = ["app"]
