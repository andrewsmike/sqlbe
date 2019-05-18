from models import Relation, Example

example_tables = {
    'student': Relation(
        select=None,
        columns=('id', 'name', 'department_id'),
        rows=frozenset([
            (1, 'Mike', 1),
            (2,  'Sam', 1),
            (3, 'Drew', 2),
            (4, 'Jane', 2),
            (5, 'Shaw', 2),
            (6, 'Mike', 2),
        ]),
    ),
    'department': Relation(
        select=None,
        columns=('id', 'name', 'funding'),
        rows=frozenset([
            (1, 'Chemistry', 100000),
            (2,   'CompSci',  53243),
            (3,   'Physics', 900000),
        ]),
    ),
    'department_students': Relation(
        select="""
        SELECT department.name AS department_name, SUM(1) AS students
          FROM student
          LEFT JOIN department
            ON department.id = student.department_id
         GROUP BY department.name
        """,
        columns=('department_name', 'students'),
        rows=frozenset([
            ('Chemistry', 2),
            ('CompSci', 4),
        ]),
    ),
    'all_department_students': Relation(
        select="""
        SELECT department.name AS department_name, SUM(1) AS students
          FROM department
          LEFT JOIN student
            ON department.id = student.department_id # Can't notice the name similarity.
         GROUP BY department.name
        """,
        columns=('department_name', 'students'),
        rows=frozenset([
            ('Chemistry', 2),
            ('CompSci', 4),
            ('Physics', 0),
        ]),
    ),
    'student_funding': Relation(
        select="""
        SELECT student.name AS name, department.funding AS department_funding
          FROM student
          JOIN department
            ON department.id = student.department_id # Can't notice the name similarity.
         GROUP BY student.name
        """,
        columns=('department_name', 'students'),
        rows=frozenset([
            ('Chemistry', 2),
            ('CompSci', 4),
            ('Physics', 0),
        ]),
    ),
    'student_name_stats': Relation(
        select="""
        SELECT student.name AS name, COUNT(DISTINCT student.student_id) AS students, AVG(department.funding) AS avg_department_funding
          FROM student
          JOIN department
            ON department.id = student.department_id # Can't notice the name similarity.
         GROUP BY student.name
        """,
        columns=('name', 'students', 'avg_department_funding'),
        rows=frozenset([
            ('Mike', 2,  76621),
            ( 'Sam', 1, 100000),
            ('Drew', 1,  53243),
            ('Jane', 1,  53243),
            ('Shaw', 1,  53243),
        ]),
    ),
}

student_dept_input_relations = frozenset([
    ('student', example_tables['student']),
    ('department', example_tables['department']),
])

problems = [
    Example(
        input_relations=student_dept_input_relations,
        output_relation=example_tables['department_students'],
    ),
    Example(
        input_relations=student_dept_input_relations,
        output_relation=example_tables['all_department_students'],
    ),
    Example(
        input_relations=student_dept_input_relations,
        output_relation=example_tables['student_funding'],
    ),
    Example(
        input_relations=student_dept_input_relations,
        output_relation=example_tables['student_name_stats'],
    ),
]
