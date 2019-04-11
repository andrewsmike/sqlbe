from search import progress_bar, search_methods
from examples import problems

def main():
    for problem in problems:
        print('Problem:')
        print(problem)

        print('Searching for solutions...')
        solution = progress_bar(search_methods['faux'], problem)

        if solution:
            print('Solution found:')
            pprint(solution)
        else:
            print('Could not find a solution.')

if __name__ == '__main__':
    main()
