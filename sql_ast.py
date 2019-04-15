"""
Should element list length be a CFG?
- Screws up depth statistics
- Maybe do it wide, but do a bias? Artificial depth / perceptual coplexity constant?

depth score - primarily focusing on join depth


need to anticipate typing info getting pushed down


Example syntax trees:



There's a difference between node-type / node-class (basic group) and node and instantiation of node.

... Actually...

You can have nodes of multiple types. For example, expressions can be used in both aggregating and non-aggregating setups.

What's the difference between typing information and syntax information?
...
So we're dealing with a transition matrix between symbols.
We can choose to explode the set of symbols to encompass more possibilities.
OR
We can choose to minimize the set of symbols, dedup'ing some, and having additional (inferrable) information be extracted via
    secondary process.

What are the consequences?
- Effectively, during the search, we're searching over the _collection_ of possible nodes. 
- Branching factor is minimized.
- A full AST _must_ enforce a single representation.
    Otherwise, we'll just be searching over sets of graphs, and will need to reiterate.
    ... Unless we can do _hierarchical/iterated_ elimination of possible plan phenotypes, where earlier passes are very fast...
Let's start with something more brute-force. :)

- If you can look at the tree, and with _simple_ up/down/combine propagation rules of simple types,
    completely decide the types of all nodes, we're done.
- I should make those propagation rules more explicit. There is an advantage to pushing typing to the AST layer:
- - These typing conflicts get to be detected more efficiently.


2019-04-14
Efficient representation of joint-argument witness function constraints (allowing for efficient descent of tree.)
These include, in typical order:
- Syntactic constraints
- Typing constraints
- Data constraints (from input/output pairs)

Say you have an AST.
- Production rules
- Weights for depth?
- Genericized witness functions?

Let's start with a brute-force AST.
- Go over all possible trees.
- Have a few early-aborts.
- Explore in all directions once time made available.


Rules for nodes:
- Node type names should unambiguously specify a child node set.
"""

from collections import defaultdict

from tools import id_memoize

node_type_depth = defaultdict(lambda: 1, {
    'SELECT_AGG': 20,
    'SEL_EXPRS': 10,
    'JOINS': 20,
    'EQ': 2,
    'GROUP_EXPRS': 10,
})

node_group = {
    'EXPR': {'EQ', 'DOT', 'SYMBOL', 'SUM'},
    'JOIN': {'LEFT_JOIN_ON'},
}

node_productions = {
    'SELECT_AGG': [{'SELECT_EXPRS', 'EXPR_AS'}, {'JOINS', 'FROM'}, {'GROUP_EXPRS', 'GROUP_EXPR'}],
    'SELECT_EXPRS': ['EXPR_AS', {'SELECT_EXPRS', 'EXPR_AS'}],
    'EXPR_AS': [node_group['EXPR'], 'SYMBOL'],
    'JOINS': ['FROM', node_group['JOIN']],
    'FROM': ['SYMBOL'],
    'LEFT_JOIN_ON': ['SYMBOL', node_group['EXPR']],
    'GROUP_EXPRS': ['GROUP_EXPR', {'GROUP_EXPRS', 'GROUP_EXPR'}],
    'GROUP_EXPR': [node_group['EXPR']],
    'EQ': [node_group['EXPR'], node_group['EXPR']],
    'DOT': ['SYMBOL', 'SYMBOL'],
    'SUM': [node_group['EXPR']],
    'SYMBOL': [None], # Special case.
}

def all_node_types():
    defined_nodes = set(node_productions.keys())
    for production_item in node_productions.values():
        for node_type_spec in production_item:
            if isinstance(node_type_spec, set):
                defined_nodes |= node_type_spec
            elif isinstance(node_type_spec, str):
                defined_nodes.add(node_type_spec)
            elif isinstance(node_type_spec, type(None)):
                pass
            else:
                raise ValueError(
                    'Bad encoding type in node production map: ' + str(type(node_type_spec))
                )

    return defined_nodes

def undefined_node_types():
    return all_node_types() - set(node_productions.keys())

@id_memoize
def syntax_valid(node):
    node_type = node[0]
    if node_type == 'SYMBOL':
        return (
            len(node[1:]) == 1 and
            isinstance(node[1], str)
        )
    else:
        return (
            node_type in node_productions and
            len(node_productions[node_type]) == len(node[1:]) and
            all((child_node[0] == child_node_type) or (child_node[0] in child_node_type)
                for child_node, child_node_type in zip(node[1:], node_productions[node_type])
            ) and
            all(syntax_valid(child_node)
                for child_node in node[1:])
        )

def tree_depth(node, dynamic_depth=True):
    """
    Total depth of the tree.

    :param AST node: AST to measure.
    :param dynamic_depth bool: Use custom height weights defined by
        sql_ast.node_type_depth?
    :rtype: int
    :return: Depth of tree as a number.

    :Example:
    >>> tree_depth
    """
    if dynamic_depth:
        node_height = node_type_depth[node[0]]
    else:
        node_height = 1

    return node_height + max([
        tree_depth(child_node, dynamic_depth=dynamic_depth)
        for child_node in node[1:]
        if isinstance(child_node, list)
    ] + [0])

@id_memoize
def tree_map(node, func, func_args=None, func_kwargs=None):
    func_args = func_args or []
    func_kwargs = func_kwargs or {}

    node_type = node[0]
    node_children = node[1:]
    node_func_value = func(node, *func_args, **func_kwargs)
    return [
        node_func_value,
        node_type,
    ] + [
        tree_map(node_child, func, func_args, func_kwargs) if isinstance(node_child, list) else node_child
        for node_child in node_children
    ]

# Tree-map with custom push-down kernels for debugging.

def tree_heights(node, dynamic_depth=True, depth=0):
    node_type = node[0]
    if dynamic_depth:
        node_height = node_type_depth[node_type]
    else:
        node_height = 1

    return [
        depth,
        node_type,
    ] + [
        (tree_heights(
            child_node,
            dynamic_depth=dynamic_depth,
            depth=depth + node_height
        )
         if isinstance(child_node, list)
         else child_node)
        for child_node in node[1:]
    ]
