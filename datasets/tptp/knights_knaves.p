% Source: Raymond Smullyan, classic Knights and Knaves puzzle tradition.
% Status : Theorem
fof(ax1, axiom, ! [X] : (knight(X) | knave(X))).
fof(ax2, axiom, ! [X] : ~(knight(X) & knave(X))).
fof(ax3, axiom, ! [X] : (knight(X) => truth_teller(X))).
fof(ax4, axiom, ! [X] : (knave(X) => ~truth_teller(X))).
fof(ax5, axiom, truth_teller(alice) <-> knight(alice)).
fof(goal, conjecture, knight(alice)).
