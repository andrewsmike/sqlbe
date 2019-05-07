====2019-05-02
Reached SQL query enumeration today.
Notes:
- It seems to be searching around for the next cheapest pattern that is
    complete, then flushes all SYMBOL options (due to structure of expansion
    graph.)
    - Hey, expansion graph math. Neat. Fun simple patterns.
- You can _feel_ it groaning with the branching factor.
- I need to start the iterative process of optimizing this algorithm.
- I will get a useful impression of what sort of factored representations are
    necessary to do this effectively over time.



====2019-04-14
Efficient representation of joint-argument witness function constraints (allowing for efficient descent of tree.)
These include, in typical order:
- Syntactic constraints
- Typing constraints
- Data constraints (from input/output pairs)

Say you have an AST.
- Production rules
- Weights for depth?
- Genericized witness functions?




Question: Do I want to enumerate over logical plans or syntax?
Answer: Syntax.
Question: Can I make them isomorphic?
Answer: ... No, unfortunately.
Question: Can I treat the syntax as a superset of the logical plan?
Answer: ... I think so? What other restrictions are there? You're just representing
    operation configuration, beyond inputs, as nodes.
