SQL By Example
==============
Given an example database and a desired output, receive functional SQL statements.



Backlog
-------
- Build out a dataset for evaluating complexity
- [Optional] Build a query plan representation
- Build out SQL eval functions
- [OPTIONAL] Separate out generic CFG tools from SQL CFG
- Write search.py
- Enumerate.py cleanup

Current status
--------------
- [X] Enumerate SQL programs
- - [X] Build SQL CFG
- [ ] Execute SQL programs
- [ ] Display enumeration progress nicely
- [X] Render SQL programs into query string

- [X] CFG tools (syntax verification, debugging, etc)
- [X] Representative SQL CFG
- [X] Able to render SQL ASTs into query strings
- [ ] Ability to execute SQL programs against relations
- [ ] Ability to enumerate (in order of ascending complexity/depth) CFGs
- [X] Progress bar tools (funsies)

Files
-----
- sql_ast: CFG/AST tools, SQL CFG, SQL AST -> SQL query string
- enumerate: CFG enumeration methods.
WIP:
- models: Useful models.
- sql_eval: Evaluate SQL queries.
- search: Search for SQL queries that satisfy example pairs.

History of methodology
----------------------
History:
- Enumerative search over non-typed AST elements using min-heap of partial trees. Top-down building.
    Sorted by max depth, then number of nodes.
    This seems to take forever to find new "patterns", then generates a bundle, then continue.
    Hard limit at 20 depth.
- Switch to sorting by complexity, complexity = sum(node_weights)
    This performs _SO MUCH BETTER_. Need to establish metrics.

TODO:
- Establish evaluation criteria / metrics.
- Qualitative description of failures of enumeration.
- Crafting AST nodes (Pushing AGG/No-AGG rules up.)
- Cross AST contextual constraints (Pushing AVAILABLE-COLUMN? constraints up.)

