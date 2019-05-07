"""
AST enumeration method with internal stub AST representation.
"""
from collections import namedtuple
from copy import deepcopy
from itertools import product
from pprint import pformat
from heapq import heapify, heappop, heappush

__all__ = [
    "ast_enumerated"
]

"""
Stub format and methods.
Requirements:
- Add additional leaves in O(1)
- Be able to enumerate directions
- Be able to materialize into an AST
- Be able to detect when completed
- Be able to measure depth efficiently

TODO:
- [DOC] There's some confusion in variable naming about parent/child refering to
     both child/parent _nodes_ and child/parent _partial ASTs_.
- [DOC] Explicitly document and set terms for operations and relationships
    between nodes and partial ASTs.
- [DOC] Switch the partial_ast's __str__ to a __repr__ and redo docs
- [DOC] Completely flush max_depth through docs
"""

class PartialAst(namedtuple('PartialAst', [
        'nodes',
        'max_depth',
        'open_node_indices',
])):
    """
    Partial AST for efficient AST tree enumeration.

    Note: Node children indices should be treated as immutable.
    This allows us to use shallow copies for most operations.

    :param List[ Tuple[str, int, Optional[List[int]]] ] nodes:
        Indexed list of nodes of the tree.
        The first node is the root of the tree.
        Nodes are represented as a tuple with these fields:
        - Node type.
        - Node depth (cached.)
        - Node children (optional list of indices.)
    :param int max_depth: Maximum depth of any node in partial AST.
    :param Set[int] open_node_indices: Set of leaf nodes.

    :Example:
    >>> from enumerate import PartialAst
    >>> my_partial_ast = PartialAst(
            nodes=[
                ('SELECT_AGG', 1, [1, 2, 3]),
                ('SELECT_EXPRS', 2, None),
                ('TOP_JOINS', 2, None),
                ('EXPR', 2, None),
            ],
            max_depth=2,
            open_node_indices=frozenset({1, 2, 3}),
        )

    """

    def __str__(self):
        def pformated(arg):
            return pformat(arg, width=60, indent=2).replace('\n', '\n    ')

        return (
            'PartialAst(\n'
            '    nodes={nodes},\n'
            '    max_depth={max_depth},\n'
            '    open_node_indices={open_nodes},\n'
            ')'
        ).format(
            nodes=pformated(self.nodes),
            max_depth=int(self.max_depth),
            open_nodes=pformated(self.open_node_indices),
        )
"""
Partial AST operations.
- initial_partial_asts: The initial partial ASTs for a given CFG.
- next_partial_asts: The next iteration of partial ASTs
    for a given CFG + partial AST.
- partial_ast_complete: Is this partial AST complete?
- ast_from_partial_ast: The AST for a completed partial AST.
"""

def initial_partial_asts(entry_tokens, node_weights):
    """
    The initial set of partial_asts for the given set of entry tokens and
    node_weights.

    :Example:
    >>> from sql_ast import sql_entry_tokens, sql_heuristic_weight

    >>> pprint(list(initial_partial_asts(sql_entry_tokens, sql_heuristic_weight)))
    [PartialAst(nodes=[('SELECT_AGG', 4, None)], max_depth=4, open_node_indices=frozenset({0})),
     PartialAst(nodes=[('SELECT_AGG_WHERE', 4, None)], max_depth=4, open_node_indices=frozenset({0}))]
    """
    for node_type in entry_tokens:
        node_type_weight = node_weights[node_type]
        yield PartialAst(
            nodes=[(node_type, node_type_weight, None)],
            max_depth=node_type_weight,
            open_node_indices=frozenset({0}),
        )

def most_shallow_node_index(partial_ast):
    """
    Selects the next node to expand.
    Picks the next node based on depth, then type, then arbitrary.

    :Example:
    >>> from sql_ast import sql_heuristic_weight
    >>> from enumerate import most_shallow_node_index
    >>> from example_partial_asts import example_partial_asts
    >>> root = example_partial_asts['root']
    >>> level_1 = example_partial_asts['level_1']

    >>> root
    PartialAst(nodes=[('SELECT_AGG', 1, None)], max_depth=1, open_node_indices=frozenset({0}))
    >>> most_shallow_node_index(root)
    0

    >>> level_1
    PartialAst(nodes=[('SELECT_AGG', 0, [1, 2, 3]), ('SELECT_EXPRS', 1, None), ('TOP_JOINS', 1, None), ('EXPR', 1, None)], open_node_indices=frozenset({1, 2, 3}))
    >>> most_shallow_node_index(level_1)
    3
    """
    assert partial_ast.open_node_indices

    best_node_key, best_node_index = ((2 ** 31, ''), None)
    for leaf_node_index in partial_ast.open_node_indices:
        node_type, node_depth, _ = (
            partial_ast.nodes[leaf_node_index]
        )
        node_key = (node_depth, node_type)
        if best_node_key > node_key:
            best_node_key, best_node_index = (node_key, leaf_node_index)

    assert best_node_index != None

    return best_node_index

def node_children_type_patterns(node_type, cfg):
    """
    :Example:

    >>> from sql_ast import sql_cfg
    >>> pprint(list(node_children_type_patterns('SELECT_AGG', sql_cfg)))
    [('SELECT_EXPRS', 'FROM', 'GROUP_EXPRS'),
     ('SELECT_EXPRS', 'FROM', 'EXPR'),
     ('SELECT_EXPRS', 'TOP_JOINS', 'GROUP_EXPRS'),
     ('SELECT_EXPRS', 'TOP_JOINS', 'EXPR'),
     ('EXPR_AS', 'FROM', 'GROUP_EXPRS'),
     ('EXPR_AS', 'FROM', 'EXPR'),
     ('EXPR_AS', 'TOP_JOINS', 'GROUP_EXPRS'),
     ('EXPR_AS', 'TOP_JOINS', 'EXPR')]
    """
    return product(*(
        elem if isinstance(elem, set) else {elem}
        for elem in cfg[node_type]
    ))

def pattern_expanded_partial_ast(
        partial_ast,
        selected_node_index,
        children_type_pattern,
        node_weights,
):
    """
    The resulting expanded partial AST given a partial AST, a selected leaf, and
    a particular children pattern / child node type pattern.
    """
    parent_node_type, parent_node_depth, _ = partial_ast.nodes[
        selected_node_index
    ]

    if children_type_pattern == (None,): # Terminating special case.
        return PartialAst(
            nodes=list(partial_ast.nodes),
            max_depth=partial_ast.max_depth,
            open_node_indices=(
                partial_ast.open_node_indices - {selected_node_index}
            ),
        )

    children_node_indices = list(range(
        len(partial_ast.nodes),
        len(partial_ast.nodes) + len(children_type_pattern),
    ))

    next_nodes = partial_ast.nodes + [
        (child_type, parent_node_depth + node_weights[child_type], None)
        for child_type in children_type_pattern
    ]
    next_nodes[selected_node_index] = (
        parent_node_type,
        parent_node_depth,
        children_node_indices,
    )

    max_depth = max(
        parent_node_depth + node_weights[child_type]
        for child_type in children_type_pattern
    )

    next_open_node_indices = (
        partial_ast.open_node_indices - {selected_node_index}
    ) | frozenset(children_node_indices)

    return PartialAst(
        nodes=next_nodes,
        max_depth=max_depth,
        open_node_indices=next_open_node_indices,
    )

def partial_asts_after_expanding(
        partial_ast,
        selected_node_index,
        cfg,
        node_weights,
):
    """
    The partial ASTs derived from expanding a node on a partial AST.

    TODO:
    - [SIMPLICITY] Pull in helper and replace with expand_nodes helper, instead
        of wrapping full functionality of partial_ast (making helpers more
        complicated.)
    :Example:

    >>> from sql_cfg import sql_cfg, sql_heuristic_weight
    >>> from example_partial_asts import example_partial_asts
    >>> root = example_partial_asts['root']

    >>> root_expanded = list(partial_asts_after_expanding(root, 0, sql_cfg, sql_heuristic_weight))
    >>> pprint(root_expanded)
    [PartialAst(nodes=[('SELECT_AGG', 0, [1, 2, 3]), ('SELECT_EXPRS', 4, None), ('FROM', 4, None), ('GROUP_EXPRS', 20, None)], open_node_indices=frozenset({1, 2, 3})),
     PartialAst(nodes=[('SELECT_AGG', 0, [1, 2, 3]), ('SELECT_EXPRS', 4, None), ('FROM', 4, None), ('EXPR', 4, None)], open_node_indices=frozenset({1, 2, 3})),
     PartialAst(nodes=[('SELECT_AGG', 0, [1, 2, 3]), ('SELECT_EXPRS', 4, None), ('TOP_JOINS', 4, None), ('GROUP_EXPRS', 20, None)], open_node_indices=frozenset({1, 2, 3})),
     PartialAst(nodes=[('SELECT_AGG', 0, [1, 2, 3]), ('SELECT_EXPRS', 4, None), ('TOP_JOINS', 4, None), ('EXPR', 4, None)], open_node_indices=frozenset({1, 2, 3})),
     PartialAst(nodes=[('SELECT_AGG', 0, [1, 2, 3]), ('EXPR_AS', 4, None), ('FROM', 4, None), ('GROUP_EXPRS', 20, None)], open_node_indices=frozenset({1, 2, 3})),
     PartialAst(nodes=[('SELECT_AGG', 0, [1, 2, 3]), ('EXPR_AS', 4, None), ('FROM', 4, None), ('EXPR', 4, None)], open_node_indices=frozenset({1, 2, 3})),
     PartialAst(nodes=[('SELECT_AGG', 0, [1, 2, 3]), ('EXPR_AS', 4, None), ('TOP_JOINS', 4, None), ('GROUP_EXPRS', 20, None)], open_node_indices=frozenset({1, 2, 3})),
     PartialAst(nodes=[('SELECT_AGG', 0, [1, 2, 3]), ('EXPR_AS', 4, None), ('TOP_JOINS', 4, None), ('EXPR', 4, None)], open_node_indices=frozenset({1, 2, 3}))]

    >>> pprint([ast_from_partial_ast(ast, allow_incomplete=True) for ast in root_expanded])
    [['SELECT_AGG', ['SELECT_EXPRS'], ['FROM'], ['GROUP_EXPRS']],
     ['SELECT_AGG', ['SELECT_EXPRS'], ['FROM'], ['EXPR']],
     ['SELECT_AGG', ['SELECT_EXPRS'], ['TOP_JOINS'], ['GROUP_EXPRS']],
     ['SELECT_AGG', ['SELECT_EXPRS'], ['TOP_JOINS'], ['EXPR']],
     ['SELECT_AGG', ['EXPR_AS'], ['FROM'], ['GROUP_EXPRS']],
     ['SELECT_AGG', ['EXPR_AS'], ['FROM'], ['EXPR']],
     ['SELECT_AGG', ['EXPR_AS'], ['TOP_JOINS'], ['GROUP_EXPRS']],
     ['SELECT_AGG', ['EXPR_AS'], ['TOP_JOINS'], ['EXPR']]]
    """
    assert selected_node_index in partial_ast.open_node_indices

    node_type, _, _ = partial_ast.nodes[selected_node_index]

    for children_type_pattern in node_children_type_patterns(node_type, cfg):
        yield pattern_expanded_partial_ast(
            partial_ast,
            selected_node_index,
            children_type_pattern,
            node_weights,
        )
    
def next_partial_asts(partial_ast, cfg, node_weights):
    """
    The the next partial and complete ASTs built on top of a given partial AST.

    Selects the most shallow node, then sorts by type name, then arbitrary.
    """
    selected_node_index = most_shallow_node_index(partial_ast)

    for next_partial_ast in partial_asts_after_expanding(
            partial_ast,
            selected_node_index,
            cfg,
            node_weights,
    ):
        yield next_partial_ast

def partial_ast_complete(partial_ast):
    return not partial_ast.open_node_indices

def ast_from_partial_ast(partial_ast, node_index=0, allow_incomplete=False):
    """
    """
    assert allow_incomplete or partial_ast_complete(partial_ast)

    node_type, _, node_children_indices = partial_ast.nodes[node_index]

    if node_type == 'SYMBOL': # SYMBOL HANDLING POINT
        if not node_children_indices:
            return [node_type]
        else:
            assert len(node_children_indices) == 1
            (child_index,) = node_children_indices
            child_type, _, child_indices = partial_ast.nodes[child_index]
            assert child_type.startswith('SYMBOL_') and not child_indices
            return ['SYMBOL', child_type[len("SYMBOL_"):]]

    return [node_type] + [
        ast_from_partial_ast(
            partial_ast,
            node_index=child_node_index,
            allow_incomplete=allow_incomplete
        )
        for child_node_index in (node_children_indices or [])
    ]

def cfg_with_symbols(cfg, symbols):
    """
    A SYMBOL-injected version of a CFG.
    Useful for extracting SYMBOLs from the environment and making them available
    to the CFG search, IE so you can use table names.
    """
    cfg = deepcopy(cfg) # SYMBOL HANDLING POINT
    cfg['SYMBOL'] = [{
        'SYMBOL_' + symbol
        for symbol in symbols
    }]

    cfg.update(
        ('SYMBOL_' + symbol, [None])
        for symbol in symbols
    )

    return cfg

def ast_enumerated(
        entry_tokens,
        cfg_spec,
        weights=None,
        max_depth=None,
        symbols=None,
):
    """
    The enumerated list of all SQL ASTs.

    :Example:
    >>> from sql_ast import (
            sql_query_str,
            sql_cfg,
            sql_entry_tokens,
            sql_heuristic_weight,
        )
    >>> from itertools import islice

    >>> def sql_queries_enumerated():
            for sql_ast in ast_enumerated(
                    sql_entry_tokens,
                    sql_cfg,
                    weights=sql_heuristic_weight,
                    symbols=['student', 'department'],
                    max_depth=20,
            ):
                yield sql_query_str(sql_ast)

    >>> for query in islice(sql_queries_enumerated(), 3):
            print()
            print(query)

    SELECT department AS student
      FROM student
     GROUP BY department

    SELECT student AS student
      FROM department
     GROUP BY student

    SELECT student AS department
      FROM department
     GROUP BY student
    """
    # SYMBOL HANDLING POINT
    cfg_spec = cfg_with_symbols(cfg_spec, symbols)

    current_partial_asts = [
        (partial_ast.max_depth,
         (len(partial_ast.nodes), id(partial_ast)), # Arbitrary sort key.
         partial_ast)
        for partial_ast in initial_partial_asts(entry_tokens, weights)
    ]
    heapify(current_partial_asts)

    while True:
        global_min_depth, _, shallowest_partial_ast = heappop(current_partial_asts)
        if max_depth and global_min_depth > max_depth:
            return

        print(len(current_partial_asts))

        for next_partial_ast in (
                next_partial_asts(shallowest_partial_ast, cfg_spec, weights)
        ):
            if partial_ast_complete(next_partial_ast): # SYMBOL HANDLING IN COND
                yield ast_from_partial_ast(next_partial_ast)
            else:
                heappush(current_partial_asts, (
                    next_partial_ast.max_depth,
                    (len(next_partial_ast.nodes),
                     id(next_partial_ast)),
                    next_partial_ast,
                ))
