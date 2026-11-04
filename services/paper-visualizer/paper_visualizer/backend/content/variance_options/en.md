---
paper_slug: variance_options
lang: en
sections:
  - id: context
    title: "Background and Motivation"
  - id: objects
    title: "Key Mathematical Objects"
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

Options on realized variance — contracts whose payoff depends on the annualized quadratic variation $T^{-1}\int_0^T V_s\eta^2(S_s)\,\dd s$ — have become instruments of first-class practical importance following the 2024 launch of CBOE S&P 500 Variance Futures. Pricing these products requires understanding how the risk-neutral distribution of realized variance concentrates near expiry. The standard tool is **large deviations theory**: as $T \to 0$, the probability that the time-average variance lands far from its starting value $V_0\eta^2(S_0)$ is exponentially suppressed, and the exponent is the *rate function* $I_\rho$. The precise link is $\lim_{T\to 0} T\log C(T) = -I_\rho$, where $C(T)$ is the OTM variance call price.

The foundational paper by Pirjol, Wang and Zhu (PWZ, 2025) cast $I_\rho$ as the value of a constrained two-path variational problem — an optimization over the joint log-price path $g(t) = \log S_t$ and log-variance path $h(t) = \log V_t$ — and solved it **explicitly only when the asset–volatility correlation $\rho = 0$**. For general $\rho$, PWZ obtained the sandwich bounds $(1+|\rho|)^{-1}I_0 \leq I_\rho \leq (1-|\rho|)^{-1}I_0$ and noted that the Euler–Lagrange equations for correlated paths "seem impossible to solve in closed form."

This paper fills that gap in three complementary ways. First, it proves that $I_\rho$ is **real-analytic** in $\rho$ near zero via the analytic implicit function theorem in Banach spaces, giving a rigorous Taylor series with explicit remainder bounds. Second, it computes the expansion coefficients — especially the first-order correction $I_1 = -C[g_0,h_0]$ via the envelope theorem — and discovers the striking **correlation-invariance** result: for pure stochastic volatility (SV) models with constant local volatility $\eta$, one has $I_\rho = I_0$ for *all* $\rho \in (-1,1)$, not just perturbatively. Third, in the Heston model, it reduces the $\rho=0$ variational problem to the classical Ermakov–Pinney ODE, obtaining a **fully explicit closed-form** expression for $I_0$ and thereby for the entire rate function. A final thread connects these rate-function expansions to the Alo`s decomposition of option prices, identifying the cross-correlation functional $C[g,h]$ as a universal sensitivity that governs both the tail and the bulk of the variance distribution.

## Key Mathematical Objects {#objects}

**The local-stochastic volatility model.** Under the risk-neutral measure, asset price $S_t$ and variance $V_t$ evolve as

$$
\frac{\dd S_t}{S_t} = \eta(S_t)\sqrt{V_t}\bigl(\rho\,\dd Z_t + \sqrt{1-\rho^2}\,\dd W_t\bigr), \qquad \frac{\dd V_t}{V_t} = \mu(V_t)\,\dd t + \sigma(V_t)\,\dd Z_t,
$$

with $W_t, Z_t$ independent. The function $\eta(\cdot)$ is the *local volatility multiplier* (constant $\eta = 1$ gives pure SV, e.g. Heston). Non-triviality: the coupling of $\eta(S_t)$ to both $S_t$ and $V_t$ through the variance constraint is what makes the correlated variational problem hard and the LSV case qualitatively different from pure SV.

**The action functional and its decomposition.** For absolutely continuous paths $(g,h)$ on $[0,1]$, the action is

$$
\Lambda_\rho[g,h] = \frac{1}{2(1-\rho^2)}\bigl(A[g,h] + B[g,h] - 2\rho\,C[g,h]\bigr),
$$

where the three fundamental quadratic forms are

$$
A[g,h] := \int_0^1 \frac{(g')^2}{\eta^2(e^g)\,e^h}\,\dd t, \quad B[g,h] := \int_0^1 \frac{(h')^2}{\sigma^2(e^h)}\,\dd t, \quad C[g,h] := \int_0^1 \frac{g'(t)\,h'(t)}{\eta(e^g)\,e^{h/2}\,\sigma(e^h)}\,\dd t.
$$

$A$ is the *asset action*, $B$ is the *volatility action*, and $C$ is the *cross-correlation functional*. Non-triviality: the factor $1/(1-\rho^2)$ makes $\Lambda_\rho$ singular as $\rho\to\pm 1$, but the infimum $I_\rho$ may remain finite because the minimizer can make the numerator $A+B-2\rho C$ vanish (exactly so in the pure SV case).

**The rate function as a constrained variational problem.**

$$
I_\rho(S_0, V_0, K) = \inf_{\substack{g(0)=\log S_0,\; h(0)=\log V_0 \\ \int_0^1 e^{h}\eta^2(e^g)\,\dd t = K}} \Lambda_\rho[g,h],
$$

with transversality conditions $g'(1) = h'(1) = 0$ at the free right endpoint. Non-triviality: the integral constraint $\int e^h\eta^2(e^g)\,\dd t = K$ couples the two paths in a nonlinear way, making the Euler–Lagrange system a non-standard two-component fourth-order BVP.

**The cross-correlation functional $C_0 = C[g_0,h_0]$.** This is $C$ evaluated at the $\rho=0$ optimal paths $(g_0,h_0)$. By the Cauchy–Schwarz inequality, $|C_0| \leq \sqrt{A_0 B_0} \leq I_0$, which keeps the first-order expansion self-consistent with the PWZ bounds. Financially, $C_0$ measures the alignment between optimal asset-price and volatility fluctuations along the most-likely rare path.

**The Ermakov–Pinney equation.** In the Heston model, after the substitution $u = 1/\sqrt{v}$ (where $v = e^h$ is the variance path), the Euler–Lagrange equation for the variance path reduces to

$$
u''(t) = -\frac{\lambda}{u^3(t)},
$$

a classical nonlinear ODE from quantum mechanics and cosmology. Its general solution is $u(t) = \sqrt{A + Bt + Ct^2}$, yielding an algebraically explicit optimal variance path. Non-triviality: this is, to the authors' knowledge, the first appearance of the Ermakov–Pinney equation in option pricing.

**The Euler–Lagrange map $F$.** For the analyticity argument, one encodes the full system (E-L equations + constraint + transversality) as a map $F: \mathcal{X} \times (-1,1) \to \mathcal{Y}$ between Banach spaces, where $\mathcal{X} \subset H^1[0,1]^2 \times \mathbb{R}$. Analyticity of $I_\rho$ then follows from the analytic implicit function theorem applied to $F(g,h,\lambda;\rho) = 0$. Non-triviality: invertibility of the bordered Hessian at $\rho=0$ (Assumption~3) is the key hypothesis that must be verified model by model.

## Main Results {#main-results}

:::theorem{id=thm_main label="First-Order Perturbation of the Rate Function"}
Under Assumptions 1–3, the rate function admits the expansion

$$
I_\rho = I_0 - \rho\, C[g_0, h_0] + O(\rho^2),
$$

where $C[g_0, h_0]$ is the cross-correlation integral evaluated on the $\rho = 0$ optimal paths. Equivalently,

$$
I_1 := \left.\frac{\dd I_\rho}{\dd\rho}\right|_{\rho=0} = -\int_0^1 \frac{g_0'(t)\,h_0'(t)}{\eta\bigl(e^{g_0(t)}\bigr)\,e^{h_0(t)/2}\,\sigma\bigl(e^{h_0(t)}\bigr)}\,\dd t = -C_0.
$$
:::

The envelope theorem (Danskin's theorem) says: to differentiate the minimum value with respect to a parameter, just differentiate the integrand at the minimizer — the minimizer's own $\rho$-derivative contributes nothing because it satisfies the E-L equations. Setting $\rho = 0$ in $\partial\Lambda_\rho/\partial\rho$ kills the $(A_0+B_0)$ term (it is multiplied by $\rho$) and leaves $-C_0$. Thus the first-order correction is a single, explicit integral over the already-known $\rho=0$ paths. The Cauchy–Schwarz bound $|I_1| = |C_0| \leq I_0$ guarantees this is consistent with the PWZ sandwich bounds at first order.

**Why it's surprising:** The simplest possible application of the envelope theorem yields the first-order correction as a single computable integral — no need to solve any new BVP at this order, even though the full Euler–Lagrange system at $\rho \neq 0$ is intractable.

---

:::theorem{id=cor_SV label="Correlation Invariance for Pure Stochastic Volatility"}
When $\eta(\cdot) \equiv \eta_0$ is constant, the rate function is independent of the correlation:

$$
I_\rho = I_0 \qquad \text{for all } \rho \in (-1,1).
$$

That is, $I_k = 0$ for all $k \geq 1$. Equivalently, $I_\rho$ extends continuously to $\rho = \pm 1$ with $I_{\pm 1} = I_0$.
:::

When $\eta$ is constant, the variance constraint $\int e^h\,\dd t = K/\eta_0^2$ involves only the volatility path $h$, leaving the asset path $g$ completely free. For any feasible $h$, one can define a *correlated* asset path

$$
g_\rho(t) := \log S_0 + \rho\int_0^t \frac{e^{h(s)/2}\,h'(s)}{\sigma(e^{h(s)})}\,\dd s,
$$

which satisfies the transversality $g_\rho'(1) = 0$ automatically (because $h'(1)=0$) and, when substituted into $\Lambda_\rho$, causes the cross term in the action to cancel exactly, yielding $\Lambda_\rho[g_\rho, h] = B[h]/2$. Minimizing over $h$ gives $I_\rho \leq I_0$; the reverse inequality is trivial since $\Lambda_\rho \geq B[h]/2$ for any $(g,h)$.

**Why it's surprising:** Equity option implied volatility skews are entirely driven by $\rho$ (Heston, Black–Scholes). Yet for variance options in pure SV models, $\rho$ has *zero effect* on the short-maturity tail. The free endpoint of the asset path absorbs the correlation at zero cost. This is a qualitative structural difference between equity and variance option skews.

---

:::theorem{id=thm_analyticity label="Analyticity of the Rate Function"}
Under Assumptions 1–3, there exists $r > 0$ such that:
(i) The minimizer $(g^*(\rho), h^*(\rho), \lambda^*(\rho))$ is real-analytic as a map $(-r,r) \to H^1[0,1]^2 \times \mathbb{R}$.
(ii) The rate function $I_\rho = \Lambda_\rho[g^*(\rho), h^*(\rho)]$ is real-analytic on $(-r,r)$.
(iii) The convergence radius satisfies

$$
r \geq \frac{\alpha}{\|D_\rho F|_0\|},
$$

where $\alpha$ is the coercivity constant and $\|D_\rho F|_0\|$ is the operator norm of the $\rho$-derivative of $F$ at the origin.
(iv) For any $N \geq 0$ and $|\rho| < r$, the truncation error satisfies

$$
\left|I_\rho - \sum_{k=0}^N I_k\,\rho^k\right| \leq \frac{M\,|\rho|^{N+1}}{r - |\rho|}.
$$
:::

The Euler–Lagrange map $F(g,h,\lambda;\rho)=0$ is analytic jointly in $(g,h,\lambda)$ and $\rho$ because: the model coefficients $\eta, \sigma$ are analytic (Assumption 1), their compositions with $e^g, e^h$ are analytic on $H^1$, and the only $\rho$-dependence is through the analytic factor $1/(1-\rho^2)$. Invertibility of the bordered Hessian at $\rho=0$ (Assumption 3) licenses the analytic IFT in Banach spaces, producing the analytic curve of minimizers. The error bound then follows from the standard Cauchy estimate $|I_k| \leq M/r^k$.

**Why it's surprising:** The formal perturbation series is not just asymptotic — it converges on a genuine interval. The radius $r$ is bounded away from zero by a coercivity-over-sensitivity ratio, which is explicitly computable in the Heston model (giving $r = \infty$ trivially since all nontrivial coefficients vanish).

---

:::theorem{id=thm_heston label="Explicit Heston Solution via the Ermakov–Pinney Equation"}
In the Heston model ($\eta \equiv 1$, $\sigma(V) = \xi\sqrt{V}$), define $p \in (0,1)$ by the constraint equation

$$
\frac{\arctan\!\left(\sqrt{p/(1-p)}\right)}{\sqrt{p\,(1-p)}} = \frac{K}{V_0}.
$$

Then the $\rho=0$ optimal variance path is

$$
v^*(t) = \frac{V_0}{1 - p + p(t-1)^2}, \qquad t \in [0,1],
$$

and the rate function is

$$
I_0(K) = \frac{2p}{\xi^2 V_0}\left[1 - \sqrt{\frac{1-p}{p}}\,\arctan\!\left(\sqrt{\frac{p}{1-p}}\right)\right].
$$

For $K > V_0$ (OTM call), $p > 0$ and $v^*$ is increasing; for $K < V_0$ (OTM put), $p < 0$ and $v^*$ is decreasing; at $K = V_0$ (ATM), $p = 0$ and $v^* \equiv V_0$.
:::

The change of variables $u = 1/\sqrt{v}$ converts the isoperimetric problem $\min \frac{1}{\xi^2}\int (v')^2/v^3\,\dd t$ subject to $\int v\,\dd t = K$ into $\min \frac{2}{\xi^2}\int (u')^2\,\dd t$ subject to $\int u^{-2}\,\dd t = K$. The Euler–Lagrange equation $u'' = -\lambda/u^3$ is exactly the Ermakov–Pinney ODE, whose general solution is $u(t) = \sqrt{A+Bt+Ct^2}$. Imposing boundary conditions $u(0) = 1/\sqrt{V_0}$ and $u'(1)=0$ fixes two constants, and the constraint $\int v\,\dd t = K$ determines $p = CV_0$ via an arctangent integral. Back-substituting gives the rational form of $v^*(t)$ and a closed-form integral for $I_0$.

**Why it's surprising:** A centuries-old nonlinear ODE from quantum mechanics ($u'' = -\lambda/u^3$) produces a closed-form formula for the variance option rate function involving only arctangent and square roots — with no special functions beyond the elementary. Moreover, since the Heston model is pure SV, Corollary~$I_\rho = I_0$ applies, making this explicit formula exact for all correlations.

---

:::theorem{id=prop_saturation label="Far-Wing Saturation of the Rate Function"}
In the Heston model, as $K \to \infty$:

$$
I_0(K) \;\to\; I_0^{\max} := \frac{2}{\xi^2 V_0}.
$$

More precisely, as $p \to 1^-$:

$$
I_0(K) = \frac{2}{\xi^2 V_0}\left[1 - \sqrt{\frac{1-p}{p}}\,\frac{\pi}{2} + O(1-p)\right] \to \frac{2}{\xi^2 V_0}.
$$
:::

As $K \to \infty$, the constraint forces the variance path to reach arbitrarily large values, which requires increasingly extreme volatility fluctuations. Yet $I_0$ does not diverge: it saturates at $2/(\xi^2 V_0)$ because the geometric structure of the Heston variance path (a rational function with a single free parameter $p$) limits how much action can be "squeezed out" by driving $p \to 1$. When $K \to \infty$ we have $p \to 1$, and $v^*(1) = V_0/(1-p) \to \infty$, but the integral $\int_0^1 (v^{*\prime})^2/(v^*)^3\,\dd t$ converges to a finite limit.

**Why it's surprising:** For standard equity options, the Lee moment formula gives implied volatility growing as $\sqrt{\log K}$ in the far wing, driven by a diverging rate function. Here $I_0$ saturates, so the variance option implied volatility grows only as $|\log(K/F_V)|/\sqrt{2I_0^{\max}}$ — the smile *flattens* rather than steepens in deep OTM variance calls. This is a fundamental structural difference between variance and equity option wings.

---

:::theorem{id=thm_alos_connection label="Connection with the Aloès Decomposition"}
Consider a pure stochastic volatility model ($\eta \equiv 1$). Then:
(i) In the rate-function expansion, $I_1 = -C[g_0, h_0] = 0$ because the $\rho=0$ optimal asset path satisfies $g_0' \equiv 0$.
(ii) In the Aloès decomposition for variance options, the first-order $\rho$-correction $\Delta_1(T)$ is proportional to

$$
\mathbb{E}\!\left[\int_0^T \Gamma_t^V \cdot \rho\cdot \langle \dd S_t, \dd V_t\rangle\right],
$$

where $\Gamma_t^V$ is the Gamma of the variance option payoff with respect to variance. For variance options with constant $\eta$, this expectation is zero by the same structural cancellation that gives $g_0' \equiv 0$.

Both the Aloès decomposition (bulk regime, moderate strikes) and the rate-function expansion (tail regime, extreme strikes) are controlled by the same cross-correlation functional $C[g,h]$, and both independently predict $\rho$-invariance when $\eta$ is constant.
:::

The Aloès decomposition is a martingale representation that splits an option price into its Black–Scholes price plus a correction from stochastic volatility. For variance options, this correction is driven by $\rho\langle \dd S, \dd V\rangle$, which integrates $g'\cdot h'$ along sample paths — exactly the integrand of $C[g,h]$. In the pure SV case, the expectation of this integrand vanishes because the optimal (most likely) path has $g_0' \equiv 0$, which is also why $C_0 = 0$. The two theories thus converge on the same zero, but through completely different mechanisms (martingale decomposition vs. large-deviations optimization).

**Why it's surprising:** The same functional $C[g,h]$ simultaneously controls the Black–Scholes delta/vega correction at typical strikes (Aloès, bulk) and the rate-function perturbation at extreme strikes (large deviations, tail). This suggests $C[g,h]$ is a fundamental quantity of variance option sensitivities, not an artifact of either technique.

## Proof Sketches {#proofs}

:::proof-sketch{for=thm_main}
1. **Envelope theorem (Danskin).** Write $I_\rho = \inf_{(g,h)\in\mathcal{C}} \Lambda_\rho[g,h]$. Since the minimizer is unique and smooth in $\rho$ (guaranteed later by Theorem~`thm_analyticity`), $\dd I_\rho/\dd\rho = \partial\Lambda_\rho/\partial\rho|_{g^*(\rho),h^*(\rho)}$ — the optimizer's own $\rho$-derivative contributes zero because it satisfies the E-L equations.
2. **Differentiate $\Lambda_\rho$ at fixed paths.** From the decomposition $\Lambda_\rho = (A+B-2\rho C)/(2(1-\rho^2))$, one computes $\partial\Lambda_\rho/\partial\rho = \rho(A+B)/(1-\rho^2)^2 - (1+\rho^2)C/(1-\rho^2)^2$.
3. **Evaluate at $\rho=0$.** The term $\rho(A_0+B_0)/(1-\rho^2)^2$ vanishes at $\rho=0$, leaving $-C_0$.
:::

:::proof-sketch{for=cor_SV}
1. **Construct a feasible path for each $\rho$.** For any fixed feasible $h$ (satisfying $\int\eta_0^2 e^h\,\dd t = K$), define $g_\rho(t) = \log S_0 + \rho\int_0^t e^{h/2}h'/\sigma(e^h)\,\dd s$. This satisfies $g_\rho(0) = \log S_0$ and, since $h'(1) = 0$, the transversality $g_\rho'(1) = 0$.
2. **Plug into the action.** The cross term $g_\rho'/(\eta_0 e^{h/2}) = \rho h'/\sigma(e^h)$ exactly matches $\rho$ times the volatility speed, so the integrand in the $1/(2(1-\rho^2))$ bracket becomes $(\rho h'/\sigma - \rho h'/\sigma)^2 = 0$. Hence $\Lambda_\rho[g_\rho, h] = B[h]/2$.
3. **Two-sided inequality.** The upper bound $I_\rho \leq \inf_h B[h]/2 = I_0$ follows from feasibility. The lower bound $I_\rho \geq I_0$ follows since $\Lambda_\rho[g,h] \geq B[h]/2$ for any $(g,h)$ (the omitted first integral is non-negative). Together, $I_\rho = I_0$.
:::

:::proof-sketch{for=thm_analyticity}
1. **Analytic Euler–Lagrange map.** The map $F(g,h,\lambda;\rho)$ encodes E-L equations + constraint + transversality. Its analyticity in all arguments follows from: model coefficients $\eta,\sigma$ are analytic (Assumption 1); $\rho$-dependence enters only via the analytic factor $1/(1-\rho^2)$; compositions $\eta(e^g)$, $\sigma(e^h)$ are analytic on $H^1$ by the chain rule for analytic Banach-space maps.
2. **Invertibility of the bordered Hessian.** At $\rho=0$, the derivative $D_{(g,h,\lambda)}F$ is the bordered operator $\begin{pmatrix}\delta^2\mathcal{L}_0 & \delta\Phi^T \\ \delta\Phi & 0\end{pmatrix}$. Under Assumption 3, $\delta^2\mathcal{L}_0$ is coercive on $\ker\delta\Phi$, and $\delta\Phi$ is surjective; by the Bonnans–Shapiro theory of constrained optimization, this implies invertibility.
3. **Analytic implicit function theorem.** Since $F$ is analytic and $D_{(g,h,\lambda)}F|_{\rho=0}$ is invertible, the analytic IFT (Deimling, Zeidler) produces an analytic curve $\rho\mapsto(g^*(\rho),h^*(\rho),\lambda^*(\rho))$ on $(-r,r)$. Composing with the analytic map $\Lambda_\rho$ gives analyticity of $I_\rho$, and Cauchy estimates yield the error bound $|R_{N+1}| \leq M|\rho|^{N+1}/(r-|\rho|)$.
:::

:::proof-sketch{for=thm_heston}
1. **Change of variables $u = 1/\sqrt{v}$.** The action $\int (v')^2/v^3\,\dd t$ transforms to $4\int (u')^2\,\dd t$, and the constraint $\int v\,\dd t = K$ becomes $\int u^{-2}\,\dd t = K$. The variational problem is now $\min \int(u')^2$ subject to $\int u^{-2} = K$ — a standard isoperimetric problem.
2. **Solve the Ermakov–Pinney equation.** The Euler–Lagrange equation is $u'' = -\lambda/u^3$. Its general solution is $u(t) = \sqrt{A+Bt+Ct^2}$. Imposing $u(0) = 1/\sqrt{V_0}$ gives $A = 1/V_0$; imposing $u'(1) = 0$ gives $B = -2C$; setting $p = CV_0$ yields $v^*(t) = V_0/(1-p+p(t-1)^2)$.
3. **Determine $p$ from the constraint.** Substituting $v^*$ into $\int_0^1 v^*\,\dd t = K$ and evaluating via the arctangent integral gives the transcendental equation $\arctan(\sqrt{p/(1-p)})/\sqrt{p(1-p)} = K/V_0$, which determines $p = p(K/V_0)$.
4. **Compute $I_0$.** From $I_0 = (2/\xi^2)\int(u')^2\,\dd t$ with $u' = C(t-1)/u(t)$, a substitution $s = 1-t$ reduces the integral to $\int_0^1 s^2/((1-p)+ps^2)\,\dd s$, which evaluates in closed form via partial fractions and the arctangent, yielding the stated formula.
:::

:::proof-sketch{for=prop_saturation}
1. **Asymptotic of $p \to 1$.** As $K\to\infty$, the constraint equation $\arctan(\sqrt{p/(1-p)})/\sqrt{p(1-p)} = K/V_0$ forces $p\to 1$, since the left side diverges as $p\to 1^-$ (the numerator approaches $\pi/2$ while the denominator $\to 0$).
2. **Limit of the rate function formula.** Substituting $p\to 1$ into $I_0 = (2p/\xi^2 V_0)[1 - \sqrt{(1-p)/p}\arctan(\sqrt{p/(1-p)})]$: the factor $\sqrt{(1-p)/p}\arctan(\sqrt{p/(1-p)}) \to \sqrt{1-p}\cdot(\pi/2) \to 0$, giving $I_0 \to 2/(\xi^2 V_0)$.
3. **Smile implication.** Via the large-deviations link $C(T) \sim e^{-I_0/T}$ and the Black–Scholes inversion, the variance implied volatility satisfies $\Sigma_V(K) \sim |\log(K/F_V)|/\sqrt{2I_0^{\max}}$ as $K\to\infty$: only logarithmic growth rather than the power-law growth seen for equity options.
:::

## Numerical Illustration {#numerics}

**Heston model validation.** The closed-form formula for $I_0$ (Theorem~`thm_heston`) is compared against full numerical optimization of the variational problem (direct minimization of $\Lambda_0$ over discretized paths) and against the near-ATM formula of PWZ. The agreement is confirmed to machine precision across parameter ranges $\xi \in [0.5, 3]$, $V_0 \in [0.05, 0.5]$, and strikes $K/V_0 \in [0.5, 5]$. Critically, the correlation invariance $I_\rho = I_0$ is verified for all $\rho \in [-0.9, 0.9]$ by comparing the full numerical solution at each $\rho$ with the $\rho=0$ formula; the discrepancy is everywhere below