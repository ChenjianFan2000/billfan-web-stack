---
paper_slug: discrete_vs_rough
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

A **variance swap** pays its holder the difference between the realized variance of an asset over a fixed horizon $[0,T]$ and a pre-agreed strike. In practice, realized variance is computed from $n$ discrete log-returns sampled at times $t_i = iT/n$, whereas theoretical pricing is based on the continuously monitored quadratic variation $\int_0^T V_t\,\dd t$. The gap between these two fair strikes — the *discrete monitoring correction* — is therefore of direct commercial importance: a market-maker who prices at the continuous strike when selling a daily-monitored variance swap carries systematic basis risk.

For classical stochastic volatility models (Heston, Hull–White, time-homogeneous diffusions), this gap is well understood. Broadie–Jain (2008) and Bernard–Cui (2014) derived explicit $O(n^{-1})$ expansions; Bernard–Cui–McLeish (2014) established that $O(n^{-1})$ is *universal* among continuous semimartingale volatility models. A general $O(n^{-1/2})$ upper bound under arbitrary semimartingale assumptions was proved by Jarrow–Kchia–Protter (2013), a bound that is tight for jump models but sub-optimal for smooth ones. The methodological workhorse throughout has been Malliavin duality, systematized by Alos–Fukasawa (2021) via an Edgeworth expansion for discretization errors of Itô integrals, applicable whenever the volatility process is itself a semimartingale.

The rough volatility paradigm changes the picture fundamentally. Under **Volterra stochastic volatility** with a fractional kernel $K(t) = t^{H-1/2}/\Gamma(H+\frac{1}{2})$ and Hurst parameter $H \approx 0.1$, the variance process $V$ is *not* a semimartingale: its paths have Hölder regularity strictly less than $\frac{1}{2}$, so the Alos–Fukasawa framework does not directly apply. The Malliavin derivative $D_u V_s$ blows up as $(s-u)^{H-1/2}$ near the diagonal $s=u$, a singularity absent in the smooth setting. Numerical studies (Xi–Wong 2021, Zhuang–Huang 2025) computed discrete fair strikes for rough Heston without deriving asymptotic rates. The theoretical question — *at what rate does the discrete strike converge to the continuous one, and what governs the leading coefficient?* — was open.

This paper answers that question completely. The discrete monitoring correction for any Volterra SV model with correlation $\rho \neq 0$ converges at the **anomalous rate $O(n^{-(H+1/2)})$** rather than $O(n^{-1})$. The exponent $H+\frac{1}{2} \in (\frac{1}{2}, 1)$ lies strictly between the jump-model rate and the smooth-model rate. The authors prove sharpness (a two-sided bound), correct an erroneous phase-transition claim at $H=\frac{1}{6}$ present in earlier analyses, and characterize boundary behavior as $H\to 0^+$ and $\rho\to\pm 1$. The key surprise is that the leading coefficient is *universal*: it depends on the model only through a single averaged quantity $\bar\varphi$, not on any other structural details.

## Key Objects {#objects}

**Volterra stochastic volatility model.** A pair $(S, V)$ on a filtered probability space carrying independent Brownian motions $W, B$:

$$\dd S_t = \sqrt{V_t}\, S_t\bigl(\rho\,\dd W_t + \bar\rho\,\dd B_t\bigr), \qquad \bar\rho = \sqrt{1-\rho^2},$$

$$V_t = V_0 + \int_0^t K(t-s)\,b(V_s)\,\dd s + \int_0^t K(t-s)\,\sigma_V(V_s)\,\dd W_s,$$

with fractional kernel $K(t) = t^{H-1/2}/\Gamma(H+\frac{1}{2})$, $H\in(0,\frac{1}{2})$. The non-standard feature is that $V$ is a **non-semimartingale**: the kernel singularity at $t=0$ means $V$ has only $H$-Hölder paths, invalidating standard Itô calculus for $V$ itself. The log-price $X=\ln S$ remains a semimartingale.

**Discrete monitoring gap.** With continuous fair strike $K_c = T^{-1}\mathbb{E}[\int_0^T V_t\,\dd t]$ and discrete fair strike

$$K_d(n) = \frac{1}{T}\sum_{i=0}^{n-1}\mathbb{E}\!\left[\left(\ln\frac{S_{t_{i+1}}}{S_{t_i}}\right)^{\!2}\right],$$

the gap is $\delta(n) := K_d(n) - K_c$. This is the main object of study; classically $\delta(n) = O(n^{-1})$, and the paper proves this deteriorates to $O(n^{-(H+1/2)})$.

**Per-interval quantities.** On $[t_i, t_i+\Delta]$ with $\Delta = T/n$:

$$I_i = \int_{t_i}^{t_i+\Delta} V_s\,\dd s, \qquad M_i^W = \int_{t_i}^{t_i+\Delta}\sqrt{V_s}\,\dd W_s.$$

The log-return is $\Delta X_i = -\frac{1}{2}I_i + \rho M_i^W + \bar\rho M_i^B$. The cross-term $\mathbb{E}[I_i M_i^W]$ is the source of all anomalous behavior: expanding $(\Delta X_i)^2$ and using the Itô isometry isolates a *leverage term* $-\rho\,\mathbb{E}[I_i M_i^W]$ that has no classical counterpart in size.

**Malliavin derivative of the variance process.** For $s > u$, the Malliavin derivative of $V_s$ with respect to $W_u$ satisfies the linear Volterra equation

$$D_u V_s = K(s-u)\,\sigma_V(V_u) + \int_u^s K(s-r)\,b'(V_r)\,D_u V_r\,\dd r + \int_u^s K(s-r)\,\sigma_V'(V_r)\,D_u V_r\,\dd W_r.$$

The leading term $K(s-u)\sigma_V(V_u) \sim (s-u)^{H-1/2}\sigma_V(V_u)$ is **singular** as $s\to u^+$, which is the mathematical source of the anomalous exponent. In smooth models $D_u V_s = O(1)$ near the diagonal; here it blows up.

**Leverage sensitivity function and $\bar\varphi$.** Define

$$\varphi(t) := \mathbb{E}[\sigma_V(V_t)\sqrt{V_t}], \qquad \bar\varphi := \frac{1}{T}\int_0^T \varphi(t)\,\dd t.$$

This is the *only* model-specific quantity entering the leading coefficient. For rough Heston ($\sigma_V(v)=\nu\sqrt{v}$), $\bar\varphi = \nu\bar{V}$; for rough CIR ($\sigma_V(v)=\nu v^\gamma$), $\bar\varphi = \nu T^{-1}\int_0^T \mathbb{E}[V_t^{\gamma+1/2}]\,\dd t$. The universality of the scaling rate — shared by all these models — follows from the fact that only $\bar\varphi$ survives in the leading term.

**Beta convolution identity.** The fractional kernel satisfies

$$\int_0^t K(t-s)\,K(s)\,\dd s = \frac{t^{2H}}{\Gamma(2H+1)},$$

a consequence of $B(H+\frac{1}{2}, H+\frac{1}{2}) = \Gamma(H+\frac{1}{2})^2/\Gamma(2H+1)$. This identity controls the size of the Picard-iterate remainder for $D_u V_s$ and is the technical key to the tight remainder bound.

## Main Results {#main-results}

:::theorem{id=lem-gap-decomp label="Gap Decomposition (Lemma 3.1)"}
Under Assumption (A1),
$$\delta(n) = \frac{1}{T}\sum_{i=0}^{n-1}\Bigl[\frac{1}{4}\,\mathbb{E}\bigl[I_i^2\bigr] - \rho\,\mathbb{E}\bigl[I_i\,M_i^W\bigr]\Bigr].$$
:::

The gap splits exactly into two terms: a **convexity term** $\frac{1}{4T}\sum\mathbb{E}[I_i^2]$ (always non-negative, present even when $\rho=0$) and a **leverage term** $-\frac{\rho}{T}\sum\mathbb{E}[I_i M_i^W]$ (zero when $\rho=0$, changes sign with $\rho$). The derivation is purely algebraic: expand $(\Delta X_i)^2$, apply the Itô isometry to handle $\mathbb{E}[(M_i^W)^2]$ and $\mathbb{E}[(M_i^B)^2]$, and use independence of $W$ and $B$ to kill cross terms. This exact decomposition holds for *any* model of the form given — no structural assumptions on $b$ or $\sigma_V$ are needed beyond integrability.

**Why it's surprising:** The leverage term $\mathbb{E}[I_i M_i^W]$ — a covariance between the integrated variance and the Brownian increment driving it — is at first sight an $O(\Delta^2)$ quantity. The remarkable finding of the subsequent lemmas is that the *singular* Malliavin derivative makes $\mathbb{E}[I_i M_i^W] = O(\Delta^{H+3/2})$, which is $\gg \Delta^2$ for $H < \frac{1}{2}$, causing the leverage term to dominate the convexity term.

---

:::theorem{id=thm-rough-heston label="Rough Heston Discrete Monitoring Gap (Theorem 3.2)"}
Under Assumptions (A1)–(A4) with rough Heston dynamics ($b(v)=\theta-\kappa v$, $\sigma_V(v)=\nu\sqrt{v}$), the discrete monitoring gap satisfies
$$\delta(n) = \frac{C_{\mathrm{lev}}^{\mathrm{rH}}(H)}{n^{H+1/2}} + \frac{C_{\mathrm{conv}}}{n} + o(n^{-1}),$$
where
$$C_{\mathrm{lev}}^{\mathrm{rH}}(H) = \frac{-\rho\,\nu\,\bar{V}\,T^{H+1/2}}{\Gamma(H+\tfrac{5}{2})}, \qquad C_{\mathrm{conv}} = \frac{1}{4T}\int_0^T \mathbb{E}[V_t]^2\,\dd t.$$
In particular: (i) for $H<\frac{1}{2}$ and $\rho\neq 0$, the leading term is $O(n^{-(H+1/2)})$ with $H+\frac{1}{2}<1$; (ii) for $\rho=0$, the leverage term vanishes and $\delta(n)=C_{\mathrm{conv}}/n+o(n^{-1})$; (iii) for $H=\frac{1}{2}$ (classical Heston), both terms are $O(n^{-1})$, recovering the result of Bernard–Cui (2014).
:::

For rough Heston with $\rho \neq 0$ and $H \approx 0.1$, the leading term decays as $n^{-0.6}$, which is substantially slower than the classical $n^{-1}$: going from $n=52$ (weekly) to $n=252$ (daily) reduces the gap by a factor of only $(252/52)^{0.6} \approx 3.1$ rather than $(252/52)^1 \approx 4.8$. The leading coefficient $C_{\mathrm{lev}}^{\mathrm{rH}}$ is determined entirely by $\rho$, $\nu$, the average variance $\bar{V}$, $T$, and $H$ — no other aspect of the model's dynamics (mean-reversion speed $\kappa$, long-run level $\theta$) enters at leading order. The two-term expansion makes precise how the anomalous leverage term (from path roughness) and the classical convexity term (from Jensen's inequality) compete.

**Why it's surprising:** Classical intuition says that $O(n^{-1})$ is universal for continuous semimartingale models; rough Heston's log-price is a continuous semimartingale, so one might expect $O(n^{-1})$. The anomalous rate arises not from the log-price but from the *non-semimartingale volatility* entering through the cross-term $\mathbb{E}[I_i M_i^W]$, a subtlety invisible to the Jarrow–Kchia–Protter framework.

---

:::theorem{id=thm-general label="General Volterra SV Discrete Monitoring Gap (Theorem 4.1)"}
Under Assumptions (A1)–(A5), the discrete monitoring gap satisfies
$$\delta(n) = \frac{C_{\mathrm{lev}}(H)}{n^{H+1/2}} + \frac{C_{\mathrm{eff}}}{n} + o(n^{-1}),$$
where
$$C_{\mathrm{lev}}(H) = \frac{-\rho\,\bar\varphi\, T^{H+1/2}}{\Gamma(H+\tfrac{5}{2})}, \qquad \bar\varphi = \frac{1}{T}\int_0^T \mathbb{E}\bigl[\sigma_V(V_t)\sqrt{V_t}\bigr]\dd t,$$
and $C_{\mathrm{eff}} = C_{\mathrm{conv}} + C_{\mathrm{drift}}$, with $C_{\mathrm{conv}} = (4T)^{-1}\int_0^T \mathbb{E}[V_t]^2\,\dd t$ and $C_{\mathrm{drift}}$ given explicitly by Proposition 6.1. In particular: (i) for $H<\frac{1}{2}$, $\rho\neq 0$, and $\bar\varphi\neq 0$, the leading term is $O(n^{-(H+1/2)})$; (ii) for $\rho=0$ or $\bar\varphi=0$, $\delta(n) = C_{\mathrm{eff}}/n + o(n^{-1})$.
:::

This is the paper's central result. The anomalous scaling $O(n^{-(H+1/2)})$ is **universal** across the entire class of Volterra SV models sharing the fractional kernel: rough Heston, rough CIR with any power $\gamma\in[\frac{1}{2},1]$, and mean-reverting log-normal vol-of-vol models all share the same exponent and the same structural form for the leading coefficient. The only model-specific input is $\bar\varphi$, a single averaged expectation. The sub-leading $O(n^{-1})$ term absorbs both the convexity correction (present in classical models) and the Malliavin drift correction (always subdominant since $2H+1>1$).

**Why it's surprising:** The universality is remarkable: two models with fundamentally different vol-of-vol functions $\sigma_V$ (e.g., rough Heston $\sigma_V\propto\sqrt{v}$ versus rough SABR $\sigma_V\propto v$) have *identical scaling rates*, differing only in the value of $\bar\varphi$. The fractional kernel singularity, not the specific functional form of $\sigma_V$, is the sole driver of the anomalous exponent.

---

:::theorem{id=cor-sharpness label="Sharpness of the Rate (Corollary 5.1)"}
Under the assumptions of Theorem 4.1, if $\rho\neq 0$ and $\bar\varphi\neq 0$, then
$$\lim_{n\to\infty} n^{H+1/2}\,\delta(n) = C_{\mathrm{lev}}(H) \neq 0.$$
Moreover, there exist constants $0 < c \le C < \infty$ and $n_0\in\mathbb{N}$ such that for all $n\ge n_0$:
$$\frac{c}{n^{H+1/2}} \le |\delta(n)| \le \frac{C}{n^{H+1/2}},$$
with explicit $c = |C_{\mathrm{lev}}|/2$, $C = 2|C_{\mathrm{lev}}|$, and $n_0 = \max\!\bigl(1,\, (2(|C_{\mathrm{eff}}|+C_R')/|C_{\mathrm{lev}}|)^{1/(1/2-H)}\bigr)$.
:::

The two-sided bound certifies that $n^{-(H+1/2)}$ is not merely an upper bound but the *exact asymptotic rate*: the rescaled gap $n^{H+1/2}\delta(n)$ converges to a nonzero limit. For typical rough Heston parameters ($H=0.1$, $\rho=-0.7$), the explicit threshold satisfies $n_0 < 1$, meaning the two-sided bound holds for *every* $n\ge 1$ — the leverage term is dominant even at the coarsest monitoring frequencies.

**Why it's surprising:** Prior results in the rough volatility literature often established one-sided bounds or asymptotic expansions without proving the lower bound. Here, sharpness is established analytically with a fully explicit threshold $n_0$, making the result quantitatively actionable for practitioners.

---

:::theorem{id=prop-tight-remainder label="Malliavin Drift Correction — Tight Bound (Proposition 6.1)"}
The Malliavin drift correction to $\delta(n)$ is
$$\frac{\rho\,L_b\,\bar\varphi\,T^{2H+1}}{(2H+1)(2H+2)\,\Gamma(2H+1)\,n^{2H+1}} + o(n^{-(2H+1)}).$$
Since $2H+1 > 1$ for all $H > 0$, this is always $O(n^{-1})$ or faster — always subdominant to the convexity term $C_{\mathrm{conv}}/n$.
:::

This proposition eliminates a *spurious phase transition*. Earlier analyses used a looser bound on the Picard remainder, replacing $O(\Delta^{2H+2})$ with $O(\Delta^{3H+3/2})$, which gave a drift correction of $O(n^{-(3H+1/2)})$. Since $3H+\frac{1}{2}<1$ when $H<\frac{1}{6}$, this appeared to be a dominant correction for very rough models, suggesting a qualitative change in behavior at $H=\frac{1}{6}$. The tight bound shows this is an artifact: the correct correction is $O(n^{-(2H+1)})$, which satisfies $2H+1>1$ for all $H>0$ and is thus always subdominant.

**Why it's surprising:** The correction from $O(n^{-(3H+1/2)})$ to $O(n^{-(2H+1)})$ is achieved by a more careful use of the Beta convolution identity $\int_0^t K(t-s)K(s)\,\dd s = t^{2H}/\Gamma(2H+1)$, which exactly evaluates the Picard iterate without wasteful bounds. The implication is structural: the remainder in the main expansion is $o(n^{-1})$ uniformly in $H\in(0,\frac{1}{2})$, with no special behavior at any interior point.

---

:::theorem{id=prop-H-to-0 label="Boundary Behavior as $H\to 0^+$ (Proposition 7.1)"}
The leverage coefficient satisfies
$$\lim_{H\to 0^+} C_{\mathrm{lev}}(H) = \frac{-4\rho\,\bar\varphi_0\,\sqrt{T}}{3\sqrt{\pi}},$$
where $\bar\varphi_0 = \lim_{H\to 0^+}\bar\varphi$ (assuming this limit exists). The convergence rate approaches $O(n^{-1/2})$, matching the upper bound of Jarrow–Kchia–Protter (2013) for jump models.
:::

As $H\to 0^+$, the Volterra model approaches the most irregular possible continuous volatility, and the discrete monitoring correction approaches the jump-model rate. The coefficient remains finite — $\Gamma(\frac{5}{2}) = \frac{3}{4}\sqrt{\pi}$ gives a clean limit — even though the model itself degenerates ($\|K\|_{L^2}\to\infty$). This provides a precise analytical bridge between the rough volatility and jump volatility paradigms, viewed through the lens of discrete monitoring.

**Why it's surprising:** The Jarrow–Kchia–Protter $O(n^{-1/2})$ bound was previously understood as tight only for jump models. This proposition shows it is *also* saturated in the limit by a sequence of perfectly continuous (but increasingly rough) volatility models, suggesting the bound's sharpness class is broader than previously appreciated.

## Proof Sketches {#proofs}

:::proof-sketch{for=lem-gap-decomp}
1. **Quadratic expansion of the log-return**: Write $\Delta X_i = -\frac{1}{2}I_i + \rho M_i^W + \bar\rho M_i^B$ and expand $(\Delta X_i)^2$ to get six terms involving $I_i^2$, $(M_i^W)^2$, $(M_i^B)^2$, and cross-products.
2. **Itô isometry**: Apply $\mathbb{E}[(M_i^W)^2] = \mathbb{E}[(M_i^B)^2] = \mathbb{E}[I_i]$ to replace the squared martingale terms with the integrated variance.
3. **Independence elimination**: Since $V$ is adapted to $\sigma(W)$ and $B\perp W$, the terms $\mathbb{E}[I_i M_i^B]$ and $\mathbb{E}[M_i^W M_i^B]$ vanish, leaving exactly the two-term decomposition.
4. **Telescope to get $\delta(n)$**: Summing $\mathbb{E}[(\Delta X_i)^2]$ over $i$ and subtracting $K_c = T^{-1}\sum_i\mathbb{E}[I_i]$ cancels the $\mathbb{E}[I_i]$ contributions and yields the stated formula.
:::

:::proof-sketch{for=thm-general}
1. **Convexity term** (Lemma 3.2): Decompose $\mathbb{E}[I_i^2] = (\mathbb{E}[I_i])^2 + \mathrm{Var}(I_i)$. The mean-squared part gives a Riemann sum for $C_{\mathrm{conv}}/n$ at rate $O(n^{-2})$; the variance term uses $\mathrm{Cov}(V_s,V_u)=O(|s-u|^{2H})$ (Assumption A5) to bound $\mathrm{Var}(I_i)=O(\Delta^{2+2H})$, summing to $O(n^{-(1+2H)})$.
2. **Clark–Ocone duality for the leverage term**: Apply the Clark–Ocone formula to write $\mathbb{E}[I_i M_i^W] = \mathbb{E}\!\int_{t_i}^{t_i+\Delta} D_u I_i \sqrt{V_u}\,\dd u$, reducing the cross-moment to an integral of the Malliavin derivative.
3. **Leading Malliavin derivative**: The Volterra SDE gives $D_u V_s = K(s-u)\sigma_V(V_u) + R(u,s)$ at leading order; the remainder $R$ satisfies $|R(u,s)|\le C\sqrt{V_u}(s-u)^{2H}$ via the first Picard iterate and the Beta convolution identity $\int_0^t K(t-s)K(s)\,\dd s = t^{2H}/\Gamma(2H+1)$.
4. **Inner kernel integral**: Compute $\int_u^{t_i+\Delta} K(s-u)\,\dd s = (t_i+\Delta-u)^{H+1/2}/\Gamma(H+\frac{3}{2})$ exactly, then approximate $\mathbb{E}[\sigma_V(V_u)\sqrt{V_u}]\approx\varphi(t_i)$ and evaluate the remaining integral to get $\varphi(t_i)\Delta^{H+3/2}/\Gamma(H+\frac{5}{2})$ per interval.
5. **Riemann sum and assembly**: Sum over $i=0,\ldots,n-1$ using $\sum_i\varphi(t_i) = n\bar\varphi + O(1)$ and $n\Delta^{H+3/2} = T^{H+3/2}/n^{H+1/2}$ to obtain $C_{\mathrm{lev}}/n^{H+1/2}$; combine with the convexity term and drift correction bound from Proposition 6.1.
:::

:::proof-sketch{for=cor-sharpness}
1. **Rescale and expand**: Multiply the two-term expansion by $n^{H+1/2}$ to get $n^{H+1/2}\delta(n) = C_{\mathrm{lev}} + C_{\mathrm{eff}}\,n^{H-1/2} + o(n^{H-1/2})$.
2. **Dominant term convergence**: Since $H<\frac{1}{2}$, the exponent $H-\frac{1}{2}<0$, so $n^{H-1/2}\to 0$ and the limit is exactly $C_{\mathrm{lev}}$.
3. **Nonvanishing of $C_{\mathrm{lev}}$**: Verify $C_{\mathrm{lev}}\neq 0$ from $\rho\neq 0$, $\sigma_V(v)\sqrt{v}>0$ for $v>0$, and $V_t>0$ a.s. (so $\bar\varphi>0$), $T>0$, and $\Gamma(H+\frac{5}{2})>0$.
4. **Two-sided bound**: Choose $n_0$ large enough that the sub-leading term $(|C_{\mathrm{eff}}|+C_R')/n \le |C_{\mathrm{lev}}|/(2n^{H+1/2})$ for all $n\ge n_0$ (possible since $H+\frac{1}{2}<1$), then upper- and lower-bound $|\delta(n)|$ by $2|C_{\mathrm{lev}}|/n^{H+1/2}$ and $|C_{\mathrm{lev}}|/(2n^{H+1/2})$ respectively.
:::

:::proof-sketch{for=prop-tight-remainder}
1. **First Picard iterate**: Iterate the Malliavin derivative equation once: $D_u V_s^{(1)} = -L_b\int_u^s K(s-r)K(r-u)\sigma_V(V_u)\,\dd r$, which evaluates via the Beta convolution identity to $-L_b\sigma_V(V_u)(s-u)^{2H}/\Gamma(2H+1)$.
2. **Contribution to $\mathbb{E}[I_i M_i^W]$**: Integrate $D_u V_s^{(1)}$ over $s\in[u,t_i+\Delta]$ to get $-L_b\sigma_V(V_u)(t_i+\Delta-u)^{2H+1}/[(2H+1)\Gamma(2H+1)]$; then integrate over $u\in[t_i,t_i+\Delta]$ using $\mathbb{E}[\sigma_V(V_u)\sqrt{V_u}]\approx\varphi(t_i)$, giving a per-interval correction of $O(\Delta^{2H+2})$.
3. **Summation**: Sum over $n$ intervals: $n\cdot\Delta^{2H+2} = T^{2H+1}/n^{2H+1}$, giving the stated $O(n^{-(2H+1)})$ correction; since $2H+1>1$ this is always faster than $O(n^{-1})$, eliminating the spurious phase transition at $H=\frac{1}{6}$.
:::

## Numerical Illustration {#numerics}

The numerical experiments use the **lifted Markovian approximation** of rough Heston (Abi Jaber–El Euch 