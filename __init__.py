try:
    from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
except ImportError:
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}

__version__ = "1.0.0"

WEB_DIRECTORY = "./js"
TYPE_NAME = "SVG"
EXTENSION_NAME = "ComfyUI-SVGFullfill"
