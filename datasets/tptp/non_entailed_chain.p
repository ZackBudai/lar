% Status : CounterSatisfiable
fof(nc_base, axiom, ! [X, Y] : (r(X,Y) => reach(X,Y))).
fof(nc_step, axiom, ! [X, Y, Z] : ((r(X,Y) & reach(Y,Z)) => reach(X,Z))).
fof(nc_f1, axiom, r(n1,n2)).
fof(nc_f2, axiom, r(n2,n3)).
fof(nc_goal, conjecture, reach(n1,n5)).
