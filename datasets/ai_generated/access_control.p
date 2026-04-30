% AI-generated: Access control and permission propagation
% Status: Theorem
% Tests role-based access with permission inheritance through multiple organizational levels
fof(org_ax1, axiom, role(ceo)).
fof(org_ax2, axiom, role(manager)).
fof(org_ax3, axiom, role(employee)).
fof(org_ax4, axiom, supervises(manager, employee)).
fof(org_ax5, axiom, supervises(ceo, manager)).
fof(perm_ax1, axiom, permission(ceo, approve_budget)).
fof(perm_ax2, axiom, permission(ceo, hire)).
fof(perm_ax3, axiom, permission(manager, assign_tasks)).
fof(inherit_rule, axiom, ! [R1,R2,P] : ((supervises(R1,R2) & permission(R1,P)) => permission(R2,P))).
fof(trans_rule, axiom, ! [R1,R2,R3] : ((supervises(R1,R2) & supervises(R2,R3)) => can_delegate(R1,R3))).
fof(conj1, conjecture, permission(employee, assign_tasks)).
