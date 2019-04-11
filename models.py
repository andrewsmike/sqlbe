from collections import namedtuple
from tabulate import tabulate

__all__ = [
    'Relation',
    'Example',
]

class Relation(namedtuple('Relation', ['select', 'columns', 'rows'])):
    def __str__(self):
        return tabulate(
            [
                list(self.columns),
            ] + list(map(list, self.rows)),
            headers="firstrow",
            missingval="NULL",
            tablefmt="grid",
        )

class Example(namedtuple('Example', ['input_relations', 'output_relation'])):
    def __str__(self):
        return '\n'.join([
            "Input relations:",
        ] + [relation_name + ' relation:\n' + str(relation)
             for relation_name, relation in self.input_relations] + [
            "Output:",
            str(self.output_relation),
        ])
    

