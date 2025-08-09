from .__main__ import app
# from .initialize import register_segmenter_initialize
from .parse import register_segmenter_parse
from .visualize_layer import register_segmenter_visualize_layer

# _ = register_segmenter_initialize(app)
_ = register_segmenter_parse(app)
_ = register_segmenter_visualize_layer(app)

__all__ = ["app"]

