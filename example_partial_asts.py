"""
Example partial SQL ASTs.
Used for debugging and testing.
"""

from enumerate import (
    PartialAst,
)

__all__ = [
    'example_partial_asts'
]

example_partial_asts = {
    'empty': PartialAst(
        nodes=[],
        max_depth=0,
        open_node_indices=frozenset(),
    ),
    'root': PartialAst(
        nodes=[
            ('SELECT_AGG', 1, None),
        ],
        max_depth=1,
        open_node_indices=frozenset({0}),
    ),
    "level_1": PartialAst(
        nodes=[
            ('SELECT_AGG', 1, [1, 2, 3]),
            ('SELECT_EXPRS', 2, None),
            ('TOP_JOINS', 2, None),
            ('EXPR', 2, None),
        ],
        max_depth=2,
        open_node_indices=frozenset({1, 2, 3}),
    )
}
