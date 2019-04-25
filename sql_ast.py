"""
CFG / AST tools, SQL CFG, and a SQL AST -> Query string mapper.

TODO:
- CFG specifying patterns (left/right recursion/repetition)
- Push in / pull out typing info at will
- Collapse some nodes on creation for cleaner AST? (EXPR deflate.)
- SQL query -> SQL AST? (This would be _awesome_ for testing.
    I could also use tree enumeration to test the encode/decode functions
    against each other.)
"""
from collections import defaultdict
from typing import (
    List,
    Optional,
    Set,
    Tuple,
)
from itertools import chain

from tools import id_memoize

__all__ = [

    "all_node_types",
    "undefined_node_types",

    "syntax_valid",
    "tree_depth",
    "tree_map",

    "sql_entry_tokens",
    "sql_cfg",
    "sql_heuristic_weight",

    "sql_query_str"
]

# SQL CFG spec and heuristic weights for depth measurements
"""
CFG specs:
- Each node type has a single production rule spec.
- Each node type's production rule is structured as a sequence of child node links and their possible types.

CFG example:
SELECT = [{SELECT_AGG, SELECT_DUAL}]
SELECT_AGG = [{SELECT_EXPRS, EXPR_AS}, {JOINS, FROM}, {GROUP_EXPRS, GROUP_EXPR}]
SELECT_DUAL = [{SELECT_EXPRS, EXPR_AS}]
"""

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
    Is this AST subtree _syntactically_ valid?

    :param AST node: AST subtree to inspect.
    :param dict(str, list(str|set)) cfg_spec: CFG for the AST.

    :rtype: bool
    :return: Is this AST syntactically valid according to this CFG?

    :Example:
    >>> from sql_ast import sql_entry_tokens, sql_cfg

    >>> def sql_program_syntax_valid(program):
            return (
                program[0] in sql_entry_tokens and
                syntax_valid(program, sql_cfg)
            )
    >>> my_subtree = ['SYMBOL', 'departments']

    >>> sql_program_syntax_valid(my_subtree)
    False
    >>> syntax_valid(my_subtree, sql_cfg)
    True
    """
    node_type, node_children = node[0], node[1:]

    if node_type == "SYMBOL":
        return len(node_children) == 1 and isinstance(node_children[0], str)

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
        Optional, defaults to unifrom weights (1).
    :rtype: int
    :return: Depth of this AST subtree.

    :Example:
    >>> from example_asts import example_asts
    >>> example_ast = example_asts['department_students']

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

    WARNING: ID memoized. Don't mutate anything going into or coming out of this function.

    :param AST node: Subtree to work against.
    :param callable(node, *args, **kwargs) -> obj func:
        Function to apply to all AST subtrees.

    :rtype: "Debugging" AST, format: [debug_info, type, children...]
    :return: Debugging AST for pretty printing.

    :Example:
    >>> from example_asts import example_asts
    >>> example_ast = example_asts['department_students']

    >>> from pprint import pprint
    >>> from sql_ast import tree_depth, tree_map, sql_cfg, sql_heuristic_weight
    >>> pprint(tree_map(example_ast, tree_depth, args=[sql_heuristic_weight]))
    [32,
     'SELECT_AGG',
     [20,
      'SELECT_EXPRS',
      [16,
       'EXPR_AS',
       [12, 'EXPR', [8, 'DOT', [4, 'SYMBOL', 'department'], [4, 'SYMBOL', 'name']]],
       [4, 'SYMBOL', 'department_name']],
      [16,
       'EXPR_AS',
       [12, 'SUM', [8, 'EXPR', [4, 'SYMBOL', '1']]],
       [4, 'SYMBOL', 'students']]],
     [28,
      'TOP_JOINS',
      [8, 'FROM', [4, 'SYMBOL', 'students']],
      [24,
       'LEFT_JOIN_ON',
       [4, 'SYMBOL', 'department'],
       [20,
        'EXPR',
        [16,
         'EQ',
         [12, 'EXPR', [8, 'DOT', [4, 'SYMBOL', 'department'], [4, 'SYMBOL', 'id']]],
         [12,
          'EXPR',
          [8, 'DOT', [4, 'SYMBOL', 'student'], [4, 'SYMBOL', 'department_id']]]]]]],
     [12, 'EXPR', [8, 'DOT', [4, 'SYMBOL', 'student'], [4, 'SYMBOL', 'name']]]]
    """
    args = args or []
    kwargs = kwargs or {}

    node_type, node_children = node[0], node[1:]

    node_func_value = func(node, *args, **kwargs)

    return [
        node_func_value,
        node_type,
    ] + [
        tree_map(node_child, func, args=args, kwargs=kwargs)
        if isinstance(node_child, list)
        else node_child
        for node_child in node_children
    ]

def ast_flatten(node,
                type_blacklist : Optional[Set[str]]=None,
                type_whitelist : Optional[Set[str]]=None):
    """
    The traversal-sorted list of the top-most nodes of a matching type.
    Used to flatten multiple (potentially unbalanced) levels of an AST.

    Assumes all descent paths eventually reach a matching node.

    You may only specify a whitelist or a blacklist.

    If the top-level node is a matching node, return [top_node].

    :param AST node: Subtree to iterate across.
    :param type_whitelist: Types of nodes to return.
        May not be specified with blacklist.
    :param type_blacklist: Types of nodes to ignore.
        May not be specified with whitelist.

    :rtype: List(AST)
    :return: List of the top-most matching nodes in traversal order.

    :Example:
    >>> from pprint import pprint
    >>> example_subtree = [
            "IF",
            ["EXPR", ["=", ["EXPR", ...], ["EXPR", ...]]], # Cond
            ["EXPR", ...], # A
            ["EXPR", ...], # B
        ]
    >>> pprint(list(ast_flatten(example_subtree, type_whitelist={'EXPR'})))
    [['EXPR', ['=', ['EXPR', ...], ['EXPR', ...]]], # Cond
     ['EXPR', ...], # A
     ['EXPR', ...]] # B
    >>> # Notice how the Cond subtree is _NOT_ explored or duplicated.
    """
    node_type, node_children = node[0], node[1:]

    assert bool(type_whitelist) ^ bool(type_blacklist), (
        "The top-most AST nodes matching a type whitelist and "
        "blacklist makes no sense, only match on one criteria."
    ) if type_whitelist and type_blacklist else (
        "The top-most AST nodes need a matching criteria. Add a whitelist or a "
        "blacklist."
    )

    if ((type_whitelist and (node_type in type_whitelist)) or
        (type_blacklist and (node_type not in type_blacklist))):
        return [node]

    return chain(*[
        ast_flatten(child, type_whitelist=type_whitelist, type_blacklist=type_blacklist)
        for child in node_children
    ])

"""
SQL CFG and tools.

Notes about CFG:
- Targetting a simple SELECT or SELECT GROUP BY statement.
- One or more JOINs, not many JOIN types specified.
- Not many types of expression operators available.
"""
sql_entry_tokens = {'SELECT_AGG', 'SELECT_AGG_WHERE'}

sql_cfg = {
    'SELECT_AGG': [{'SELECT_EXPRS', 'EXPR_AS'}, {'TOP_JOINS', 'FROM'}, {'GROUP_EXPRS', 'EXPR'}],
    'SELECT_AGG_WHERE': [{'SELECT_EXPRS', 'EXPR_AS'}, {'TOP_JOINS', 'FROM'}, {'GROUP_EXPRS', 'EXPR'}, 'EXPR'],
    'SELECT_EXPRS': [{'EXPR_AS'}, {'SELECT_EXPRS', 'EXPR_AS'}],
    'EXPR_AS': ['EXPR', 'SYMBOL'],
    'EXPR': [{'EQ', 'DOT', 'SYMBOL', 'SUM', 'AND'}],
    'TOP_JOINS': ['FROM', {'JOINS', 'LEFT_JOIN_ON'}],
    'JOINS': ['LEFT_JOIN_ON', {'JOINS', 'LEFT_JOIN_ON'}],
    'FROM': ['SYMBOL'],
    'LEFT_JOIN_ON': ['SYMBOL', 'EXPR'],
    'GROUP_EXPRS': ['EXPR', {'GROUP_EXPRS', 'EXPR'}],
    'AND': ['EXPR', 'EXPR'],
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

# Helper for building SQL queries from SQL ASTs
def query_str(
        select_exprs : List[str]=None,
        joins : List[Tuple[str, str, List[str]]]=None,
        where_exprs : Optional[List[str]]=None,
        group_by_exprs : Optional[List[str]]=None,
        order_by_exprs : Optional[List[str]]=None,
        limit_exprs : Optional[List[str]]=None,
):
    """
    The subquery-free SQL query string corresponding to these arguments.

    :param select_exprs: List of SELECT expressions and aliases.
        Example: "SUM(blah)/SUM(1) AS avg_blah"
    :param joins: List of JOINs.
        Each JOIN is a tuple with:
        - The JOIN type ("INNER" or "LEFT")
        - The table with alias "my_db.departments AS student_department"
        - The JOIN ON expressions:
            ["student.department_id = student_department.id",
             "student_department.active = True"]
    :param where_exprs: List of WHERE expressions.
        Example: ["student.name = 'Mike'", "student.age < 21"]
    :param group_by_exprs: List of GROUP BY expressions.
        Example: ["student.year", "department.name"]
    :param order_by_exprs: List of ORDER BY expressions, with ASC/DESC.
        Example: ["year ASC", "cost DESC"]
    :param limit_exprs: List of LIMIT expressions.
        Example: ["40", "20"]

    :rtype: str
    :return: SQL query string with the given parameters and structure.

    :Example:
    >>> from sql_ast import query_ast
    >>> print(query_str(
            select_exprs=[
                "dept.name AS department_name",
                "SUM(1) AS students",
            ],
            joins=[
                ("INNER", "student", []),
                ("LEFT", "department AS debt", ["dept.id = student.department_id"]),
            ],
            where_exprs=["dept.name != 'admin'"],
            group_by_exprs=["dept.name"],
            order_by_exprs=["2 DESC"],
        ))
    SELECT dept.name AS department_name,
           SUM(1) AS students
      FROM student
      LEFT JOIN department AS debt
        ON dept.id = student.department_id
     WHERE dept.name != 'admin'
     GROUP BY dept.name
     ORDER BY 2 DESC
    """
    select_str = "SELECT " + ",\n       ".join(select_exprs)

    joins_str = ""
    first_join = True
    for join_type, join_table, join_on_exprs in joins:
        assert join_type in ("INNER", "LEFT")

        if first_join:
            assert join_type == "INNER"
            join_type_str = "  FROM"
            where_exprs += join_on_exprs
        elif join_type == "INNER":
            join_type_str = "\n INNER JOIN"
        elif join_type == "LEFT":
            join_type_str = "\n  LEFT JOIN"

        first_join = False

        joins_str += (
            "{join_type} {join_table}"
            "{join_on}"
        ).format(
            join_type=join_type_str,
            join_table=join_table,
            join_on=(
                "" if not join_on_exprs else
                ("\n    ON " + "\n   AND ".join(join_on_exprs))
            ),
        )

    where_str = "" if not where_exprs else (
        " WHERE " + "\n   AND ".join(where_exprs)
    )

    group_by_str = "" if not group_by_exprs else (
        " GROUP BY " + "\n   AND ".join(group_by_exprs)
    )

    order_by_str = "" if not order_by_exprs else (
        " ORDER BY " + "\n   AND ".join(order_by_exprs)
    )

    limit_str = "" if not limit_exprs else (
        " LIMIT " + ", ".join(limit_exprs)
    )

    query_parts = [
        part
        for part in [
                select_str,
                joins_str,
                where_str,
                group_by_str,
                order_by_str,
                limit_str,
        ]
        if part
    ]

    return "\n".join(query_parts)


# Functions to convert various subtree types into strings.
# Used to build queries from SQL ASTs.
def sql_expr_str(expr_node):
    """
    The SQL query string encoding for an expression subtree.
    Correctly handles any SQL query expression node type, so anything used
    in a formula is fair game.
    """
    node_type, node_children = expr_node[0], expr_node[1:]

    if node_type == "EXPR":
        return sql_expr_str(node_children[0])
    elif node_type == "DOT":
        left, right = node_children
        return sql_expr_str(left) + "." + sql_expr_str(right)
    elif node_type == "EQ":
        left, right = node_children
        return sql_expr_str(left) + " = " + sql_expr_str(right)
    elif node_type == "SYMBOL":
        return node_children[0] # SYMBOL DECODE POINT
    elif node_type == "SUM":
        return "SUM(" + sql_expr_str(node_children[0]) + ")"
    else:
        raise ValueError(
            "SQL AST expr node -> str logic missing for node type " + node_type
        )

def sql_group_by_exprs(group_by_node):
    """
    """
    for expr_node in ast_flatten(group_by_node, type_whitelist={"EXPR"}):
        yield sql_expr_str(expr_node)

def sql_select_exprs(select_exprs_node):
    """
    The list of SQL query SELECT ... AS ..., ... statements for a particular SQL
    SELECT_EXPRs subtree.
    """
    for expr_as_node in ast_flatten(select_exprs_node, type_whitelist={"EXPR_AS"}):
        node_type, (expr_node, symbol_node) = expr_as_node[0], expr_as_node[1:]

        assert node_type == "EXPR_AS"
        yield (
            "{expr} AS {alias}".format(
                expr=sql_expr_str(expr_node),
                alias=symbol_node[1], # SYMBOL DECODE POINT
            )
        )

def sql_and_exprs_strs(and_exprs_node):
    """
    The list of SQL query encoded expressions for each AND condition for an EXPR
    SQL subtree.
    """
    node_type, node_children = and_exprs_node[0], and_exprs_node[1:]

    assert node_type == "EXPR"

    expr_child_node = node_children[0]

    node_type, node_children = expr_child_node[0], expr_child_node[1:]

    if node_type != "AND":
        yield sql_expr_str(expr_child_node)
    else:
        for and_cond_node in ast_flatten(expr_child_node, type_blacklist={"AND"}):
            yield sql_expr_str(and_cond_node)

def sql_joins(joins_node):
    for join_node in ast_flatten(joins_node, type_whitelist={"FROM", "LEFT_JOIN_ON"}):
        
        node_type, node_children = join_node[0], join_node[1:]
        if node_type == "FROM":
            (table_name_node,) = node_children
            yield ("INNER", table_name_node[1], []) # SYMBOL DECODE POINT
        elif node_type == "LEFT_JOIN_ON":
            (table_name_node, join_on_expr_node) = node_children
            yield (
                "LEFT",
                table_name_node[1], # SYMBOL DECODE POINT
                list(sql_and_exprs_strs(join_on_expr_node)),
            )
        else:
            raise RuntimeError(
                "Missing logic to decode JOIN node type into str: " + node_type
            )

def sql_query_str(program):
    """
    The corresponding SQL query string for a particular SQL AST.

    :param AST program: SQL AST to render.

    :Example:
    >>> from example_asts import example_asts
    >>> example_ast = example_asts['department_students_weird_cond']

    >>> print(sql_query_str(example_ast))
    SELECT department.name AS department_name,
           SUM(1) AS students
      FROM students
      LEFT JOIN department
        ON some_flag
       AND department.id = student.department_id
     GROUP BY department.name
    """
    node_type, node_children = program[0], program[1:]
    assert node_type in sql_entry_tokens and syntax_valid(program, sql_cfg)

    if node_type == "SELECT_AGG":
        select_exprs_node, joins_node, group_by_exprs_node = node_children
        where_node = None
    elif node_type == "SELECT_AGG_WHERE":
        (select_exprs_node,
         joins_node,
         group_by_exprs_node,
         where_node) = node_children
    else:
        raise RuntimeError(
            "Missing node-type decoding logic for generating SQL query from AST."
        )

    return query_str(
        select_exprs=list(sql_select_exprs(select_exprs_node)),
        joins=list(sql_joins(joins_node)),
        where_exprs=list(sql_and_exprs_strs(where_node)) if where_node else [],
        group_by_exprs=list(sql_group_by_exprs(group_by_exprs_node)),
        order_by_exprs=[],
        limit_exprs=[],
    )

