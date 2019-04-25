"""
AST enumeration method with internal stub AST representation.
"""
from collections import namedtuple

__all__ = [
    "ast_enumerated"
]

"""
Stub format and methods.
Requirements:
- Add additional leaves in O(1)
- Be able to enumerate directions # Get the lowest depth nodes, enumerate directions in CFG.
- Be able to materialize into an AST # 
- Be able to detect when completed # No incomplete leaf nodes
- Be able to measure depth efficiently # 

Assumptions I don't want to make:
- Depth is uniform (we will later bias depth based on the branch expr type.)

"""

class Stub(namedtuple('Stub', ['nodes', 'leaf_node_indices'])):
    """
    Partial AST for efficient AST tree enumeration.

    :param List[ Tuple[str, int, Optional[List[int]]] ] nodes:
        Indexed list of nodes of the tree.
        The first node is the root of the tree.
        Nodes are represented as a tuple with these fields:
        - Node type.
        - Node depth (cached.)
        - Node children (list of indices.)
    :param Set[int] leaf_node_indices: Set of leaf nodes.

    :Example:
    >>> from enumerate import Stub
    >>> my_stub = Stub(
            nodes=[
                ('SELECT_AGG', 0, [1, 2, 3]),
                ('SELECT_EXPRS', 1, None),
                ('TOP_JOINS', 1, None),
                ('EXPR', 1, None),
            ],
            open_node_indices={1, 2, 3},
        )
    """

def initial_stubs(entry_tokens):
    """
    Return the initial set of stubs for the given set of entry tokens.
    """
    for token in entry_tokens:
        yield Stub(
            top_node=0,
            nodes=[(top_node, 0, None)],
            leaf_node_indices={0},
        )

def next_stubs(stub):
    """
    """
    min_leaf_depth = min(
        stub['nodes'][index][1]
        for index in stub['leaf_node_indices']
    )

    top_leaf_node_indices = {
        leaf_node_index
        for leaf_node_index in stub['leaf_node_indices']
        if stub['nodes'][leaf_node_index][1] == min_leaf_depth
    }

    for top_leaf_node_index in top_leaf_node_indices:
        # Enumerate types, make copy stubs with destination types,
        # update
        pass

    


def stub_ast(stub, node_index=0):
    raise NotImplementedError


def stub_sorted(stubs):
    raise NotImplementedError()
    return sorted(stubs)

def stub_complete(stub):
    return not stub['leaf_node_indices']

def ast_enumerated(entry_tokens, cfg_spec, depth_measure=None, max_depth=None):
    """
    
    """
    assert not depth_measure

    current_stubs = initial_stubs(entry_tokens)

    current_depth = 1
    while not max_depth or max_depth > current_depth:
        current_depth += 1

        next_stubs = {}
        for parent_stub in stub_sorted(current_stubs):
            children_stubs = stub_sorted(next_stubs(stub))
            for child_stub in children_stubs:
                if stub_complete(child_stub):
                    yield stub_ast(child_stub)
                else:
                    next_stubs.add(child_stub)

        current_stubs = next_stubs
