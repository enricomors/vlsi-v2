include "globals.mzn";

int: w; % width of the plate
int: n; % number of circuits
int: maxh; % higher bound for plate height
int: minh; % lower bound for plate height

set of int: circuits = 1..n;

array [circuits] of 1..w: xinput;
array [circuits] of 1..maxh: yinput;

array [circuits] of var 1..w: x;
array [circuits] of var 1..maxh: y;
array [circuits] of var bool: rotated;

var minh..maxh: h; % height of the plate

array [circuits] of var 0..w-min(xinput): xhat; % horizontal coordinate of circuits
array [circuits] of var 0..maxh-min(yinput): yhat; % vertical coordinate of circuits

% constraints
constraint forall(i in circuits)(yhat[i] < h);
constraint forall(i in circuits)(xhat[i] + x[i] <= w);
constraint forall(i in circuits)(yhat[i] + y[i] <= h);
constraint diffn(xhat, yhat, x, y) :: domain;

% implied constraints
constraint cumulative(xhat, x, y, h) :: domain;
constraint cumulative(yhat, y, x, w) :: domain;

% rotation constraint
constraint forall (i in circuits)(if rotated[i]
then y[i] == xinput[i] /\ x[i] == yinput[i]
else x[i] == xinput[i] /\ y[i] == yinput[i] endif);

% constraint for square circuits
constraint forall (i in circuits) (xinput[i] == yinput[i] -> rotated[i] = false);

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