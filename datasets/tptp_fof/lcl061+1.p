%--------------------------------------------------------------------------
% File     : LCL061+1 : TPTP v9.2.1. Released v9.1.0.
% Domain   : Logic Calculi (Implication/Negation 2 valued sentential)
% Problem  : CN-59 depends on the Lukasiewicz system
% Version  : [McC92] axioms.
% English  : Axiomatisations of the Implication/Negation 2 valued
%            sentential calculus are {CN-1,CN-2,CN-3} by Lukasiewicz,
%            {CN-18,CN-21,CN-35,CN-39,CN-39,CN-40,CN-46} by Frege,
%            {CN-3,CN-18,CN-21,CN-22,CN-30,CN-54} by Hilbert, {CN-18,
%            CN-35,CN-49} by Church, {CN-19,CN-37,CN-59} by Lukasiewicz,
%            {CN-19,CN-37,CN-60} by Wos, and the single Meredith axiom.
%            Show that CN-59 depends on the short Lukasiewicz system.

% Refs     : [MW92]  McCune & Wos (1992), Experiments in Automated Deductio
%          : [McC92] McCune (1992), Email to Geoff Sutcliffe
%          : [Wos96] Wos (1996), The Power of Combining Resonance with Heat
%          : [RW+23] Rawson et al. (2023), Lemmas: Generation, Selection, A
% Source   : [McC92]
% Names    : thesis_59 [Wos96]
%          : CN-22 [MW92]

% Status   : Theorem
% Rating   : 0.80 v9.1.0
% Syntax   : Number of formulae    :    5 (   4 unt;   0 def)
%            Number of atoms       :    7 (   0 equ)
%            Maximal formula atoms :    3 (   1 avg)
%            Number of connectives :    2 (   0   ~;   0   |;   1   &)
%                                         (   0 <=>;   1  =>;   0  <=;   0 <~>)
%            Maximal formula depth :    5 (   3 avg)
%            Maximal term depth    :    5 (   2 avg)
%            Number of predicates  :    1 (   1 usr;   0 prp; 1-1 aty)
%            Number of functors    :    5 (   5 usr;   3 con; 0-2 aty)
%            Number of variables   :    8 (   8   !;   0   ?)
% SPC      : FOF_THM_RFO_NEQ

% Comments :
%--------------------------------------------------------------------------
fof(condensed_detachment,axiom,
    ! [X,Y] :
      ( ( is_a_theorem(implies(X,Y))
        & is_a_theorem(X) )
     => is_a_theorem(Y) ) ).

fof(cn_1,axiom,
    ! [X,Y,Z] : is_a_theorem(implies(implies(X,Y),implies(implies(Y,Z),implies(X,Z)))) ).

fof(cn_2,axiom,
    ! [X] : is_a_theorem(implies(implies(not(X),X),X)) ).

fof(cn_3,axiom,
    ! [X,Y] : is_a_theorem(implies(X,implies(not(X),Y))) ).

fof(prove_cn_59,conjecture,
    is_a_theorem(implies(implies(not(a),c),implies(implies(b,c),implies(implies(a,b),c)))) ).

%--------------------------------------------------------------------------