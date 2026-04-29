% Source: standard recursive ancestor example from logic programming textbooks.
% Status : Theorem
fof(p1, axiom, parent(john,mary)).
fof(p2, axiom, parent(mary,susan)).
fof(p3, axiom, parent(susan,alice)).
fof(r1, axiom, ! [X,Y] : (parent(X,Y) => ancestor(X,Y))).
fof(r2, axiom, ! [X,Y,Z] : ((parent(X,Y) & ancestor(Y,Z)) => ancestor(X,Z))).
fof(goal, conjecture, ancestor(john,alice)).
