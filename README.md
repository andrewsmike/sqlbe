SQL By Example
==============
Given an example database and a desired output, receive functional SQL statements.

Backlog:
- [Optional] Build a query plan representation
- Build out SQL eval functions
- [OPTIONAL] Separate out generic CFG tools from SQL CFG
- Write search.py
- Enumerate.py cleanup

Current status:
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

Breakdown
- sql_ast: CFG/AST tools, SQL CFG, SQL AST -> SQL query string
- enumerate: CFG enumeration methods.
WIP:
- models: Useful models.
- sql_eval: Evaluate SQL queries.
- search: Search for SQL queries that satisfy example pairs.

