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
