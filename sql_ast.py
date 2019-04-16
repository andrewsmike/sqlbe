"""
Tools related to ASTs and the SQL CFG.

CFG definition:
- Each node type has a single production rule spec.
- Each node type's production rule is structured as a sequence of child node links and their possible types.

Example:
SELECT = [{SELECT_AGG, SELECT_DUAL}]
SELECT_AGG = [{SELECT_EXPRS, EXPR_AS}, {JOINS, FROM}, {GROUP_EXPRS, GROUP_EXPR}]
SELECT_DUAL = [{SELECT_EXPRS, EXPR_AS}]

The SQL CFG:
- Targetting a simple SELECT or SELECT GROUP BY statement.
- One or more JOINs, not many JOIN types specified.
- Not many types of expression operators available.

TODO:
- CFG specifying patterns (left/right recursion/repetition)
- Push in / pull out typing info at will
- Collapse some nodes on creation for cleaner AST?
"""
from collections import defaultdict

from tools import id_memoize

__all__ = [
    "sql_cfg",
    "sql_heuristic_weight",

    "all_node_types",
    "undefined_node_types",

    "syntax_valid",
    "tree_depth",
    "tree_map",
]


# SQL CFG spec and heuristic weights for depth measurements
sql_cfg = {
    'SELECT_AGG': [{'SELECT_EXPRS', 'EXPR_AS'}, {'TOP_JOINS', 'FROM'}, {'GROUP_EXPRS', 'EXPR'}],
    'SELECT_AGG_WHERE': [{'SELECT_EXPRS', 'EXPR_AS'}, {'TOP_JOINS', 'FROM'}, {'GROUP_EXPRS', 'EXPR'}, 'EXPR'],
    'SELECT_EXPRS': [{'EXPR_AS'}, {'SELECT_EXPRS', 'EXPR_AS'}],
    'EXPR_AS': ['EXPR', 'SYMBOL'],
    'EXPR': [{'EQ', 'DOT', 'SYMBOL'}],
    'TOP_JOINS': ['FROM', {'JOINS', 'LEFT_JOIN_ON'}],
    'JOINS': ['LEFT_JOIN_ON', {'JOINS', 'LEFT_JOIN_ON'}],
    'FROM': ['SYMBOL'],
    'LEFT_JOIN_ON': ['SYMBOL', 'EXPR'],
    'GROUP_EXPRS': ['EXPR', {'GROUP_EXPRS', 'EXPR'}],
    'EQ': ['EXPR', 'EXPR'],
    'DOT': ['SYMBOL', 'SYMBOL'],
    'SUM': ['EXPR'],
    'SYMBOL': [None], # Special case. Accepts anything as a direct argument.
}

sql_heuristic_weight = defaultdict(lambda: 4, {
    'JOINS': 30,
    'GROUP_EXPRS': 20,
    'SEL_EXPRS': 10,
})

def all_node_types(cfg_spec):
    """
    The set of all node types in a CFG spec.
    Mostly useful for debugging CFGs.

    :param dict(str, list(str|set)) cfg_spec: CFG to evaluate.
    :rtype: set
    :return: Set of node types in this CFG.
    """
    node_types = set(cfg_spec.keys())
    for production_item in cfg_spec.values():
        for node_type_spec in production_item:
            if isinstance(node_type_spec, set):
                node_types |= node_type_spec
            elif isinstance(node_type_spec, str):
                node_types.add(node_type_spec)
            elif isinstance(node_type_spec, type(None)):
                pass
            else:
                raise ValueError(
                    'Bad encoding type in node production map: ' + str(type(node_type_spec))
                )

    return frozenset(node_types)

def undefined_node_types(cfg_spec):
    """
    The set of undefined, but referenced, node types in a CFG spec.

    :param dict(str, list(str|set)) cfg_spec: CFG to evaluate.
    :rtype: frozenset
    :return: Frozenset of undefined, but referenced, node types in this CFG spec.
    """
    return all_node_types(cfg_spec) - frozenset(cfg_spec.keys())

@id_memoize
def syntax_valid(node, cfg_spec):
    """
    Is this AST _syntactically_ valid?

    :param AST node: AST subtree to inspect.
    :param dict(str, list(str|set)) cfg_spec: CFG for the AST.
    :rtype: bool
    :return: Is this AST syntactically valid according to this CFG?
    """
    node_type, node_children = node[0], node[1:]

    return (
        node_type in cfg_spec
        and len(cfg_spec[node_type]) == len(node_children)
        and all((child_node[0] == child_node_type) or
                (child_node[0] in child_node_type) or
                (child_node_type is None)
                for child_node, child_node_type in (
                        zip(node_children, cfg_spec[node_type])
                )
        )
        and all(syntax_valid(child_node, cfg_spec)
                for child_node in node_children)
    )


@id_memoize
def tree_depth(node, node_type_weight=None):
    """
    The total depth of an AST.

    :param AST node: AST subtree in question.
    :param dict(str, int) node_type_weight:
        Custom weights to use for each node type.
        Some things should be used more sparingly than others, and add to depth.
    :rtype: int
    :return: Depth of this AST subtree.

    :Example:
    >>> from example_asts import example_asts
    >>> example_ast = list(example_asts.values())[0] # Optionally pprint this.

    >>> from collections import defaultdict
    >>> from sql_ast import tree_depth
    >>> tree_depth(example_ast, defaultdict(lambda: 5, {
            "SELECT_AGG": 200,
            "JOINS": 50,
            "TOP_JOINS": 50,
        }))
        280
    """
    node_type, node_children = node[0], node[1:]

    if node_type_weight:
        node_weight = node_type_weight[node_type]
    else:
        node_weight = 1

    return node_weight + max([
        tree_depth(child_node, node_type_weight=node_type_weight)
        for child_node in node_children
        if isinstance(child_node, list)
    ] + [0])

@id_memoize
def tree_map(node, func, args=None, kwargs=None):
    """
    Insert the result of a function into every list in the AST for debugging.

    :param AST node: Subtree to work against.
    :param callable(node, *args, **kwargs) -> obj func:
        Function to apply to all AST subtrees.

    :rtype: "Debugging" AST, format: [debug_info, type, children...]
    :return: Debugging AST for pretty printing.

    :Example:
    >>> from example_asts import example_asts
    >>> example_ast = list(example_asts.values())[0] # Optionally pprint this.

    >>> from pprint import pprint
    >>> from sql_ast import tree_depth, tree_map, sql_cfg
    >>> pprint(tree_map(example_ast, tree_depth, args=[sql_node_productions]))
    """
    func_args = func_args or []
    func_kwargs = func_kwargs or {}

    node_type, node_children = node[0], node[1:]
    node_func_value = func(node, *func_args, **func_kwargs)
    return [
        node_func_value,
        node_type,
    ] + [
        tree_map(node_child, func, func_args, func_kwargs)
        if isinstance(node_child, list)
        else node_child
        for node_child in node_children
    ]

def query_str(
        select_exprs,
        joins,
        where_exprs,
        group_by_exprs,
        order_by_exprs,
        limit_exprs,
):
    select_str = "SELECT " + ",\n        ".join(select_exprs)

    joins_str = ""
    first_join = True
    for join_type, join_table, join_on_exprs in joins:
        assert join_type in ("INNER", "LEFT")

        if first_join:
            assert join_type == "INNER"
            join_type_str = "   FROM"
            where_exprs += join_on_exprs
        elif join_type == "INNER":
            join_type_str = "\n  INNER JOIN"
        elif join_type == "LEFT":
            join_type_str = "\n   LEFT JOIN"

        first_join = False

        joins_str.append((
            "{join_type} {join_table}"
            "{join_on}"
        ).format(
            join_type=join_type_str,
            join_table=join_table,
            join_on=(
                "" if not join_on_exprs else
                ("\n     ON " + "\n    AND ".join(join_on_exprs))
            ),
        ))

    where_str = "" if not where_exprs else (
        "  WHERE " + "\n    AND ".join(where_exprs)
    )

    group_by_str = "" if not group_by_exprs else (
        "  GROUP BY " + "\n    AND ".join(group_by_exprs)
    )

    order_by_str = "" if not order_by_exprs else (
        "  ORDER BY " + "\n    AND ".join(order_by_exprs)
    )

    limit_str = "" if not limit_exprs else (
        "  LIMIT " + ", ".join(limit_exprs)
    )

    return "\n".join([
        select_str,
        joins_str,
        where_str,
        group_by_str,
        order_by_str,
        limit_str,
    ])
            
        

def ast_query_str(node, indent=''):
    select_exprs
    return query_str(
        select_exprs=[],
        joins=[],
        where_exprs=[],
        group_by_exprs=[],
        order_by_exprs=[],
        limit_exprs=[],
    )

