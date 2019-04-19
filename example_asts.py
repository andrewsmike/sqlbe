"""
Example SQL ASTs.
Used for debugging, testing, and demonstrating valid ASTs.
"""

__all__ = [
    'example_asts'
]

example_asts = {
    'department_students': (
        ['SELECT_AGG',
         [
             'SELECT_EXPRS', 
             ['EXPR_AS',
              ['EXPR',
               ['DOT',
                ['SYMBOL', 'department'],
                ['SYMBOL', 'name'],
               ],
              ],
              ['SYMBOL', 'department_name'],
             ],
             ['EXPR_AS',
              ['EXPR',
               ['SUM',
                ['EXPR', ['SYMBOL', '1']],
               ],
              ],
              ['SYMBOL', 'students'],
             ],
         ],
         [
             'TOP_JOINS',
             ['FROM',
              ['SYMBOL', 'students'],
             ],
             ['LEFT_JOIN_ON',
              ['SYMBOL', 'department'],
              ['EXPR',
               ['AND', ['EXPR', ['SYMBOL', 'some_symbol']], ['EXPR', [
                   'EQ',
                   ['EXPR',
                    ['DOT',
                     ['SYMBOL', 'department'],
                     ['SYMBOL', 'id'],
                    ],
                   ],
                   ['EXPR',
                    ['DOT',
                     ['SYMBOL', 'student'],
                     ['SYMBOL', 'department_id'],
                    ],
                   ],
               ],],],
              ],
             ],
         ],
         [
             'EXPR',
             ['DOT',
              ['SYMBOL', 'department'],
              ['SYMBOL', 'name'],
             ],
         ],
        ]
    ),
}
