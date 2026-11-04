---
paper_slug: sr_p001
lang: en
sections:
  - id: context
    title: "Background and Motivation"
  - id: objects
    title: "Key Objects"
  - id: main-results
    title: "Main Results"
  - id: proofs
    title: "Proof Sketches"
  - id: numerics
    title: "Numerical Illustration"
  - id: connections
    title: "Connections"
---

## Background and Motivation {#context}

The **Schrödinger bridge problem** asks: given two probability measures $\mu_0$ and $\mu_T$, what is the most likely evolution of a cloud of independent Brownian particles that starts distributed as $\mu_0$ and ends distributed as $\mu_T$? In modern stochastic control language, one minimizes the relative entropy of a semimartingale law with respect to Wiener measure subject to marginal constraints. The optimal process has unit diffusion and a controlled drift — the diffusion coefficient is frozen at the identity. The **Bass martingale transport**, by contrast, seeks a *martingale* (zero drift) interpolation by controlling only the diffusion coefficient, without touching the drift at all.

Henry-Labordère, Loeper, Mazhar, Pham, and Touzi (2026) introduced the **Schrödinger–Bass Bridge** (SBB), a one-parameter family indexed by $\beta > 0$ that interpolates between these two classical frameworks: large $\beta$ forces the diffusion to the identity (Schrödinger limit), while small $\beta$ suppresses the drift (Bass limit). The cost penalizes both the drift quadratically and deviations of the diffusion matrix from the identity via $\frac{1}{2}|\alpha_t|^2 + \frac{\beta}{2}\|\sigma_t\sigma_t^\top - I\|_F^2$. The Gaussian case was first solved via PDE methods (Legendre transforms, heat equation) in a companion paper; computational aspects were addressed separately. However, several structural questions remained open: the *precise* solvability boundary for Gaussian marginals, whether that boundary extends to non-Gaussian marginals, the nature of the optimal process exactly at the boundary, and the behavior when covariance matrices do not commute.

This paper fills these gaps via a self-contained **Pontryagin maximum principle** approach, which has two advantages over the PDE route: it produces the explicit optimizer directly through a scalar quadratic equation, and the adjoint (costate) equation $\dot p = 2p^2$ can be solved in closed form. This yields the exact solvability threshold $\gamma_T^* = (\gamma_0 + \beta T^2)/(1+2\beta T)^2$ and a proof that this Gaussian threshold is in fact a **universal lower bound** for all centered marginal pairs, not just Gaussian ones. The degenerate boundary regime — finite cost but vanishing terminal diffusion — is characterized explicitly, and a non-commuting $2\times 2$ numerical example reveals anisotropic costate coupling inaccessible to scalar decompositions.

## Key Objects {#objects}

**The SBB cost functional.** For a controlled semimartingale $dX_t = \alpha_t\,dt + \sigma_t\,dW_t$ with $X_0\sim\mu_0$, $X_T\sim\mu_T$, the cost is

$$J(\alpha,\sigma) = \int_0^T \mathbb{E}\!\left[\frac{1}{2}|\alpha_t|^2 + \frac{\beta}{2}\|\sigma_t\sigma_t^\top - I_d\|_F^2\right]dt.$$

The non-standard feature is the simultaneous penalization of drift *and* diffusion deviation: the Schrödinger bridge keeps only the first term (with $\sigma \equiv I$) while the Bass construction keeps only the second (with $\alpha \equiv 0$).

**The Gaussian reduced problem.** Under Gaussian marginals $\mu_0 = \mathcal{N}(0,\Gamma_0)$, $\mu_T = \mathcal{N}(0,\Gamma_T)$, one may restrict to affine drifts $\alpha_t = A_t X_t$ and deterministic diffusions $\Sigma_t$. The covariance $\Gamma_t$ satisfies

$$\dot\Gamma = A_t\Gamma_t + \Gamma_t A_t^\top + \Sigma_t\Sigma_t^\top,$$

and the cost reduces to

$$J = \int_0^T\left[\frac{1}{2}\operatorname{tr}(A_t^2\Gamma_t) + \frac{\beta}{2}\|\Sigma_t\Sigma_t^\top - I_d\|_F^2\right]dt.$$

The reduction is non-trivial because it requires a Jensen/convexity argument to show that stochastic controls cannot beat deterministic ones.

**The costate (adjoint) variable $p(t)$.** In the Pontryagin framework, $p(t)$ is conjugate to $\gamma(t)$. Its equation of motion,

$$\dot p = 2p^2,$$

has the closed-form solution $p(t) = p_0/(1-2p_0 t)$, which blows up in finite time if $p_0 > 0$ and $t$ reaches $1/(2p_0)$. Admissibility requires $1-2p_0 T > 0$, i.e., the blowup time must exceed $T$. This is the source of the solvability boundary.

**The solvability boundary $\gamma_T^*$.** For fixed $\gamma_0, \beta, T > 0$, define

$$\gamma_T^* = \frac{\gamma_0 + \beta T^2}{(1 + 2\beta T)^2}.$$

This is the minimum target variance achievable at finite cost. Its non-trivial nature is that it is always strictly positive (unlike the Schrödinger bridge, where any $\gamma_T > 0$ is achievable in the $\beta\to\infty$ limit).

**The scalar boundary value quadratic.** The shooting problem for the initial costate $p_0$ reduces, via an integrating factor $\varphi(t) = \gamma(t)/(1-2p_0 t)^2$, to a single quadratic equation in $v = 1/(1-2p_0 T)$:

$$v^2\!\left(\gamma_T + \frac{1}{4\beta}\right) - Tv - \left(\gamma_0 + \frac{1}{4\beta}\right) = 0.$$

This is the key structural reduction: an infinite-dimensional variational problem collapses to finding the positive root of a degree-2 polynomial.

**The matrix Riccati equation (multi-d).** In $d$ dimensions the adjoint equation becomes

$$\dot P = 2P^2, \qquad P(t) = P_0(I - 2P_0 t)^{-1}, \quad P_0\in S_d.$$

When $\Gamma_0$ and $\Gamma_T$ do not commute, $P_0$ has non-trivial off-diagonal entries coupling coordinate directions, producing genuinely multi-dimensional phenomena absent in the scalar or commuting cases.

## Main Results {#main-results}

:::theorem{id=thm:1d label="One-Dimensional Optimizer"}
Let $\gamma_0, \gamma_T > 0$, $\beta > 0$, and $T > 0$. Define
$$v = \frac{T + \sqrt{T^2 + 4\bigl(\gamma_T + \tfrac{1}{4\beta}\bigr)\bigl(\gamma_0 + \tfrac{1}{4\beta}\bigr)}}{2\bigl(\gamma_T + \tfrac{1}{4\beta}\bigr)},$$
and set $p_0 = (v-1)/(2vT)$. Then the unique optimal controls are
$$\alpha^*(t) = \frac{-2p_0}{1 - 2p_0 t}, \qquad \sigma^{*2}(t) = 1 - \frac{p_0}{\beta(1 - 2p_0 t)}.$$
The optimal costate is $p(t) = p_0/(1 - 2p_0 t)$, and the conserved Hamiltonian along the optimal trajectory is
$$H^* = -2p_0^2 \gamma_0 + p_0 - \frac{p_0^2}{2\beta}.$$
:::

The optimal drift is a time-dependent mean-reversion rate $-2p(t)$ that diverges as $t\to 1/(2p_0)$; the optimal volatility is a decreasing function of time that "squeezes" toward zero. Both controls are determined by a single scalar $p_0$ found by solving a quadratic. The variance trajectory is then recovered by integrating the controlled ODE with these explicit coefficients. The conserved Hamiltonian provides an immediate formula for the optimal value.

**Why it's surprising:** The entire infinite-dimensional optimal control problem collapses to finding the positive root of a single quadratic polynomial — a remarkable algebraic simplification driven by the Bernoulli structure of the adjoint equation $\dot p = 2p^2$.

---

:::theorem{id=thm:solvability label="Solvability Boundary"}
Let $\beta > 0$, $T > 0$, and $\gamma_0 > 0$. Define the critical target variance
$$\gamma_T^* = \frac{\gamma_0 + \beta T^2}{(1 + 2\beta T)^2}.$$
Then:
(a) The Gaussian SBB with data $(\gamma_0, \gamma_T, \beta, T)$ is solvable if and only if $\gamma_T \ge \gamma_T^*$.
(b) At $\gamma_T = \gamma_T^*$, the optimal terminal volatility degenerates: $\sigma^*(T) = 0$.
(c) $\gamma_T^* > 0$ for all $\beta, T > 0$.
(d) As $\beta \to \infty$: $\gamma_T^* \to 0$.
(e) As $\beta \to 0$: $\gamma_T^* \to \gamma_0$.
:::

For fixed $\beta$ and $T$, there is a hard floor below which no finite-cost Gaussian SBB exists. This floor is strictly positive for every finite $\beta$ — even when the penalty parameter is large, one cannot reach arbitrarily small target variances. In the Schrödinger limit ($\beta\to\infty$) the floor vanishes, recovering the classical result that any positive $\gamma_T$ is reachable with unit diffusion. In the Bass limit ($\beta\to 0$) the floor rises to $\gamma_0$, reflecting that a driftless process can only increase its variance.

**Why it's surprising:** The condition $\beta T > 1$ from the original paper ensures universal solvability across *all* marginals, but this theorem shows that specific marginal pairs may be solvable even when $\beta T \leq 1$, and conversely that even with $\beta T > 1$ there are unreachable target variances — the infeasible region is marginal-dependent and always non-empty.

---

:::theorem{id=thm:nongaussian label="Second-Moment Lower Bound (Non-Gaussian)"}
Let $\mu_0, \mu_T \in \mathcal{P}_2(\mathbb{R})$ with $m_0 = m_T = 0$. Define $\gamma_0 = \int x^2\,d\mu_0$, $\gamma_T = \int x^2\,d\mu_T$. If
$$\gamma_T < \frac{\gamma_0 + \beta T^2}{(1 + 2\beta T)^2},$$
then $\mathrm{SBB}(\mu_0, \mu_T) = +\infty$. That is, the Gaussian solvability boundary $\gamma_T^*$ is a universal lower bound on the reachable second moment for any centered marginal pair.
:::

The Gaussian threshold is not an artifact of the Gaussian restriction: it is a structural constraint on the second-moment dynamics of *any* admissible semimartingale. If the target second moment is below $\gamma_T^*$, no transport plan — Gaussian or otherwise — can achieve it at finite cost. Non-Gaussian marginals may have an even larger infeasible region (due to higher-moment constraints), but the Gaussian boundary provides a universal certificate.

**Why it's surprising:** By a Cauchy–Schwarz/Jensen reduction, the cost of any stochastic transport is lower bounded by the cost of a *deterministic* control problem (the Gaussian one), so the Gaussian infeasibility propagates to all distributions — a rare instance where Gaussian optimality provides a universal impossibility result.

---

:::theorem{id=thm:multid label="Multi-Dimensional Optimizer"}
Let $\Gamma_0, \Gamma_T \in S_d^{++}$, $\beta > 0$, $T > 0$. The Pontryagin system yields:
(a) The optimal controls are
$$A^*(t) = -2P_0(I - 2P_0 t)^{-1}, \qquad \Sigma^{*2}(t) = I - \frac{P_0}{\beta}(I - 2P_0 t)^{-1},$$
where $P_0 \in S_d$ is the initial costate.
(b) The matrix adjoint equation $\dot P = 2P^2$ has explicit solution $P(t) = P_0(I - 2P_0 t)^{-1}$.
(c) When $\Gamma_0\Gamma_T = \Gamma_T\Gamma_0$, the problem decomposes into $d$ independent scalar problems with data $(\gamma_0^{(k)}, \gamma_T^{(k)}, \beta, T)$.
:::

The $d$-dimensional structure mirrors the scalar case almost perfectly: the scalar Bernoulli ODE $\dot p = 2p^2$ becomes the matrix Bernoulli equation $\dot P = 2P^2$, which admits the same resolvent-type formula. The commutativity condition for decoupling is natural (simultaneous diagonalizability), and when it fails, the off-diagonal entries of $P_0$ produce genuine inter-coordinate coupling.

**Why it's surprising:** The matrix equation $\dot P = 2P^2$ has a perfectly explicit solution $P_0(I-2P_0 t)^{-1}$ that commutes with $P_0$ by a simple algebraic identity — this commutativity, which holds even when $P_0$ has mixed signs, is the key that makes the multi-dimensional problem as tractable as the scalar one.

## Proof Sketches {#proofs}

:::proof-sketch{for=thm:1d}
1. **Pontryagin Hamiltonian and FOCs.** Write the control Hamiltonian $H = \frac{1}{2}\alpha^2\gamma + \frac{\beta}{2}(\sigma^2-1)^2 + p(2\alpha\gamma + \sigma^2)$; stationarity in $\alpha$ gives $\alpha^* = -2p$ and stationarity in $\sigma^2$ gives $\sigma^{*2} = 1 - p/\beta$.
2. **Adjoint equation in closed form.** Compute $\dot p = -\partial H/\partial\gamma = 2p^2$ (a Bernoulli ODE) with explicit solution $p(t) = p_0/(1-2p_0 t)$.
3. **Integrating factor reduction.** Set $\varphi(t) = \gamma(t)/(1-2p_0 t)^2$; differentiation collapses the variance ODE to $\dot\varphi = (1-2p_0 t)^{-2} - p_0\beta^{-1}(1-2p_0 t)^{-3}$, integrable in closed form.
4. **Boundary value problem as a quadratic.** Evaluating the integrated equation at $t=T$ and substituting $v = 1/(1-2p_0 T)$ yields the single quadratic $v^2(\gamma_T + 1/(4\beta)) - Tv - (\gamma_0 + 1/(4\beta)) = 0$, whose unique positive root gives $v$ and hence $p_0$.
5. **Hamiltonian conservation.** Since $H$ has no explicit time dependence, $H^*$ is constant; evaluating at $t=0$ with $(\alpha^*(0),\sigma^{*2}(0),p_0,\gamma_0)$ gives the closed-form value $H^* = -2p_0^2\gamma_0 + p_0 - p_0^2/(2\beta)$.
:::

:::proof-sketch{for=thm:solvability}
1. **Admissibility constraint.** Since $p(t)$ is increasing (for $p_0>0$), the binding constraint $\sigma^{*2}(t) = 1 - p(t)/\beta \geq 0$ is tightest at $t=T$, giving $v \leq 1 + 2\beta T$.
2. **Critical threshold by substitution.** Plug $v^* = 1 + 2\beta T$ into the quadratic BVP and solve algebraically for the corresponding $\gamma_T^*$; the numerator simplifies to $\gamma_0 + \beta T^2$ after cancellation.
3. **Monotonicity via implicit function theorem.** Differentiate the quadratic $F(v,\gamma_T)=0$ to show $dv/d\gamma_T < 0$: larger $\gamma_T$ maps to smaller $v$, so $\gamma_T \geq \gamma_T^*$ if and only if $v \leq v^*$, completing the if-and-only-if characterization.
4. **Limit analysis.** For $\beta\to\infty$: $\gamma_T^* \sim 1/(4\beta)\to 0$. For $\beta\to 0$: $\gamma_T^* \to \gamma_0/1 = \gamma_0$. Positivity follows directly from $\gamma_0>0$ and $\beta T^2>0$.
:::

:::proof-sketch{for=thm:nongaussian}
1. **Itô decomposition of the second moment.** For any admissible plan $P$, write $\gamma(T) = \gamma(0) + \int_0^T(2\mathbb{E}[\alpha_t X_t] + \mathbb{E}[\sigma_t^2])\,dt$ via Itô's formula.
2. **Cauchy–Schwarz on the drift.** Apply $\mathbb{E}[\alpha_t X_t]^2 \leq \mathbb{E}[\alpha_t^2]\cdot\gamma(t)$ to lower-bound $\frac{1}{2}\mathbb{E}[\alpha_t^2] \geq \frac{\mathbb{E}[\alpha_t X_t]^2}{2\gamma(t)}$.
3. **Jensen on the diffusion.** Apply Jensen to $s\mapsto(s-1)^2$ to get $\mathbb{E}[(\sigma_t^2-1)^2] \geq (\mathbb{E}[\sigma_t^2]-1)^2$.
4. **Reduction to Gaussian deterministic control.** Define $\bar\alpha(t) = \mathbb{E}[\alpha_t X_t]/\gamma(t)$ and $\bar\sigma^2(t) = \mathbb{E}[\sigma_t^2]$; the cost is bounded below by the one-dimensional Gaussian problem with these deterministic controls, which is infeasible when $\gamma_T < \gamma_T^*$ by Theorem~\ref{thm:solvability}.
:::

:::proof-sketch{for=thm:multid}
1. **Matrix Hamiltonian and FOCs.** Write the matrix Hamiltonian with symmetric costate $P$; stationarity gives $A^* = -2P$ and $\Sigma^{*2} = I - P/\beta$, exactly mirroring the scalar case.
2. **Adjoint equation.** Compute $\dot P = -\partial H/\partial\Gamma$ (using the trace inner product) to obtain $\dot P = 2P^2$; verify the solution $P(t) = P_0(I-2P_0 t)^{-1}$ using the fact that $P_0$ commutes with $(I-2P_0 t)^{-1}$.
3. **Commuting case decomposition.** When $\Gamma_0$ and $\Gamma_T$ commute, simultaneous diagonalizability forces $P_0$ to be diagonal in the shared eigenbasis, decoupling all matrix equations into $d$ independent scalar problems of the form in Theorem~\ref{thm:1d}.
:::

## Numerical Illustration {#numerics}

Three numerical examples illustrate the theory. **Example 7.1** (baseline, $\gamma_0=1$, $\gamma_T=2$, $\beta=T=1$) confirms a clean closed-form solution: the quadratic gives $v=1$, hence $p_0=0$, the optimal process is a standard Brownian motion with zero cost — consistent with the fact that $\sigma^2=1$ is the unconstrained diffusion minimum.

**Example 7.2** (near the boundary, $\gamma_0=1$, $\gamma_T=2/9=\gamma_T^*$, $\beta=T=1$) verifies terminal degeneracy: $v=3$, $p_0=1/3$, and direct evaluation gives $\sigma^{*2}(1) = 1 - 1/(3-2) = 0$, confirming Theorem~\ref{thm:solvability}(b). The table in Example 7.3 traces $\gamma_T^*$ across five values of $\beta$ ($0.1$ through $100$), quantitatively showing the monotone expansion of the solvable region as $\beta$ increases.

**Example 10.1** (non-commuting $2\times 2$ matrices) is the main numerical experiment. With $\Gamma_0 = \bigl(\begin{smallmatrix}2&1\\1&1\end{smallmatrix}\bigr)$ and $\Gamma_T = \bigl(\begin{smallmatrix}1&0\\0&3\end{smallmatrix}\bigr)$ (non-commuting, verified by direct computation), a Newton shooting method yields $P_0 \approx \bigl(\begin{smallmatrix}0.183&0.096\\0.096&-0.154\end{smallmatrix}\bigr)$. The off-diagonal entry $P_0^{(12)}\approx 0.096$ is non-zero, demonstrating that the optimal costate couples both coordinate directions to simultaneously steer the cross-covariance from $(\Gamma_0)_{12}=1$ to $(\Gamma_T)_{12}=0$. The eigenvalues of $P_0$ have opposite signs ($\approx +0.23$ and $\approx -0.20$), meaning the optimal process inflates variance in one eigendirection while contracting it in the other — a phenomenon invisible to scalar or commuting analysis. The terminal volatility eigenvalues ($\approx 0.64$ and $\approx 1.13$) are both positive, confirming this marginal pair lies strictly inside the solvable region.

## Connections {#connections}

- [variance_options](/papers/variance_options): both papers control variance dynamics via Pontryagin/HJB methods and encounter solvability thresholds determined by quadratic Riccati-type equations.
- [mv_games](/papers/mv_games): mean–variance covariance dynamics under controlled drift and diffusion appear in both settings; the Gaussian reduction and covariance ODE $\dot\Gamma = A\Gamma + \Gamma A^\top + \Sigma\Sigma^\top$ is a shared structural object.
- [sr_p005](/papers/sr_p005): Schrödinger bridge / optimal transport techniques for marginal-constrained semimartingales overlap directly; the Gaussian Schrödinger bridge limit ($\beta\to\infty$) recovered here connects to results there.
- [sr_p006](/papers/sr_p006): the Bass martingale transport limit ($\beta\to 0$) and martingale interpolation between marginals is a shared theme.