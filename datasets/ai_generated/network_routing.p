% AI-generated: Network routing and connectivity
% Status: Theorem
% Tests transitive reachability in complex networks with multiple paths
fof(edge_1, axiom, edge(router_a, router_b)).
fof(edge_2, axiom, edge(router_b, router_c)).
fof(edge_3, axiom, edge(router_c, router_d)).
fof(edge_4, axiom, edge(router_b, router_d)).
fof(edge_5, axiom, edge(router_a, router_e)).
fof(edge_6, axiom, edge(router_e, router_f)).
fof(rule_1, axiom, ! [X,Y] : (edge(X,Y) => reachable(X,Y))).
fof(rule_2, axiom, ! [X,Y,Z] : ((reachable(X,Y) & reachable(Y,Z)) => reachable(X,Z))).
fof(conj1, conjecture, reachable(router_a, router_d)).
