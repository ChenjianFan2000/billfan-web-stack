---
paper_slug: sr_p006
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

The overdamped Langevin diffusion $dX_t = -\nabla U(X_t)\,dt + \sqrt{2}\,dB_t$ is the canonical continuous-time algorithm for sampling from a target distribution $\pi \propto e^{-U}$. Its practical use in Bayesian inference, statistical mechanics, and machine learning hinges on quantitative control of how fast the law of $X_t$ converges to $\pi$. The gold standard tool for this is **exponential Wasserstein contraction**: if two solutions started from different initial conditions satisfy $W_1(\Law(X_t), \Law(X'_t)) \le e^{-ct} W_1(\mu_0, \nu_0)$, then the rate $c$ simultaneously controls the mixing time, the bias of the unadjusted Langevin algorithm (ULA), and the propagation-of-chaos error for mean-field particle systems.

When $U$ is globally $m$-strongly convex the story is clean: synchronous coupling immediately gives contraction at rate $m$ in $W_2$. The difficult and practically important case is $U = U_0 + V$ where $U_0$ is $m$-strongly convex but $V$ is a bounded-gradient, possibly non-convex perturbation (e.g., a log-likelihood with bounded features). The full potential $U$ need not be convex and may have metastable wells. The foundational tool for this regime is Eberle's 2016 reflection-coupling theorem, which proves exponential $W_1$-type contraction at a variational rate determined by a Sturm–Liouville problem — but the rate is generally not available in closed form.

This paper fills a concrete gap: for the specific decomposition $U = U_0 + V$ with $\|\nabla V\|_\infty \le K$ and $K < \sqrt{m}$ (the **subcritical regime**), it carries out Eberle's program explicitly, extracting the closed-form rate $c^\star = m - K\sqrt{m}$ and an explicit power-law concave distance $f$. The result is dimension-free, depends on $V$ only through $K = \|\nabla V\|_\infty$ (not $\|V\|_\infty$), and plugs directly into ULA discretisation error bounds and mean-field propagation-of-chaos estimates — all with fully explicit constants.

## Key Objects {#objects}

**Overdamped Langevin SDE.** The stochastic differential equation
$$dX_t = -\nabla U(X_t)\,dt + \sqrt{2}\,dB_t, \qquad U = U_0 + V,$$
where $U_0$ is $m$-strongly convex (Assumption A1) and $\|\nabla V\|_\infty \le K$ (Assumption A2). Non-trivial because $U$ itself need not be convex.

**Eberle reflection coupling.** Given a solution $(X_t)$, the companion process $(X'_t)$ is defined by
$$dX'_t = -\nabla U(X'_t)\,dt + \sqrt{2}(I - 2e_t e_t^\top)\,dB_t, \qquad e_t := \frac{X_t - X'_t}{|X_t - X'_t|},$$
run until the coupling time $\tau = \inf\{t : X_t = X'_t\}$, after which $X'_t \equiv X_t$. Non-trivial because the reflected noise makes both processes marginally correct solutions while maximising the chance of collision.

**Radial process.** The scalar process $r_t := |X_t - X'_t|$ satisfies the one-dimensional SDE
$$dr_t = -e_t \cdot (\nabla U(X_t) - \nabla U(X'_t))\,dt + 2\sqrt{2}\,dW_t$$
for a scalar Brownian motion $W_t$. Non-trivial because the $d$-dimensional coupling reduces to a one-dimensional diffusion, enabling explicit calculations.

**Explicit parameters and concave distance.** In the subcritical regime $K < \sqrt{m}$, set
$$\beta := \frac{K}{\sqrt{m}} \in [0,1), \qquad R_0 := \frac{2}{\sqrt{m}}, \qquad c^\star := m(1-\beta) = m - K\sqrt{m},$$
and define the **concave distance function**
$$f(r) := \frac{R_0}{1-\beta}\Bigl[(1 + r/R_0)^{1-\beta} - 1\Bigr], \qquad r \ge 0.$$
Non-trivial because this specific power-law shape is the unique maximiser (within the two-parameter family) of the achievable contraction rate.

**Modified Wasserstein metric.** For probability measures $\mu, \nu$ on $\mathbb{R}^d$,
$$W_{1,f}(\mu, \nu) := \inf_{\pi} \int f(|x - y|)\,d\pi(x,y),$$
the Kantorovich–Rubinstein transport with cost $f(|x-y|)$. Since $f(r) \le r$ and $f$ is bi-Lipschitz equivalent to the identity on bounded sets, $W_{1,f}$ is sandwiched between two multiples of the standard $W_1$ on bounded coupling sets.

## Main Results {#main-results}

:::theorem{id=thm:main label="Wasserstein-1 Contraction (Main Theorem)"}
Assume A1–A3. Let $(X_t)_{t\ge 0}$, $(X'_t)_{t\ge 0}$ be two solutions of $dX_t = -\nabla U(X_t)\,dt + \sqrt{2}\,dB_t$ coupled via the Eberle reflection coupling, with (possibly different) initial laws $\mu_0, \nu_0$. Then for all $t \ge 0$,
$$\mathbb{E}\bigl[f(|X_t - X'_t|)\bigr] \;\le\; e^{-c^\star t}\,\mathbb{E}\bigl[f(|X_0 - X'_0|)\bigr],$$
where $f$ is defined by \eqref{eq:fdef} and $c^\star = m - K\sqrt{m}$. Consequently,
$$W_{1,f}\bigl(\mathrm{Law}(X_t), \mathrm{Law}(X'_t)\bigr) \;\le\; e^{-c^\star t}\,W_{1,f}(\mu_0, \nu_0).$$
:::

The theorem says that in the modified metric $W_{1,f}$, the two Langevin trajectories contract exponentially toward each other at the explicit rate $c^\star = m - K\sqrt{m}$, regardless of the starting laws. As $K \to 0$ the rate recovers the strongly-convex baseline $m$; as $K \nearrow \sqrt{m}$ the rate vanishes linearly. The result is **dimension-free**: $c^\star$ depends only on the two scalar quantities $m$ and $K$, not on $d$ or on $\|V\|_\infty$.

**Why it's surprising:** The rate is independent of $\|V\|_\infty$ — only the gradient sup-norm $K$ appears. This contrasts sharply with the Holley–Stroock perturbation bound for log-Sobolev constants, which degrades as $e^{\mathrm{osc}(V)}$.

---

:::theorem{id=thm:ula label="Discrete-Time Contraction for ULA"}
Assume A1–A4. There exists an absolute constant $C_1 > 0$ such that, for every step size $h \le h_0 := \min(m/(2L^2),\,1/L,\,1/c^\star)$, every initial law $\nu_0$ with $M_0 := \mathbb{E}_{\nu_0}[|X - x^\star|^2] < \infty$, and every $N \ge 1$,
$$W_{1,f}\bigl(\nu_0 P_h^N,\, \pi\bigr) \;\le\; e^{-c^\star N h/2}\,W_{1,f}(\nu_0, \pi) \;+\; \frac{C_1\,L^2\,\sqrt{M^\star + d}\,\sqrt{h}}{c^\star},$$
where $x^\star$ is the minimiser of $U$, $M^\star = M_0 + 4(2K^2 + md)/m^2$, and $P_h$ is the ULA Markov kernel.
:::

This bound has the standard **geometric decay + asymptotic bias** form for MCMC algorithms. The first term decays geometrically at rate $c^\star/2$ (half the continuous-time rate, with the other half absorbed into the discretisation error). The additive bias is $\mathcal{O}(\sqrt{h})$, consistent with the Euler–Maruyama strong error order. The dimension enters only through $\sqrt{M^\star + d}$, a second-moment quantity that scales mildly.

**Why it's surprising:** The contraction rate in discrete time is the *same* $c^\star$ as in continuous time (up to the factor of 2); discretisation does not degrade the spectral gap, only adds a controllable additive bias.

---

:::theorem{id=thm:poc label="Uniform-in-Time Propagation of Chaos"}
Assume A1, A5, and $K < \sqrt{m}$. Assume the initial data are i.i.d.: $X^{i,N}_0 \sim \mu_0$ i.i.d., and let $Y^i_t$ denote the McKean–Vlasov solution with $Y^i_0 = X^{i,N}_0$. Then there exists an absolute constant $C_2 > 0$ such that for every $N \ge 2$, every $t \ge 0$, and every $i \in \{1,\dots,N\}$,
$$W_{1,f}\bigl(\mathrm{Law}(X^{i,N}_t),\, \mu_t\bigr) \;\le\; \frac{C_2\,K}{\sqrt{N-1}\cdot c^\star}, \qquad c^\star = m - K\sqrt{m}.$$
The bound is uniform in time $t$ and dimension-free: the right-hand side does not depend on $t$ or $d$.
:::

Classical Sznitman-type propagation-of-chaos bounds grow as $e^{Lt}/\sqrt{N}$, rendering them useful only on finite time horizons. This result replaces the exponentially growing factor with the constant $2/c^\star$: no matter how long the interacting particle system is run, the single-particle law stays within $\mathcal{O}(K/(c^\star \sqrt{N}))$ of the mean-field limit $\mu_t$.

**Why it's surprising:** The uniform-in-time, dimension-free $1/\sqrt{N}$ rate holds purely because the same contraction $c^\star$ applies to the McKean–Vlasov effective potential — no additional log-Sobolev inequality or entropy argument is needed.

---

:::theorem{id=prop:sharpness label="Sharpness of the Exponent"}
Consider the two-parameter family $f_{R,\beta}(r) := \frac{R}{1-\beta}[(1+r/R)^{1-\beta}-1]$, $R > 0$, $\beta \in [0,1)$, and the associated contraction rate
$$c(R,\beta) := \sup\{c \ge 0 : 4f''_{R,\beta}(r) + (2K - mr)f'_{R,\beta}(r) + c\,f_{R,\beta}(r) \le 0\ \forall r \ge 0\}.$$
Then, under $K < \sqrt{m}$,
$$\sup_{R > 0,\,\beta \in [0,1)} c(R,\beta) = m - K\sqrt{m},$$
and this supremum is attained uniquely at $(R,\beta) = (2/\sqrt{m},\, K/\sqrt{m})$.
:::

Within the natural two-parameter family of power-law concave distances, there is no better choice than the one used in the main theorem. Any other $(R, \beta)$ either fails the supermartingale inequality or gives a strictly smaller contraction rate.

**Why it's surprising:** The optimum is characterised by a single tangency condition ($h'(1) = 0$ in the proof), yielding a unique maximiser with a clean closed-form expression — the power-law structure is not just convenient but is provably optimal within its class.

## Proof Sketches {#proofs}

:::proof-sketch{for=thm:main}
1. **Reduce to a scalar SDE.** By Itô's formula applied to $r_t = |X_t - X'_t|$ under the reflection coupling, the $d$-dimensional problem reduces to a one-dimensional diffusion $dr_t = \alpha_t\,dt + 2\sqrt{2}\,dW_t$ with drift bounded above by $2K - mr_t$ (Lemma lem:rt-sde). All subsequent work is on this scalar process.

2. **Verify the supermartingale inequality (Lemma lem:key).** Substitute $f', f''$ into the expression $(2K - mr)f'(r) + 4f''(r) + c^\star f(r)$ and change variables $y = 1 + r/R_0$. The inequality reduces to showing $h(y) \le \sqrt{m}$ for $y \ge 1$, where $h(y) = y^{-\beta-1}[(K+\sqrt{m})y - K]$. Check: $h(1) = \sqrt{m}$, $h'(1) = 0$, and $h'(y) < 0$ for $y > 1$ (the bracket is linear with negative slope), so $h$ is strictly decreasing — QED.

3. **Apply Itô's formula and take expectations.** Use the key inequality to bound the drift of $f(r_t^{\tau})$: $d\,\mathbb{E}[f(r_t^\tau)]/dt \le -c^\star \mathbb{E}[f(r_t^\tau)]$. Since $f' \le 1$, the stochastic integral is a genuine $L^2$-martingale with zero mean. Grönwall's lemma then gives $\mathbb{E}[f(r_t)] \le e^{-c^\star t}\mathbb{E}[f(r_0)]$.

4. **Coupling-to-Wasserstein reduction.** Optimize over the initial coupling $\gamma_0$ of $(\mu_0, \nu_0)$ to pass from the pathwise inequality to the $W_{1,f}$ statement.
:::

:::proof-sketch{for=thm:ula}
1. **Semigroup triangle inequality.** Decompose one ULA step as $W_{1,f}(\mu_{k+1}, \pi) \le W_{1,f}(\mu_k P_h, \mu_k T_h) + W_{1,f}(\mu_k T_h, \pi)$, where $T_h$ is the exact Langevin semigroup (which fixes $\pi$).

2. **One-step strong error (Lemma lem:onestep-strong).** Couple the Euler–Maruyama step and the exact SDE to the *same* Brownian increment. Write $X_h - \bar{X}_1 = -\int_0^h [\nabla U(X_s) - \nabla U(x_0)]\,ds$, apply Cauchy–Schwarz and Grönwall to get $\mathbb{E}[|X_h - \bar{X}_1|^2] \le C_0 L^2 h^3 (|\nabla U(x_0)|^2 + d)$. This translates to $W_{1,f}(\mu_k P_h, \mu_k T_h) \le C\,L^2 h^{3/2}\sqrt{M^\star + d}$.

3. **Uniform moment bound (Lemma lem:ula-moment).** Use the distant-dissipativity estimate and the step-size condition $h \le m/(2L^2)$ to show $\mathbb{E}[|\bar{X}_k - x^\star|^2]$ is uniformly bounded in $k$, giving the uniform control needed on the one-step error.

4. **Geometric iteration.** Combine the $e^{-c^\star h} \le 1 - c^\star h/2$ contraction with the additive discretisation error and sum the geometric series over $k = 0, \ldots, N-1$.
:::

:::proof-sketch{for=thm:poc}
1. **Couple particles to independent McKean–Vlasov solutions.** Drive particle $X^{i,N}$ and its McKean–Vlasov shadow $Y^i$ by the *same* Brownian motion; since initial data are matched, $\Delta^i_0 = X^{i,N}_0 - Y^i_0 = 0$.

2. **Identify effective potential and apply Lemma lem:key.** The McKean–Vlasov drift defines an effective time-dependent potential $U^{\mathrm{eff}}_t(x) = U_0(x) + \int W(x,y)\mu_t(dy)$ satisfying A1–A2–A3 uniformly in $t$ (since $\|\nabla_1 W(\cdot, y)\|_\infty \le K$ uniformly). Itô's formula applied to $f(|\Delta^i_t|)$ yields $\frac{d}{dt}\mathbb{E}[f(|\Delta^i_t|)] \le -c^\star \mathbb{E}[f(|\Delta^i_t|)] + \mathbb{E}[|\mathcal{F}^i_t|]$, where $\mathcal{F}^i_t$ is the empirical-vs-mean-field fluctuation.

3. **Dimension-free fluctuation bound.** Split $\mathcal{F}^i_t$ into a centred empirical average (variance $\le 4K^2/(N-1)$ by i.i.d. bounded summands) and a drift correction bounded by $L_W \mathbb{E}[|\Delta^j_t|]$. This gives $\mathbb{E}[|\mathcal{F}^i_t|] \le 2K/\sqrt{N-1} + L_W \mathbb{E}[|\Delta^i_t|]$ — no $\sqrt{d}$ factor appears.

4. **Close the ODE by Grönwall.** The subcritical condition $L_W \le c^\star/2$ ensures the $L_W$ term can be absorbed into the contraction side, yielding $\phi'(t) \le -c^\star\phi(t) + C_2 K/\sqrt{N-1}$. With $\phi(0) = 0$, Grönwall gives the uniform-in-time bound.
:::

:::proof-sketch{for=prop:sharpness}
1. **Necessary upper bound $c \le m(1-\beta)$.** The coefficient of $y^{1-\beta}$ in the supermartingale inequality is $R(c - m(1-\beta))/(1-\beta)$; if $c > m(1-\beta)$ this term diverges to $+\infty$ as $y \to \infty$, violating the inequality.

2. **Tangency constraint at $y=1$.** Setting $c = m(1-\beta)$ reduces the inequality to $H(y; R, \beta) \le mR$ for all $y \ge 1$. The condition $H(1) \le mR$ forces $R \le 2\beta/K$.

3. **Monotonicity constraint on $H$.** Requiring $H$ to be non-increasing on $[1,\infty)$ (so that the $y=1$ bound propagates) forces $\beta \ge K/\sqrt{m}$. Since $c = m(1-\beta)$ is decreasing in $\beta$, the optimal $\beta$ is $K/\sqrt{m}$, giving $R = 2/\sqrt{m}$ and $c^\star = m - K\sqrt{m}$ as the unique maximiser.
:::

## Numerical Illustration {#numerics}

Five experiments validate the theoretical predictions. **Experiment E1** tracks $\mathbb{E}[|X_t - X'_t|]$ under the reflection coupling for varying $K$ with fixed $m$, comparing empirical decay rates against the formula $c^\star = m - K\sqrt{m}$. The measured rates match the theoretical prediction closely across the full subcritical range, with deviations below 5%.

**Experiment E2** repeats E1 in dimensions $d \in \{1, 2, 5, 10, 50, 100\}$ with fixed $(m, K)$. The empirical contraction rate is essentially constant across dimensions, confirming the dimension-freeness of $c^\star$. This is a non-trivial validation: the *proof* is dimension-free, but it is reassuring that discretisation artefacts do not introduce dimension-dependent corrections at practical step sizes.

**Experiment E3** measures the ULA asymptotic bias as $h \to 0$ and verifies the $\sqrt{h}$ scaling predicted by Theorem thm:ula. **Experiment E4** applies the bound to a Bayesian logistic regression posterior (a concrete instance of $U_0 = $ Gaussian prior, $V = $ bounded log-likelihood), showing that the theoretical $c^\star$ predicts the mixing time to within a small constant factor. **Experiment E5** studies critical slowing down as $K \uparrow \sqrt{m}$: the measured mixing time grows as $1/c^\star = 1/(\sqrt{m}\,\varepsilon)$, consistent with Proposition prop:critical's prediction of a **linear** vanishing of $c^\star$ in $\varepsilon = \sqrt{m} - K$, not a faster (e.g., quadratic) collapse.

## Connections {#connections}

- [sr_p005](/papers/sr_p005): The same reflection-coupling technology and concave-distance supermartingale strategy are the core tool; sr_p006 specialises the general Eberle variational framework to a class where the rate is extractable in closed form.
- [mv_games](/papers/mv_games): The uniform-in-time propagation-of-chaos result (Theorem thm:poc) uses the same McKean–Vlasov particle system structure and the same contraction-via-$c^\star$ argument that appears in mean-field game convergence analyses.
- [sr_p001](/papers/sr_p001): The ULA discretisation analysis (Theorem thm:ula, Lemma lem:onestep-strong) shares the Euler–Maruyama one-step strong-error bound and the geometric-decay-plus-additive-bias structure used in related Langevin MCMC complexity results.
- [project7](/papers/project7): The mixing-time complexity scaling $\mathcal{O}(L^4(M^\star+d)/(c^\star)^3\varepsilon^2)$ (Corollary cor:mix) is the type of bound that feeds into algorithm complexity comparisons studied in project7's framework.