% Status : Theorem
fof(ft_rule, axiom, ! [X, Y, Z] : ((parent(X,Y) & parent(Y,Z)) => grandparent(X,Z))).
fof(ft_f1, axiom, parent(alice,bob)).
fof(ft_f2, axiom, parent(bob,charlie)).
fof(ft_goal, conjecture, grandparent(alice,charlie)).
