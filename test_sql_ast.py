from pprint import pprint
from sys import argv

from sql_ast import tree_depth, tree_heights, syntax_valid, tree_map
from example_asts import examples

view_funcs = {
    'depth': lambda example: str(tree_depth(example)),
    'depth_desc': lambda example: pprint(tree_heights(example), indent=6),
    'depth_asc': lambda example: pprint(tree_map(example, tree_depth), indent=6),

    'uni_depth': lambda example: str(tree_depth(example, dynamic_depth=False)),
    'uni_depth_desc': lambda example: pprint(tree_heights(example, dynamic_depth=False), indent=6),
    'uni_depth_asc': lambda example: pprint(tree_map(example, tree_depth, func_kwargs=dict(dynamic_depth=False)), indent=6),

    'syntax_valid': lambda example: str(syntax_valid(example)),
    'syntax_valid_asc': lambda example: pprint(tree_map(example, syntax_valid)),
}

def main(views=None):
    views = views or ','.join(view_funcs.keys())
    views = views.split(',')
    for example_name, example in examples.items():
        print(example_name + ':')
        pprint(example)
        for view in views:
            print('####' + view)
            res = view_funcs[view](example)
            if isinstance(res, str):
                print(res)
    

if __name__ == '__main__':
    main(*(argv[1:]))
