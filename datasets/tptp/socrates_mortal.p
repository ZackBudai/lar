% Source: Aristotle's classic syllogism, commonly presented in logic textbooks and derived from Prior Analytics.
% Status : Theorem
fof(ax1, axiom, ! [X] : (greek(X) => human(X))).
fof(ax2, axiom, ! [X] : (human(X) => mortal(X))).
fof(ax3, axiom, greek(socrates)).
fof(goal, conjecture, mortal(socrates)).
