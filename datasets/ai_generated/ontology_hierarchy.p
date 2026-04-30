% AI-generated: Semantic web ontology reasoning
% Status: Theorem  
% Tests class hierarchy and instance reasoning with multiple inheritance levels
fof(class_axiom_1, axiom, subclass(developer, professional)).
fof(class_axiom_2, axiom, subclass(professional, person)).
fof(class_axiom_3, axiom, subclass(manager, professional)).
fof(class_axiom_4, axiom, ! [X,Y,Z] : ((instance(X,Y) & subclass(Y,Z)) => instance(X,Z))).
fof(class_axiom_5, axiom, ! [X,Y,Z] : ((subclass(X,Y) & subclass(Y,Z)) => subclass(X,Z))).
fof(instance_fact_1, axiom, instance(alice, developer)).
fof(instance_fact_2, axiom, instance(bob, manager)).
fof(property_rule, axiom, ! [X] : (instance(X,professional) => has_skills(X))).
fof(conj1, conjecture, has_skills(alice)).
