from humanize import naturalsize
from pprint import pprint
from psutil import virtual_memory


from enumerate import (
    ast_enumerated,
    ast_from_partial_ast,
)

from sql_ast import (
    sql_query_str,
    sql_cfg,
    sql_entry_tokens,
    sql_heuristic_weight,
)


def report_search_status(next_ast, partial_ast_count):
    mem_stats = virtual_memory()
    print("<<<BEGIN SYSTEM STATISTICS>>>")
    print(("Partial ASTs: {partial_ast_count}\n"
           "Memory: {memory_used}/{memory_total} [{memory_percent}]\n"
           "Min complexity: {complexity}"
    ).format(
        partial_ast_count=partial_ast_count,
        memory_used=naturalsize(mem_stats.used),
        memory_total=naturalsize(mem_stats.total),
        memory_percent=str(mem_stats.percent),
        complexity=str(next_ast.complexity),
    ))
    print("Sampled AST:")
    pprint(ast_from_partial_ast(next_ast, allow_incomplete=True))
    print("<<<END SYSTEM STATISTICS>>>")

def sql_queries_enumerated():
    for sql_ast in ast_enumerated(
            sql_entry_tokens,
            sql_cfg,
            weights=sql_heuristic_weight,
            symbols=['student', 'department'],
            max_complexity=256,
            status_func=report_search_status,
    ):
        yield sql_query_str(sql_ast)

def main():
    for sql_query in sql_queries_enumerated():
        print(sql_query)

if __name__ == '__main__':
    main()
