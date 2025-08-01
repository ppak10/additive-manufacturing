from .__main__ import segmenter_app
from .initialize import register_segmenter_initialize
from .parse import register_segmenter_parse
from .visualize_layer import register_segmenter_visualize_layer

_ = register_segmenter_initialize(segmenter_app)
_ = register_segmenter_parse(segmenter_app)
_ = register_segmenter_visualize_layer(segmenter_app)

__all__ = ["segmenter_app"]
