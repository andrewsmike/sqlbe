"""
Tools related to query plans.
- 
"""
from models import Relation

__all__ = [
    'enumerate_sql',
    'eval_sql',
]

def enumerate_sql(input_relations):
    raise NotImplementedError

def eval_sql(sql, input_relations):
    raise NotImplementedError

def typing_validate_sql(program, input_relations):
    pass

@id_memoize
def data_validate_sql(program, input_relations, output_relation):
    pass




# Question: Do I want to enumerate over logical plans or syntax?
# Answer: Syntax.
# Question: Can I make them isomorphic?
# Answer: ... No, unfortunately.
# Question: Can I treat the syntax as a superset of the logical plan?
# Answer: ... I think so? What other restrictions are there? You're just representing
#     operation configuration, beyond inputs, as nodes.
"""
class PartialSyntaxElement(object):
    def __init__(self, rules):
        self.rules = rules
    def __or__(self, other):
        if isinstance(other)

class SyntaxElement(object):
    def __init__(self, name):
        pass
    def __or__(self, other):
        return PartialSyntaxElement(
            [[self]],
        ) | other


# There are contextual/typing constraints - Column names, length, etc.
# Maybe we could push typing information as we descend the AST, then do a second verification check?
# After that, we try executing on a test case.
sql_syntax = {
    'query': either(
        'select',
        'union',
        'set_diff',
        'intersection',
    ),
    'select': either(
    ),
}

"""
"""
Example trees:

"""

"""
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
