%--------------------------------------------------------------------------
% File     : LCL230+1 : TPTP v9.2.1. Released v2.0.0.
% Domain   : Logic Calculi (Propositional)
% Problem  : Principia Mathematica 2.85
% Version  : Especial.
% English  : Judged by [SRM73] to be the 'hardest' of the
%            first 67 theorems of [WR27].

% Refs     : [WR27]  Whitehead & Russell (1927), Principia Mathematica
%          : [SRM73] Siklossy et al. (1973), Breadth First Search: Some Sur
%          : [Pel86] Pelletier (1986), Seventy-five Problems for Testing Au
%          : [Hah94] Haehnle (1994), Email to G. Sutcliffe
% Source   : [Hah94]
% Names    : Pelletier 5 [Pel86]

% Status   : Theorem
% Rating   : 0.00 v4.1.0, 0.06 v4.0.1, 0.05 v3.7.0, 0.33 v3.5.0, 0.12 v3.4.0, 0.08 v3.3.0, 0.00 v3.2.0, 0.11 v3.1.0, 0.00 v2.5.0, 0.33 v2.4.0, 0.33 v2.2.1, 0.00 v2.1.0
% Syntax   : Number of formulae    :    1 (   0 unt;   0 def)
%            Number of atoms       :    7 (   0 equ)
%            Maximal formula atoms :    7 (   7 avg)
%            Number of connectives :    6 (   0   ~;   3   |;   0   &)
%                                         (   0 <=>;   3  =>;   0  <=;   0 <~>)
%            Maximal formula depth :    4 (   4 avg)
%            Maximal term depth    :    0 (   0 avg)
%            Number of predicates  :    3 (   3 usr;   3 prp; 0-0 aty)
%            Number of functors    :    0 (   0 usr;   0 con; --- aty)
%            Number of variables   :    0 (   0   !;   0   ?)
% SPC      : FOF_THM_PRP

% Comments :
%--------------------------------------------------------------------------
fof(pel5,conjecture,
    ( ( ( p
        | q )
     => ( p
        | r ) )
   => ( p
      | ( q
       => r ) ) ) ).

%--------------------------------------------------------------------------