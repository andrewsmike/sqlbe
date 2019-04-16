from pprint import pprint

from sql_eval import eval_sql
from example_asts import examples as sql_examples
from example_searches import example_tables

def main():
    for sql_example in sql_examples:
        eval_sql(sql_example, example_tables)
    

if __name__ == '__main__':
    main(*(argv[1:]))
