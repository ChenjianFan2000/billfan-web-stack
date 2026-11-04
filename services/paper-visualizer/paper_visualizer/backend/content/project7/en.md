---
paper_slug: project7
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

Reserve-backed stablecoins — digital tokens such as USDC and USDT that hold collateral and offer 1:1 redemption — form the liquidity backbone of cryptocurrency markets, settling daily on-chain volumes comparable to major card networks. Despite their reserve backing, they experience periodic *depeg events*: the USDC crisis of March 2023, triggered by the FDIC closure of Silicon Valley Bank (which held roughly \$3.3 billion of Circle's reserves), drove the secondary-market price to \$0.878 within 70 hours. These events are rare but consequential, precisely the regime in which Freidlin–Wentzell (FW) large deviation theory is the natural tool: one asks for the probability that the reserve value $V_t^\varepsilon$ crosses the peg threshold $p^*L$ within a time horizon $T$, in the limit of small noise $\varepsilon \to 0$.

The classical starting point is the FW sample-path large deviation principle (LDP) of Dembo–Zeitouni and Freidlin–Wentzell, which gives $-\varepsilon^2 \log \mathbb{P}(\tau_\varepsilon \leq T) \to I(T,\lambda)$ for a rate function $I$ determined by a variational (instanton) problem. For the simplest *linear-drain* model ($b = -\lambda$, $\sigma = \sigma_0$), $I$ is a quadratic in $\lambda$ and the peg-break probability is an inverse-Gaussian tail — tractable but not the deepest content. The interesting mathematics emerges for stablecoin designs whose *deterministic limit* has a **saddle-node bifurcation** at a critical redemption pressure $\lambda_c$: below $\lambda_c$, a stable reserve equilibrium exists above the peg threshold; above $\lambda_c$, no such equilibrium exists and the peg breaks deterministically. Near $\lambda_c$, the activation barrier vanishes as $(\lambda_c - \lambda)^{3/2}$ — the universal *$3/2$ critical exponent* for saddle-node escape known in statistical physics — while the Eyring–Kramers prefactor simultaneously diverges, creating an indeterminate form that neither classical FW nor standard Eyring–Kramers can resolve.

The resolution is the 2021 Hathcock–Sethna Airy scaling function, which provides a uniform asymptotic formula for the mean exit time across the metastable, critical, and supercritical regimes in terms of Airy functions $\operatorname{Ai}$ and $\operatorname{Bi}$. This result was derived by renormalization-group methods in a statistical mechanics journal and has had essentially no exposure in mathematical finance or applied probability. The present paper bridges three communities — Hathcock–Sethna (stat-mech RG), Berglund–Gentz / Dembo–Zeitouni (applied probability, slow-fast SDEs), and the stablecoin mathematical finance literature — by (i) rigorously establishing the FW LDP and Airy crossover for stablecoin reserve dynamics, (ii) extending to multi-asset reserves via center manifold reduction, (iii) calibrating to the USDC 2023 depeg, and (iv) deriving genuinely new special-function identities for the Hathcock–Sethna function along the way.

---

## Key Objects {#objects}

**The small-noise reserve SDE.** The reserve value $V_t^\varepsilon$ solves
$$
\mathrm{d} V_t^\varepsilon = b(V_t^\varepsilon;\lambda)\,\mathrm{d}t + \varepsilon\,\sigma(V_t^\varepsilon)\,\mathrm{d}W_t, \qquad V_0^\varepsilon = V_0,
$$
where $\lambda \geq 0$ is the *redemption pressure* (a positive drain rate parameterizing net outflows) and $\varepsilon > 0$ is the small-noise scale. The *peg-break time* is $\tau_\varepsilon = \inf\{t \geq 0 : V_t^\varepsilon \leq p^*L\}$, where $p^* \in (0,1]$ is the peg threshold and $L > 0$ is the fixed liability. Non-trivial point: the small-noise limit is the *rare-event* regime where depegs are exponentially unlikely; the parameter $\varepsilon$ controls this rarity and is not a calibrated quantity but a scaling device.

**The Freidlin–Wentzell action functional and rate function.** For a path $\phi \in C([0,T],\mathbb{R})$, the FW action with parameter $\lambda$ is
$$
S_T(\phi;\lambda) = \frac{1}{2}\int_0^T \frac{\bigl(\dot\phi(t) - b(\phi(t);\lambda)\bigr)^2}{\sigma(\phi(t))^2}\,\mathrm{d}t,
$$
and the rate function for peg-break within $[0,T]$ is the infimum over all paths that touch the peg threshold:
$$
I(T,\lambda) = \inf_{\phi \in \mathcal{A}_T} S_T(\phi;\lambda), \qquad \mathcal{A}_T = \bigl\{\phi\in C([0,T],\mathbb{R}) : \phi(0) = V_0,\ \exists\,t\in[0,T]\ \phi(t)\leq p^*L\bigr\}.
$$
The minimizer $\phi^*$ (the *instanton*) is the most likely path to depeg. Non-trivial point: computing $I$ in closed form requires solving a Euler–Lagrange ODE, which is tractable only for special drift structures.

**The saddle-node local normal form.** At the critical pair $(v_*, \lambda_c)$, the drift admits a Taylor expansion
$$
b(v_* + u;\,\lambda_c - \nu) = A\nu - Bu^2 + R(u,\nu), \qquad |R(u,\nu)| \leq C(|u|^3 + \nu^2 + u^2|\nu|),
$$
with $A, B > 0$ and $\nu = \lambda_c - \lambda \geq 0$. The stable and unstable equilibria of the leading-order drift $A\nu - Bu^2$ are at $u_\pm = \pm\sqrt{A\nu/B}$ and collide at $\nu = 0$. Non-trivial point: this normal form is *not* an assumption about the full model; Proposition 9.1 shows it is derivable from any model with a local maximum of the arbitrage feedback function $f$, covering a broad class of stablecoin designs.

**The Hathcock–Sethna scaling function.** The key special function is
$$
\mathcal{T}_{HS}(\eta) = 2^{1/3}\pi^2\Bigl[\operatorname{Ai}^2(2^{2/3}\eta) + \operatorname{Bi}^2(2^{2/3}\eta)\Bigr],
$$
where $\operatorname{Ai}$ and $\operatorname{Bi}$ are the standard Airy functions of the first and second kind, and $\eta$ is the dimensionless *distance to criticality*
$$
\eta = A\,B^{-1/3}(\lambda_c - \lambda)(\varepsilon\sigma(v_*))^{-4/3}.
$$
This function interpolates: $\mathcal{T}_{HS}(\eta) \sim \pi\eta^{-1/2}e^{(8/3)\eta^{3/2}}$ for $\eta \gg 1$ (Eyring–Kramers), $\mathcal{T}_{HS}(0) \approx 6.27$ at criticality, and $\mathcal{T}_{HS}(\eta) \sim \pi/\sqrt{|\eta|}$ for $\eta \to -\infty$ (supercritical deterministic traversal). Non-trivial point: the function is *universal* — independent of all model details except through the rescaling constants $\alpha, \beta, \eta$.

**The rescaling constants.** The conversion from original $(V,t)$ coordinates to the canonical saddle-node SDE $\mathrm{d}y = (\eta - y^2)\,\mathrm{d}\tau + \mathrm{d}W_\tau$ is effected by
$$
\alpha = (\varepsilon\sigma(v_*))^{2/3}B^{-1/3}, \qquad \beta = (\varepsilon\sigma(v_*))^{-2/3}B^{-2/3},
$$
where $\alpha$ has units of reserve value (spatial scale) and $\beta$ has units of time. The mean peg-break time scales as $\mathbb{E}[\tau_\varepsilon] \approx \beta\,\mathcal{T}_{HS}(\eta)$. Non-trivial point: $\beta \sim \varepsilon^{-2/3}$ diverges as $\varepsilon \to 0$, reflecting that even at criticality the mean exit time is parametrically large.

**The finite-boundary Hathcock–Sethna function.** For a finite rescaled absorbing barrier $\chi_+ \in \mathbb{R}$,
$$
\mathcal{T}_+(\eta,\chi_+) := 2\int_{\chi_+}^\infty \mathrm{d}y\int_{-\infty}^y \mathrm{d}z\,\exp\!\bigl(2\eta(y-z) - (2/3)(y^3 - z^3)\bigr),
$$
which equals the mean first-passage time of the canonical SDE from $+\infty$ to $\chi_+$, and recovers $\mathcal{T}_{HS}(\eta)$ as $\chi_+ \to -\infty$. Non-trivial point: this double integral is reduced by a sum/difference substitution to a computable one-dimensional integral, a reduction not previously carried out in the literature.

---

## Main Results {#main-results}

:::theorem{id=thm:LDP label="Freidlin–Wentzell LDP for Peg-Break"}
Under Assumption H1–H4, the peg-break time $\tau_\varepsilon = \inf\{t \geq 0 : V_t^\varepsilon \leq p^*L\}$ satisfies
$$
\lim_{\varepsilon \to 0^+} -\varepsilon^2\,\log\mathbb{P}(\tau_\varepsilon \leq T) = I(T,\lambda) := \inf_{\phi \in \mathcal{A}_T} S_T(\phi;\lambda),
$$
where
$$
S_T(\phi;\lambda) = \frac{1}{2}\int_0^T \frac{(\dot\phi(t) - b(\phi(t);\lambda))^2}{\sigma(\phi(t))^2}\,\mathrm{d}t,
$$
and $\mathcal{A}_T = \{\phi \in C([0,T],\mathbb{R}) : \phi(0) = V_0,\ \exists\,t\in[0,T]\ \phi(t) \leq p^*L\}$.
:::

This theorem asserts that in the small-noise limit, the log-probability of a depeg event within time $T$ is governed entirely by the minimum "energetic cost" of driving the reserve path from $V_0$ down to $p^*L$. The cost of a path $\phi$ is the integrated squared deviation from the drift, normalized by the local diffusion: paths that fight the drift strongly are exponentially unlikely. The key structural insight is that the rate function depends on $\lambda$ only through $b(\cdot;\lambda)$, so the full $(\lambda, T)$ parameter space of depeg risk is encoded in a single variational problem.

**Why it's surprising:** The LDP holds under only Lipschitz and non-characteristic-boundary regularity, with *no* convexity or gradient structure assumed on $b$, which is essential for the nonlinear feedback drifts appearing in real stablecoin models.

---

:::theorem{id=thm:linear label="Linear-Drain Rate Function and Prefactor"}
For the SDE $\mathrm{d}V_t^\varepsilon = -\lambda\,\mathrm{d}t + \varepsilon\sigma_0\,\mathrm{d}W_t$ with $a = V_0 - p^*L > 0$ and $\lambda_c = a/T$:

1. For $\lambda \in [0,\lambda_c)$:
$$
\lim_{\varepsilon\to 0^+} -\varepsilon^2\log\mathbb{P}(\tau_\varepsilon \leq T) = \frac{T(\lambda_c - \lambda)^2}{2\sigma_0^2}.
$$

2. Sharp Eyring–Kramers prefactor:
$$
\mathbb{P}(\tau_\varepsilon \leq T) = \frac{2\lambda_c\,\varepsilon\sigma_0}{\sqrt{2\pi T}\,(\lambda_c^2 - \lambda^2)}\,\exp\!\Bigl(-\frac{T(\lambda_c-\lambda)^2}{2\varepsilon^2\sigma_0^2}\Bigr)\,(1 + O(\varepsilon^2)).
$$

3. At $\lambda = \lambda_c$: $\lim_{\varepsilon\to 0^+}\mathbb{P}(\tau_\varepsilon \leq T) = 1/2$.

4. For $\lambda > \lambda_c$: $\lim_{\varepsilon\to 0^+}\mathbb{P}(\tau_\varepsilon \leq T) = 1$ exponentially fast.
:::

For the simplest linear drain, the depeg probability transitions sharply across three regimes as $\lambda$ crosses the critical drain rate $\lambda_c = a/T$: exponentially rare below (with an explicit quadratic rate function), exactly $1/2$ at criticality (a universally clean result), and certain above. The prefactor in regime 2 provides a complete asymptotic formula — exponential rate plus algebraic prefactor — that is exact up to $O(\varepsilon^2)$ corrections.

**Why it's surprising:** The closed-form prefactor $2\lambda_c\varepsilon\sigma_0/[\sqrt{2\pi T}(\lambda_c^2 - \lambda^2)]$ is *not* the naive Gaussian tail approximation; it comes from the full inverse-Gaussian first-passage density and correctly captures both terms in the Mills'-ratio expansion, including the non-trivial factor $1/(\lambda_c^2 - \lambda^2)$ rather than $1/(\lambda_c - \lambda)$.

---

:::theorem{id=thm:saddle label="Saddle-Node Universal $3/2$ Exponent and Eyring–Kramers Prefactor"}
Suppose Assumptions H1–H4 and the saddle-node hypothesis H5–H7 hold.

*(i) Critical asymptotic.* As $\lambda \to \lambda_c^-$, provided $T > T_{\min}(\lambda) = O((\lambda_c-\lambda)^{-1/2}\log(1/(\lambda_c-\lambda)))$:
$$
I(T,\lambda) = \frac{8\,A^{3/2}}{3\sqrt{B}\,\sigma(v_*)^2}\,(\lambda_c - \lambda)^{3/2}\,(1 + o(1)).
$$

*(ii) Eyring–Kramers prefactor.* For $\lambda_c - \lambda \geq c_0 > 0$:
$$
\mathbb{E}[\tau_\varepsilon] = \frac{\pi}{\sqrt{AB(\lambda_c - \lambda)}}\,\exp\!\Bigl(\frac{8\,A^{3/2}(\lambda_c-\lambda)^{3/2}}{3\sqrt{B}\,\sigma(v_*)^2\,\varepsilon^2}\Bigr)\,(1 + O(\varepsilon)).
$$
:::

Part (i) identifies the universal $3/2$ critical exponent: regardless of the specific stablecoin design (as long as it has a saddle-node bifurcation), the activation energy for depeg vanishes as $(\lambda_c - \lambda)^{3/2}$ and not as any other power. Part (ii) gives the Eyring–Kramers formula with an explicit prefactor $\pi/\sqrt{AB(\lambda_c-\lambda)}$, where the factors $A$ (sensitivity of the drift to redemption pressure) and $B$ (curvature at the bifurcation point) appear with specific square-root powers that are easy to get wrong without careful convention conversion.

**Why it's surprising:** The prefactor contains $\sqrt{A}$ in the denominator — a factor absent from naive dimensional analysis and arising from the Berglund saddle-exit formula after careful conversion between the $\mathrm{d}X = -U'\,\mathrm{d}t + \sqrt{2}\varepsilon\,\mathrm{d}W$ convention and the $\mathrm{d}V = b\,\mathrm{d}t + \varepsilon\sigma\,\mathrm{d}W$ convention used here; this factor is verified by SymPy symbolic computation.

---

:::theorem{id=thm:airy label="Universal Airy Crossover (Hathcock–Sethna)"}
Under Assumptions H1–H4, H5–H7, with $\sigma$ of class $C^2$ near $v_*$, define
$$
\alpha = (\varepsilon\sigma(v_*))^{2/3}B^{-1/3},\quad \beta = (\varepsilon\sigma(v_*))^{-2/3}B^{-2/3},\quad \eta = A\,B^{-1/3}(\lambda_c - \lambda)(\varepsilon\sigma(v_*))^{-4/3}.
$$
Fix a bounded set $K \subset \mathbb{R}$. Then, as $\varepsilon \to 0^+$ along sequences $(\varepsilon_n, \nu_n)$ with $\eta_n \in K$,
$$
\mathbb{E}[\tau_{\varepsilon_n}] = \beta_n\,\mathcal{T}_{HS}(\eta_n)\,\bigl(1 + O(\varepsilon_n^{2/3}\log(1/\varepsilon_n))\bigr),
$$
uniformly in $\eta \in K$, where
$$
\mathcal{T}_{HS}(\eta) = 2^{1/3}\pi^2\Bigl[\operatorname{Ai}^2(2^{2/3}\eta) + \operatorname{Bi}^2(2^{2/3}\eta)\Bigr].
$$
:::

This is the central result of the paper. The single formula $\beta\,\mathcal{T}_{HS}(\eta)$ interpolates uniformly across all three regimes: deep metastable ($\eta \gg 1$, exponentially long exit times), critical ($\eta = 0$, finite universal constant $\mathcal{T}_{HS}(0) \approx 6.27$), and supercritical ($\eta < 0$, deterministic traversal time). The rescaling $\eta \propto \nu\varepsilon^{-4/3}$ shows that the crossover width in $\nu = \lambda_c - \lambda$ is $O(\varepsilon^{4/3})$: a thin region that shrinks as noise decreases. The error rate $O(\varepsilon^{2/3}\log(1/\varepsilon))$ is explicit and sharp.

**Why it's surprising:** The formula is *genuinely uniform* in $\eta$: the same closed form, without case distinctions, recovers the exponential Eyring–Kramers formula for large $\eta$ and the algebraic $\pi/\sqrt{|\eta|}$ formula for negative $\eta$, via the known asymptotics of Airy functions — a single special function encodes all three physical regimes of a financial stability problem.

---

:::theorem{id=thm:airy-integral label="Airy-Squared Integral Identity and 1D Representation of $\mathcal{T}_{HS}$"}
The Hathcock–Sethna scaling function admits the one-dimensional integral representation
$$
\mathcal{T}_{HS}(\eta) = \sqrt{2\pi}\int_0^\infty t^{-1/2}\,e^{2\eta t - t^3/6}\,\mathrm{d}t = 2^{1/3}\pi^2\Bigl[\operatorname{Ai}^2(2^{2/3}\eta) + \operatorname{Bi}^2(2^{2/3}\eta)\Bigr],
$$
valid for all $\eta \in \mathbb{R}$. Equating the two closed forms yields the Airy-squared integral identity
$$
\int_0^\infty t^{-1/2}\,e^{2\eta t - t^3/6}\,\mathrm{d}t = 2^{-1/6}\,\pi^{3/2}\,\Bigl[\operatorname{Ai}^2(2^{2/3}\eta) + \operatorname{Bi}^2(2^{2/3}\eta)\Bigr], \qquad \eta \in \mathbb{R}.
$$
:::

This theorem gives an elementary proof path to the Hathcock–Sethna closed form that bypasses their Schrödinger spectral analysis entirely: one simply changes variables in the double Pontryagin integral to sum/difference coordinates, evaluates the Gaussian inner integral, and takes $\chi_+ \to -\infty$. The resulting 1D integral representation is amenable to direct numerical quadrature and Laplace/stationary-phase analysis, allowing all three limiting regimes to be recovered from a single formula (see Remark on asymptotic consistency). The Airy-squared identity on the right does not appear to have been recorded in Abramowitz–Stegun, DLMF §9.11, or Gradshteyn–Ryzhik.

**Why it's surprising:** The identity connects a Laplace-type integral with a cubic exponent and a square-root weight — a form that appears naturally in saddle-node escape — to the *sum* $\operatorname{Ai}^2 + \operatorname{Bi}^2$ of Airy function squares, a combination that typically arises in wave-theoretic contexts via the Wronskian; that these two very different mathematical worlds are identified by an elementary substitution is unexpected.

---

:::theorem{id=thm:multid-saddle label="Multi-Dimensional Saddle-Node: Persistence of $3/2$ Exponent"}
Suppose the multi-asset reserve SDE satisfies a multi-dimensional saddle-node assumption, and that the noise is non-degenerate in the slow (center manifold) direction: $\sigma_\|^2 := \ell^T\sigma(v_*)\sigma(v_*)^T\ell > 0$ where $\ell$ is the left eigenvector of $D_vb(v_*;\lambda_c)$ for the zero eigenvalue. Then, as $\varepsilon \to 0^+$ and $\nu := \lambda_c - \lambda \to 0^+$ with $\nu \gg \varepsilon^{4/3}$,
$$
I(T,\lambda) = \frac{8\,A^{3/2}}{3\sqrt{B}\,\sigma_\|^2}\,\nu^{3/2}\,(1+o(1)),
$$
and the Eyring–Kramers prefactor is $\pi/\sqrt{AB\nu}$ for $\lambda$ bounded away from $\lambda_c$. The universal $3/2$ critical exponent persists, with $\sigma(v_*)^2$ replaced by $\sigma_\|^2$.
:::

For stablecoins holding multiple reserve assets (e.g., a mixture of T-bills, money market funds, and bank deposits), the reserve state space is multi-dimensional. This theorem shows that after projecting onto the center manifold direction $\ell$, the entire saddle-node LDP theory — including the $3/2$ exponent and Eyring–Kramers prefactor — carries through unchanged, with only $\sigma(v_*)^2$ replaced by the effective noise strength $\sigma_\|^2$ in the slow direction. The fast directions are exponentially slaved to the slow manifold and contribute only to higher-order corrections.

**Why it's surprising:** The universality of the $3/2$ exponent is robust even to arbitrary multi-asset mixing: a stablecoin backed by $n$ assets reduces to a *one-dimensional* saddle-node problem on its center manifold, with all the one-dimensional Airy-crossover formulae applying with a single model-dependent scalar $\sigma_\|$.

---

## Proof Sketches {#proofs}

:::proof-sketch{for=thm:LDP}
1. **Sample-path LDP on a compact interval.** Apply Dembo–Zeitouni Theorem 5.6.3 to the family $\{V^\varepsilon\}$ on $C([0,T],\mathbb{R})$ restricted to $[p^*L - \delta, V_{\max}]$, where the Lipschitz hypothesis (H1) guarantees the LDP with rate function $S_T$.
2. **Exit-time LDP from the absorbing boundary condition.** Translate the sample-path LDP into an exit-time statement using Freidlin–Wentzell Chapter 4 §2 Theorem 4.2.1, invoked under the non-characteristic boundary hypothesis (H3), which ensures the exit problem is well-posed and the infimum is attained.
3. **Identification of the rate function as a variational infimum.** The event $\{\tau_\varepsilon \leq T\}$ corresponds exactly to sample paths in $\mathcal{A}_T$, so $I(T,\lambda) = \inf_{\phi \in \mathcal{A}_T} S_T(\phi;\lambda)$ by contraction of the sample-path LDP onto $\mathcal{A}_T$.
:::

:::proof-sketch{for=thm:linear}
1. **Variational computation via Cauchy–Schwarz.** For any path $\phi$ reaching $p^*L$ by time $t^* \leq T$, Cauchy–Schwarz on $\int_0^{t^*}(\dot\phi + \lambda)^2\,\mathrm{d}t$ gives a lower bound $(\lambda t^* - a)^2/(2\sigma_0^2 t^*)$, minimized over $t^* \in (0,T]$ at $t^* = T$ when $\lambda < \lambda_c$ (the function $g(t^*) = (\lambda t^* - a)^2/t^*$ is decreasing on $(0,T]$), yielding the closed-form rate $T(\lambda_c - \lambda)^2/(2\sigma_0^2)$.
2. **Sharp prefactor via the exact first-passage formula.** The exact inverse-Gaussian formula $\mathbb{P}(\tau_\varepsilon \leq T) = \Phi(z_1) + e^{2\lambda a/(\varepsilon\sigma_0)^2}\Phi(z_2)$ from Karatzas–Shreve §2.5.2 is expanded using Mills' ratio $\Phi(-x) \sim e^{-x^2/2}/(x\sqrt{2\pi})$; SymPy-verified algebra yields the stated prefactor.
3. **Critical and supercritical cases.** At $\lambda = \lambda_c$, $z_1 = 0$ so $\Phi(0) = 1/2$ and the second term is exponentially small. For $\lambda > \lambda_c$, the deterministic path $V_0 - \lambda t$ crosses $p^*L$ before $T$, so the event has probability tending to 1.
:::

:::proof-sketch{for=thm:saddle}
1. **Instanton action via the time-reversed flow.** The optimal escape path satisfies $\dot\phi = -b_{\text{normal}}(\phi)$ (the time-reversed saddle-node drift). Direct integration from $u_+ = +\sqrt{A\nu/B}$ to $u_- = -\sqrt{A\nu/B}$ gives
$$S_{\min}(\nu) = -\frac{2}{\sigma(v_*)^2}\int_{u_+}^{u_-}(A\nu - Bu^2)\,\mathrm{d}u = \frac{8A^{3/2}\nu^{3/2}}{3\sqrt{B}\,\sigma(v_*)^2},$$
verified by SymPy (Appendix V2).
2. **Taylor remainder bound.** The correction from the cubic-and-higher terms $R(u,\nu)$ to the action is bounded using the instanton duration $T_{\text{inst}} = O(\nu^{-1/2}\log(1/\nu))$: the cross-term $\mathcal{E}_1 = O(\nu^2\log(1/\nu))$ and the quadratic remainder $\mathcal{E}_2 = O(\nu^{5/2}\log(1/\nu))$ are both $o(\nu^{3/2})$, establishing $S_{\min}(\nu) = (8A^{3/2}/3\sqrt{B}\sigma_*^2)\nu^{3/2}(1+o(1))$.
3. **Eyring–Kramers prefactor via Berglund's formula.** Converting from the Berglund $\mathrm{d}X = -U'\,\mathrm{d}t + \sqrt{2}\varepsilon\,\mathrm{d}W$ convention to the present convention (factor of 2 in the exponent), the effective potential $U(u) = -A\nu u + Bu^3/3$ gives curvatures $U''(u_\pm) = 2\sqrt{AB\nu}$ at both equilibria, and the prefactor formula yields $\pi/\sqrt{AB\nu}$ with the $\sqrt{A}$ factor verified by SymPy (Appendix V3).
:::

:::proof-sketch{for=thm:airy}
1. **Pontryagin formula and local–nonlocal split.** Write the mean exit time via the Pontryagin double-integral formula on $[p^*L, +\infty)$. Split the integration domain into a local region $|u| \