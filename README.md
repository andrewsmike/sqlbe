SQL By Example
==============
Given an example database and a desired output, receive functional SQL statements.

Backlog:
- [OPTIONAL] Separate out generic CFG tools from SQL CFG
- Build enumerate CFG func
- [Optional] Build a query plan representation
- Build out SQL eval functions
- Write search.py

Current status:
- [ ] Enumerate SQL programs
- - [X] Build SQL CFG
- [ ] Execute SQL programs
- [ ] Estimate and display enumeration progress
- [X] Render SQL programs into query string

- [X] CFG tools (syntax verification, debugging, etc)
- [X] Representative SQL CFG
- [X] Able to render SQL ASTs into query strings
- [ ] Ability to execute SQL programs against relations
- [ ] Ability to enumerate (in order of ascending complexity/depth) CFGs
- [X] Progress bar tools (funsies)

Breakdown
- sql_ast: CFG/AST tools, SQL CFG, SQL AST -> SQL query string
- sql_eval: Evaluate SQL queries.
- search: SQL CFG search methods.
- models: Useful models.

