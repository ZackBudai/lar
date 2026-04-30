%--------------------------------------------------------------------------
% File     : LCL073+1 : TPTP v9.2.1. Released v9.1.0.
% Domain   : Logic Calculi (Implication/Negation 2 valued sentential)
% Problem  : CN-1 depends on the single Meredith axiom
% Version  : [McC92] axioms.
% English  : Axiomatisations of the Implication/Negation 2 valued
%            sentential calculus are {CN-1,CN-2,CN-3} by Lukasiewicz,
%            {CN-18,CN-21,CN-35,CN-39,CN-39,CN-40,CN-46} by Frege,
%            {CN-3,CN-18,CN-21,CN-22,CN-30,CN-54} by Hilbert, {CN-18,
%            CN-35,CN-49} by Church, {CN-19,CN-37,CN-59} by Lukasiewicz,
%            {CN-19,CN-37,CN-60} by Wos, and the single Meredith axiom.
%            Show that CN-1 depends on the single Meredith axiom.

% Refs     : [MW92]  McCune & Wos (1992), Experiments in Automated Deductio
%          : [McC92] McCune (1992), Email to G. Sutcliffe
%          : [RW+23] Rawson et al. (2023),  Lemmas: Generation, Selection,
% Source   : [McC92]
% Names    : CN-34 [MW92]

% Status   : Theorem
% Rating   : 1.00 v9.1.0
% Syntax   : Number of formulae    :    3 (   2 unt;   0 def)
%            Number of atoms       :    5 (   0 equ)
%            Maximal formula atoms :    3 (   1 avg)
%            Number of connectives :    4 (   2   ~;   2   |;   0   &)
%                                         (   0 <=>;   0  =>;   0  <=;   0 <~>)
%            Maximal formula depth :    6 (   5 avg)
%            Maximal term depth    :    7 (   2 avg)
%            Number of predicates  :    1 (   1 usr;   0 prp; 1-1 aty)
%            Number of functors    :    2 (   2 usr;   0 con; 1-2 aty)
%            Number of variables   :   10 (  10   !;   0   ?)
% SPC      : FOF_THM_RFO_NEQ

% Comments :
%--------------------------------------------------------------------------
fof(condensed_detachment,axiom,
    ! [X,Y] :
      ( ~ is_a_theorem(implies(X,Y))
      | ~ is_a_theorem(X)
      | is_a_theorem(Y) ) ).

fof(cn_CAMeredith,axiom,
    ! [X,Y,Z,U,V] : is_a_theorem(implies(implies(implies(implies(implies(X,Y),implies(not(Z),not(U))),Z),V),implies(implies(V,X),implies(U,X)))) ).

fof(prove_cn_1,conjecture,
    ! [A,B,C] :
      is_a_theorem(implies(implies(A,B),implies(implies(B,C),implies(A,C)))) ).

%--------------------------------------------------------------------------