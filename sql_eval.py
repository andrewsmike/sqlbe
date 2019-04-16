"""
Evaluate SQL.

TODO:
- Build separate execution plan datastructure (SIMPLIFY CODE)
- Build out better tree iteration functionals
"""
from models import Relation

__all__ = [
    'eval_sql',
]

def enumerate_sql(input_relations):
    raise NotImplementedError

def eval_sql(node, input_relations):
    node_type, node_children = node[0], node[1:]
    pass

"""
There's a subset of AST elements that roughly correspond to the query execution plan.
They all return relationships. These functions distill out these members.
.......
This is pretty much just laying out the query plan tree on the return stack of these functions.
Maybe it'd be better if I just reencoded these trees.
...
I'll see this approach through, then switch to properly genericized trees.
"""

def node_type(type_match):
    def node_type_assertion_decorator(func):
        @wraps(func)
        def node_type_asserted_wrapped(node, *args, **kwargs):
            assert node[0] == type_match or node[0] in type_match
            return func(node, *args, **kwargs)
        return node_type_asserted_wrapped
    return node_type_assertion_decorator

def children_types(*type_matches):
    def children_type_assertion_decorator(func):
        @wraps(func)
        def children_type_asserted_wrapped(node, *args, **kwargs):
            children = node[1:]
            assert len(children) == len(type_matches)
            for type_match, child in zip(type_matches, children):
                assert child[0] == type_match or child[0] in type_match
            return func(node, *args, **kwargs)
        return children_type_asserted_wrapped
    return children_type_assertion_decorator

def expr_eval(columns, row, expr):
    pass


@node_type({'EXPR_AS', 'EXPR_AS'})
@children_types({'EXPR'}, 'SYMBOL')
def flattened_expr_as(expr_as):
    node_type, node_children = select_exprs[0], select_exprs[1:]
    expr_child, as_child = node_children

    return (as_child[1], expr_child[1])

@node_type('SELECT_EXPR')
def flatted_select_exprs(select_exprs):
    node_type, node_children = select_exprs[0], select_exprs[1:]

    exprs = [flattened_expr_as(node_children[0])]
    if node_children[1][0] == 'SELECT_EXPRS':
        exprs = exprs + flattened_select_exprs(node_children[1])
    else:
        exprs = exprs + [flattened_expr_as(node_children[1])]

    return exprs

def select_view(src, select_exprs):
    """
    Take a relation and non-aggregating SELECT_EXPRS as input, output new relation.
    """
    select_column_exprs = flattened_select_exprs(select_exprs)

    cols = [
        column
        for column, expr in select_column_exprs
    ]

    return Relation(
        select=None,
        columns=cols,
        rows=frozenset(
            tuple(
                expr_eval(src.columns, row, expr)
                for column, expr in select_column_exprs
            )
            for row in src.rows
        ),
    )


def where(src, cond_expr):
    """
    Take a relation and a filtering expression, return a relation with all non-matching
    rows filtered out.
    """
    return Relation(
        select=None,
        columns=src.columns,
        rows=frozenset(
            row
            for row in src.rows
            if expr_eval(src.columns, row, cond_expr)
        ),
    )

def joins(input_relations, joins):
    pass

def agg(src, agg_columns):
    

    return Relation(
        select=None,
        columns=columns,
        rows=None,
    )

@op
def select(input_relations, select_exprs, joins):
    return select_view(joins(input_relations, joins), select_exprs)
@op
def select_where(input_relations, select_exprs, joins, where_expr):
    return where(select(input_relations, select_exprs, joins), where_expr)

"""
Manipulate EXPR trees that have an aggregating function inside somewhere.
Separate out 1000 * SUM(FLOOR(humans/1000)) into pre:"FLOOR(humans/1000)" and post:"1000 * pre" 
"""
def pre_agg_select_expr(node):
    """
    Returns node, HitAggregator.
    Bubble up the expression, returning the tree.
    Any aggregators will push up the HitAggregator flag.
    From there on, the child with the HitAggregator flag wins.
    """
    node_type, node_children = node[0], node[1:]

    if node_type == 'SUM': # when hitting agg
        return node_children[0], True

    children_pre_aggd_exprs = map(pre_agg_select_expr, node_children)
    hit_agg_exprs = [
        expr
        for expr, hit_agg in children_pre_aggd_exprs
        if hit_agg
    ]
    if len(hit_agg_exprs) > 1:
        raise ValueError('Cannot have multiple aggregating expressions yet.')
    elif len(hit_agg_exprs) == 1:
        return hit_agg_exprs[0], True
    else:
        return node, False

@node_type('SELECT_EXPRS')
def pre_agg_select_exprs(select_exprs):
    """
    Return a SELECT_EXPRs node with all aggregating expressions replaced with the pre-aggregation
    column expression under the same name, prefixed with '_agg_', and a list of True/False pairs for
    whether each column has an aggregating function.
    """
    left, right = select_exprs[1:]

    left_pre_agg_expr, left_has_agg = pre_agg_select_expr(left[1])
    left = ['EXPR_AS', left_pre_agg_expr, ('_agg_' + left[2]) if left_has_agg else left[2]]

    if right[0] == 'SELECT_EXPRS':
        right, right_agg_list = pre_agg_select_exprs(right)
    else:
        right_pre_agg_expr, right_has_agg = pre_agg_select_expr(right[1])

        right = ['EXPR_AS', right_pre_agg_expr, ('_agg_' + right[2]) if right_has_agg else right[2]]
        right_agg_list = [right_has_agg]

    return [
        'SELECT_EXPRS',
        left,
        right,
    ], ([left_has_agg] + right_agg_list)

def post_agg_select_expr(node, name):
    node_type, node_children = node[0], node[1:]

    if node_type == 'SUM':
        return ['SYMBOL', '_agg_' + name]

    return [
        node_type,
    ] + map(lambda child: post_agg_select_expr(child, name), node_children)

@node_type('SELECT_EXPRS')
def post_agg_select_exprs(select_exprs):
    left, right = select_exprs[1:]

    left = ['EXPR_AS', post_agg_select_expr(left[1], left[2]), left[2]]

    if right[0] == 'SELECT_EXPRS':
        right = post_agg_select_exprs(right)
    else:
        right = ['EXPR_AS', post_agg_select_expr(right[1], right[2]), right[2]]

    return [
        'SELECT_EXPRS',
        left,
        right,
    ]

@op
def select_agg(input_relations, select_exprs, joins, group_exprs):
    pre_agg_exprs, agg_columns = pre_agg_select_exprs(select_exprs)

    column_select_exprs = flattened_select_exprs(select_exprs)
    select_expr_set = {
        expr
        for column, expr in column_select_exprs
    }
    # TODO: Fix assertions.
    # assert all(group_expr in select_expr_set
    #            for group_expr in group_exprs)
    # assert all(
    #     for is_agg_column, (col, expr) in zip(agg_columns, column_select_exprs)
    # )

    return (
        select_view(
            agg(
                select(
                    input_relations,
                    pre_agg_exprs
                    joins
                ),
                agg_columns,
            ),
            post_agg_select_exprs(select_exprs)
        )
@op
def select_agg_where(input_relations, select_exprs, joins, where_expr, group_exprs):
    return (
        where(
            select_agg(
                input_relations, select_exprs, joins, group_exprs
            ),
            where_expr,
        )
    )
