#!/usr/bin/env python

"""Get edges as (child, parent) tuples on a tree.

Methods
-------
Get tuples of Nodes on either side of each edge creating a bipartition
>>> tree.iter_edges('idx')                # ((0, 4), (1, 4), (2, 5), ...

Get a table of the edges in a tree as an array or dataframe
>>> tree.get_edges('idx')                 # np.array([(0, 4), ...])

"""

from typing import Iterator, Tuple, Optional, Union
# from loguru import logger
import pandas as pd
import numpy as np
from toytree import Node, ToyTree
from toytree.core.apis import TreeEnumAPI, add_subpackage_method, add_toytree_method

# logger = logger.bind(name="toytree")

__all__ = [
    "iter_edges",
    "get_edges",
]


@add_toytree_method(ToyTree)
@add_subpackage_method(TreeEnumAPI)
def iter_edges(self, feature: Optional[str] = None) -> Iterator[Tuple[Node, Node]]:
    """Generator of (Node, Node) tuples representing edges in tree.

    Given the current tree rooting edges are yielded in idx order
    as (child, parent). The edges set will include edges connected
    to the root Node even if the tree is unrooted. To instead view
    edges as bipartitions of Node sets see `iter_bipartitions`.

    Parameters
    ----------
    feature: str
        An optional feature of a Node returned in place of the Node
        object to represent it. For example, 'name' or 'idx'.

    Example
    -------
    >>> tree = toytree.rtree.unittree(5, seed=123)
    >>> list(iter_edges(feature='idx'))
    >>> # [(0, 5), (1, 5), (2, 6), (3, 7), (4, 7), (5, 6), (6, 8), (7, 8)]
    """
    if feature:
        for node in self[:-1]:
            yield (getattr(node, feature), getattr(node._up, feature))
    else:
        for node in self[:-1]:
            yield (node, node._up)


@add_toytree_method(ToyTree)
@add_subpackage_method(TreeEnumAPI)
def get_edges(self, feature: Optional[str] = None, df: bool = False) -> Union[np.ndarray, pd.DataFrame]:
    """Return matrix of (child, parent) edges.

    Given the current tree rooting edges are yielded in idx order
    as (child, parent).

    Parameters
    ----------
    feature: str or None
        Edges can be represented by Node features such as 'idx' or
        'name' (default='idx'). None returns Node objects.
    df: bool
        If True the matrix is returned as a pd.DataFrame rather
        than as a np.ndarray.

    See Also
    --------
    tree.iter_edges
    """
    edges = list(self.iter_edges(feature=feature))
    if df:
        return pd.DataFrame(edges, columns=["child", "parent"])
    return np.array(edges)


if __name__ == "__main__":

    import toytree
    tree = toytree.rtree.unittree(10, seed=123)
    edges = list(tree.iter_edges())
    print(edges)
    print(tree.get_edges('idx', df=True))
