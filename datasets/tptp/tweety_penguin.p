% Source: Russell & Norvig, Artificial Intelligence: A Modern Approach, Tweety/penguin example.
% Status : CounterSatisfiable
fof(ax1, axiom, ! [X] : (penguin(X) => bird(X))).
fof(ax2, axiom, ! [X] : ((bird(X) & ~penguin(X)) => fly(X))).
fof(ax3, axiom, penguin(tweety)).
fof(goal, conjecture, fly(tweety)).
