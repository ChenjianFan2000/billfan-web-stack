---
paper_slug: uniswap_tick_correction
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

Uniswap v3 introduced *concentrated liquidity*: instead of spreading capital uniformly over all prices, a liquidity provider (LP) deposits into a specific price interval $[p_\ell, p_u]$, earning swap fees only when the market price lies inside this range. The protocol discretizes the price space into a multiplicative grid called *ticks*, with adjacent tick levels spaced by a factor $(1+\gamma)$ where $\gamma$ depends on the pool's fee tier — ranging from $0.01\%$ (stablecoin pools) up to $2.02\%$ (exotic pairs). The LP earns a fee on every crossing of a tick boundary, so the total fee revenue is governed by the crossing statistics of the price process over this spatial grid.

The foundational asymptotic theory was developed by Echenim, Gobet, and Maurice (EGM, 2025). Their main result shows that as $\gamma \to 0$, the renormalized fee revenue $\gamma \cdot \mathrm{Fees}$ converges to an integral of the semimartingale local time of the log-price process. Under geometric Brownian motion (GBM), this gives an explicit expected-fee formula. However, in practice $\gamma$ is fixed by the pool's fee tier and can be as large as $2\%$, so the asymptotic formula is used in a regime where its accuracy is untested. For a \$10M LP position in the $1\%$ pool, a $1.5\%$ error in the fee estimate translates to $\$15{,}000$ per year in systematic mispricing.

This paper derives three families of finite-$\gamma$ corrections that go beyond the EGM limit. First, it shows that the first-order correction coefficient $\kappa_1$ — previously computed as $1/4$ under risk-neutral GBM — is in fact *non-universal*: it depends on the drift $\mu$ and equals $1/4$ only under the risk-neutral GBM measure. Under the physical measure for Bitcoin ($r \approx 50\%$, $\sigma \approx 80\%$), the correction is more than $2.5\times$ larger. Second, when an LP's chosen price boundary does not align with the tick grid, the boundary tick earns a reduced fraction $R(\delta) = 2(1-\delta)/(2-\delta)$ of the interior tick's fee — a rational function of the fractional offset $\delta$, completely unlike the irrational Wiener–Hopf constant $\zeta(1/2)/\sqrt{2\pi}$ that governs temporal barrier corrections (Broadie–Glasserman–Kou). Third, incorporating the finite-tick correction into the revenue optimization shifts the fee-maximizing range width downward by $1$–$2$ ticks relative to the EGM prediction, with the largest effect in the $0.05\%$ pool where optimal ranges are widest.

## Key Objects {#objects}

**Log-price process.** The log-price $X_t = \log p_t$ satisfies
$$dX_t = \mu\,dt + \sigma\,dW_t, \quad X_0 = 0,$$
with constant drift $\mu \in \mathbb{R}$ and volatility $\sigma > 0$. The key non-standard feature is that the paper works with *general* constant drift, not just the risk-neutral value $\mu = -\sigma^2/2$, to expose the drift-dependence of finite-tick corrections.

**Drift parameter.** Define
$$\alpha \coloneqq -\frac{2\mu}{\sigma^2},$$
so that risk-neutral GBM corresponds to $\alpha = 1$ and ABM to $\alpha = 0$. This parametrization diagonalizes the scale function and makes the crossing probability $p_\uparrow = 1/(1+e^{\alpha h})$ explicit.

**Scale function and crossing probability.** The scale function of the diffusion is
$$S(x) = \frac{1}{\alpha}(e^{\alpha x} - 1), \quad \alpha \neq 0,$$
with $S(x) = x$ in the limit $\alpha \to 0$. The gambler's ruin formula then yields the probability of an upcrossing from grid level $kh$:
$$p_\uparrow(h) = \frac{S(h)}{S(2h)} = \frac{1}{1+e^{\alpha h}}.$$
This is non-trivial because the asymmetry $p_\uparrow \neq 1/2$ under drift directly feeds into the fee-per-crossing formula.

**Prefactor function.** The coefficient of the fee earned per upcrossing at tick $kh$ is encapsulated in
$$c(h) \coloneqq \frac{\gamma}{h} \cdot \frac{e^{h/2}-1}{1+e^{\alpha h}}, \qquad \psi(h) \coloneqq \frac{4c(h)}{h}.$$
The normalized prefactor $\psi(h)$ measures how much the actual fee-per-crossing differs from its $h \to 0$ limit; its Taylor expansion is the first source of the finite-tick correction.

**Crossing weight function and its EGM counterpart.** Define
$$f(x) \coloneqq e^{x/2}\,\mathbb{E}[L^x_T], \qquad g(x) \coloneqq e^{-3x/2}\,\mathbb{E}[L^x_T],$$
where $L^x_T$ is the semimartingale local time of $X$ at level $x$ up to time $T$. The discrete crossing-count sum uses $f$, while the EGM asymptotic integral uses $g$. Their discrepancy is the second source of finite-tick corrections, and the key structural fact is that $f'(0) = 0$ if and only if $\mu = -\sigma^2/2$ (risk-neutral GBM).

**Expected renormalized fee and EGM benchmark.** The expected $Y$-token fee from the LP position over $N$ ticks is
$$\Psi(\gamma) = \frac{\phi}{1-\phi}\sum_{k=-N/2}^{N/2-1} c(h)\cdot e^{kh/2}\cdot \mathbb{E}[L^{kh}_T],$$
while the EGM asymptotic benchmark is
$$F_0^Y(\gamma) = \frac{\phi}{4(1-\phi)}\int_{-Nh/2}^{Nh/2} e^{-3x/2}\,\mathbb{E}[L^x_T]\,dx.$$
The ratio $\Psi(\gamma)/F_0^Y(\gamma)$ is the central object of the paper; it equals $1$ in the limit $\gamma \to 0$ and its power series in $\gamma$ encodes all finite-tick corrections.

## Main Results {#main-results}

:::theorem{id=thm:general_kappa1 label="General First-Order Correction (Non-Universality of $\\kappa_1$)"}
Let the log-price follow $dX_t = \mu\,dt + \sigma\,dW_t$ with constant $\mu \in \mathbb{R}$ and $\sigma > 0$. For an $N$-tick LP range centered at $X_0 = 0$, the expected renormalized fee satisfies
$$\frac{\Psi(\gamma)}{F_0^Y(\gamma)} = 1 + \kappa_1(\mu,\sigma)\,\gamma + O(\gamma^2),$$
where
$$\kappa_1(\mu,\sigma) = \frac{1}{2} + \frac{\mu}{2\sigma^2}.$$
:::

The ratio $\Psi/F_0^Y$ measures how much the discrete tick-grid fee deviates from the continuous-limit EGM formula. The theorem says the first-order deviation is linear in the tick spacing $\gamma$ with a coefficient that depends linearly on $\mu/\sigma^2$. Under the risk-neutral drift $\mu = -\sigma^2/2$, the formula gives $\kappa_1 = 1/4$, recovering the GBM special case. But under the physical measure with expected return $r > 0$, one gets $\kappa_1^P = 1/4 + r/(2\sigma^2)$, which for Bitcoin parameters gives $\kappa_1^P \approx 0.64$ — more than twice the risk-neutral value. The decomposition $\kappa_1 = \kappa_1^\psi + \kappa_1^{EM}$ into a prefactor piece and an Euler–Maclaurin piece shows exactly where the drift-dependence enters.

**Why it's surprising:** The value $\kappa_1 = 1/4$ was previously known only for risk-neutral GBM and might have appeared "universal"; the theorem shows it is not — the correction coefficient is a simple affine function of the Sharpe ratio $\mu/\sigma^2$, and practitioners using risk-neutral formulas to estimate finite-tick effects will systematically underestimate corrections whenever the underlying has positive expected return.

---

:::theorem{id=thm:main label="Full Two-Term Expansion under GBM"}
Under risk-neutral GBM with constant $\sigma > 0$, $T > 0$, and $N$ even:
$$\frac{\Psi(\gamma)}{F_0^Y(\gamma)} = 1 + \frac{1}{4}\,\gamma - \frac{N^2}{6}\,\gamma^2 + O(\gamma^3).$$
In particular, $\kappa_1 = \lim_{\gamma \to 0}[\Psi/F_0^Y - 1]/\gamma = 1/4$, independent of $\sigma$, $T$, and $N$.
:::

This is the most complete result under the canonical GBM model. The first-order term $\gamma/4$ is universal (independent of $\sigma$, $T$, $N$), arising entirely from the prefactor $\psi(h)$; the Euler–Maclaurin boundary term vanishes because $f'(0)=0$ under the risk-neutral drift. The second-order term $-N^2\gamma^2/6$ carries a negative sign: it reflects a geometric mismatch between the $e^{x/2}$ weight in the fee formula and the $e^{-3x/2}$ weight in the EGM integral — the discrepancy grows as the square of the range half-width $a = Nh/2$. This means the EGM formula overestimates fees for wide ranges ($N^2\gamma > 3/2$) and underestimates them for narrow ones.

**Why it's surprising:** The universality of $\kappa_1 = 1/4$ (independent of all model parameters under risk-neutral GBM) is not an accident but traces to a precise algebraic cancellation $f'(0) = 0$ that holds only for the risk-neutral drift; the second-order term breaks this universality and explicitly depends on the range width $N$.

---

:::theorem{id=cor:crossover label="Sign Crossover for the Finite-Tick Correction"}
The relative correction $\Psi/F_0^Y - 1$ changes sign at
$$\gamma^* = \frac{3}{2N^2}.$$
For $\gamma < \gamma^*$, the asymptotic formula underestimates fees; for $\gamma > \gamma^*$, it overestimates.
:::

The EGM formula is not simply a lower or upper bound — it crosses from underestimating to overestimating depending on whether the tick spacing is small or large relative to the range. For a 20-tick range, $\gamma^* \approx 0.375\%$, placing the crossover in the $0.30\%$ fee tier. An LP using the EGM formula for a 20-tick position in the $0.05\%$ pool ($\gamma = 0.001 < \gamma^*$) will *underestimate* fees, while the same formula in the $1\%$ pool ($\gamma = 0.02 > \gamma^*$) will *overestimate* them.

**Why it's surprising:** The sign of the error is not monotone in $\gamma$; it depends on both the tick spacing and the range width through the combination $N^2\gamma$, a dimensionless product that governs the regime.

---

:::theorem{id=thm:misaligned label="Misalignment Correction"}
For an LP range with fractional offset $\delta$ at the lower boundary and $\delta'$ at the upper boundary, each with $N$ interior ticks, the total fee correction acquires an additional first-order term:
$$\frac{\Psi_{\mathrm{mis}}}{\Psi_{\mathrm{align}}} = 1 - \frac{1}{N}\left[\frac{\delta}{2-\delta} + \frac{\delta'}{2-\delta'}\right] + O(N^{-2}),$$
where $\Psi_{\mathrm{align}}$ is the aligned fee from Theorem~\ref{thm:main}. The correction is always non-positive, with equality if and only if both boundaries are aligned ($\delta = \delta' = 0$).
:::

When an LP sets a price boundary that falls between two ticks, the innermost boundary tick sits in an asymmetric strip of width $(2-\delta)h$ rather than the standard $2h$ strip. Its crossing probability is therefore $R(\delta) = 2(1-\delta)/(2-\delta)$ times that of an interior tick. Since there are two boundary ticks and $N$ total ticks, the aggregate reduction is of order $1/N$. The formula gives a concrete, analytically tractable correction: a $50\%$ fractional offset ($\delta = 1/2$) reduces the boundary tick's fee by $33\%$ and reduces total fee revenue by $2/(3N)$.

**Why it's surprising:** The correction is a *rational* function of $\delta$, in sharp contrast to the irrational Wiener–Hopf constant $\beta = \zeta(1/2)/\sqrt{2\pi} \approx -0.5826$ that governs temporal barrier corrections (BGK). The reason is fundamental: continuous price paths cross every spatial level with probability one, so there is no overshoot; the correction arises purely from gambler's ruin geometry.

---

:::theorem{id=prop:optimal_N label="Corrected Optimal Range Width"}
The fee-maximizing number of ticks under the corrected formula satisfies
$$N^*_{\mathrm{corr}} = N^*_{\mathrm{EGM}}\left(1 - \frac{(N^*_{\mathrm{EGM}})^2\,\gamma^2}{2} + O(\gamma)\right).$$
The correction is always negative: the finite-tick effect reduces the optimal range width.
:::

The EGM asymptotic treats fee revenue as growing linearly in $N$, balanced against impermanent loss growing as $N^2$. The finite-tick correction adds an additional $-N^3\gamma^3/6$ penalty in fee revenue (from the second-order term in Theorem~\ref{thm:main}), making wider ranges relatively less attractive and shifting the optimum inward. Because $N^*_\mathrm{EGM} = O(\gamma^{-1})$, the product $(N^*_\mathrm{EGM})^2\gamma^2 = O(1)$ is not small; for the $0.05\%$ pool the shift is $-2$ ticks, worth approximately $\$200$/day for a \$1M position.

**Why it's surprising:** The correction is not merely a perturbative adjustment — it is $O(1)$ in absolute tick count, not $O(\gamma)$, because the range width scales as $\gamma^{-1}$ at the optimum.

## Proof Sketches {#proofs}

:::proof-sketch{for=thm:general_kappa1}
1. **Decompose the ratio.** Write $\Psi/F_0^Y = \psi(h) \cdot (\sum h\,f(kh) / I_f(h)) \cdot (I_f(h)/I_g(h))$, separating the prefactor correction, the Riemann-sum-to-integral correction, and the weight-function discrepancy.
2. **Expand the prefactor** $\psi(h) = 4c(h)/h$ via Taylor series in $h$: factor $\gamma/h = 1 + h/2 + O(h^2)$, expand $e^{h/2}-1 = h/2 + h^2/8 + O(h^3)$, and expand $1/(1+e^{\alpha h}) = 1/2 - \alpha h/4 + O(h^2)$; multiplying gives $\kappa_1^\psi = 3/4 + \mu/\sigma^2$.
3. **Apply the Euler–Maclaurin formula** to the Riemann sum $\sum h\,f(kh)$: the leading boundary correction is $(h/2)[f(-a)-f(a)] = -(Nh^2/2)f'(0) + O(N^3h^4)$; dividing by $I_f = Nh\,f(0) + O(N^3h^3)$ gives $\kappa_1^{EM} = -f'(0)/(2f(0)) = -1/4 - \mu/(2\sigma^2)$, using $f'(0) = (1/2 + \mu/\sigma^2)\mathbb{E}[L^0_T]$.
4. **Check the weight-function ratio** $I_f(h)/I_g(h) = 1 + O(h^2)$: since $f(x) - g(x) = (e^{x/2} - e^{-3x/2})\mathbb{E}[L^x_T] = 2x\,\mathbb{E}[L^x_T] + O(x^2)$, the difference integral is $O(a^3/a) = O(h^2)$ and contributes only at second order.
5. **Combine:** $\kappa_1 = \kappa_1^\psi + \kappa_1^{EM} = (3/4 + \mu/\sigma^2) + (-1/4 - \mu/(2\sigma^2)) = 1/2 + \mu/(2\sigma^2)$, and convert $h \to \gamma$ at first order.
:::

:::proof-sketch{for=thm:main}
1. **Prefactor under GBM.** Set $\alpha = 1$ in the general prefactor lemma to get $\psi(h) = 1 + h/4 + O(h^2)$; the first-order coefficient is $\kappa_1^\psi = 3/4 - 1/2 = 1/4$.
2. **Euler–Maclaurin under GBM vanishes to first order.** Since $f'(0) = (1/2 + \mu/\sigma^2)\mathbb{E}[L^0_T] = 0$ when $\mu = -\sigma^2/2$, the boundary term in the Riemann sum error is $O(N^3h^4)$ rather than $O(Nh^2)$; the sum approximates the integral to $O(h^2)$.
3. **Second-order weight discrepancy.** Compute $f''(0) - g''(0)$ using the explicit Gaussian transition density: $f''(0) = -\lambda_0/4 + \lambda_2$ and $g''(0) = 15\lambda_0/4 + \lambda_2$, giving $f''(0) - g''(0) = -4\lambda_0$. Then $I_f - I_g = (-4\lambda_0/2)(2a^3/3) + O(a^5)$, and dividing by $I_g \approx 2a\lambda_0$ yields $I_f/I_g = 1 - 2a^2/3 + O(a^4) = 1 - N^2h^2/6 + O(h^4)$.
4. **Assemble and convert.** Multiply the three factors: $(1 + h/4)(1 + O(h^2))(1 - N^2h^2/6) = 1 + h/4 - N^2h^2/6 + O(h^3)$; then use $h = \gamma - \gamma^2/2 + O(\gamma^3)$ to rewrite in terms of $\gamma$.
:::

:::proof-sketch{for=thm:misaligned}
1. **Asymmetric strip geometry.** When the lower boundary $a_\ell = mh + \delta h$ falls between ticks, the boundary tick $x_b = (m+1)h$ is at distance $\varepsilon = (1-\delta)h$ above $a_\ell$ and $h$ below the next tick; the standard gambler's ruin applies in the strip $[a_\ell, x_b + h]$ of width $(2-\delta)h$.
2. **Boundary crossing probability via scale function.** The probability of upcrossing from $x_b$ to $x_b + h$ before hitting $a_\ell$ is $p_b = S(\varepsilon)/S(\varepsilon + h) = S((1-\delta)h)/S((2-\delta)h)$; taking $h \to 0$ with $S(x) \approx x$ gives the efficiency ratio $R(\delta) = 2(1-\delta)/(2-\delta)$.
3. **Aggregate over $N$ ticks.** Each boundary tick has $N$ interior ticks alongside it; its reduced efficiency $R(\delta) = 1 - \delta/(2-\delta)$ enters with weight $1/N$ in the total sum, giving the $O(1/N)$ correction $-[{\delta/(2-\delta)} + {\delta'/(2-\delta')}]/N$.
4. **Rationality vs.\ BGK.** Since $S(x) \approx x$ as $h \to 0$ (all constant-coefficient diffusions have $S'(0) = 1$), the efficiency ratio $R(\delta)$ depends only on the linear term of $S$ and is purely rational in $\delta$; the irrational BGK constant $\zeta(1/2)/\sqrt{2\pi}$ does not appear because continuous paths have no temporal overshoot.
:::

:::proof-sketch{for=prop:optimal_N}
1. **Revenue model.** The corrected net revenue is $\mathrm{Net}(N) = C_\mathrm{fee} N\gamma(1 + \gamma/4 - N^2\gamma^2/6) - C_\mathrm{IL} N^2\gamma^2$, where $C_\mathrm{fee} \propto \sigma\sqrt{T}$ and $C_\mathrm{IL} = \sigma^2 T/24$ encode the fee income and impermanent loss scaling.
2. **First-order condition.** Differentiate with respect to $N$ and set to zero: the cubic term $-C_\mathrm{fee} N^2\gamma^3/2$ is new relative to the EGM optimality condition and acts as an additional penalty on wide ranges.
3. **Perturbative solution.** Write $N = N^*_\mathrm{EGM}(1 + \epsilon)$ and expand the first-order condition in $\epsilon$; use the EGM optimality condition $2C_\mathrm{IL} N^*_\mathrm{EGM}\gamma = C_\mathrm{fee}$ to cancel leading terms, yielding $\epsilon = \gamma/4 - (N^*_\mathrm{EGM})^2\gamma^2/2$; since $N^*_\mathrm{EGM} = O(\gamma^{-1})$ the dominant shift is $\epsilon \approx -(N^*_\mathrm{EGM})^2\gamma^2/2 < 0$.
:::

## Numerical Illustration {#numerics}

The paper validates all three main results against semi-analytical computations in which $\mathbb{E}[L^x_T]$ is evaluated by numerical quadrature of the Gaussian transition density and the sums and integrals defining $\Psi(\gamma)$ and $F_0^Y(\gamma)$ are computed directly. For the general $\kappa_1$ formula (Theorem~\ref{thm:general_kappa1}), Table~2 in the paper tests five drift values ranging from $\mu = -0.20$ to $\mu = 0.10$ with $\sigma = 0.4$, $T = 1$, $N = 20$; the numerically extracted slopes at $\gamma = 10^{-4}$ and $\gamma = 10^{-3}$ agree with the theoretical predictions $\kappa_1 = 1/2 + \mu/(2\sigma^2)$ to within $O(\gamma)$ residuals. Notably, the case $\mu = -0.20$ yields $\kappa_1 \approx -0.125$, confirming that the correction coefficient can be negative for sufficiently downward-drifting processes, a regime where the EGM formula overestimates fees even for small $\gamma$.

For the full two-term GBM expansion (Theorem~\ref{thm:main}), the numerical experiments verify both the universal $\kappa_1 = 1/4$ first-order term and the $-N^2\gamma^2/6$ second-order term across a range of $N$ values. A sensitivity analysis over time horizons $T \in \{0.5, 1, 2\}$ days and volatilities $\sigma \in \{0.3, 0.8, 1.2\}$ confirms that $\kappa_1$ is indeed independent of these parameters, while the coefficient of the second-order term is confirmed to be exactly $N^2/6$ independent of $\sigma$ and $T$. The sign crossover predicted by Corollary~\ref{cor:crossover} at $\gamma^* = 3/(2N^2)$ is clearly visible in plots of $\Psi/F_0^Y - 1$ against $\gamma$ for $N = 20$.

The misalignment correction (Theorem~\ref{thm:misaligned}) is validated by directly computing $\Psi_\mathrm{mis}$ and $\Psi_\mathrm{align}$ for fractional offsets $\delta \in \{0, 0.25, 0.5, 0.75\}$ with $N \in \{10, 20, 50\}$; the rational formula $R(\delta) = 2(1-\delta)/(2-\delta)$ matches the numerical boundary efficiency ratio to $O(h^2)$ uniformly across parameter values. A practical summary table for the four Uniswap fee tiers ($\phi \in \{0.01\%, 0.05\%, 0.30\%, 1.00\%\}$) quantifies the combined effect of all corrections for representative LP range widths, with the largest effects concentrated in the $0.05\%$ pool due to its wide optimal ranges.

## Connections {#connections}

- [variance_options](/papers/variance_options): Both papers use the semimartingale local time as the central object linking discrete observations (tick crossings or variance swap payoffs) to continuous-time limits; the Euler–Maclaurin analysis of Riemann sums over a spatial grid parallels the quadratic-variation approximation machinery used there.
- [discrete_vs_rough](/papers/discrete_vs_rough): The comparison between spatial and temporal discretization corrections — rational vs. Wiener–Hopf constants — parallels this paper's analysis of how rough-path corrections relate to discrete-time approximations; both papers study the interplay between discretization scheme geometry and the resulting correction constants.
- [var_ratio](/papers/var_ratio): The occupation-time / local-time representation of fee revenue connects to variance ratio statistics studied there; local time integrals appear in both as the bridge between path occupation density and cumulative quadratic variation.