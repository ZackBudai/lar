% Status : Theorem
fof(bp_r1, axiom, ! [X] : (penguin(X) => bird(X))).
fof(bp_r2, axiom, ! [X] : (bird(X) => has_wings(X))).
fof(bp_f1, axiom, penguin(tux)).
fof(bp_goal, conjecture, has_wings(tux)).
