%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%         ESERCIZIO 1        %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

A = [ -3 3 0; 0 0 1; 0 -2 -3];
B = [1; 2; -0.5];
C = [0 1 2];
D = 0;

%% Esercizio 1.1
%
% Calcolare gli autovettori e gli autovalori della matrice A.
% 
% The function "eig" returns two matrices:
% - V: each column of V is an eigenvector
% - E: each diagonal element of E is an eigenvalue
%
% Note that the i-th column of V is the eigenvector corresponding to the
% eigenvalue in the i-th diagonal element of E

[V,E] = eig(A);

%% Esercizio 1.2
%
% The fact that the matrix A has all distinct eigenvalues is a sufficient
% condition (but not necessary) for the existence of a similarity matrix P
% capable of obtaining A' diagonal. Such matrix P is computed through
% concatenation of the eigenvectors, i.e., V as computed above.
% 
% This transformation is not unique as there are infinitely many different
% choices for the eigenvectors.

P = V;

%% Esercizio 1.3
%

Ap = inv(V)*A*V;
Bp = V\B;           % This is an alternative way to compute inv(V)*B
Cp = C*V;
Dp = D;

%% Esercizio 1.4

% From the state-space representation, we can compute the coefficients of
% the input/output representation by means of the function "ss2tf". 
%
% In particular:
%
% "num" contains the input's coefficients in descending derivative's
%       order, that is the coefficients of the transfer function's
%       numerator in descending power of s
% "den" contains the output's coefficients in descending derivative's
%       order, that is the coefficients of the transfer function's
%       denominator in descending power of s
%
% Then, we can use the function "tf" to create the matlab object for the
% input-output representation.

[num,den] = ss2tf(A,B,C,D);
sys_IU = tf(num,den);

[num_d,den_d] = ss2tf(Ap,Bp,Cp,Dp);
sys_IU_d = tf(num_d,den_d);


% We can use the function "ss" to create the matlab object for the state
% variable representation. Note that we could also construct the matrices
% A,B,C,D from the input-output representation.

% [A,B,C,D] = tf2ss(num,den);
sys_VS = ss(A,B,C,D);

% [Ap,Bp,Cp,Dp] = tf2ss(num_d,den_d);
sys_VS_d = ss(Ap,Bp,Cp,Dp);

%% Esercizio 1.5
%
% We can plot the step response by means of the function "step"

figure(1)
step(sys_VS)
figure(2)
step(sys_IU)

% If we want to decide the precise time interval to be displayed and
% the resolution, we can % create a vector of discrete time instants.

close all % This command closes all figures

delta = 0.0001;
time=0:delta:10;
step(sys_VS,time)

% Alternatively, we can also store the step response into a vector, and
% then plot a custom figure.

y_step_VS = step(sys_VS,time);
y_step_IU = step(sys_IU,time);
y_step_VS_d = step(sys_VS_d,time);
y_step_IU_d = step(sys_IU_d,time);

figure(1)
plot(time,y_step_VS,'LineWidth',2)
hold on
plot(time,y_step_VS,'LineWidth',2)
plot(time,y_step_VS_d,'LineWidth',2)
plot(time,y_step_VS_d,'LineWidth',2)
hold off
title('Excercise 1.5','FontSize',17)
ylabel('Step response','FontSize',15)
xlabel('Time','FontSize',15)
legend("VS","IU","VS_d","IU_d")
grid

%% Esercizio 1.6
%
% We can plot the impulse response by means of the function "impulse"

y_impulse_VS = impulse(sys_VS,time);
y_impulse_IU = impulse(sys_IU,time);
y_impulse_VS_d = impulse(sys_VS_d,time);
y_impulse_IU_d = impulse(sys_IU_d,time);

figure(2)
plot(time,y_impulse_VS,'LineWidth',2)
hold on
plot(time,y_impulse_VS,'LineWidth',2)
plot(time,y_impulse_VS_d,'LineWidth',2)
plot(time,y_impulse_VS_d,'LineWidth',2)
hold off
title('Excercise 1.6','FontSize',17)
ylabel('Impulse response','FontSize',15)
xlabel('Time','FontSize',15)
legend("VS","IU","VS_d","IU_d")
grid

%% Esercizio 1.7

u_step = ones(1,length(time));
x0 = [0 0 0]';
y0 = 0;
y_step_VS_custom = lsim(sys_VS,u_step,time,x0);
y_step_IU_custom = lsim(sys_IU,u_step,time,y0);
figure(3)
plot(time,y_step_VS_custom,'LineWidth',2)
hold on
plot(time,y_step_IU_custom,'LineWidth',2)
hold off
title('Excercise 1.7','FontSize',17)
ylabel('Step response (custom)','FontSize',15)
xlabel('Time','FontSize',15)
legend("VS","IU")
grid

time = [time time(end)+delta];

u_imp = zeros(1,length(time));
u_imp(1) = 1/delta;
y_impulse_VS_custom = lsim(sys_VS,u_imp,time);
y_impulse_IU_custom = lsim(sys_IU,u_imp,time);
figure(4)
plot(time(1:end-1),y_impulse_VS_custom(2:end),'LineWidth',2)
hold on
plot(time(1:end-1),y_impulse_IU_custom(2:end),'LineWidth',2)
hold off
title('Excercise 1.7','FontSize',17)
ylabel('Impulse response (custom)','FontSize',15)
xlabel('Time','FontSize',15)
legend("VS","IU")
grid


%% Esercizio 1.8
%
% To simulate the step response, we create a unitary constant vector input
% and put the initial conditions equal to zero.

syms t real
eAt = expm(A*t);
eApt = expm(Ap*t);

Ap_better = (V\A)*V;
eApt_better = expm(Ap_better*t);


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%         ESERCIZIO 2        %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

syms t real

f1 = 1+4*t*exp(3*t);
L1 = laplace(f1);
pretty(L1)

f2 = 7*(t^2+1)^2;
L2 = laplace(f2);
pretty(L2)

f3 = 3*(t^2+1)^2;
L3 = laplace(f3);
pretty(L2)

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%         ESERCIZIO 3        %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

syms s

L4 = (3*s-2)/(s^3 + 4*s^2 + 20*s);
f4 = ilaplace(L4);

L4_num_coeff = [3 -2];
L4_den_coeff = [1 4 20 0];

[res,pol,~] = residue(L4_num_coeff,L4_den_coeff);


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%         ESERCIZIO 4        %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

den = [1 50 625];
num = [100 0];
sys_IU = tf(num,den);

y0 = [2, 1];

delta = 0.000001;
time=0:delta:2;

y_ell = risposta_libera(den,y0,time);         % Dal sito del professsore
y_imp = risposta_impulsiva(num,den,time);     % Dal sito del professsore
y_ind = risposta_indiciale(num,den,time);     % Dal sito del professsore

u_imp = sin(time*20);
y_sin = lsim(sys_IU,u_imp,time);


figure(5)
plot(time,y_ell,'LineWidth',2)
hold on
plot(time,y_imp,'LineWidth',2)
plot(time,y_ind,'LineWidth',2)
plot(time,y_sin,'LineWidth',2)
hold off
title('Excercise 4','FontSize',17)
ylabel('Free response (professor code)','FontSize',15)
xlabel('Time','FontSize',15)
legend("Libera","Impulsiva", "Indiciale", "Armonica")
grid


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%         ESERCIZIO 5        %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

M = 300;
b_A = 900; 
b_B = 3000;
K = 12000;

% b_A = alto livello di comfort ai passeggeri (sistema meno smorzato)
% b_B = alta tenuta di strata (sistema più smorzato)


% If I'm driving a Land Rover, I expect to encounter many potholes along
% my route, and for each pothole I encounter, I would like its effect to
% be as gentle as possible (low damping), while I can accept that the
% effect persists over time (high time constant).
%
% Therefore, mode mA is suitable for these characteristics, being less damped although slower.

% If I'm driving a Ferrari, I expect to encounter no potholes along my
% route. If I were to accidentally encounter small unevenness in the
% terrain, I would want its effect to fade away as quickly as possible
% (low time constant) so that I can regain control of the car immediately,
% while I can tolerate that its effect (such as the impact) is very
% abrupt (high damping).
% 
% Therefore, mode mB is suitable for these characteristics, being the fastest even though more damped.

num_A = [b_A K];
den_A = [M b_A K];
sys_A=tf(num_A,den_A);
num_B = [b_B K];
den_B = [M b_B K];
sys_B=tf(num_B,den_B);
%
t_max = 5;
step =0.01;
t=0:step:t_max;
t1=0:step:1-step;
u_rise=0:0.01:0.2;
u = [zeros(size(t1)) u_rise 0.2*ones(1,158)  0.2-u_rise zeros(size(t1)) zeros(size(t1)) 0;] ;

y_A = lsim(sys_A,u,t);
y_B = lsim(sys_B,u,t);

figure(1)
plot(t,y_A,'LineWidth',2)
hold on
plot(t,y_B,'LineWidth',2)
plot(t,u,'LineWidth',2)
hold off
axis([0 5 -0.2 0.35])
grid
title('Excercise 5','FontSize',17)
% ylabel('Output and Input','FontSize',15)
xlabel('Time','FontSize',15)
legend("Position with small b","Position with high b", "Street profile")
grid


fk_A = -K*(y_A'-u);
fk_B = -K*(y_B'-u);
fb_A = [-b_A*diff(y_A'-u)/step 0];
fb_B = [-b_B*diff(y_B'-u)/step 0];

figure(2)
plot(t,fk_A+fb_A,'LineWidth',2)
hold on
plot(t,fk_B+fb_B,'LineWidth',2)
hold off
axis([0 5 -4000 4000])
grid
title('Excercise 5','FontSize',17)
% ylabel('Output and Input','FontSize',15)
xlabel('Time','FontSize',15)
legend("Force with with small b","Force with high b")
grid



