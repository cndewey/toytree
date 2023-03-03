#!/usr/bin/env python

"""Random Tree generation functions. Uses numpy RNG.

"""

from typing import Optional
import numpy as np
import pandas as pd
from loguru import logger
from toytree.core.tree import ToyTree
from toytree.core.node import Node
from toytree.utils import ToytreeError

# pylint: disable=invalid-name, too-many-branches, too-many-statements

logger = logger.bind(name="toytree")


def _assign_names(tree: ToyTree, random: bool, rng: np.random.Generator) -> ToyTree:
    """Set name attributes on Nodes of a tree in place."""
    if not random:
        for nidx in range(tree.ntips):
            tree[nidx].name = f"r{nidx}"
    else:
        tidxs = rng.choice(range(tree.ntips), tree.ntips, replace=False)
        for nidx in range(tree.ntips):
            tree[nidx].name = f"r{tidxs[nidx]}"


def rtree(ntips: int, random_names: bool = False, seed: Optional[int] = None) -> ToyTree:
    """Return a random topology (fastest method).

    Default values are set on node support (0) and dist (1.0)
    features and can be modified after tree generation.

    Parameters
    ----------
    ntips: int
        The number of tips in the tree.
    seed: Optional[int]
        An integer seed for the numpy random number generator.

    Example
    -------
    >>> tree = toytree.rtree.rtree(ntips=10, seed=123)
    """
    # seed generator
    rng = np.random.default_rng(seed)

    # generate random topology with N tips.
    root = Node()
    current_tips = [root]

    # add children n-1 times, updating who the current children are.
    for _ in range(ntips - 1):
        tip = rng.choice(current_tips)
        current_tips.remove(tip)
        child0 = Node()
        child1 = Node()
        tip._add_child(child0)
        tip._add_child(child1)
        current_tips.extend([child0, child1])

    # assign tip labels as r{idx} for leaf nodes.
    tree = ToyTree(root)
    _assign_names(tree, random_names, rng)
    return tree


def unittree(
    ntips: int,
    treeheight: float = 1.0,
    random_names: bool = False,
    seed: Optional[int] = None,
) -> ToyTree:
    """Return an ultrametric tree where internal edges are all 1.

    A random tree is generated by iteratively splitting edges with
    equal probability. All internal edges are set to dist=1, and
    external edges are extended to make the tree ultrametric. The
    total tree height can be scaled to any arbitrary height, and
    other Nodes are scaled proportionately.

    Parameters
    ----------
    ntips: int
        The number of tips in the tree.
    treeheight: float
        All nodes in the tree will be scaled to retain relative node
        heights when scaling the total tree height to a new age.
    random_names: bool
        If True then names on the tips are randomized, else they are
        set to match with the node idx order.
    seed: Optional[int]
        An integer seed for the np random number generator.

    Examples
    --------
    >>> tree = toytree.rtree.unittree(ntips=10, treeheight=1e6)
    """
    # seed generator
    rng = np.random.default_rng(seed)

    # generate random topology with N tips
    tree = rtree(ntips, seed=rng.integers(0, 2**31))

    # extend terminal edges to align, scale total height
    tree.mod.edges_scale_to_root_height(treeheight, inplace=True)
    tree.mod.edges_extend_tips_to_align(inplace=True)

    # randomize names
    _assign_names(tree, random_names, rng)
    return tree


def imbtree(
    ntips: int ,
    treeheight: float = 1.0,
    random_names: bool = False,
    seed: Optional[int] = None,
) -> ToyTree:
    """Return an imbalanced (ladder-like) tree topology.

    Parameters
    ----------
    ntips: int
        The number of tips in the tree.
    treeheight: float
        All nodes in the tree will be scaled to retain relative node
        heights when scaling the total tree height to a new age.
    random_names: bool
        If True then names on the tips are randomized, else they are
        set to match with the node idx order.
    seed: Optional[int]
        An integer seed for the np random number generator.

    Example
    -------
    >>> tree = toytree.rtree.imbtree(ntips=10, seed=123)
    """
    # generate random topology with N tips.
    root = Node()
    tip = root

    # add children n-1 times
    for _ in range(ntips - 1):
        child0 = Node()
        child1 = Node()
        tip._add_child(child0)
        tip._add_child(child1)
        tip = child0

    # will ladderize the tree and assign names and idxs
    tree = ToyTree(root)
    tree.mod.edges_extend_tips_to_align(inplace=True)
    tree.mod.edges_scale_to_root_height(treeheight, inplace=True)

    # randomize names
    _assign_names(tree, random_names, np.random.default_rng(seed))
    return tree


def baltree(
    ntips: int,
    treeheight: float = 1.0,
    random_names: bool = False,
    seed: Optional[int] = None,
) -> ToyTree:
    """Return a balanced tree topology.

    Raises an error in ntips is not an even number.

    Parameters
    ----------
    ntips: int
        The number of tips in the tree.
    treeheight: float
        All nodes in the tree will be scaled to retain relative node
        heights when scaling the total tree height to a new age.
    random_names: bool
        If True then names on the tips are randomized, else they are
        set to match with the node idx order.
    seed: Optional[int]
        An integer seed for the np random number generator.

    Example
    -------
    >>> tree = toytree.rtree.baltree(ntips=10, seed=123)
    """
    # in the construction algorithm below I store 'dist' values for
    # each node as the node distance from the root, to evenly create
    # splits. 'dists' are later overwritten by extend_tips_to_align.

    # get a root Node and keep track of nancestors
    root = Node()

    # add children n-1 times. Visits leaf nodes
    curtips = 0
    while curtips < ntips - 1:

        # get node from smaller subtree
        parent = _get_small_child(root)

        # add children to the selected node and store
        child0 = Node()
        child1 = Node()

        # remove parent from dict
        parent._add_child(child0)
        parent._add_child(child1)
        curtips += 1

    # align tips, optionally set a to a height, add names, and return
    tree = ToyTree(root)
    tree.mod.edges_extend_tips_to_align(inplace=True)
    tree.mod.edges_scale_to_root_height(treeheight, inplace=True)
    _assign_names(tree, random_names, np.random.default_rng(seed))
    return tree


# def bdtree_stadler():
#     """More efficient method to simulate b-d trees (Stadler 2011).
#     """


def bdtree(
    ntips: int = 10,
    time: float = 4,
    b: float = 1,
    d: float = 0,
    stop: str = "taxa",
    seed: Optional[int] = None,
    retain_extinct: bool = False,
    random_names: bool = False,
    verbose: bool = False,
) -> ToyTree:
    """Return a parametric birth/death tree.

    The tree is generated by randomly sampling birth or death events
    starting from a single ancestor until a stopping criterion is
    reached. If the tree goes extinct it is restarted.

    The waiting time to the next speciation event is exponential with 
    parameter `b`; the waiting time to the next extinction event 
    is exponential with parameter `d`. Only one or the other will 
    be the next event. The waiting time to the next event (either type)
    is exponential with parameter b+d. The probability that an event
    is speciation is b/(b + d), extinction d/(b + d).

    Parameters
    ----------
    ntips: int
        Number of tips to generate for 'taxa' stopping criterion.
    time: float
        Amount of time to simulate for 'time' stopping criterion.
    b: float
        Birth rate per time unit
    d: death
        Death rate per time unit (d=0 produces Yule trees)
    stop: str
        Stopping critereon. Valid values are only 'taxa' or 'time'.
    seed: Optional[int]
        Random number generator seed.
    retain_extinct: bool
        (NotYetImplemented) Whether to retain internal nodes leading to
        extinct tips.
    random_names: bool
        Whether to randomize tip names or name them in order.
    verbose: bool
        Sets logging level to INFO to show statistics

    Examples
    --------
    >>> rtre = toytree.rtree.bdtree(ntips=10, b=1.0, d=0.5)
    """
    # require an appropriate option for stopping
    if stop not in ["taxa", "time"]:
        raise ToytreeError("stop must be either 'taxa' or 'time'")

    # random generator
    rng = np.random.default_rng(seed)

    taxa_stop = ntips
    time_stop = time

    # start from random tree (idxs will be re-assigned at end)
    root = Node(name="0")
    root.tdiv = 0

    # counters for extinctions, total events, and time
    resets = 0
    ext = 0
    evnts = 0
    time = 0

    # keep track of current leaf Nodes
    tips = [root]

    # continue until stop var
    while 1:

        # sample time until next event, increment t and events
        dtime = rng.exponential(1 / (len(tips) * (b + d)))
        time += dtime
        evnts += 1

        # sample a [0-1] to choose birth or death and sample a tip node
        rvar = rng.random()
        tip = rng.choice(tips)

        # event is a birth
        if rvar <= b / (b + d):
            # add child 1
            child1 = Node(name=f"{evnts}-1", dist=0)
            child1.tdiv = time
            tip._add_child(child1)
            # add child 2
            child2 = Node(f"{evnts}-2", dist=0)
            child2.tdiv = time
            tip._add_child(child2)
            # update tip list
            tips.extend([child1, child2])
            tips.remove(tip)

        # else event is extinction
        else:
            # get sisters
            sisters = tip.get_sisters()

            # drop the extinct tip
            tips.remove(tip)

            # sister exists and retains connect to unary parent
            if sisters:
                tip.up._remove_child(tip)

            # no sisters exist, so in addition to removing
            # this node we also remove any unary parent nodes
            # until we reach either the root, or a bipartition
            # since no descendants exist on this branch.
            else:
                while 1:
                    if tip.is_leaf() and not tip.is_root():
                        unary_node = tip
                        tip = tip.up
                        tip._remove_child(unary_node)
                    else:
                        break

            # if parent is None then reset
            if tip.up is None:
                resets += 1
                ext = 0
                evnts = 0
                root._dist = time = 0
                root._children = ()
                tips = [root]

            # advance extinction counter
            ext += 1

        # update branch lengths so all tips end at time=current
        for tip in tips:
            tip._dist += dtime

        # check stopping criterion
        if stop == "taxa":
            if len(tips) >= taxa_stop:
                break
        else:
            if time >= time_stop:
                break

    # log statistics
    if verbose:
        results = pd.Series({
            'time': time,
            'ntips': len(tips),
            'b': evnts - ext,
            'd': ext,
            'b/d': evnts / (evnts - ext),
            'resets': resets,
        })
        print(results)

    # if not retain_extinct then remove all internal unary nodes
    if not retain_extinct:
        # remove any unary nodes
        nodes = list(root._traverse_idxorder())
        for node in nodes[:-1]:
            if not node.is_leaf():
                if len(node.children) < 2:
                    node._delete(True, False)
        # make root the deepest node containing a split.
        while 1:
            if len(root.children) == 1:
                root = root.children[0]
            else:
                break

    # update coords and return
    # tre = tre.mod.ladderize()
    tree = ToyTree(root)
    _assign_names(tree, random_names, np.random.default_rng(seed))
    return tree


def coaltree(k: int, N: int, seed: Optional[int] = None) -> ToyTree:
    """Return a random ToyTree generated under the n-coalescent.

    Waiting times between coal events under the n-coalescent are 
    exponentially distributed with rate 4N / (k * k-1). A tree is 
    constructed by randomly samples waiting times from an exponential 
    for each value of k from k to 1, and randomly joining Nodes at 
    each coalescent interval.

    Parameters
    ----------
    k: int
        The number of gene copies sampled at the present.
    N: int
        The effective population size (Ne).
    seed: int or None
        A seed for the numpy random number generator.
    """
    # seed rng
    rng = np.random.default_rng(seed)

    # get waiting times
    kvals = np.arange(k, 1, -1)
    times = rng.exponential((4 * N) / (kvals * (kvals - 1)))

    # make tip Nodes for k samples
    nodes = {i: Node(name=str(i)) for i in range(k)}

    # iterate over coalescent time intervals
    for time in times:
        # increment the dist for all current Nodes
        for node in nodes:
            nodes[node]._dist += time

        # randomly sample two Nodes and connect to a new parent
        node0 = nodes.pop(rng.choice(tuple(nodes)))
        node1 = nodes.pop(rng.choice(tuple(nodes)))
        new_node = Node(str(k + 1))
        new_node._add_child(node0)
        new_node._add_child(node1)

        # advance name counter and update tips dict
        k = k + 1
        nodes[k] = new_node
    return ToyTree(new_node)


def _get_small_child(node):
    """A recursive to return a Node from the smaller subclade of a
    tree, used for building balanced trees."""
    if not node.children:
        return node
    ldesc, rdesc = (len(i.get_leaves()) for i in node.children)
    if ldesc < rdesc:
        return _get_small_child(node.children[0])
    return _get_small_child(node.children[1])


# def coaltree(ntips, Ne, random_names=False, seed=None):
#     """Return a coalescent tree with ntips.
#
#     samples and waiting times ...
#     between coalescent events drawn from the kingman coalescent:
#     (4N)/(k*(k-1)), where N is effective population size (ne) and
#     k is sample size (ntips). Edge lengths on the tree are in
#     generations.
#     """
#     rng = np.random.default_rng(seed)

#     # convert units
#     coalunits = False
#     if not ne:
#         coalunits = True
#         ne = 10000

#     # build tree: generate N tips as separate Nodes then attach together
#     # at internal nodes drawn randomly from coalescent waiting times.
#     tips = [
#         toytree.tree().treenode.add_child(name=str(i))
#         for i in range(ntips)
#     ]
#     while len(tips) > 1:
#         rtree = toytree.tree()
#         tip1 = tips.pop(random.choice(range(len(tips))))
#         tip2 = tips.pop(random.choice(range(len(tips))))
#         kingman = (4. * ne) / float(ntips * (ntips - 1))
#         dist = random.expovariate(1. / kingman)
#         rtree.treenode.add_child(tip1, dist=tip2.height + dist)
#         rtree.treenode.add_child(tip2, dist=tip1.height + dist)
#         tips.append(rtree.treenode)

#     # build new tree from the newick string
#     self = toytree.tree(tips[0].write())
#     self.treenode.ladderize()

#     # make tree edges in units of 2N (then N doesn't matter!)
#     if coalunits:
#         for node in self.treenode.traverse():
#             node.dist /= (2. * ne)

#     # ensure tips are at zero (they sometime vary just slightly)
#     for node in self.treenode.traverse():
#         if node.is_leaf():
#             node.dist += node.height

#     # set tipnames to r{idx}
#     nidx = list(range(self.ntips))
#     if random_names:
#         random.shuffle(nidx)
#     for idx, node in enumerate(self):
#         if node.is_leaf():
#             node.name = "r{}".format(nidx[idx])

#     # decompose fills in internal node names and idx
#     self._coords.update()
#     return self


if __name__ == "__main__":

    TREE = rtree(10)
    print(TREE.get_tip_labels())

    TREE = unittree(10)
    print(TREE.get_tip_labels())

    TREE = bdtree(10, b=0.5, d=0.5, verbose=1)
    # TREE._draw_browser()
    # print(TREE.get_tip_labels())
    # print(TREE.treenode.draw_ascii())

    # TREE = bdtree(10)
    # print(TREE.get_tip_labels())

    # sim_trees = [
    #     toytree.rtree.rtree(10),
    #     toytree.rtree.baltree(10),
    #     toytree.rtree.imbtree(10),
    #     toytree.rtree.bdtree(10),
    #     toytree.rtree.unittree(10),
    # ]
    # print(sim_trees)