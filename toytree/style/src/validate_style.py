#!/usr/bin/env python

"""Validate style arguments to ToyTree.draw.

Note: validate_x() functions are written specifically to work in two
fairly different scenarios: `draw_tree` and `annotation`. 

In `draw_tree` they take an attribute of a TreeStyle as input, expand
it to an array, and return it to set it back on the TreeStyle object.
It could be simpler to just set values on the TreeStyle, but for
compatibility with the second method we don't do that.

on the dict info
of TreeStyle objects because this allows for re-using these more
easily in annotation functions.
"""

from typing import Mapping, Any, Dict, TypeVar
from loguru import logger

from toytree.style import TreeStyle
from toytree.style.src.validate_nodes import (
    validate_node_mask,
    validate_node_sizes,
    validate_node_markers,
    validate_node_hover,
    validate_node_colors,
    validate_node_style,
)
from toytree.style.src.validate_node_labels import (
    validate_node_labels,
    validate_node_labels_style,
)
from toytree.style.src.validate_tips import (
    validate_tip_labels,
    validate_tip_labels_angles,
    validate_tip_labels_colors,
    validate_tip_labels_style,
)
from toytree.style.src.validate_edges import (
    validate_edge_widths,
    validate_edge_colors,
    validate_edge_style,
    validate_edge_align_style,
)

# from toytree.style.src.validate_edges import validate_edge_widths
logger = logger.bind(name="toytree")
ToyTree = TypeVar("ToyTree")
NON_VALIDATED = [
    "height",
    "width",
    "layout",
    "edge_type",
    "tip_labels_align",
    "use_edge_lengths",
    "scale_bar",
    "padding",
    "xbaseline",
    "ybaseline",
    "admixture_edges",
    "shrink",
    # "fixed_order",
    # "fixed_position",
]


def get_dict(kwargs: Mapping[str, Any], name: str) -> Any:
    """Return user value if provided (not None) else BaseStyle value.

    This is necessary because the key is usually present and mapped to
    a value of None, but we want {} returned if the value is None.
    """
    return kwargs[name] if kwargs.get(name) is not None else {}


def validate_style(
    tree: ToyTree,
    style: TreeStyle,
    **kwargs,
) -> TreeStyle:
    """Validate style arguments to ToyTree.draw() before creating Mark.

    The TreeStyle is a copy from the ToyTree and kwargs arguments are
    user args to the .draw() function which override the TreeStyle
    defaults. This expands arguments into values and checks the size
    and type. Many of the functions within are also used in annotations.
    """
    # validate node settings
    style.node_mask = validate_node_mask(tree, style, **kwargs)
    style.node_sizes = validate_node_sizes(tree, style, **kwargs)
    style.node_markers = validate_node_markers(tree, style, **kwargs)
    style.node_hover = validate_node_hover(tree, style, **kwargs)
    style.node_labels = validate_node_labels(tree, style, **kwargs)
    style.node_colors, node_fill_color = validate_node_colors(tree, style, **kwargs)
    if node_fill_color is not None:
        style.node_style.fill = node_fill_color

    # validate edge settings
    style.edge_widths = validate_edge_widths(tree, style, **kwargs)
    style.edge_colors, edge_stroke = validate_edge_colors(tree, style, **kwargs)
    if edge_stroke is not None:
        style.edge_style.stroke = edge_stroke

    # validate tip settings
    style.tip_labels = validate_tip_labels(tree, style, **kwargs)
    style.tip_labels_angles = validate_tip_labels_angles(tree, style, **kwargs)
    style.tip_labels_colors, tip_fill_color = validate_tip_labels_colors(tree, style, **kwargs)
    if tip_fill_color is not None:
        style.tip_labels_style.fill = tip_fill_color

    # validate style dictionaries
    style.node_style = validate_node_style(tree, style.node_style, **get_dict(kwargs, "node_style"))
    style.edge_style = validate_edge_style(tree, style.edge_style, **get_dict(kwargs, "edge_style"))
    style.node_labels_style = validate_node_labels_style(tree, style.node_labels_style, **get_dict(kwargs, "node_labels_style"))
    style.edge_align_style = validate_edge_align_style(tree, style.edge_align_style, **get_dict(kwargs, "edge_align_style"))
    style.tip_labels_style = validate_tip_labels_style(tree, style.tip_labels_style, **get_dict(kwargs, "tip_labels_style"))

    # set remaining key:val that do not have validators
    for key in NON_VALIDATED:
        val = kwargs.get(key, None)
        if val is not None:
            setattr(style, key, val)
    # for key, val in kwargs.items():
    #     if key in NON_VALIDATED:
    #         if val is not None:
    #             setattr(style, key, val)
    return style


if __name__ == "__main__":

    import toytree
    from toytree.style import get_base_tree_style_by_name
    from toytree.drawing.src.draw_toytree import get_tree_style_base

    tree = toytree.rtree.unittree(8)

    style = get_tree_style_base(tree, ts='c', node_colors="red")
    style = validate_style(tree, style)

    print(style.node_colors)
    print(style.node_style)