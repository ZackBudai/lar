% Source: standard function-symbol example used in first-order logic teaching materials.
% Status : Theorem
fof(ax1, axiom, ! [X] : parent(X,father(X))).
fof(ax2, axiom, parent(john,mary)).
fof(goal, conjecture, parent(john,father(john))).