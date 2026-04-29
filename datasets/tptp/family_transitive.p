% Source: standard family-relation transitivity example from first-order logic textbooks.
% Status : Theorem
fof(ax1, axiom, ! [X,Y] : (parent(X,Y) => ancestor(X,Y))).
fof(ax2, axiom, ! [X,Y,Z] : ((parent(X,Y) & ancestor(Y,Z)) => ancestor(X,Z))).
fof(ax3, axiom, parent(john,mary)).
fof(ax4, axiom, parent(mary,alice)).
fof(goal, conjecture, ancestor(john,alice)).