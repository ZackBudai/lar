% AI-generated: Social network influence propagation
% Status: Theorem
% Tests influence spreading through follower relationships with multi-hop propagation
fof(follow1, axiom, follows(alice, bob)).
fof(follow2, axiom, follows(bob, charlie)).
fof(follow3, axiom, follows(charlie, diana)).
fof(follow4, axiom, follows(bob, diana)).
fof(influence1, axiom, influential(alice)).
fof(rule1, axiom, ! [X,Y] : (follows(X,Y) => can_reach(X,Y))).
fof(rule2, axiom, ! [X,Y,Z] : ((can_reach(X,Y) & can_reach(Y,Z)) => can_reach(X,Z))).
fof(rule3, axiom, ! [X,Y] : ((influential(X) & can_reach(X,Y)) => receives_influence(Y,X))).
fof(rule4, axiom, ! [X] : ((receives_influence(X,_)) => potentially_influential(X))).
fof(conj1, conjecture, receives_influence(diana, alice)).
