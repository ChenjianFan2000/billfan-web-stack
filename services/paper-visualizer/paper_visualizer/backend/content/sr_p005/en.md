---
paper_slug: sr_p005
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

A **variance call option** with strike $K$ and maturity $T$ pays $\bigl(\frac{1}{T}\int_0^T V_s\eta^2(S_s)\,ds - K\bigr)^+$, where $V_t$ is the instantaneous variance and $\eta(S_t)$ is the local volatility function. Following the September 2024 launch of CBOE S&P 500 Variance Futures (ticker VA), analytical pricing methods for these instruments have renewed urgency. The short-maturity regime $T\to 0$ is the natural analytical entry point: it isolates the essential geometry of the problem via a large-deviation rate function $I_\rho$, with option prices behaving as $C(T)\sim e^{-I_\rho/T}$.

Under a general local-stochastic volatility (LSV) model, the asset $S_t$ and variance $V_t$ are driven by correlated Brownian motions with correlation $\rho\in(-1,1)$. Pirjol, Wang, and Zhu (2025) established that $\lim_{T\to 0} T\log C(T) = -I_\rho(S_0,V_0,K)$, where $I_\rho$ is the solution to a **two-dimensional constrained variational problem**: minimize the action $\Lambda_\rho[g,h]$ over trajectories $(g,h)$ in the $(S,V)$ log-space subject to an isoperimetric constraint $\int_0^1 e^{h(t)}\eta^2(e^{g(t)})\,dt = K$. For $\rho=0$ the problem decouples and reduces to a known Asian option rate function; for $\rho=\pm 1$ the singular prefactor $1/(1-\rho^2)$ forces a degeneracy that again yields a one-dimensional problem. For **general $\rho\in(-1,1)\setminus\{0\}$** the problem resisted explicit solution.

This paper fills that gap under the assumption of constant volatility-of-volatility $\sigma(v)\equiv\sigma_0$. Three complementary approaches are developed: (i) a Hamiltonian conservation law that constrains optimal trajectories, (ii) a one-parameter family of upper bounds reducing the two-dimensional problem to a sequence of one-dimensional Asian-option problems, and (iii) a perturbation expansion in $\rho$ around the known $\rho=0$ solution. Together these provide tight, computable pricing approximations across the full correlation range.

## Key Objects {#objects}

**The LSV model and realized variance.** The asset and variance satisfy
$$\frac{dS_t}{S_t} = \eta(S_t)\sqrt{V_t}\bigl(\rho\,dZ_t + \sqrt{1-\rho^2}\,dW_t\bigr), \qquad \frac{dV_t}{V_t} = \mu(V_t)\,dt + \sigma(V_t)\,dZ_t,$$
with $W,Z$ independent Brownian motions. The **realized variance** is $[{\log S}]_T = \int_0^T V_s\eta^2(S_s)\,ds$. The non-trivial feature is the entanglement of the local volatility $\eta(S)$ with the stochastic variance $V$, making path-dependent payoffs genuinely two-dimensional.

**The rate function and variational problem.** For out-of-the-money variance calls,
$$I_\rho(S_0,V_0,K) = \inf_{\substack{g(0)=\log S_0,\;h(0)=\log V_0 \\ \int_0^1 e^{h(t)}\eta^2(e^{g(t)})\,dt = K}} \Lambda_\rho[g,h],$$
where the action in velocity variables $a(t) = g'(t)/\bigl(\eta(e^{g(t)})\sqrt{e^{h(t)}}\bigr)$ and $b(t) = h'(t)/\sigma_0$ is
$$\Lambda_\rho[g,h] = \frac{1}{2(1-\rho^2)}\int_0^1\bigl(a(t)^2 - 2\rho\,a(t)\,b(t) + b(t)^2\bigr)\,dt.$$
The difficulty: when $\rho\neq 0$ the integrand mixes the $g$ and $h$ directions, preventing decoupling.

**The alpha-coupling function.** For $\alpha\in\mathbb{R}$, $F_\alpha:(0,\infty)\to(0,\infty)$ is defined by the implicit relation
$$\int_{S_0}^{F_\alpha(x)}\frac{dy}{y\,\eta(y)} = \frac{2\alpha}{\sigma_0}\bigl(\sqrt{x}-\sqrt{V_0}\bigr), \qquad F_\alpha(V_0)=S_0.$$
This **square-root coupling** ties the asset path to the variance path; its defining feature is that the proportionality ansatz $a(t)=\alpha\,b(t)$ integrates exactly to give $e^{g(t)}=F_\alpha(e^{h(t)})$, collapsing the two-dimensional path space to one dimension.

**The effective payoff and one-dimensional rate function.** Given the coupling, define $G_\alpha(x) = x\,\eta^2(F_\alpha(x))$ and the one-dimensional rate function
$$J_\alpha(V_0,K) = \inf_{\substack{h(0)=\log V_0 \\ \int_0^1 G_\alpha(e^{h(t)})\,dt = K}} \frac{1}{2\sigma_0^2}\int_0^1\bigl(h'(t)\bigr)^2\,dt.$$
This is an **Asian option rate function** with modified local volatility $\sqrt{G_\alpha(v)/v}$, computable by the methods of Pirjol–Zhu (2023).

**The coefficient function.** The scalar prefactor
$$C(\alpha,\rho) = \frac{\alpha^2 - 2\alpha\rho + 1}{1-\rho^2}$$
satisfies $C(\alpha,\rho)\geq 1$ for all $\alpha,\rho$, with equality at $\alpha=\rho$. It encodes how much the action inflates when the trajectory is constrained to the $\alpha$-proportionality subspace instead of optimized freely.

**The Asian option rate function $J(V_0,z)$.** From Pirjol–Zhu (2023), $J(V_0,z)$ is the rate function for the short-maturity asymptotics of Asian options in a pure local volatility model; it solves a one-dimensional isoperimetric problem in $H^1$ and admits an explicit finite-dimensional reduction. It serves as the $\rho$-independent building block that appears in the exact formula for constant $\eta$.

## Main Results {#main-results}

:::theorem{id="thm:hamiltonian" label="Hamiltonian Conservation (Proposition 2.1)"}
Assume $\sigma(v)\equiv\sigma_0$. Let $(g,h)$ be a smooth critical point of the constrained variational problem. Define the Hamiltonian
$$\mathcal{H}(t) = \frac{1}{2(1-\rho^2)}\bigl(a(t)^2 - 2\rho\,a(t)\,b(t) + b(t)^2\bigr) - \lambda\,e^{h(t)}\eta^2(e^{g(t)}).$$
Then $\mathcal{H}(t) = E$ for all $t\in[0,1]$, where $E$ is a constant determined by the boundary conditions.
:::

The Lagrangian density has no explicit time dependence when $\sigma$ is constant, so by Noether's theorem (time-translation symmetry) the associated Hamiltonian is conserved. Concretely, the "kinetic energy" $\frac{1}{2(1-\rho^2)}\|w(t)\|^2$ and the "potential energy" $\lambda e^h\eta^2(e^g)$ must sum to a constant $E$ along every optimal trajectory. This reduces the effective dimensionality of the Euler–Lagrange system from four to three, providing a structural constraint that any numerical or analytical solver must satisfy.

**Why it's surprising:** The variational problem is not a classical mechanics problem — it arises from a financial large-deviation principle — yet it admits a perfect mechanical analogy with conserved energy. This conservation law was not previously noted in the variance options literature.

---

:::theorem{id="thm:alpha" label="Alpha-Parametric Upper Bound (Theorem 3.1)"}
Assume $\sigma(v)\equiv\sigma_0$. For any $\rho\in(-1,1)$,
$$I_\rho(S_0,V_0,K) \leq \inf_{\alpha\in\mathbb{R}}\,C(\alpha,\rho)\cdot J_\alpha(V_0,K),$$
where
$$C(\alpha,\rho) = \frac{\alpha^2 - 2\alpha\rho + 1}{1-\rho^2},$$
and $J_\alpha(V_0,K)$ is the one-dimensional rate function
$$J_\alpha(V_0,K) = \inf_{\substack{h(0)=\log V_0 \\ \int_0^1 G_\alpha(e^{h(t)})\,dt = K}} \frac{1}{2\sigma_0^2}\int_0^1 \bigl(h'(t)\bigr)^2\,dt.$$
:::

The theorem converts the intractable two-dimensional variational problem into a one-parameter family of one-dimensional problems, each of which is an Asian option rate function and hence explicitly solvable. For each fixed $\alpha$, restricting to paths satisfying $a(t)=\alpha b(t)$ (the proportionality ansatz) yields the factored bound $C(\alpha,\rho)\cdot J_\alpha$. Optimizing over $\alpha$ then produces the tightest bound in this family. Setting $\alpha=\rho$ recovers a unit-coefficient bound $I_\rho\leq J_\rho$ (Corollary 3.2). When $\eta$ is constant the bound is exact (Corollary 3.4). Numerically, the improvement over the best prior bound reaches 75% for $\rho=-0.7$.

**Why it's surprising:** A one-parameter ansatz — constraining the ratio $a/b$ to be constant along the path — is in principle a severe restriction on the full function space, yet it produces the exact answer when $\eta$ is constant and near-exact answers for realistic non-constant $\eta$.

---

:::theorem{id="cor:exactconst" label="Exactness for Constant Local Volatility (Corollary 3.4)"}
When $\eta(x)\equiv\eta_0$ (constant), the alpha-parametric bound is exact:
$$I_\rho(S_0,V_0,K) = J\!\left(V_0,\,\frac{K}{\eta_0^2}\right),$$
which is independent of $\rho$. Here $J(V_0,z)$ is the Asian option rate function from Pirjol–Zhu (2023).
:::

When the local volatility is flat, the asset price $S_t$ does not feed back into the variance constraint, so the optimal $g$-path can be chosen freely to minimize the action. The unconstrained minimization over $g$ forces $a=\rho b$ pointwise, which is exactly the $\alpha=\rho$ proportionality, and $C(\rho,\rho)=1$. The effective payoff reduces to $G_\rho(x)=x\eta_0^2$, yielding the pure Asian rate function rescaled by $\eta_0^2$.

**Why it's surprising:** The rate function is completely $\rho$-independent in the constant-$\eta$ case. Correlation between asset and variance noises has zero effect on the short-maturity price of variance options when there is no leverage function.

---

:::theorem{id="thm:perturb" label="First-Order Perturbation Expansion (Theorem 4.1)"}
Under the regularity assumption (unique $H^1$ minimizer, $C^1$ in $\rho$) with $\sigma(v)\equiv\sigma_0$, the rate function admits the expansion
$$I_\rho(S_0,V_0,K) = I_0(S_0,V_0,K) - \rho\int_0^1 a_0(t)\,b_0(t)\,dt + O(\rho^2),$$
where $I_0=I_{\rho=0}$ is the uncorrelated rate function, and $(a_0,b_0)$ are the velocity variables evaluated at the $\rho=0$ optimal trajectories $(g_0,h_0)$.
:::

The envelope theorem says: when differentiating the infimum with respect to a parameter, the derivative of the value function equals the partial derivative of the Lagrangian with respect to that parameter, evaluated at the optimum. Here, $\partial\Lambda_\rho/\partial\rho\big|_{\rho=0} = -\int_0^1 a_0 b_0\,dt$. The sign has immediate financial content: for an OTM variance call with leverage ($\eta$ decreasing, $\rho<0$), the optimal $\rho=0$ trajectory has $a_0,b_0>0$, so $I_\rho$ increases with $|\rho|$ for $\rho<0$, meaning negative correlation suppresses variance option prices.

**Why it's surprising:** The first-order correction requires only the $\rho=0$ solution — which is already known explicitly — and no additional optimization. The correction is thus completely explicit and computationally free given the uncorrelated problem.

## Proof Sketches {#proofs}

:::proof-sketch{for="thm:hamiltonian"}
1. **Time-autonomy of the Lagrangian**: Since $\sigma\equiv\sigma_0$, the Lagrangian density $\mathcal{L}(g,g',h,h')$ has no explicit $t$-dependence, making the system autonomous.
2. **Computation of conjugate momenta**: Direct differentiation gives $p_g = (a-\rho b)/[(1-\rho^2)\eta(e^g)\sqrt{e^h}]$ and $p_h = (b-\rho a)/[(1-\rho^2)\sigma_0]$.
3. **Legendre transform**: Compute $p_g g' + p_h h' = (a^2-2\rho ab+b^2)/(1-\rho^2)$, which is exactly twice the Lagrangian kinetic part; subtracting $\mathcal{L}$ yields $\mathcal{H}$ as in the statement.
4. **Conservation**: By the standard theory of autonomous Lagrangian systems (Noether, time-translation), $d\mathcal{H}/dt=0$ along Euler–Lagrange solutions.
:::

:::proof-sketch{for="thm:alpha"}
1. **Proportionality ansatz**: Restrict to paths where $a(t) = \alpha b(t)$ for all $t$; since this is a subspace of the full feasible set, its infimum is an upper bound.
2. **Integration to determine $g$ from $h$**: The ansatz integrates to $\Phi(e^{g(t)}) = \frac{2\alpha}{\sigma_0}(\sqrt{e^{h(t)}}-\sqrt{V_0})$, i.e., $e^{g(t)}=F_\alpha(e^{h(t)})$, collapsing the two-dimensional path to one.
3. **Factorization of the action**: Substituting $a=\alpha b$ into $\Lambda_\rho$ gives $\Lambda_\rho = C(\alpha,\rho)\cdot\frac{1}{2\sigma_0^2}\int_0^1(h')^2\,dt$, a scalar multiple of the $h$-only action.
4. **Constraint transformation**: With $g=\log F_\alpha(e^h)$, the isoperimetric constraint becomes $\int_0^1 G_\alpha(e^h)\,dt=K$, which is exactly the Asian option constraint for $J_\alpha$.
5. **Optimization over $\alpha$**: Since the bound holds for every $\alpha$, taking the infimum over $\alpha$ yields the sharpest bound in the family.
:::

:::proof-sketch{for="thm:perturb"}
1. **Envelope theorem**: Differentiate the value function $I_\rho = \inf_{(g,h)\in\mathcal{A}}\Lambda_\rho[g,h]$ with respect to $\rho$; by the envelope theorem, $dI_\rho/d\rho\big|_{\rho=0} = \partial\Lambda_\rho/\partial\rho\big|_{(g_0,h_0),\rho=0}$.
2. **Explicit derivative of action**: From $\Lambda_\rho = \frac{1}{2(1-\rho^2)}\int(a^2-2\rho ab+b^2)\,dt$, differentiate with respect to $\rho$ and evaluate at $\rho=0$: all $\rho$-dependent prefactors vanish, leaving $-\int_0^1 a_0(t)b_0(t)\,dt$.
3. **Taylor remainder bound**: The $O(\rho^2)$ bound follows from the fact that the second derivative of $\Lambda_\rho$ with respect to $\rho$ is controlled by the $C^2$-norm of $\eta$ and the $H^1$-norm of the optimizers.
:::

## Numerical Illustration {#numerics}

The numerical experiments use the **Tanh local volatility model** $\eta(S) = f_0 + f_1\tanh(\log(S/S_0)-x_0)$ with parameters $V_0=1$, $\sigma_0=2$, $f_0=1$, $f_1=-0.5$, $x_0=0$ (a decreasing, leverage-type local volatility). For each $(\rho, K)$ pair, the one-dimensional rate function $J_\alpha(V_0,K)$ is computed for a grid of $\alpha$ values using the Pirjol–Zhu (2023) Asian option algorithm, and the product $C(\alpha,\rho)\cdot J_\alpha$ is minimized numerically over $\alpha$.

Table 1 reports three OTM strike levels ($K=1.2,1.5,2.0$) and six correlation values ($\rho\in\{-0.7,-0.5,-0.3,+0.3,+0.5,+0.7\}$). The alpha-optimal bound ("$\alpha$-opt") is compared to the Proposition 13 bound of Pirjol–Wang–Zhu (2025) ("P13"), which equals $J(V_0,K/\eta_0^2)/(1-\rho^2)$. The improvement is dramatic for negative correlation: at $\rho=-0.7$, $K=1.5$, the $\alpha$-optimal bound reduces P13 by 75%. For positive $\rho$ the improvement is modest (0–8%), reflecting that the square-root coupling is better adapted to the leverage regime.

The optimal coupling parameter $\alpha^*$ shows a systematic pattern: it lies consistently to the left of $\rho$ (more negative), tracking the decreasing shape of $\eta$ in the Tanh model. As $\rho\to +0.5$, $\alpha^*$ approaches zero, and the improvement nearly vanishes — consistent with the analytical result that the bound is exact for constant $\eta$ at $\alpha=\rho$. The perturbation expansion $I_\rho \approx I_0 - \rho\int_0^1 a_0 b_0\,dt$ is verified to be accurate for $|\rho|\leq 0.3$, with errors growing as expected for larger $|\rho|$.

## Connections {#connections}

- [variance_options](/papers/variance_options): The foundational paper (Pirjol–Wang–Zhu 2025) whose two-dimensional variational problem this paper solves; the $\rho=0$ and $\rho=\pm 1$ explicit solutions and Propositions 13, 14, 17 are the direct starting points.
- [sr_p001](/papers/sr_p001): The Pirjol–Zhu (2023) Asian option rate function $J(V_0,z)$ and its finite-dimensional reduction algorithm are the core computational engine for evaluating $J_\alpha$ in the alpha-parametric bound.
- [sr_p006](/papers/sr_p006): The Pirjol–Zhu (2024) LSV Asian option paper uses a logarithmic coupling technique that is the direct methodological predecessor to the square-root coupling introduced here; the two couplings are complementary and their comparison motivates the combined bound.
- [var_ratio](/papers/var_ratio): Work on short-maturity asymptotics for variance-ratio and related path-dependent options in the LSV framework shares the large-deviation/variational-problem structure and the role of local volatility geometry.