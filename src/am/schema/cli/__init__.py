from .__main__ import app

from .build_parameters import register_schema_build_parameters

_ = register_schema_build_parameters(app)

__all__ = ["app"]
