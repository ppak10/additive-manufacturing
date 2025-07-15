from .__main__ import segmenter_app
from .initialize import register_segmenter_initialize

_ = register_segmenter_initialize(segmenter_app)

__all__ = ["segmenter_app"]

