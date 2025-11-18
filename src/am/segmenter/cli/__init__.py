from .__main__ import app
from .parse import register_segmenter_parse
from .visualize_layer import register_segmenter_visualize_layer
from .shape_2d import register_segmenter_shape_2d

_ = register_segmenter_parse(app)
_ = register_segmenter_shape_2d(app)
_ = register_segmenter_visualize_layer(app)

__all__ = ["app"]
