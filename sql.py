"""
This should be done as a CNF and a series of eval functions (with decorators indicating important invariances.)
"""
from tying import Set

from models import Relation

__all__ = [
    'enumerate_sql',
    'eval_sql',
]

def enumerate_sql(input_relations):
    raise NotImplementedError

def eval_sql(sql, input_relations):
    raise NotImplementedError

# - I need a better type definition and interface for intermediate tuple trees + their metadata... do I?
# - I need constraints that are propagated down
# In most cases where we have joining or filtering columns, we really want expressions (in fact, multiple expressions.) Should this get shoved into a lower select? Potentially implying an upper select? UGH.
# Starting simple: SELECT filters, you have a command to eval, etc.

def subtuple(rel, elem, keys):
    return tuple(
        elem[rel.columns.index(key)]
        for key in keys
    )

def row_append(*args):
    return tuple(sum(args, []))

@op
@same_columns
def union(left: Relation, right: Relation):
    return left | right

@op
@same_columns
def difference(left: Relation, right: Relation):
    return left - right

@op
@all_columns
def join(left: Relation, right: Relation, key_cols: Set[str]):
    return Relation(
        select=None,
        columns=
        rows=frozenset(
            row_append(left_row, right_row)
            for left_row in left.rows
            for right_row in right.rows
            if all(left_row[left.columns.index(col)] == right_row[right.columns.index(col)]
                   for col in key_cols)
        ]
    )

@op
@needs_columns(key_cols)
def left_join(left: Relation, right: Relation, key_cols: Set[str]):
    key_order = sorted(key_cols)

    result_rows = set()
    for left_row in left.rows:
        left_key = subtuple(left, left_row, key_order)
        matches = 0
        for right_row in right.rows:
            if left_key == subtuple(right, right_row, key_order):
                result_rows.add(row_append(left_row, right_row))
                matches += 1
        if not matches:
            result_rows.add(
                row_append(left_row,
                           [None] * len(right.columns))
            )

    return result_rows

# Not represented: Cols is subset of str.
@op
def select(source: Relation, cols: Set[str]):
    return 
    raise NotImplementedError

# Missing type annotation: isinstance(source[key_col], bool) == True
@op
def where(source: Relation, key_col: str):
    return frozenset(row for row in source if row[key_col] == True)

# Need to combine aggregation step with aggregation functions.
@op
def group(source: Relation, key_cols: Set[str]):
    raise NotImplementedError

@op
def sum(source: Relation, key_cols: Set[str]):
    raise NotImplementedError

@op
def avg(source: Relation, key_cols: Set[str]):
    raise NotImplementedError

# Formula
@op
def eq(source: Relation, key_cols: Set[str]):
    raise NotImplementedError

@op
def const(source: Relation, key_cols: Set[str]):
    raise NotImplementedError

"""
operators = {
        'subset': subset_operator, # Parameterized by subset of columns to keep
        'filter': filter_operator, # Parameterized by column
        'expr': expr_operator, # Parameterized by  basic operator tree (<, =, AND, OR, NOT, SYMBOL) and columns
        'agg': agg_operator, # Parameterized by type and columns (sum, count, average, maximum, and minimum)
    'num_expr': {
        'add': add_operator,
        'sub': sub_operator,
        'mul': mul_operator,
        'div': div_operator,
    },
    'bool_expr': {
        'eq': eq_operator,
        'lt': lt_operator,
        'gt': gt_operator,

        'or': or_operator,
        'and': and_operator,
        'not': not_operator,
    }
"""
