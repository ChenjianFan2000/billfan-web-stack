---
paper_slug: mv_games
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

Institutional fund managers face two simultaneous pressures: they compete against peers on relative performance, and they must make portfolio decisions without observing fundamental parameters such as expected return. The intersection of these two forces — competitive pressure and informational uncertainty — creates subtle and potentially dangerous effects on tail risk. The mean-variance game framework formalizes the competitive channel: each investor maximizes a mean-variance objective over her own wealth net of a fraction $\lambda$ of the peer average, where the parameter $\lambda \in [0,1)$ quantifies competition intensity. The seminal work of Basak and Makarov (2014) showed that benchmarking induces risk-shifting; subsequent works established existence of Nash equilibria under various preference structures. In a parallel literature, Bayesian filtering theory provides the tools for learning an unobserved drift from price observations, generating stochastic optimal investment strategies even in apparently simple market models.

Huang and Sun (2025) brought these two threads together, solving $N$-player mean-variance games under both full information (FI, drift is observed) and partial information (PI, drift is unknown), providing explicit Nash equilibria in a Bayesian filtering framework. Their numerical experiments revealed a striking phenomenon: relative performance concerns dramatically amplify the probability of simultaneous large drawdowns when investors operate under partial information, an effect absent under full information. They identified characterizing this "downward amplification" rigorously as an open problem.

The present paper resolves this open problem and finds a result more precise and more surprising than conjectured. The key discovery is a **risk reversal**: the direction of the first-passage comparison between FI and PI investors depends on the unobserved true state of the drift. Under the good state ($\mu = \mu_1$, high drift), partial information makes investors *safer* — their ruin probability is exponentially lower than under full information. Under the bad state ($\mu = \mu_2$, low drift), the comparison reverses: partial information makes investors dramatically *more* endangered, with ruin probability amplified by factors up to $300\times$ in the infinite-horizon limit. This "paradox of ignorance" — ignorance protects when the state is favorable, and endangers when it is not — is established through four rigorous theorems and validated by large-scale Monte Carlo simulation.

## Key Objects {#objects}

**The risky asset and probability measures.** The single stock satisfies

$$\frac{dS(t)}{S(t)} = \mu\,dt + \sigma\,dW(t), \qquad S(0) = s_0 > 0,$$

where $\mu \in \{\mu_1, \mu_2\}$ is fixed but possibly unobserved, $\mu_1 > \mu_2 > 0$, and $\delta := \mu_1 - \mu_2$ is the drift gap. Two physical measures $\Prob_{\mu_1}$ and $\Prob_{\mu_2}$ correspond to the good and bad state respectively; under $\Prob_{\mu_k}$, $W$ is a standard Brownian motion. The non-triviality is that the same strategy $\pi^*(t)$ must serve under both measures simultaneously.

**Nash equilibrium strategies.** Under full information with true drift $\mu_k$, the symmetric Nash equilibrium strategy is the deterministic constant

$$\pi_k^{\mathrm{FI}} := \frac{\mu_k}{\sigma^2\,\gamma(1-\lambda)}.$$

The competition intensity $\lambda$ inflates the position via the effective risk-aversion reduction $\gamma \to \gamma(1-\lambda)$. Under partial information, the PI Nash equilibrium is

$$\pi^*(t,q) = \frac{g(t,q)}{\gamma(1-\lambda)}, \qquad g(t,q) = \underbrace{\frac{\theta(q)}{\sigma^2}}_{\text{myopic}} - \underbrace{\frac{\beta(q)}{\sigma}\,\frac{\partial_q c(t,q)}{\kappa}}_{\text{hedging}},$$

where $g(t,q)$ depends on $\lambda$ only through the explicit prefactor — a structural cancellation unique to the symmetric game.

**The Bayesian filter.** The posterior probability $P(t) := \Prob(\mu = \mu_1 \mid \mathcal{F}^S_t)$ satisfies the filtering SDE

$$dP(t) = \beta(P(t))\,d\widehat{W}(t), \qquad P(0) = p,$$

with filter volatility $\beta(q) := \frac{\delta}{\sigma}\,q(1-q)$ and estimated drift $\theta(q) := \delta\,q + \mu_2$. The innovation $\widehat{W}$ is a Brownian motion under the observation filtration $\mathcal{F}^S$. Crucially, $P(t) \to 1$ under $\Prob_{\mu_1}$ (good news confirmed) but $P(t) \to 0$ under $\Prob_{\mu_2}$ (bad news confirmed), yet only after infinite time.

**First-passage time (ruin time).** For a wealth process $X$ with initial value $x > D$ and safety margin $a := x - D > 0$, the ruin time is

$$\tau := \inf\{t \ge 0 : X(t) \le D\}.$$

We write $\tau_k^{\mathrm{FI}}$ for the FI ruin time under state $k$ and $\tau^{\mathrm{PI}}$ for the PI ruin time. Because $\pi^*$ is path-dependent through $P(t)$, the PI ruin problem has no closed form and requires probabilistic bounding techniques.

**The martingale measure $Q$.** Defined by the Radon–Nikodym density

$$\frac{dQ}{d\Prob_{\mu_1}}\bigg|_{\mathcal{F}_T} = \exp\!\biggl(-\frac{\mu_1}{\sigma}\,W(T) - \frac{\mu_1^2}{2\sigma^2}\,T\biggr),$$

under which the stock has zero drift and both wealth processes become continuous local martingales. The passage to $Q$ removes the drift and allows quadratic-variation-based comparison — but transferring inequalities back to $\Prob_{\mu_1}$ via Girsanov requires additional work due to correlation between the density and the ruin events.

**The Bachelier–Lévy ruin probability.** For a Brownian motion with constant drift $b > 0$ and diffusion $c > 0$ starting at $0$, the ruin probability to reach $-a$ by time $T$ is denoted $\mathfrak{p}(a, b, c, T)$, with infinite-horizon limit $e^{-2ba/c^2}$. The classical formula $\Prob_{\mu_k}(\tau_k^{\mathrm{FI}} < \infty) = e^{-2\gamma(1-\lambda)a}$ is the benchmark against which all PI comparisons are made.

## Main Results {#main-results}

:::theorem{id="thm:expo_bound" label="Exponential Safety Bound (Good State)"}
Under $\Prob_{\mu_1}$, for any $T > 0$:
$$\Prob_{\mu_1}\bigl(\tau^{\mathrm{PI}} \le T\bigr) \;\le\; \exp\!\biggl(-\frac{2\mu_1\,a}{\pi_1^{\mathrm{FI}}\,\sigma^2}\biggr) \;=\; \Prob_{\mu_1}\bigl(\tau_1^{\mathrm{FI}} < \infty\bigr).$$
That is, the PI finite-horizon ruin probability is bounded above by the FI *infinite-horizon* ruin probability.
:::

The theorem says that even if we give the FI investor infinite time to fail (rather than just horizon $T$), the PI investor is still less likely to be ruined by time $T$. The PI investor under-invests relative to the FI optimum because she does not know the state is favorable, and this conservatism reduces portfolio volatility more than it reduces expected return. The bound is expressed in terms of the Lundberg exponent: $\Prob_{\mu_1}(\tau^{\mathrm{PI}} \le T) \le e^{-\psi^{\mathrm{FI}} a}$ where $\psi^{\mathrm{FI}} = 2\gamma(1-\lambda)$, and Monte Carlo shows the true PI exponent is $5$–$6\times$ larger.

**Why it's surprising:** A finite-horizon probability is bounded by an infinite-horizon probability from a *different* (more aggressive) strategy — the PI investor's ignorance provides exponentially stronger protection than the FI investor's optimal knowledge.

---

:::theorem{id="thm:Q_comparison" label="Martingale Measure Comparison (Dubins–Schwarz)"}
Define $Q$ by the Radon–Nikodym density
$$\frac{dQ}{d\Prob_{\mu_1}}\bigg|_{\mathcal{F}_T} = \exp\!\biggl(-\frac{\mu_1}{\sigma}\,W(T) - \frac{\mu_1^2}{2\sigma^2}\,T\biggr).$$
Under $Q$, both FI and PI wealth processes are continuous local martingales, and $\widetilde{W}(t) := W(t) + (\mu_1/\sigma)\,t$ is a standard $Q$-Brownian motion. Then:
$$Q\bigl(\tau^{\mathrm{PI}} \le T\bigr) \;\le\; Q\bigl(\tau_1^{\mathrm{FI}} \le T\bigr),$$
with equality if and only if $\pi^*(t, P(t)) = \pi_1^{\mathrm{FI}}$ for Lebesgue-a.e.\ $t \in [0,T]$, $Q$-a.s.
:::

Under the risk-neutral measure $Q$, all drift is removed. The FI wealth process is a time-changed Brownian motion run at deterministic clock speed $U(T) = (\pi_1^{\mathrm{FI}} \sigma)^2 T$, while the PI process runs at a *slower* stochastic clock $V(T) = \sigma^2 \int_0^T [\pi^*(s)]^2\,ds \le U(T)$. A slower clock means fewer barrier crossings, hence a lower ruin probability. The Dubins–Schwarz theorem converts the quadratic variation inequality into a first-passage inequality by reducing both processes to standard Brownian motions evaluated at different stopping times.

**Why it's surprising:** The comparison is clean and exact under $Q$, yet transferring it back to the physical measure $\Prob_{\mu_1}$ faces a fundamental obstruction: the Girsanov weight $L(T)$ correlates differently with the two ruin events through the stock path, and this gap is left as an open conjecture supported entirely by simulation.

---

:::theorem{id="thm:bad_state" label="Bad-State Ruin Amplification"}
Under $\Prob_{\mu_2}$, let $\bar{\pi} := \pi^*(0) = \theta(p)/[\sigma^2\gamma(1-\lambda)]$. Then:

(i) *(Infinite-horizon comparison.)* For all $a > 0$ and $p \in (0,1)$:
$$\Prob_{\mu_2}\bigl(\tau^{\mathrm{PI}} < \infty\bigr) > \Prob_{\mu_2}\bigl(\tau_2^{\mathrm{FI}} < \infty\bigr).$$

(ii) *(Quantitative bound.)* For any $\epsilon \in (0, \delta p/\mu_2)$ and $h > 0$:
$$\Prob_{\mu_2}\bigl(\tau^{\mathrm{PI}} \le h\bigr) \;\ge\; \mathfrak{p}\!\bigl((1+\epsilon)a,\; \bar{\pi}\mu_2,\; \bar{\pi}\sigma,\; h\bigr) - \frac{K\,h^2}{\epsilon^2\,a^2},$$
where $K = \frac{2\delta^4 p^2(1-p)^2}{\sigma^6\gamma^2(1-\lambda)^2}(4\sigma^2 + \mu_2^2)$.
:::

Under the bad state, the PI investor does not know the drift is low and continues investing as if there is substantial probability of a high-drift environment. At time zero, she invests at $\bar{\pi} = (1 + \delta p/\mu_2)\pi_2^{\mathrm{FI}}$, which is $5.5\times$ the FI optimum at the calibrated parameters. Part (i) proves the PI infinite-horizon ruin probability strictly exceeds the FI counterpart. Part (ii) quantifies this: the PI ruin probability is bounded below by the ruin probability of a constant portfolio at the over-invested level $\bar{\pi}$, corrected by a small $L^2$ tracking error that vanishes as $h \to 0$ or $a \to \infty$.

**Why it's surprising:** The amplification is not merely additive — it is exponential in the safety margin $a$. The ratio $\Prob_{\mu_2}(\tau^{\mathrm{PI}} < \infty)/\Prob_{\mu_2}(\tau_2^{\mathrm{FI}} < \infty)$ grows as $C \exp(2\gamma(1-\lambda)a\,\delta p/(\delta p + \mu_2))$, reaching $307\times$ at the reference parameters.

---

:::theorem{id="thm:sensitivity" label="$\\lambda$-Sensitivity Amplification"}
The FI ruin probability satisfies
$$-\log \Prob_{\mu_k}\bigl(\tau_k^{\mathrm{FI}} < \infty\bigr) = 2\gamma(1-\lambda)\,a,$$
so that $\frac{d}{d\lambda}[-\log \Prob_{\mu_k}(\tau_k^{\mathrm{FI}} < \infty)] = -2\gamma\,a.$

Since $\pi^*(t) = g(t,P(t))/[\gamma(1-\lambda)]$ and $g$ is $\lambda$-independent, the PI Lundberg exponent scales as
$$\psi^{\mathrm{PI}}(\lambda) = \psi^{\mathrm{PI}}(0)\,(1-\lambda), \qquad \frac{d\psi^{\mathrm{PI}}}{d\lambda} = -\psi^{\mathrm{PI}}(0).$$
Because $\psi^{\mathrm{PI}}(0) \gg \psi^{\mathrm{FI}}(0) = 2\gamma$, the sensitivity ratio satisfies
$$\frac{d/d\lambda\,[-\log \Prob(\tau^{\mathrm{PI}} \le T)]}{d/d\lambda\,[-\log \Prob(\tau_k^{\mathrm{FI}} < \infty)]} \;\approx\; \frac{\psi^{\mathrm{PI}}(0)}{\psi^{\mathrm{FI}}(0)} \;\approx\; 5\text{--}6.$$
:::

The theorem shows that while the PI investor starts from a much safer position under the good state, her safety margin erodes $5$–$7$ times faster as competition intensity $\lambda$ increases. The mechanism is structural: since $g(t,q)$ does not depend on $\lambda$ (by the symmetric-game cancellation), the entire $\lambda$-dependence of $\pi^*$ is through the explicit factor $1/(1-\lambda)$. This means the PI strategy is scaled by the same factor as the FI strategy, but the PI Lundberg exponent starts at a much higher baseline, so the absolute sensitivity $|d\psi/d\lambda| = \psi(0)$ is proportionally larger for PI.

**Why it's surprising:** This is the precise theoretical mechanism behind the "downward amplification" observed by Huang and Sun (2025): increasing $\lambda$ erodes the PI safety buffer disproportionately, explaining why co-drawdown correlations appear dramatically amplified under partial information even when individual ruin probabilities are absolutely lower.

## Proof Sketches {#proofs}

:::proof-sketch{for="thm:expo_bound"}
1. **Portfolio upper bound.** Since $\theta(q) = \delta q + \mu_2 \le \delta + \mu_2 = \mu_1$ for $q \in [0,1]$, we have $\pi^*(s) \le \pi_1^{\mathrm{FI}} =: \pi_{\max}$ almost surely for all $s \ge 0$ under $\Prob_{\mu_1}$.
2. **Exponential supermartingale.** Define the tilting parameter $\vartheta = -2\mu_1/(\pi_{\max}\sigma^2) < 0$ and the process $Z(t) = \exp(\vartheta(X^{\mathrm{PI}}(t) - x) - \int_0^t \psi(s)\,ds)$, where $\psi(s) = \vartheta\pi^*(s)\mu_1 + \frac{\vartheta^2}{2}(\pi^*(s))^2\sigma^2$. Itô's formula shows $dZ(t) = Z(t)\vartheta\pi^*(t)\sigma\,dW(t)$, so $Z$ is a non-negative local martingale and hence a supermartingale with $\mathbb{E}[Z(t)] \le 1$.
3. **Compensator is non-positive.** Factoring $\psi(s) = \pi^*(s) \cdot (-2\mu_1^2/(\pi_{\max}\sigma^2))(1 - \pi^*(s)/\pi_{\max}) \le 0$ since $\pi^*(s) \in [0, \pi_{\max}]$. This implies $\exp(-\int_0^\tau \psi(s)\,ds) \ge 1$ at the ruin time $\tau$.
4. **Optional stopping.** On $\{\tau \le T\}$, $X^{\mathrm{PI}}(\tau) = D$ so $Z(\tau) \ge e^{-\vartheta \cdot (-a)} = \exp(2\mu_1 a/(\pi_{\max}\sigma^2))$. The supermartingale inequality $1 \ge \mathbb{E}[Z(\tau \wedge T)] \ge e^{2\mu_1 a/(\pi_{\max}\sigma^2)}\Prob_{\mu_1}(\tau \le T)$ gives the bound.
5. **Identification with FI infinite-horizon ruin.** The classical first-passage formula for Brownian motion with drift gives $\Prob_{\mu_1}(\tau_1^{\mathrm{FI}} < \infty) = \exp(-2\mu_1 a/(\pi_1^{\mathrm{FI}}\sigma^2))$, which equals the right-hand side since $\pi_{\max} = \pi_1^{\mathrm{FI}}$.
:::

:::proof-sketch{for="thm:Q_comparison"}
1. **Girsanov transformation.** Apply the Girsanov density to remove the drift: under $Q$, the process $\widetilde{W}(t) = W(t) + (\mu_1/\sigma)t$ is a standard Brownian motion, and both $X_1^{\mathrm{FI}}(t) - x = \pi_1^{\mathrm{FI}}\sigma\widetilde{W}(t)$ and $X^{\mathrm{PI}}(t) - x = \sigma\int_0^t \pi^*(s)\,d\widetilde{W}(s)$ become continuous $Q$-local martingales with zero initial value.
2. **Dubins–Schwarz time-change.** By the Dambis–Dubins–Schwarz theorem, write $X_1^{\mathrm{FI}}(t) - x = B_1(U(t))$ and $X^{\mathrm{PI}}(t) - x = B_2(V(t))$ for standard $Q$-Brownian motions $B_1$, $B_2$ and clocks $U(t) = (\pi_1^{\mathrm{FI}}\sigma)^2 t$ and $V(t) = \sigma^2\int_0^t [\pi^*(s)]^2\,ds$.
3. **Quadratic variation ordering.** Since $\pi^*(s) \le \pi_1^{\mathrm{FI}}$ a.s., we have $V(T) \le U(T)$ $Q$-a.s., with strict inequality whenever $p < 1$. This means the PI process is run on a strictly slower clock.
4. **First-passage inclusion.** The event $\{\tau^{\mathrm{PI}} \le T\} = \{\inf_{v \le V(T)} B_2(v) \le -a\} \subseteq \{\inf_{v \le U(T)} B_2(v) \le -a\}$. Taking $Q$-probabilities and using that $B_1 \overset{d}{=} B_2$ under $Q$ yields $Q(\tau^{\mathrm{PI}} \le T) \le Q(\tau_1^{\mathrm{FI}} \le T)$.
:::

:::proof-sketch{for="thm:bad_state"}
1. **Over-investment from filter dynamics.** Under $\Prob_{\mu_2}$, the likelihood ratio $\Lambda(t) = \exp(-\delta W(t)/\sigma + \delta^2 t/(2\sigma^2)) \to +\infty$ a.s. (bad state confirmed asymptotically), so $P(t) \to 0$. However, for any finite $t$, $P(t) > 0$ a.s. and the mixture-martingale property forces $\mathbb{E}_{\mu_2}[P(t)] \in (0,p)$, hence $\mathbb{E}_{\mu_2}[\pi^*(t)] > \pi_2^{\mathrm{FI}}$ (Proposition 3.3).
2. **Reference constant-portfolio comparison.** The initial PI position $\bar{\pi} = \pi^*(0) > \pi_2^{\mathrm{FI}}$ defines a constant-portfolio reference process. Lemma 4.5 (Bachelier–Lévy monotonicity) establishes that ruin probability $\mathfrak{p}(a, \pi\mu_2, \pi\sigma, T)$ is strictly increasing in $\pi$, giving $\mathfrak{p}(a, \bar\pi, T) > \mathfrak{p}(a, \pi_2^{\mathrm{FI}}, T)$.
3. **$L^2$ coupling to the reference.** The filter modulus (Lemma 4.4) bounds $\mathbb{E}[|P(s) - P(t)|^2 \mid \mathcal{F}_t] \le \delta^2(s-t)/(16\sigma^2)$, so the PI portfolio stays close to $\bar\pi$ for short times. An explicit $L^2$ argument bounds the tracking error between the PI process and the reference by the correction term $Kh^2/(\epsilon^2 a^2)$, yielding the quantitative lower bound.
4. **Infinite-horizon ratio.** Comparing the Lundberg exponents of PI (at scale $\bar\pi$) and FI (at scale $\pi_2^{\mathrm{FI}}$) yields the exponential amplification ratio $\exp(2\gamma(1-\lambda)a\,\delta p/(\delta p + \mu_2))$, which equals $307\times$ at the reference parameters.
:::

:::proof-sketch{for="thm:sensitivity"}
1. **FI Lundberg exponent.** The classical formula for Brownian motion with drift gives $\Prob_{\mu_k}(\tau_k^{\mathrm{FI}} < \infty) = \exp(-2\mu_k a / (\pi_k^{\mathrm{FI}}\sigma^2)) = \exp(-2\gamma(1-\lambda)a)$, so $-\log \Prob = 2\gamma(1-\lambda)a$ with $\lambda$-derivative $-2\gamma a$.
2. **$\lambda$-independence of $g$.** The symmetric-game cancellation (Remark 2.2 of the paper) ensures $g(t,q)$ solves a Cauchy problem with no $\lambda$ dependence, so $\pi^*(t) = g(t,P(t))/[\gamma(1-\lambda)]$ depends on $\lambda$ only through the explicit scalar prefactor $1/(1-\lambda)$.
3. **PI Lundberg exponent scaling.** Because the PI portfolio scales as $1/(1-\lambda)$, its effective drift-to-variance ratio $2\mu_1/(E[\pi^*]\sigma^2)$ scales proportionally with $(1-\lambda)$, yielding $\psi^{\mathrm{PI}}(\lambda) = \psi^{\mathrm{PI}}(0)(1-\lambda)$ and $|d\psi^{\mathrm{PI}}/d\lambda| = \psi^{\mathrm{PI}}(0)$.
4. **Sensitivity ratio.** Dividing the two absolute $\lambda$-sensitivities: $\psi^{\mathrm{PI}}(0)/\psi^{\mathrm{FI}}(0) \approx 5$–$6$ from the Theorem 3.2 bound $\psi^{\mathrm{PI}}(0) \ge 2\gamma\mu_1/\theta(p) \approx 1.82 \times \psi^{\mathrm{FI}}(0)$ as a lower bound, with Monte Carlo confirming $5$–$6\times$.
:::

## Numerical Illustration {#numerics}

The numerical analysis uses Monte Carlo simulation with $200{,}000$ paths across a grid of threshold levels $D \in \{1.5, 1.7, 1.9, 2.0, 2.1, 2.2, 2.5\}$ and competition parameters $\lambda \in \{0, 0.1, 0.3, 0.5, 0.7, 0.9\}$, at the calibrated parameters $\mu_1 = 0.2$, $\mu_2 = 0.02$, $\sigma = 0.1$, $\gamma = 5$, $x = 3$, $p = 0.5$. Under the good state $\Prob_{\mu_1}$, the PI ruin probability is uniformly lower than the FI ruin probability across the entire $(D, \lambda)$ grid, confirming Conjecture 3.1 (the open physical-measure comparison). The estimated effective PI Lundberg exponent $\psi^{\mathrm{PI}}$ is $5$–$6\times$ the theoretical FI exponent $\psi^{\mathrm{FI}} = 2\gamma(1-\lambda)$, substantially exceeding the theoretical lower bound of $\mu_1/\theta(p) \approx 1.82\times$ given by Theorem 3.2. This gap is attributed to the hedging component of the PI strategy, which further reduces portfolio exposure beyond the myopic term.

Under the bad state $\Prob_{\mu_2}$, the reversal is dramatic. The ratio $\Prob_{\mu_2}(\tau^{\mathrm{PI}} < \infty)/\Prob_{\mu_2}(\tau_2^{\mathrm{FI}} < \infty)$ reaches approximately $307\times$ at the reference parameters, consistent with the theoretical prediction from Corollary 3.3. The bad-state amplification is confirmed to grow exponentially with the safety margin $a = x - D$, as predicted by the exponent formula $2\gamma(1-\lambda)a\,\delta p/(\delta p + \mu_2)$. The sensitivity analysis shows that $-d\log\Prob(\tau^{\mathrm{PI}})/d\lambda \approx 5$–$7\times (-d\log\Prob(\tau^{\mathrm{FI}})/d\lambda)$ uniformly across the parameter grid, with the ratio increasing in $\lambda$ as competition pushes both strategies further from the risk-free position. A phase diagram in the $(D, \lambda)$ plane confirms the good-state safety region covers essentially all parameter combinations tested, while the bad-state amplification region shows the ruin ratio exceeding $100\times$ for $D \ge 2.0$ and any $\lambda$. The critical prior $p^*$ at which the mixture comparison reverses satisfies $p^* < 0.07$ across all $(D,\lambda)$ configurations, confirming that PI is safer in expectation over the prior for essentially any non-degenerate belief.

Robustness checks under alternative parameter calibrations (varying $\delta/\sigma$ ratios, $N = 5, 10, 50$ players, and heterogeneous risk aversion) confirm the qualitative findings. Under heterogeneous risk aversion $\varepsilon \neq 0$, the decorrelation effect (Proposition 3.5) reduces co-drawdown probability relative to the symmetric case, with the reduction scaling as $O(\varepsilon^2)$ as predicted by the perturbation expansion.

## Connections {#connections}

- [Variance Options](/papers/variance_options): Both papers exploit the quadratic variation structure of stochastic portfolios; the Dubins–Schwarz time-change used here to compare ruin probabilities under $Q$ is the same mechanism used to relate realized variance to stopping times in variance option pricing.
- [Discrete vs Rough](/papers/discrete_vs_rough): The Bayesian filtering SDE for $P(t)$ with volatility $\beta(q) = (\delta/\sigma)q(1-q)$ defines a diffusion on $[0,1]$ whose path regularity and discretization errors are directly relevant to the discrete-time approximation questions studied there.
- [Cross Impact](/papers/cross_impact): The $N$-player interaction structure and the mean-field limit $N \to \infty$ connect to cross-impact models where aggregate trading pressure feeds back into individual strategies; the $\lambda$-independence of $g(t,q)$ in the symmetric game is the portfolio analogue of a cross-impact cancellation.