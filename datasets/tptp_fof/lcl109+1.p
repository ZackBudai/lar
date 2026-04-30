%--------------------------------------------------------------------------
% File     : LCL109+1 : TPTP v9.2.1. Released v9.1.0.
% Domain   : Logic Calculi (Many valued sentential)
% Problem  : MV-4 depends on the Meredith system
% Version  : [McC92] axioms.
% English  : An axiomatisation of the many valued sentential calculus
%            is {MV-1,MV-2,MV-3,MV-5} by Meredith. Show that MV-4 depends
%            on the Meredith system.

% Refs     : [MW92]  McCune & Wos (1992), Experiments in Automated Deductio
%          : [RW+23] Rawson et al. (2023), Lemmas: Generation, Selection, A
%          : [Sla02] Slaney (2002), More Proofs of an Axiom of Lukasiewicz
%          : [Sla03] Slaney (2003), Email to G. Sutcliffe
% Source   : [McC92]
% Names    : MV-55 [MW92]
%          : Luka5 [ANL]

% Status   : Theorem
% Rating   : 0.95 v9.1.0
% Syntax   : Number of formulae    :    6 (   5 unt;   0 def)
%            Number of atoms       :    8 (   0 equ)
%            Maximal formula atoms :    3 (   1 avg)
%            Number of connectives :    2 (   0   ~;   0   |;   1   &)
%                                         (   0 <=>;   1  =>;   0  <=;   0 <~>)
%            Maximal formula depth :    5 (   3 avg)
%            Maximal term depth    :    4 (   2 avg)
%            Number of predicates  :    1 (   1 usr;   0 prp; 1-1 aty)
%            Number of functors    :    4 (   4 usr;   2 con; 0-2 aty)
%            Number of variables   :   11 (  11   !;   0   ?)
% SPC      : FOF_THM_RFO_NEQ

% Comments : In [Sla02] mv_2 is replaced by AxB (B->C)->((A->B)->(A->C)).
%            mv_2 can be derived from that basis [Sla03]
%--------------------------------------------------------------------------
fof(condensed_detachment,axiom,
    ! [X,Y] :
      ( ( is_a_theorem(implies(X,Y))
        & is_a_theorem(X) )
     => is_a_theorem(Y) ) ).

fof(mv_1,axiom,
    ! [X,Y] : is_a_theorem(implies(X,implies(Y,X))) ).

fof(mv_2,axiom,
    ! [X,Y,Z] : is_a_theorem(implies(implies(X,Y),implies(implies(Y,Z),implies(X,Z)))) ).

fof(mv_3,axiom,
    ! [X,Y] : is_a_theorem(implies(implies(implies(X,Y),Y),implies(implies(Y,X),X))) ).

fof(mv_5,axiom,
    ! [X,Y] : is_a_theorem(implies(implies(not(X),not(Y)),implies(Y,X))) ).

fof(prove_mv_4,conjecture,
    is_a_theorem(implies(implies(implies(a,b),implies(b,a)),implies(b,a))) ).

%--------------------------------------------------------------------------