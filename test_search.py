from search import progress_bar, search_methods
from example_searches import examples

def main():
    for example in examples:
        print('Problem:')
        print(example)

        print('Searching for solutions...')
        solution = progress_bar(search_methods['faux'], example)

        if solution:
            print('Solution found:')
            pprint(solution)
        else:
            print('Could not find a solution.')

if __name__ == '__main__':
    main()
