% Source: standard existential reasoning example from introductory logic texts.
% Status : Theorem
fof(ax1, axiom, ! [X] : (person(X) => ? [Y] : likes(X,Y))).
fof(ax2, axiom, person(socrates)).
fof(goal, conjecture, ? [Y] : likes(socrates,Y)).