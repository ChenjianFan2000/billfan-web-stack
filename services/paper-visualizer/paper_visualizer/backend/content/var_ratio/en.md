---
paper_slug: var_ratio
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

Banks are required under the Basel Accords to hold capital against credit losses at the $\alpha = 99.9\%$ confidence level—a once-in-a-thousand-years event. The standard approach is the Vasicek one-factor Gaussian copula model, which allows the portfolio Value-at-Risk (VaR) to be computed in closed form from individual default probabilities and a single correlation parameter. The model has a well-known weakness, however: it assumes a specific parametric dependence structure, and misspecifying the copula can lead to dramatic underestimation of tail risk, as vividly demonstrated during the 2008 financial crisis.

A complementary research agenda studies *dependence uncertainty*: given only partial information about the joint dependence structure (e.g., pairwise correlations), what is the worst-case portfolio VaR? The foundational work of Makarov, Rüschendorf, and Embrechts et al. shows that under *no* dependence constraint, worst-case VaR can equal the sum of individual VaRs, an extreme and often unrealistically pessimistic bound. The challenge is to obtain sharp bounds under *partial* information, such as a constraint that pairwise Pearson correlations do not exceed some small $\delta > 0$.

A striking recent result by De Vecchi, Nendel, and Streicher (2026) shows that even an *arbitrarily small* positive correlation $\delta > 0$ is compatible with perfectly comonotonic (simultaneous) defaults in the tail, via the construction of an *upper comonotonic coupling*. They define a VaR underestimation ratio $r_\alpha(n)$ and prove an asymptotic lower bound for identical Bernoulli marginals. Three gaps remain: (i) the bound is not shown to be tight; (ii) the analysis is restricted to identical marginals; (iii) the upper comonotonic coupling is treated as one construction among many, not proved to be worst-case optimal. This paper closes all three gaps—and extends the entire framework to continuous loss-given-default (LGD) distributions, establishes Berry–Esseen convergence rates, and characterizes a phase transition at a critical threshold $\gamma = 1 - p_{\min}$.

## Key Mathematical Objects {#objects}

**Upper comonotonic coupling.** Given marginal distributions $\mu_1, \ldots, \mu_n$ and a threshold $\gamma \in (0,1)$, one constructs
$$X_i^\gamma := F_{\mu_i}^{-1}\!\bigl(\gamma V_i\,\mathbf{1}_{\{U \leq \gamma\}} + U\,\mathbf{1}_{\{U > \gamma\}}\bigr),$$
where $U$ is a uniform random variable (the "systematic factor") and $V_1,\ldots,V_n$ are i.i.d.\ uniforms independent of $U$. The non-trivial feature is that this single construction simultaneously achieves *any* prescribed marginals, *any* prescribed (small) pairwise correlation, and yet produces *perfectly comonotonic* losses in the tail event $\{U > \gamma\}$.

**VaR underestimation ratio.** For exposure weights $(\lambda_i)$ and aggregate loss $S_n = \sum_i \lambda_i X_i^\gamma$,
$$r_\alpha(n) := \frac{\operatorname{VaR}_\alpha^{\mathbb{P}}(S_n)}{\operatorname{VaR}_\alpha^{\mathbb{P}}(S_n \mid U \leq \gamma)}.$$
The denominator is the VaR a risk manager would estimate from *observed normal-regime data* alone; the numerator is the true unconditional VaR. A ratio much greater than 1 means the risk manager drastically underestimates tail risk, even though the measured pairwise correlation is small.

**Conditional default probability $\tilde{p}_i$.** Under the Bernoulli specialization $\mu_i = B(1,p_i)$,
$$\tilde{p}_i := \mathbb{P}(X_i^\gamma = 1 \mid U \leq \gamma) = \frac{\gamma - 1 + p_i}{\gamma}.$$
This is strictly less than $p_i$ for $\gamma < 1$: some default probability mass has been moved into the tail regime, so the normal-regime default rate appears lower than the true rate. This is the core mechanism driving the underestimation.

**Mixing distribution $\nu$ (de Finetti representation).** For an exchangeable sequence of Bernoulli$(p)$ variables, de Finetti's theorem guarantees a probability measure $\nu$ on $[0,1]$ such that
$$\mathbb{P}(X_1 = x_1,\ldots,X_n = x_n) = \int_0^1 \prod_{i=1}^n \theta^{x_i}(1-\theta)^{1-x_i}\,d\nu(\theta).$$
The pairwise correlation becomes $\operatorname{cor}(X_i,X_j) = \operatorname{Var}_\nu(\theta)/[p(1-p)]$, so the correlation constraint translates to a *variance constraint on* $\nu$—a classical moment problem.

**Feasible set of exchangeable couplings.**
$$\mathcal{M}_n^{\mathrm{exch}}(p,\delta) := \bigl\{F \in \mathcal{P}(\{0,1\}^n) : F \text{ exchangeable},\ F_i = B(1,p),\ \operatorname{cor}_F(X_i,X_j) \leq \delta\ \forall\, i\neq j\bigr\}.$$
The non-trivial point is that once de Finetti is applied, worst-case VaR over this high-dimensional set reduces to a *one-dimensional* optimization over mixing distributions.

**Compound loss CDF (continuous LGD).** When individual loss is $X_i = D_i \cdot L_i$ with default indicator $D_i \sim B(1,p)$ and LGD $L_i \sim G$,
$$F_i(x) = \begin{cases}1-p, & x=0,\\ (1-p)+p\,G(x), & x\in(0,1],\end{cases}$$
so the quantile function has a point mass at zero (no-default state) followed by a continuous piece driven by $G$. This is the natural object for extending the Bernoulli analysis to random recovery.

## Main Results {#main-results}

:::theorem{id=thm:sharp_identical label="Sharp ratio for identical marginals"}
Let $\mu_i = B(1,p)$ for all $i \in \mathbb{N}$, $\gamma \in (1-p, 1)$, $\alpha \in [\gamma, 1)$, and let $(\lambda_i)_{i \in \mathbb{N}} \subset [0, \infty)$ satisfy the weight regularity conditions. Then $r_\alpha(n)$ converges and
$$\lim_{n \to \infty} r_\alpha(n) = \frac{\gamma}{\gamma - 1 + p} = \frac{1}{\tilde{p}},$$
where $\tilde{p} = (\gamma - 1 + p)/\gamma$ is the conditional default probability in the normal regime. In particular, the De Vecchi–Nendel–Streicher lower bound is tight if and only if $\alpha = \gamma$.
:::

This theorem gives the *exact* limit of the VaR underestimation ratio for a homogeneous portfolio. The numerator VaR equals the total portfolio exposure $L_n$ (all obligors default in the tail event), while the denominator VaR converges by the law of large numbers to $\tilde{p}\,L_n$, giving a ratio $1/\tilde{p}$. For $p=1\%$ and Pearson correlation $\delta=10\%$, one obtains $\gamma \approx 0.999$ and $r_\alpha(\infty) \approx 111$—more than double the numerical value of 50 reported by De Vecchi et al.\ for $n=1000$, confirming the bound was not yet tight at that sample size.

**Why it's surprising:** The limit $\gamma/(\gamma-1+p)$ depends only on $p$ and $\gamma$ (equivalently, on $p$ and $\delta$), not on the confidence level $\alpha$ as long as $\alpha \geq \gamma$. The ratio is the same at $\alpha = 99.9\%$ and $\alpha = 99.99\%$—all that matters is whether the quantile falls in the tail regime.

---

:::theorem{id=thm:sharp_hetero label="Sharp ratio for heterogeneous marginals"}
Let $\mu_i = B(1, p_i)$ with $p_i \in [\underline{p}, \overline{p}]$, and suppose the exposure-weighted average default probability $\bar{p}_n = \sum_i \lambda_i p_i / L_n$ converges to $\bar{p}$. Assume $\gamma > 1 - \underline{p}$ and $\alpha \in [\gamma, 1)$. Then
$$\lim_{n \to \infty} r_\alpha(n) = \frac{\gamma}{\gamma - 1 + \bar{p}} = \frac{1}{\tilde{\bar{p}}},$$
where $\tilde{\bar{p}} := (\gamma - 1 + \bar{p})/\gamma$.
:::

This extends the exact sharp limit to portfolios where each obligor has a different default probability. Remarkably, the limit depends on the PD heterogeneity *only* through the exposure-weighted mean $\bar{p}$: a portfolio with all obligors at $\bar{p}$ and a portfolio split between $\bar{p} \pm \varepsilon$ have identical limiting ratios. The intuition is purely law-of-large-numbers: the denominator concentrates at its mean, which depends only on $\bar{p}$.

**Why it's surprising:** PD heterogeneity is completely invisible in the asymptotic ratio. Two portfolios with the same average PD but very different rating distributions are equally vulnerable to dependence misspecification.

---

:::theorem{id=thm:wc_optimality label="Worst-case optimality of the upper comonotonic coupling"}
Let $p \in (0,1)$, $\delta \in (0,1)$, $\alpha \in (0,1)$, and $\gamma = (1-p)/((1-p) + \delta p)$.

**(a)** If $\gamma \geq \alpha$ (small correlation $\delta$):
$$\lim_{n \to \infty} \frac{1}{n}\sup_{F \in \mathcal{M}_n^{\mathrm{exch}}(p,\delta)} \operatorname{VaR}_\alpha(S_n) = p(1-\delta) = \tilde{p},$$
and the supremum is asymptotically achieved by the upper comonotonic coupling with threshold $\gamma$.

**(b)** If $\gamma < \alpha$ (large correlation $\delta$):
$$\sup_{F \in \mathcal{M}_n^{\mathrm{exch}}(p,\delta)} \operatorname{VaR}_\alpha(S_n) = n$$
for all $n$ sufficiently large, again achieved by the upper comonotonic coupling.
:::

This is the paper's central optimality theorem. It transforms $r_\alpha(\infty)$ from a lower bound on worst-case risk (an achievable value for one specific coupling) to the *exact* worst-case value over the entire class of exchangeable couplings with bounded correlation. The proof uses de Finetti's theorem to reduce the infinite-dimensional optimization to a one-dimensional moment problem, then solves that problem in closed form via classical results on quantile-extremizing distributions. The key structural insight is that the two-point solution to the moment problem ($\nu^* = \gamma\,\delta_{p(1-\delta)} + (1-\gamma)\,\delta_1$) is *exactly* the de Finetti mixing distribution of the upper comonotonic coupling.

**Why it's surprising:** The upper comonotonic coupling was originally introduced as a *constructive* example showing that small correlations are compatible with large VaR. This theorem proves it is not merely an example, but the *unique asymptotic worst case* among all exchangeable couplings satisfying the correlation constraint.

---

:::theorem{id=thm:lgd_ratio label="VaR ratio with random LGD"}
Consider $n$ identical obligors with PD $p$ and i.i.d.\ LGD $L_i \sim G$ on $[0,1]$, with compound marginal CDF $F$. Under the upper comonotonic coupling with $\gamma \in (1-p,1)$ and $\alpha \in [\gamma,1)$:
$$\lim_{n \to \infty} r_\alpha(n) = \frac{G^{-1}\!\left(\dfrac{\alpha - 1 + p}{p}\right)}{\dfrac{1}{\gamma}\displaystyle\int_0^\gamma F^{-1}(u)\,du}.$$
:::

This generalizes the binary Bernoulli analysis to the practically crucial setting where recovery rates are uncertain. The numerator is the $\alpha$-quantile of the LGD distribution (scaled to the conditional default event), while the denominator is the left-tail mean of the compound loss distribution over the normal regime $[0,\gamma]$. Corollary `cor:lgd_amplification` proves that this ratio is always at least as large as the Bernoulli ratio $\gamma/(\gamma-1+p)$, with strict inequality for any non-degenerate $G$: LGD uncertainty *amplifies* dependence risk.

**Why it's surprising:** For uniform LGD, the ratio is exactly *twice* the Bernoulli value ($r^{\mathrm{Unif}} = 2r^{\mathrm{Bern}}$ when $\alpha=\gamma$). The Basel IRB framework's practice of using a fixed deterministic LGD (e.g., 45% for senior unsecured) therefore understates risk in two compounding ways: wrong copula model *and* wrong LGD modeling.

---

:::theorem{id=thm:phase_transition label="Phase transition at $\gamma = 1 - p_{\min}$"}
Consider the VaR ratio $r_\alpha(\infty;\gamma)$ as a function of the tail threshold $\gamma$.

**(a)** *Homogeneous case* ($p_i = p$ for all $i$). As $\gamma \downarrow (1-p)$:
$$r_\alpha(\infty;\gamma) = \frac{\gamma}{\gamma - 1 + p} \sim \frac{1-p}{\gamma - (1-p)} \to +\infty.$$
The divergence rate is a simple pole of order 1.

**(b)** *Heterogeneous case* ($p_{\min} < \bar{p}$). As $\gamma \downarrow (1-p_{\min})$, $r_\alpha(\infty;\gamma)$ converges to a *finite* limit determined only by the sub-portfolio of obligors with $p_i > 1 - \gamma$.
:::

This theorem reveals a qualitative phase transition: for a homogeneous portfolio, reducing the tail threshold toward $1-p$ (equivalently, reducing the pairwise correlation toward zero) causes the VaR ratio to blow up, so *even vanishingly small* dependence produces unboundedly large underestimation. For a heterogeneous portfolio, below-threshold obligors (those with $p_i \leq 1-\gamma$) do not default in the tail event, so only a sub-portfolio triggers simultaneous default, and the ratio stays bounded.

**Why it's surprising:** Portfolio heterogeneity acts as a natural buffer against dependence uncertainty. A bank with a diverse rating distribution is qualitatively less exposed than one concentrating on a single rating class—not merely quantitatively less exposed.

## Proof Sketches {#proofs}

:::proof-sketch{for=thm:sharp_identical}
1. **Numerator is total exposure.** On the event $\{U > \gamma\}$, which has probability $1-\gamma \geq 1-\alpha > 0$, all obligors default simultaneously ($X_i^\gamma = 1$ for all $i$), so $S_n = L_n$. Since $\mathbb{P}(S_n > t) \geq 1-\gamma \geq 1-\alpha$ for all $t < L_n$, the $\alpha$-quantile of $S_n$ equals $L_n$.
2. **Denominator concentrates via LLN.** Conditionally on $\{U \leq \gamma\}$, the defaults $X_i^\gamma$ are i.i.d.\ $B(1,\tilde{p})$. Chebyshev's inequality together with the weight regularity condition $\sum_i \lambda_i^2 / L_n^2 \to 0$ gives $S_n^{\mathrm{ind}}/L_n \to \tilde{p}$ in probability, hence $\operatorname{VaR}_\alpha(S_n^{\mathrm{ind}})/L_n \to \tilde{p}$.
3. **Ratio and tightness.** Dividing gives $r_\alpha(n) \to 1/\tilde{p} = \gamma/(\gamma-1+p)$. Comparing with the De Vecchi–Nendel–Streicher lower bound $\alpha/(\alpha-1+p)$ (which is a decreasing function of $\alpha$) shows equality if and only if $\alpha = \gamma$.
:::

:::proof-sketch{for=thm:wc_optimality}
1. **De Finetti reduction.** By de Finetti's theorem, every exchangeable coupling in $\mathcal{M}_n^{\mathrm{exch}}(p,\delta)$ is a Bernoulli mixture with mixing distribution $\nu$ satisfying $\mathbb{E}_\nu[\theta]=p$ and $\operatorname{Var}_\nu(\theta) \leq \delta p(1-p)$. Lemma `lem:cor_mixing` makes the correlation constraint explicit: $\operatorname{cor}(X_i,X_j) = \operatorname{Var}_\nu(\theta)/[p(1-p)]$.
2. **Asymptotic reduction to a moment problem.** By Lemma `lem:var_mixing`, conditionally on $\theta$ the sample average $S_n/n \to \theta$ a.s., so $\operatorname{VaR}_\alpha(S_n)/n \to F_\nu^{-1}(\alpha)$. The supremum over all couplings thus becomes $\sup_{\nu \in \mathcal{V}(p,\delta)} F_\nu^{-1}(\alpha)$, a classical one-dimensional moment problem.
3. **Two-point optimizer.** By the theory of moment problems, the extreme points of $\mathcal{V}(p,\delta)$ are supported on at most two points. Maximizing the $\alpha$-quantile over two-point distributions with mean $p$ and variance $\delta p(1-p)$ yields uniquely $\nu^* = \gamma\,\delta_{p(1-\delta)} + (1-\gamma)\,\delta_1$.
4. **Identification with the upper comonotonic coupling.** The de Finetti mixing distribution of the upper comonotonic coupling (with threshold $\gamma$) is precisely $\nu^*$: with probability $\gamma$ the coupling operates in the normal regime (i.i.d.\ defaults at rate $\tilde{p} = p(1-\delta)$) and with probability $1-\gamma$ in the tail (all default). The two objects coincide exactly, proving optimality.
:::

:::proof-sketch{for=thm:lgd_ratio}
1. **Numerator quantile in the comonotonic tail.** On $\{U > \gamma\}$, individual losses are $X_i^\gamma = G^{-1}((U-(1-p))/p)$, a nondecreasing function of $U$. For $\alpha \geq \gamma$, the $\alpha$-quantile of $S_n/n$ falls in this comonotonic tail, evaluating at $U=\alpha$ to give $G^{-1}((\alpha-1+p)/p)$.
2. **Denominator via left-tail mean.** In the normal regime $\{U \leq \gamma\}$, conditional losses are independent with mean $\tilde{\mu} = (1/\gamma)\int_0^\gamma F^{-1}(u)\,du$ (Lemma `lem:cond_mean_lgd`). The law of large numbers gives $S_n^{\mathrm{ind}}/n \to \tilde{\mu}$.
3. **Amplification inequality.** Since $\alpha \geq \gamma$ implies $(\alpha-1+p)/p \geq (\gamma-1+p)/p$, the quantile $G^{-1}((\alpha-1+p)/p)$ is at least as large as any value of $G^{-1}$ appearing in the truncated mean, giving the inequality $r^{\mathrm{LGD}} \geq r^{\mathrm{Bern}}$ by a direct comparison of numerator and denominator.
:::

:::proof-sketch{for=thm:phase_transition}
1. **Homogeneous blow-up.** For identical $p_i = p$, the formula $r_\alpha(\infty;\gamma) = \gamma/(\gamma-1+p)$ has a simple pole at $\gamma = 1-p$. As $\gamma \downarrow 1-p$, the conditional PD $\tilde{p} = (\gamma-1+p)/\gamma \to 0$, so the normal-regime loss becomes negligible relative to the tail loss, and the ratio diverges.
2. **Heterogeneous regularization.** When $p_{\min} < \bar{p}$, obligors with $p_i \leq 1-\gamma$ do not default even in the tail event $\{U > \gamma\}$. Below the threshold $\gamma = 1-p_{\min}$, only the sub-portfolio $I_\gamma = \{i : p_i > 1-\gamma\}$ triggers simultaneous default, and the ratio is determined by this sub-portfolio's exposure fraction $f(\gamma) = \sum_{i \in I_\gamma} \lambda_i / L_n$, which remains finite.
3. **Phase diagram.** The boundary $\gamma = 1-p_{\min}$ marks the phase transition. Above it, all obligors participate in the tail event (ratio given by Theorem `thm:sharp_hetero`); below it, only the high-PD sub-portfolio participates, and the ratio formula changes qualitatively.
:::

## Numerical Illustration {#numerics}

The numerical experiments serve four validation purposes. First, they verify the *convergence* of $r_\alpha(n)$ to the predicted limit $\gamma/(\gamma-1+\bar{p})$ as $n$ increases, and confirm the $O(n^{-1/2})$ Berry–Esseen rate (Theorem `thm:berry_esseen`). For the canonical example with $p=1\%$, $\delta=10\%$, and $\alpha=99.9\%$, the limit $r_\alpha(\infty) \approx 111$ is approached very slowly: even at $n=1000$, $r_\alpha(1000) \approx 50$, which explains why De Vecchi et al.\ reported 50 as a numerical observation rather than the true asymptotic.

Second, the numerical experiments illustrate the *amplification by LGD uncertainty*. For uniform LGD, the worst-case ratio is exactly double the Bernoulli benchmark ($\approx 222$), while for Beta$(0.5, 2)$ LGD (calibrated to the Basel 45% mean), the ratio lies between the uniform and Bernoulli values but substantially exceeds the Bernoulli case. A table of ratios across rating classes (AAA through B, PD ranging from $\sim 0.03\%$ to $\sim 5\%$) shows underestimation factors of 3–29 relative to the Basel IRB VaR, with the largest factors for high-quality obligors at low PD.

Third, the *phase transition* is visualized by plotting $r_\alpha(\infty;\gamma)$ as a function of $\gamma$ for both homogeneous and heterogeneous portfolios. The homogeneous case shows a clear pole (near-vertical divergence as $\gamma \to 1-p$), while for a two-rating portfolio (50% BBB at $p=0.1\%$ and 50% BB at $p=1\%$), the ratio remains finite across all $\gamma$ values, illustrating the buffering effect of heterogeneity. Finally, Monte Carlo simulations verify the worst-case optimality result (Theorem `thm:wc_optimality`) by comparing the portfolio VaR under the upper comonotonic coupling against a grid of alternative exchangeable couplings with the same marginals and correlation bound, confirming that no tested alternative exceeds the upper comonotonic value for $n \geq 100$.

## Connections {#connections}

- [Discrete vs. Rough](/papers/discrete_vs_rough): Both papers analyze how a discretization or threshold parameter (lattice spacing there, tail threshold $\gamma$ here) controls the transition between qualitatively different regimes; the Berry–Esseen machinery applied to sums of non-identically distributed binary variables is a shared technical tool.
- [MV Games](/papers/mv_games): The moment-problem approach to finding worst-case distributions with prescribed mean and variance is a shared mechanism; both papers identify a two-point distribution as the extremal optimizer within a mean-variance feasible set.
- [Project 7](/papers/project7): Connections to optimal transport and coupling constructions for risk-measure bounding are shared; the present paper's de Finetti reduction parallels the martingale coupling arguments used there for continuous marginals.
- [Variance Options](/papers/variance_options): Both papers use quantile convergence results (specifically, stability of quantile functionals under weak convergence) as a key step in passing from finite-$n$ to asymptotic statements about risk measures.