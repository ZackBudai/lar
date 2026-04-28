% Status : Theorem
fof(cd_base, axiom, ! [X, Y] : (r(X,Y) => reach(X,Y))).
fof(cd_step, axiom, ! [X, Y, Z] : ((r(X,Y) & reach(Y,Z)) => reach(X,Z))).
fof(cd_f1, axiom, r(n1,n2)).
fof(cd_f2, axiom, r(n2,n3)).
fof(cd_f3, axiom, r(n3,n4)).
fof(cd_f4, axiom, r(n4,n5)).
fof(cd_goal, conjecture, reach(n1,n5)).
