%------------------------------------------------------------------------------
% File     : PUZ128+1 : TPTP v9.2.1. Released v4.0.0.
% Domain   : Puzzles
% Problem  : Iokaste patricide triangle
% Version  : Especial.
% English  : Iokaste is a parent of Oedipus. Iokaste is a parent of Polyneikes.
%            Oedipus is a parent of Polyneikes. Polyneikes is a parent of 
%            Thersandros. Oedipus is a patricide. Thersandros is not a 
%            patricide. Therefore, Iokaste is a parent of a patricide who is 
%            a parent of somebody who is not a patricide.

% Refs     : 
% Source   : [TPTP]
% Names    : 

% Status   : Theorem
% Rating   : 0.00 v5.3.0, 0.09 v5.2.0, 0.00 v4.1.0, 0.06 v4.0.1, 0.05 v4.0.0
% Syntax   : Number of formulae    :    7 (   6 unt;   0 def)
%            Number of atoms       :   10 (   0 equ)
%            Maximal formula atoms :    4 (   1 avg)
%            Number of connectives :    5 (   2   ~;   0   |;   3   &)
%                                         (   0 <=>;   0  =>;   0  <=;   0 <~>)
%            Maximal formula depth :    7 (   2 avg)
%            Maximal term depth    :    1 (   1 avg)
%            Number of predicates  :    2 (   2 usr;   0 prp; 1-2 aty)
%            Number of functors    :    4 (   4 usr;   4 con; 0-0 aty)
%            Number of variables   :    2 (   0   !;   2   ?)
% SPC      : FOF_THM_RFO_NEQ

% Comments : 
%------------------------------------------------------------------------------
%----Iokaste is a parent of Oedipus.
fof(iokaste_oedipus,axiom,
    parent_of(iokaste,oedipus) ).

%----Iokaste is a parent of Polyneikes.
fof(iokaste_polyneikes,axiom,
    parent_of(iokaste,polyneikes) ).

%----Oedipus is a parent of Polyneikes.
fof(oedipus_polyneikes,axiom,
    parent_of(oedipus,polyneikes) ).

%----Polyneikes is a parent of Thersandros.
fof(polyneikes_thersandros,axiom,
    parent_of(polyneikes,thersandros) ).

%----Oedipus is a patricide.
fof(oedipus_patricidal,axiom,
    patricide(oedipus) ).

%----Thersandros is not a patricide.
fof(thersandros_not_patricidal,axiom,
    ~ patricide(thersandros) ).

%----Therefore, Iokaste is a parent of a patricide who is a parent of 
%----somebody who is not a patricide.
fof(iokaste_parent_particide_parent_not_patricide,conjecture,
    ? [P,NP] :
      ( parent_of(iokaste,P)
      & patricide(P)
      & parent_of(P,NP)
      & ~ patricide(NP) ) ).

%------------------------------------------------------------------------------