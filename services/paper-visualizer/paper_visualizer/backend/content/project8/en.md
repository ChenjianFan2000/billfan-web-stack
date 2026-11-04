---
paper_slug: project8
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
    title: "Numerical Validation"
  - id: connections
    title: "Connections to Other Papers"
---

## Background and Motivation {#context}

The **Eisenberg–Noe clearing model** (2001) is the canonical framework for interbank contagion: given a network of $N$ banks with bilateral liability matrix $L_N$ and external obligations $b_i$, one seeks the *clearing vector* $p^\ast$ — the unique payment vector at which each bank either pays in full or exhausts its assets. The aggregate shortfall $\Sigma_N = N^{-1}\sum_{i \in \mathcal{D}_N}(\bar{p}_i - p^\ast_i)$ is the principal systemic-risk measure. Classical analysis treats the network as fixed; the question of *how $\Sigma_N$ fluctuates when the network is drawn at random* has received almost no attention.

A natural random model places i.i.d.\ nonneg­ative entries $\xi_{ij}/N$ in the liability matrix. The $1/N$ scaling is economically honest: each of the $\Theta(N)$ counterparty relationships carries $O(1/N)$ weight, so total interbank exposure per bank is $\Theta(1)$. In this **dense** regime the empirical spectral distribution of the centered sample covariance $\mathcal{W}_N^{\mathrm{ctr}} = N(L_N - \mathbb{E}L_N)(L_N - \mathbb{E}L_N)^\top$ converges to the Marchenko–Pastur law. This places the problem squarely within random matrix theory — but the aggregate shortfall is *not* a smooth linear spectral statistic, because the Eisenberg–Noe map involves a piecewise-linear complementarity projection.

The gap this paper fills is threefold. First, no fluctuation theorem existed for the Eisenberg–Noe clearing vector in any random-network regime. Second, linear spectral statistic (LSS) CLTs in the Bai–Silverstein–Yao tradition require *analytic* test functions; the clearing map produces test functions with interior derivative jumps. Third, the effect of heterogeneity in external liabilities $b_i$ on the critical shock $s_c$ was understood only heuristically. This paper (i) introduces the **clearing linear spectral statistic** (cLSS) framework that handles piecewise-$C^1$ test functions; (ii) proves a CLT at the non-standard $N$-rate via a structural cancellation identity; (iii) locates the exact critical shock $s_c^{\mathrm{HET}} = \gamma - b_{\max}$; and (iv) establishes Tracy–Widom GOE universality for the largest singular value of the centered liability matrix. Together these constitute the first random-matrix theory of interbank clearing.

## Key Mathematical Objects {#objects}

**The relative liability matrix $\widetilde\Pi_N$.**
$$
\widetilde\Pi_{N,ij} = \frac{L_{N,ij}}{\bar{p}_{N,i}}, \qquad \bar{p}_{N,i} = \sum_j L_{N,ij} + b_{N,i}.
$$
Because external liabilities $b_{N,i} > 0$, $\widetilde\Pi_N$ is *row-sub­stochastic* with row sums strictly below 1. This leakage $\theta_i = b_i/\bar{p}_i$ ensures the Neumann series $(I - \widetilde\Pi_N^\top)^{-1}$ converges — the fundamental contraction property of the model. Non-triviality: the row normalization $\bar{p}_{N,i}$ is itself random and heterogeneous, coupling the random-matrix and economic structure.

**The stress vector $\mathbf{s}_N$ and the clearing kernel $\mathcal{K}$.**
$$
\mathbf{s}_N := \bar{p}_N - c_N + \eta_N - \widetilde\Pi_N^\top \bar{p}_N, \qquad \mathcal{K}(x) := (I - \widetilde\Pi_N^\top)^{-1}(x)^+.
$$
The clearing vector satisfies $p^\ast_N = \bar{p}_N - \mathcal{K}(\mathbf{s}_N)$, and $\Sigma_N = N^{-1}\mathbf{1}^\top \mathcal{K}(\mathbf{s}_N)$. Non-triviality: the positive-part map $(x)^+$ is non-analytic, introducing a derivative discontinuity at the boundary of the default set that breaks the standard LSS CLT framework.

**The centered sample covariance $\mathcal{W}_N^{\mathrm{ctr}}$.**
$$
\mathcal{W}_N^{\mathrm{ctr}} = N(L_N - \mathbb{E}L_N)(L_N - \mathbb{E}L_N)^\top.
$$
Its empirical spectral distribution converges a.s.\ to the Marchenko–Pastur law $\mu_{\mathrm{MP}}$ supported on $[0, 4\sigma^2]$ (aspect ratio $q=1$). Non-triviality: $L_N$ has a rank-1 mean of order $\mu$ (a *spike*), which is $\Theta(\sqrt{N})$ in singular-value scale and lies far outside the MP bulk edge at $2\sigma$.

**The clearing linear spectral statistic (cLSS) class.** A function $g:[0,4\sigma^2]\to\mathbb{R}$ is a cLSS test function if it is continuous, piecewise-analytic on a finite partition with interior breakpoints $\mathcal{B} = \{c_1,\ldots,c_{m-1}\}\subset(0,4\sigma^2)$, and admits one-sided derivatives at each breakpoint. The corresponding statistic is
$$
\mathcal{L}_g(W_N) = N^{-1}\sum_{k=1}^N g(\lambda_k(W_N)).
$$
Non-triviality: piecewise-$C^1$ regularity ($H^{3/2-\epsilon}$ Sobolev class) is strictly below the analyticity requirement of Bai–Silverstein, yet strictly above the $H^{1/2-\epsilon}$ threshold below which microscopic variance enhancements appear.

**The Perron limit $\rho_\infty^\ast$ and the Neumann weight vector $v_\infty$.**
$$
\rho_\infty^\ast = \mu\int \frac{d\mu_\beta(b)}{\mu + b}\in(0,1), \qquad v_{\infty,i} = 1 + \frac{\mu}{(\mu+b_{N,i})(1-\rho_\infty^\ast)}.
$$
These are the leading-order spectral radius of $\widetilde\Pi_N^\top$ and the left Neumann weight, respectively. Non-triviality: $\rho_\infty^\ast$ is a *strictly convex* functional of $\mu_\beta$, which is what makes heterogeneity destabilizing.

**The LCP suppression factor $1 + \theta_\infty(0)$.** Defined via the unique positive root $u^\ast = u^\ast(\beta/\mu)$ of the transcendental equation
$$
\varphi(u) - u\,\Phi(-u) = \frac{\beta}{\mu}\,u,
$$
where $\varphi, \Phi$ are the standard Gaussian pdf and cdf. This factor captures the endogenous self-consistency of which banks actually default at criticality. Non-triviality: $u^\ast$ depends only on the dimensionless buffer ratio $\beta/\mu$ and is fully derived from first principles — it is not a calibration parameter.

## Main Results {#main-results}

:::theorem{id="thm:thm51" label="Spectral Decomposition of $\\widetilde\\Pi_N$"}
Under Assumptions H1, H4, H6, H7, as $N\to\infty$:

1. **(Row-sum concentration)** With probability $\geq 1 - 2N^{-10}$,
$$\max_{1\leq i\leq N}\left|\bar{p}_{N,i} - (\mu + b_{N,i})\right| \leq C\sigma\sqrt{\tfrac{\log N}{N}},$$
for an absolute constant $C$.

2. **(Perron concentration)** The Perron eigenvalue of $\widetilde\Pi_N^\top$ satisfies
$$\rho^\ast(\widetilde\Pi_N^\top) = \rho_\infty^\ast + O_p\!\left(\sqrt{\tfrac{\log N}{N}}\right), \quad\text{where}\quad \rho_\infty^\ast = \mu\int\frac{d\mu_\beta(b)}{\mu+b}\in(0,1).$$

3. **(Neumann contraction)** With probability $\geq 1 - 2N^{-10}$,
$$\bigl\|(I - \widetilde\Pi_N^\top)^{-1}y\bigr\|_\infty \leq (1-\rho^\ast)^{-1}\|y\|_\infty\cdot(1+o_p(1)) \qquad \forall\, y\in\mathbb{R}^N.$$
:::

This theorem establishes that the random sub-stochastic matrix $\widetilde\Pi_N$ behaves, at leading order, like a deterministic contraction. Part (1) shows the total-liability vector concentrates around its mean at a $\sqrt{\log N / N}$ rate; part (2) pins down the spectral radius to an explicit integral functional of the external-liability distribution; part (3) guarantees that the Neumann series defining the clearing kernel converges uniformly. Together they provide the rigid spectral scaffold on which the CLT proofs are built.

**Why it's surprising:** The Perron limit $\rho_\infty^\ast$ is a *strictly convex* functional of $\mu_\beta$, meaning heterogeneous networks have *larger* spectral radius than homogeneous ones — amplifying contagion rather than averaging it out, contrary to naive diversification intuition.

---

:::theorem{id="thm:thm52" label="Heterogeneous $N$-Rate CLT for Aggregate Shortfall"}
Under Assumptions H1, H4, H5a, H6, H7, there exist explicit deterministic functionals
$$\Sigma_\infty(s;\mu,\sigma^2,\mu_\beta,\gamma)\in\mathbb{R}, \qquad V(s;\mu,\sigma^2,\mu_\beta,\gamma)\geq 0,$$
each continuous and piecewise-smooth in $s$, such that for every $s\neq s_c$ in the super-critical regime,
$$\boxed{\;N\!\left(\Sigma_N - \Sigma_\infty(s)\right)\;\xrightarrow{\mathcal{L}}\; \mathcal{N}\!\left(0,V(s)\right).\;}$$
The function $s\mapsto\Sigma_\infty(s)$ is continuous and non-decreasing, with $\Sigma_\infty(s) = 0$ for $s<s_c$ and $\Sigma_\infty(s) = A_+(s-s_c)+O((s-s_c)^2)$ as $s\downarrow s_c$ for an explicit slope $A_+>0$.

Moreover $\Sigma_N - \Sigma_\infty(s)$ equals (up to $o_p(1/N)$) the linear spectral statistic $\mathcal{L}_{g_s^{\mathrm{HET}}}(\mathcal{W}_N^{\mathrm{ctr}}) - \int g_s^{\mathrm{HET}}\,d\mu_{\mathrm{MP}}$ of the clearing shock functional $g_s^{\mathrm{HET}}$. The variance $V(s) = V(g_s^{\mathrm{HET}})$ comes from the cLSS CLT.
:::

The CLT says that the fluctuation of the aggregate shortfall around its deterministic limit is Gaussian at the $N$-rate — much faster than the naive $\sqrt{N}$-rate that dimensional analysis (i.i.d.\ entries of variance $\sigma^2/N$) would suggest. The order parameter $\Sigma_\infty(s)$ undergoes a phase transition at $s_c$, with a kink but no jump — a second-order transition. The variance $V(s)$ is given in closed form by a Chebyshev-coefficient formula.

**Why it's surprising:** The $N$-rate (instead of $\sqrt{N}$) survives even with *fully heterogeneous* external liabilities $b_{N,i}$, thanks to the self-dual cancellation lemma below. Without this cancellation, heterogeneous weights would appear in the Fréchet derivative and demote the rate to $\sqrt{N}$.

---

:::theorem{id="lem:self-dual" label="Self-Dual Cancellation (Key Lemma)"}
Let $\Delta\widetilde\Pi = \widetilde\Pi_N - \mathbb{E}\widetilde\Pi_N$, let $\bar{p}_\infty\in\mathbb{R}^N$ be the deterministic vector with components $\mu+b_{N,i}$, and let $\Delta L = L_N - \mathbb{E}L_N$. Then for each $j\in\{1,\dots,N\}$,
$$(\Delta\widetilde\Pi^\top \bar{p}_\infty)_j = \sum_{i\neq j}\Delta L_{ij} + O_p(1/N).$$
Equivalently: the $(\mu+b_i)^{-1}$ weight that defines $\widetilde\Pi_{ij}$ is absorbed by the $(\mu+b_i)$ weight in $\bar{p}_\infty$, reducing the weighted column sum to the unweighted column sum of $\Delta L$.
:::

This identity is elementary algebra, but its consequence is profound: the Fréchet derivative of the aggregate shortfall, when evaluated at the deterministic limit of $\bar{p}_\infty$, produces *unweighted* column sums of $\Delta L$ regardless of the heterogeneity profile $b_{N,i}$. The heterogeneous weights cancel exactly in the leading-order term. This restores the same variance calculation as in the homogeneous case and preserves the $N$-rate CLT.

**Why it's surprising:** One would expect fully heterogeneous row normalizations to introduce $b_i$-dependent weights throughout the fluctuation analysis, breaking the homogeneous-case calculation. Instead a single algebraic cancellation eliminates all such weights from the leading-order term.

---

:::theorem{id="thm:thm52star" label="Critical-Window Refinement (Theorem 5.2*)"}
Assume the hypotheses of Theorem 5.2 and the homogeneous benchmark $b_{N,i}\equiv\beta$. Let $s_c^{(0)} := \gamma - \beta$, $A_+ := (\mu+\beta)/\beta$, $\sigma_\tau := \sigma\sqrt{2}$. Define
$$1+\theta_\infty(0) := \frac{\sqrt{2\pi}\,\beta}{\mu}\cdot u^\ast,$$
where $u^\ast = u^\ast(\beta/\mu)$ is the unique positive solution of
$$\varphi(u) - u\,\Phi(-u) = \frac{\beta}{\mu}\,u.$$
Then, as $N\to\infty$:

1. **(Derived deterministic shift)**
$$\sqrt{N}\cdot\mathbb{E}[\Sigma_N(s_c^{(0)})] \longrightarrow c_0 = \sigma\sqrt{2}\cdot\frac{\mu+\beta}{\mu}\cdot u^\ast.$$

2. **(Universality)** The suppression factor $1+\theta_\infty(0)$ depends only on the dimensionless ratio $\beta/\mu$; it is independent of $\sigma$ and $\gamma$.

3. **(Gaussian fluctuation)**
$$N\!\left(\Sigma_N(s_c^{(0)}) - \frac{c_0}{\sqrt{N}}\right) \xrightarrow{\mathcal{L}} \mathcal{N}(0, V^\ast(0)).$$

4. **(Critical exponent)** The critical exponent is $\alpha = 1/2$, not the Tracy–Widom edge scale $\alpha = 2/3$.
:::

At the critical shock $s_c$, the stress vector has zero mean and the aggregate shortfall acquires a deterministic bias of order $N^{-1/2}$ from the Gaussian fluctuations of that stress vector — banks near the boundary of the default set default with positive probability even at criticality. The bias is explicitly computable from a one-dimensional fixed-point equation for the effective stress. The CLT still holds after subtracting this shift, with the same variance formula as in the super-critical regime.

**Why it's surprising:** The critical exponent $\alpha = 1/2$ (Gaussian scale) rather than $2/3$ (Tracy–Widom) shows that the phase transition of the *clearing map* is governed by the bulk Gaussian fluctuations of the stress vector, not by the edge fluctuations of the largest eigenvalue — even though both phenomena coexist in the same model.

---

:::theorem{id="thm:thm53" label="Tracy–Widom GOE Edge Universality"}
Under Assumptions H1, H2, H4, H6, H7, let $\widetilde{L}_N = L_N - \mathbb{E}L_N$ and let $s_1(\sqrt{N}\widetilde{L}_N)$ denote its largest singular value. Then
$$N^{2/3}\cdot\frac{s_1(\sqrt{N}\widetilde{L}_N) - 2\sigma}{2^{-2/3}\sigma} \xrightarrow{\mathcal{L}} F_1^{\mathrm{GOE}},$$
where $F_1^{\mathrm{GOE}}$ is the Tracy–Widom GOE distribution. The explicit prefactor $2^{-2/3}\sigma$ arises from the Jacobian of $\lambda\mapsto\sqrt{\lambda}$ at $\lambda = 4\sigma^2$ applied to the eigenvalue-form edge scale $2^{4/3}\sigma^2$ of Pillai–Yin with $q=1$.
:::

This result establishes that the largest singular value of the centered $N\times N$ liability matrix fluctuates at the $N^{-2/3}$ scale around its deterministic limit $2\sigma$, with a universal Tracy–Widom GOE distribution independent of the entry distribution (beyond four-plus-epsilon moments). This is the same universality class as the largest eigenvalue of a GOE random matrix, arising here for a non-symmetric matrix via the singular-value route.

**Why it's surprising:** The raw liability matrix $L_N$ has a rank-1 mean of size $\sim \mu$, giving a spike singular value $\sim \mu$ that is $\Theta(\sqrt{N})$ away from the bulk edge. Yet after centering, the edge universality is exactly that of a fully i.i.d.\ Wigner/Wishart matrix — the economic rank-1 structure of the mean leaves no trace on the edge fluctuations.

---

:::theorem{id="thm:atom-dichotomy" label="Atom-vs-Continuous Dichotomy at the Heterogeneous Critical Window"}
Let $b_{\max} = \operatorname{ess\,sup}\mu_\beta$ and $A_{\mathrm{top}} := \mu_\beta(\{b_{\max}\})\in[0,1]$. Under the hypotheses of Theorem 5.2, at $s = s_c^{\mathrm{HET}} = \gamma - b_{\max}$:

1. **(Atomic case, $A_{\mathrm{top}}>0$)**. The critical-window analysis of Theorem 5.2* applies with a modified deterministic shift
$$c_0^{\mathrm{HET}}(\mu_\beta) = A_{\mathrm{top}}\cdot A_+^{\mathrm{HET}}\cdot\sigma_\tau\varphi(0)\cdot\bigl(1+\theta_\infty^{\mathrm{HET}}(0;\mu_\beta)\bigr),$$
where $A_+^{\mathrm{HET}} = 1/(1-\rho_\infty^{\ast,\mathrm{HET}})$ and $\theta_\infty^{\mathrm{HET}}$ solves a functional fixed-point equation.

2. **(Atomless case, $A_{\mathrm{top}}=0$)**. The critical-window kink is smeared out:
$$\sqrt{N}\cdot\mathbb{E}[\Sigma_N(s_c^{\mathrm{HET}})] \longrightarrow 0,$$
and the order parameter $s\mapsto\Sigma_\infty(s)$ is $C^1$ at $s = s_c^{\mathrm{HET}}$. The $N^{-1}$-scale Gaussian CLT (Theorem 5.2) is preserved, but the $N^{-1/2}$ deterministic shift vanishes.
:::

The structural dichotomy classifies heterogeneous networks by whether the essential supremum of the external-liability distribution is a mass point or not. If it is (e.g., a bimodal distribution with an atom at the top), the worst-off banks form a macroscopic fraction of the network and trigger the same critical-window kink as the homogeneous case. If it is not (e.g., a uniform or lognormal distribution), the defaults at criticality are infinitesimally rare and the order parameter smooths out.

**Why it's surprising:** This is a knife-edge phenomenon discontinuous in the *topology* of $\mu_\beta$ at its essential supremum — not in its moments or any smooth parameter. Empirically calibrated networks with continuous $b_i$ distributions may exhibit no deterministic shift near criticality, while networks with even a small point mass at the maximum show the full HOM-style $N^{-1/2}$ shift.

---

:::theorem{id="thm:cLSS-CLT" label="cLSS Central Limit Theorem"}
Let $W_N = \mathcal{W}_N^{\mathrm{ctr}}$ under Assumptions H1, H4, H5a, H6, H7, and let $g:[0,4\sigma^2]\to\mathbb{R}$ be a cLSS test function with breakpoint set $\mathcal{B}\subset(0,4\sigma^2)$. Then
$$N\!\left(\mathcal{L}_g(\mathcal{W}_N^{\mathrm{ctr}}) - \int g\,d\mu_{\mathrm{MP}}\right) \xrightarrow{\mathcal{L}} \mathcal{N}(0, V(g)),$$
with
$$V(g) = 2\sum_{k=1}^\infty k\,a_k(g)^2,$$
where $a_k(g) = (2/\pi)\int_0^\pi g(2\sigma^2(1-\cos\theta))\cos(k\theta)\,d\theta$ are the Chebyshev coefficients of $g$ under the Marchenko–Pastur change of variables.
:::

This is the master CLT underlying all other results. It extends the Bai–Silverstein–Yao theory of linear spectral statistics from analytic test functions to the piecewise-$C^1$ class, with *no modification* to the variance formula — the Chebyshev-coefficient formula holds verbatim. The key regularity insight is that derivative jumps (piecewise-$C^1$, Sobolev class $H^{3/2-\epsilon}$) lie strictly within the Sosoe–Wong threshold and produce no additional variance term.

**Why it's surprising:** A natural conjecture is that derivative jumps at breakpoints contribute a term proportional to $|\Delta g'_j|^2/\rho_{\mathrm{MP}}(c_j)$ (inverse local density). This conjecture is false: Monte Carlo confirms the variance is insensitive to the local MP density at the breakpoint, and the Chebyshev formula suffices.

## Proof Sketches {#proofs}

:::proof-sketch{for="thm:thm51"}
1. **Row-sum concentration via Bernstein's inequality**: For each bank $i$, $\bar{p}_{N,i} - (\mu + b_{N,i}) = N^{-1}\sum_{j\neq i}(\xi_{ij} - \mu) + O(1/N)$. Bernstein's inequality gives a tail bound $\leq 2N^{-11}$ per bank; a union bound over $N$ banks gives the $1 - 2N^{-10}$ probability.
2. **Perron eigenvalue by Collatz–Wielandt**: Using the all-ones test vector in the Collatz–Wielandt min-max characterization sandwiches $\rho^\ast(\widetilde\Pi_N^\top)$ between the minimum and maximum column sums, each of which concentrates around $\mu/(\mu + b_{N,i})$ by part (1). Averaging and invoking the weak convergence $\mu_\beta^{(N)} \to \mu_\beta$ gives $\rho_\infty^\ast$.
3. **Neumann contraction via Gelfand's formula**: On the concentration event, $\|\widetilde\Pi_N^\top\|_{\mathrm{op}} \leq \rho^\ast + o_p(1) < 1$. Gelfand's formula ensures absolute convergence of the Neumann series, and non-negativity of $\widetilde\Pi_N^\top$ yields the $\ell^\infty$ operator-norm bound $(1-\rho^\ast)^{-1}$.
:::

:::proof-sketch{for="thm:thm52"}
1. **LCP reformulation**: Express $\Sigma_N = N^{-1}\mathbf{1}^\top(I - \widetilde\Pi_N^\top)^{-1}(\mathbf{s}_N)^+$, reducing the clearing fixed-point to a linear complementarity problem with stress vector $\mathbf{s}_N = \bar{p}_N - c_N + \eta_N - \widetilde\Pi_N^\top\bar{p}_N$.
2. **Fréchet expansion**: Write $\widetilde\Pi_N = \widetilde\Pi_\infty + \Delta\widetilde\Pi_N$ and Taylor-expand the clearing kernel to first and second order, producing a linear term (variance $O(N^{-2})$ at the $N$-scale) and a quadratic term in $\Delta L$.
3. **Self-dual cancellation (Lemma \ref{lem:self-dual})**: The key identity $(\Delta\widetilde\Pi_N^\top\bar{p}_\infty)_j = \sum_{i\neq j}\Delta L_{ij} + O_p(1/N)$ eliminates the $b_i$-dependent weights from the leading-order Fréchet term, restoring the homogeneous-case variance structure and preserving the $N$-rate.
4. **cLSS representation of the quadratic term**: The positive-part nonlinearity introduces a spectral breakpoint $c(s)$ in the test function; the quadratic fluctuation equals $\mathcal{L}_{g_s^{\mathrm{HET}}}(\mathcal{W}_N^{\mathrm{ctr}}) - \int g_s^{\mathrm{HET}}\,d\mu_{\mathrm{MP}} + o_p(1/N)$, and the cLSS CLT yields the Gaussian limit with Chebyshev-coefficient variance.
5. **Active-set boundary control**: The discrepancy between the true default set $\mathcal{D}_N$ and the naive set $\{i: (\mathbf{s}_N)_i > 0\}$ involves $O_p(\sqrt{N\log N})$ banks each contributing $O(\sqrt{\log N/N})$, giving a total error $O_p(\log N/\sqrt{N}) = o_p(1/N)$ — negligible at the CLT scale.
:::

:::proof-sketch{for="thm:thm52star"}
1. **Stress-vector Gaussianity at criticality**: At $s = s_c^{(0)}$, the stress vector $\mathbf{s}_N$ has zero mean with marginal variance $\sigma_\tau^2/N = 2\sigma^2/N$ (from independent row and column contributions). Bernstein's inequality confirms approximate Gaussianity of each component at scale $1/\sqrt{N}$.
2. **Expected positive part via Gaussian half-mean**: For $X \sim \mathcal{N}(0,\sigma_\tau^2/N)$, $\mathbb{E}[X^+] = \sigma_\tau/\sqrt{2\pi N}$. This naive estimate gives an $O(N^{-1/2})$ mean shortfall, but overestimates by not accounting for endogenous default-set selection.
3. **LCP suppression via rank-1 Schur complement**: Approximate $\widetilde\Pi_N^\top$ by its rank-1 Perron projection $\rho_\infty^\ast \cdot (\mathbf{1}\mathbf{1}^\top/N)$. The LCP iteration reduces to the 1D scalar fixed point $\mathbb{E}[(Z - u)^+] = (\beta/\mu)u$, i.e., $\varphi(u) - u\Phi(-u) = (\beta/\mu)u$, with unique positive root $u^\ast(\beta/\mu)$. Substituting back gives the exact constant $c_0 = \sigma\sqrt{2}\cdot(\mu+\beta)/\mu\cdot u^\ast$.
4. **Residual CLT**: After removing the $c_0/\sqrt{N}$ deterministic shift, a smoothing argument at scale $N^{-1/2}$ renders the positive-part map differentiable, and the cLSS CLT applies to yield the Gaussian limit with variance $V^\ast(0)$.
:::

:::proof-sketch{for="thm:thm53"}
1. **Diagonal-zero correction is scalar**: The centered matrix $\widetilde{L}_N = L_N - \mathbb{E}L_N$ has diagonal $-\mu/N$. The "fully i.i.d." version $\tilde{L}'_N = \widetilde{L}_N + (\mu/N)I$ differs by a scalar multiple of $I