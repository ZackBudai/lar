% Status : Theorem
fof(ar_base, axiom, ! [X, Y] : (parent(X,Y) => ancestor(X,Y))).
fof(ar_step, axiom, ! [X, Y, Z] : ((parent(X,Y) & ancestor(Y,Z)) => ancestor(X,Z))).
fof(ar_f1, axiom, parent(a,b)).
fof(ar_f2, axiom, parent(b,c)).
fof(ar_f3, axiom, parent(c,d)).
fof(ar_goal, conjecture, ancestor(a,d)).
