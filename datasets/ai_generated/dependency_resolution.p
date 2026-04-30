% AI-generated: Software dependency resolution
% Status: Theorem
% Tests dependency version compatibility through complex constraint networks
fof(pkg1, axiom, package(app_core)).
fof(pkg2, axiom, package(lib_math)).
fof(pkg3, axiom, package(lib_utils)).
fof(pkg4, axiom, package(lib_network)).
fof(dep1, axiom, requires(app_core, lib_math)).
fof(dep2, axiom, requires(lib_math, lib_utils)).
fof(dep3, axiom, requires(app_core, lib_network)).
fof(dep4, axiom, requires(lib_network, lib_utils)).
fof(vers1, axiom, version(lib_utils, v1)).
fof(vers2, axiom, version(lib_math, v2)).
fof(vers3, axiom, version(lib_network, v3)).
fof(rule1, axiom, ! [X,Y] : (requires(X,Y) => transitively_depends(X,Y))).
fof(rule2, axiom, ! [X,Y,Z] : ((transitively_depends(X,Y) & transitively_depends(Y,Z)) => transitively_depends(X,Z))).
fof(rule3, axiom, ! [X,Y] : ((transitively_depends(X,Y) & package(X) & package(Y)) => must_be_compatible(X,Y))).
fof(conj1, conjecture, transitively_depends(app_core, lib_utils)).
