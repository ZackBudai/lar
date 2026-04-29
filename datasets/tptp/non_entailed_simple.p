% Source: standard non-entailed query example used in theorem-proving exercises.
% Status : CounterSatisfiable
fof(ax1, axiom, ! [X] : (cat(X) => animal(X))).
fof(ax2, axiom, cat(tom)).
fof(goal, conjecture, animal(spike)).