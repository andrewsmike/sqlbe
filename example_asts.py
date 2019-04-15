"""
Example SQL ASTs.
Used for debugging, testing, and demonstrating valid ASTs.
"""

__all__ = [
    'examples'
]

examples = {
    'department_students': (
        ['SELECT_AGG',
         [
             'SELECT_EXPRS', 
             ['EXPR_AS',
              ['DOT',
               ['SYMBOL', 'department'],
               ['SYMBOL', 'name'],
              ],
              ['SYMBOL', 'department_name'],
             ],
             ['EXPR_AS',
              ['SUM',
               ['SYMBOL', '1'],
              ],
              ['SYMBOL', 'students'],
             ],
         ],
         [
             'JOINS',
             ['FROM',
              ['SYMBOL', 'students'],
             ],
             ['LEFT_JOIN_ON',
              ['SYMBOL', 'department'],
              ['EQ',
               ['DOT',
                ['SYMBOL', 'department'],
                ['SYMBOL', 'id'],
               ],
               ['DOT',
                ['SYMBOL', 'student'],
                ['SYMBOL', 'department_id'],
               ],
              ],
             ],
         ],
         [
             'GROUP_EXPR',
             ['DOT',
              ['SYMBOL', 'student'],
              ['SYMBOL', 'name'],
             ],
         ],
        ]
    ),
}
