include "globals.mzn";

% Parameters
int: w; % width of the plate
int: n; % number of circuits to be placed
int: maxh; 
int: minh;

set of int: circuits = 1..n;
array [circuits] of int: y; % heights of each circuit
array [circuits] of int: x; % weights of each circuit

% Variables
array [circuits] of var 0..w-min(x): xhat; % horizontal vertex
array [circuits] of var 0..maxh-min(y): yhat; % vertical vertex
var minh..maxh: h; % height of the plate

% index of the circuit with the biggest area
% int : biggest_circuit_idx = arg_max([y[c] * x[c] | c in circuits]);

% Main constraints
constraint forall (i in circuits) (xhat[i] <= w - x[i]);
constraint forall (i in circuits) (yhat[i] <= h - y[i]);

% Implied constraints
constraint cumulative(xhat, x, y, h)::domain;
constraint cumulative(yhat, y, x, w)::domain;

% No-overlapping constrait
constraint diffn(xhat, yhat, x, y)::domain;

% rows and columns symmetry
constraint symmetry_breaking_constraint(
    forall (i,j in circuits where i < j) ((xhat[i] == xhat[j] /\ x[i] == x[j]) -> yhat[i] <= yhat[j] ));
constraint symmetry_breaking_constraint(
    forall (i,j in circuits where i < j) ((yhat[i] == yhat[j] /\ y[i] == y[j]) -> xhat[i] <= xhat[j] ));

% three blocks symmetry
constraint symmetry_breaking_constraint(
    forall (i,j,k in circuits where i > j /\ j > k)
        ((xhat[i] == xhat[j] /\ x[i] == x[j] /\ yhat[i] == yhat[k] /\ y[i] + y[j] == y[k]) -> xhat[k] <= xhat[i] ));
constraint symmetry_breaking_constraint(
    forall (i,j,k in circuits where i > j /\ j > k)
        ((yhat[i] == yhat[j] /\ y[i] == y[j] /\ xhat[i] == xhat[k] /\ x[i] + x[j] == x[k]) -> yhat[k] <= yhat[i] ));

% force the biggest block to be always to the bottom left of the second biggest
constraint symmetry_breaking_constraint(lex_lesseq([xhat[1], yhat[1]], [xhat[2],yhat[2]]));

% Search
string: search;
string: restart;

ann: search_xhat = 
if search == "dom" then
  int_search(xhat, dom_w_deg, indomain_min)
elseif search == "ff" then
  int_search(xhat, first_fail, indomain_min)
else
  int_search(xhat, input_order, indomain_min)
endif;

ann: search_yhat = 
if search == "dom" then 
  int_search(yhat, dom_w_deg, indomain_min)
elseif search == "ff" then
  int_search(yhat, first_fail, indomain_min)
else
  int_search(yhat, input_order, indomain_min)
endif;

ann: restart_ann = 
if restart == "lub" then
  restart_luby(150)
elseif restart == "geom" then
  restart_geometric(2, 50)
else
  restart_none
endif;

solve :: search_xhat
      :: search_yhat
      :: restart_ann
         minimize h;
%output [
%  "Plate height: ", show(h), "\n",
%  "Solution: \n", 
%   "x = ", show([xhat[i] | i in circuits]),"\n",  
%   "y = ", show([yhat[i] | i in circuits])];
