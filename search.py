from progressbar import (
    Bar,
    ETA,
    Percentage,
    ProgressBar,
)

from models import Relation, Example
from sql import (
    enumerate_sql,
    eval_sql,
)

from time import sleep


__all__ = [
    'search_methods',
    'progress_bar',
]

def brute_force_search(problem, progress_bar=None):
    """
    - Enumerate all program trees
    - Filter trees that return the correct output
    - Pull out the 'simplest' tree
    - Generate SQL statement from tree

    TODO:
    - Push set of symbols / constants
    """
    for solution in enumerate_sql(dict(problem.input_relations)):
        result = eval_sql(solution, dict(problem.input_relations))
        if result == problem.output_relation:
            return result
    else:
        return None


def faux_search(problem, progress_bar=None):
    """
    "Search" for a few seconds. Tests out progressbar.
    Reports failure to find solution.
    """
    for i in range(8):
        progress_bar.update(10 * (i + 1))
        sleep(0.5)
    return None

search_methods = {
    'bruteforce': brute_force_search,
    'faux': faux_search,
}

def progress_bar(progress_func, *args, **kwargs):
    progress_display_parts = [
        'Search Progress: ', ETA(), Percentage(), Bar()
    ]
    progress_display = ProgressBar(widgets=progress_display_parts, maxval=100)

    progress_display.start()
    progress_display.update(0)

    new_kwargs = dict(kwargs)
    new_kwargs['progress_bar'] = progress_display

    result = progress_func(*args, **new_kwargs)

    progress_display.update(100)
    progress_display.finish()

    return result
