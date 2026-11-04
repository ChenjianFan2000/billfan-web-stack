---
paper_slug: cross_impact
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

Large institutional orders move prices. In a multi-asset market, trading in one asset affects the prices of others — this is *cross-impact*. The propagator (or Volterra) model captures this through a matrix-valued kernel $G(t,s) \in \mathbb{R}^{N \times N}$: the price distortion at time $t$ caused by a strategy $u$ is $D_t^u = \int_0^t G(t,s)\,u_s\,ds$. For the model to be economically sound, it must preclude *price manipulation* — round-trip strategies (buying and then fully selling back) that generate positive expected profit from price distortions alone. The seminal work of Huberman and Stanzl (2004) and Gatheral, Schied, and Slynko (2012) established that the no-manipulation condition is equivalent to the *nonnegative definiteness* of the integral operator associated with $G$.

For a single asset, this theory is well-developed: power-law kernels $H(t) = c\,t^{-\beta}$ with $\beta \in (0,\tfrac12)$ are nonnegative-definite, and Abi Jaber and Neuman (2025) gave a full spectral characterisation. For multiple assets, Abi Jaber, Neuman, and Tuschmann (2026) provided sufficient conditions covering the *factorised* model $H(t) = C\,\varphi(t)$ where a single scalar decay function $\varphi$ modulates a constant matrix $C$. However, empirical data consistently shows that different asset pairs decay at *different* rates $\beta_{ij}$: the factorised model is therefore too restrictive for realistic markets.

This paper fills that gap. For the heterogeneous power-law kernel $H_{ij}(t) = c_{ij}\,t^{-\beta_{ij}}$ with potentially different exponents $\beta_{ij} \in (0,\tfrac{1}{2})$ for every pair $(i,j)$, the paper derives *necessary and sufficient* conditions for the absence of price manipulation. Two conditions emerge: a structural constraint on the exponent matrix (the mean-exponent condition) and a positive-definiteness constraint on a Gamma-weighted coefficient matrix. The paper further analyses what happens at the boundary: near permanent impact ($\beta \to 0^+$), for singular coefficient matrices, for large portfolios, and for a regularised kernel that handles the empirically relevant boundary case $\beta \approx \tfrac12$.

## Key Mathematical Objects {#objects}

**Volterra kernel and price distortion.** For a matrix-valued convolution kernel $H:(0,\infty)\to\mathbb{R}^{N\times N}$, the causal kernel is $G(t,s) = \mathbf{1}_{t \ge s}\,H(t-s)$. The price distortion is

$$D_t^u = \int_0^t H(t-s)\,u_s\,ds,$$

and the *transient-impact cost* of a strategy $u \in L^2([0,T],\mathbb{R}^N)$ is

$$\mathcal{C}(u) := \int_0^T u_t^\top D_t^u\,dt = \int_0^T\!\int_0^T u_t^\top G(t,s)\,u_s\,ds\,dt.$$

Non-triviality: the cost is a bilinear form over a triangular domain; symmetrising it introduces the full convolution $H(|t-s|)$, which is the key step that unlocks Fourier methods.

**Heterogeneous power-law kernel.** Under Assumption 2 (Ass. kernel), the kernel has entries

$$H_{ij}(t) = c_{ij}\,t^{-\beta_{ij}}, \quad \beta_{ij}\in\left(0,\tfrac{1}{2}\right),\quad c_{ij}=c_{ji},\quad \beta_{ij}=\beta_{ji},\quad c_{ii}\ge 0.$$

Non-triviality: the constraint $\beta_{ij} < \tfrac12$ is exactly the square-integrability threshold ($G \in L^2([0,T]^2)$). Allowing *different* exponents $\beta_{ij}$ for different pairs breaks the factorised structure and introduces rich spectral interference between entries.

**Gamma weight function.** Define

$$\gamma(\beta) := 2\,\Gamma(1-\beta)\sin\!\left(\frac{\pi\beta}{2}\right), \quad \beta \in (0,1).$$

This is strictly positive on $(0,1)$, with $\gamma(\beta) = \pi\beta + O(\beta^2)$ as $\beta\to 0^+$ (so $\gamma(0)=0$) and $\gamma(\beta)\to+\infty$ as $\beta\to 1^-$. Non-triviality: $\gamma(\beta)$ is precisely the constant appearing in the Fourier transform of the power-law kernel $|t|^{-\beta}$, serving as the spectral "weight" that translates time-domain decay into frequency-domain amplitude.

**Spectral matrix and Gamma-weighted matrix.** The Fourier transform of the symmetrised kernel yields the *spectral matrix*

$$\widehat{H}(\omega) = \left[c_{ij}\,\gamma(\beta_{ij})\,|\omega|^{\beta_{ij}-1}\right]_{i,j=1}^N, \quad \omega > 0.$$

The *Gamma-weighted matrix* is the $\omega$-independent part:

$$\widetilde{C} := \left[c_{ij}\,\gamma(\beta_{ij})\right]_{i,j=1}^N.$$

Non-triviality: whether $\widehat{H}(\omega) \ge 0$ for *all* $\omega > 0$ simultaneously depends on the interplay between the $\omega$-dependent power laws $|\omega|^{\beta_{ij}-1}$ and the matrix structure of $[c_{ij}]$. When the exponents $\beta_{ij}$ differ, these powers create a frequency-dependent "rotation" of the matrix that can destroy positive-definiteness at some frequencies while preserving it at others.

**Mean-exponent condition.** The constraint

$$\beta_{ij} = \frac{\beta_{ii} + \beta_{jj}}{2} \quad \text{for all } i,j \text{ with } c_{ij}\neq 0$$

pins each cross-impact exponent to the arithmetic mean of the two self-impact exponents. Non-triviality: this is a *structural* constraint on the exponent matrix, not the coefficient matrix. It reduces the $\binom{N}{2}$ free cross-exponents to be completely determined by $N$ self-exponents, and its necessity is not obvious — it emerges from an exponential divergence argument in the frequency domain.

**Regularised kernel.** For $t_0 > 0$ and $\beta_{ij}\in(0,1)$,

$$H_{ij}^{(t_0)}(t) = c_{ij}\,(t + t_0)^{-\beta_{ij}}.$$

Non-triviality: unlike the singular kernel, its Fourier transform is not a pure power of $|\omega|$ but involves the *upper incomplete Gamma function* $\Gamma(1-\beta, -it_0\omega)$, which does not factorise over $(i,j)$ pairs. This breaks the clean spectral analysis and leads to qualitatively new (and asymmetric) necessity conditions.

## Main Results {#main-results}

:::theorem{id="prop:equiv" label="Equivalence: No-Manipulation ↔ Nonnegative Definiteness"}
The Volterra kernel $G(t,s) = \mathbf{1}_{t\ge s}\,H(t-s)$ precludes price manipulation if and only if it is nonnegative definite in the sense of
$$\int_0^T\!\int_0^T f(t)^\top G(t,s)\,f(s)\,ds\,dt \;\ge\; 0 \qquad\text{for all } f\in L^2([0,T],\mathbb{R}^N).$$
:::

This proposition is the foundation of the entire analysis. It says that checking all possible round-trip strategies is equivalent to checking nonneg-definiteness of the bilinear form on all $L^2$ functions (not just those with zero integral). The proof reduces to showing that the "constant direction" of the kernel (the self-impact part) is automatically non-negative under the standing assumptions, so the full cone and the round-trip cone coincide. Every subsequent result in the paper is a characterisation of when this nonnegative definiteness holds.

**Why it's surprising:** The equivalence might seem to require checking an uncountably larger set of functions (all of $L^2$, not just round trips), but the symmetry of $H$ and the non-negativity of self-impact ($c_{ii}\ge 0$) make these two conditions coincide exactly.

---

:::theorem{id="thm:main" label="Main Theorem: Sharp No-Manipulation Characterisation"}
Under Assumption 2 (symmetric heterogeneous power-law kernel with $\beta_{ij}\in(0,\tfrac12)$, $c_{ij}=c_{ji}$, $\beta_{ij}=\beta_{ji}$, $c_{ii}\ge 0$), the following are equivalent.
\begin{enumerate}
\item[(i)] $G(t,s)=\mathbf{1}_{t\ge s}\,H(t-s)$ precludes price manipulation for all $T>0$.
\item[(ii)] The spectral matrix $\widehat{H}(\omega) = [c_{ij}\,\gamma(\beta_{ij})\,|\omega|^{\beta_{ij}-1}]_{i,j}$ is nonnegative definite for all $\omega>0$.
\item[(iii)] The following two conditions hold:
  \begin{enumerate}
    \item[(a)] $\beta_{ij} = \dfrac{\beta_{ii}+\beta_{jj}}{2}$ for all $i,j$ with $c_{ij}\neq 0$ \emph{(mean-exponent condition);}
    \item[(b)] $\widetilde{C} := [c_{ij}\,\gamma(\beta_{ij})]_{i,j}$ is nonneg.\ definite.
  \end{enumerate}
\end{enumerate}
:::

This is the central result of the paper. It gives an if-and-only-if characterisation of no-manipulation for heterogeneous power-law kernels, decomposed into two independent conditions: one purely about the *exponent structure* of the market and one about the *coefficient structure*. The mean-exponent condition (a) says cross-impact decay must be the arithmetic mean of the two self-impact decays — a purely structural constraint that holds or fails regardless of the coefficient magnitudes. Condition (b) then asks that the matrix of Gamma-rescaled coefficients is positive semidefinite, which is the analogue of the classical "no-manipulation requires $C \ge 0$" but corrected for the power-law weights.

**Why it's surprising:** The mean-exponent condition (a) is *necessary*: there is no way to choose the coefficients $c_{ij}$ (however small, however cleverly calibrated) to compensate for a violation of the exponent constraint. Even an infinitesimally small cross-impact $c_{ij}$ with the "wrong" exponent creates a manipulation opportunity at some frequency. This is a genuinely spectral phenomenon with no analogue in permanent-impact models.

---

:::theorem{id="prop:reg_necessity" label="Asymmetric Necessity for the Regularised Kernel"}
Let $N=2$, $t_0 > 0$, $\beta_{11}, \beta_{22}\in(0,1)$, $c_{11}, c_{22} > 0$. Set $\delta := 2\beta_{12} - \beta_{11} - \beta_{22}$.
\begin{enumerate}
\item[(i)] If $\delta < 0$ and $c_{12}\neq 0$, then $G^{(t_0)}$ admits price manipulation for some $T>0$. The mean-exponent condition $\delta = 0$ is necessary whenever $\beta_{12} < (\beta_{11}+\beta_{22})/2$.
\item[(ii)] If $\delta \ge 0$, the mean-exponent condition is \emph{not} necessary: the regularised kernel precludes manipulation for all $T>0$ provided
$$c_{12}^2 \;\le\; t_0^{\delta}\, \frac{\Gamma(1-\beta_{11})\,\Gamma(1-\beta_{22})}{\Gamma(1-\beta_{12})^2}.$$
\item[(iii)] As $t_0\to 0^+$ with $\delta > 0$, the right-hand side of the above bound vanishes, recovering the necessity of the mean-exponent condition for the singular kernel.
\end{enumerate}
:::

For the regularised kernel $H^{(t_0)}_{ij}(t) = c_{ij}(t+t_0)^{-\beta_{ij}}$, the necessity structure is *asymmetric* in the sign of $\delta = 2\beta_{12} - \beta_{11} - \beta_{22}$. When cross-impact decays *faster* than the mean ($\delta < 0$), the regularisation provides no relief: the low-frequency spectral ratio $R(\omega) \sim \text{const}\cdot\omega^{|\delta|} \to 0$ forces manipulation at long time horizons. When cross-impact decays *slower* ($\delta > 0$), the dominant constraint shifts to high frequencies where the $O(\omega^{-2})$ decay of the regularised kernel is uniform, creating a finite window of permissible cross-impact coefficients. This window shrinks to zero as $t_0 \to 0^+$, smoothly recovering the singular kernel's sharp necessity.

**Why it's surprising:** The regularisation $t_0 > 0$ was introduced for technical reasons (square-integrability near $\beta = 1/2$). The discovery that it creates a genuinely *one-sided* relaxation of the necessity conditions — depending on which direction the cross-impact exponent deviates from the mean — is unexpected and has no analogue in the single-asset theory.

---

:::theorem{id="prop:permanent" label="Permanent-Impact Limit"}
In the homogeneous-exponent case $\beta_{ij}=\beta$ for all $i,j$, as $\beta\to 0^+$:
\begin{enumerate}
\item[(i)] The Gamma-weighted matrix $\widetilde{C} = \gamma(\beta)\,C$ degenerates: $\gamma(\beta)\to 0$, so $\widetilde{C}\to 0$, and the condition $\widetilde{C}\ge 0$ becomes vacuous.
\item[(ii)] The transient-impact cost of a round-trip strategy $u$ (with $\int_0^T u_t\,dt = 0$) converges to $\mathcal{C}(u) \to 0$, regardless of the sign of $C$. This is the well-known degeneracy of permanent impact: reversing a position fully undoes the price effect.
\end{enumerate}
Thus, as $\beta\to 0^+$, the no-manipulation condition becomes vacuous (round trips are costless for any $C$).
:::

This proposition confirms that the framework interpolates smoothly between the transient and permanent regimes. As decay exponents approach zero, the impact kernel becomes approximately constant (permanent), and it is classical (Kyle 1985) that permanent impact allows costless round trips: the act of buying and then selling back resets the price exactly, so no profit can be extracted. The no-manipulation condition degenerates to $0 \ge 0$, which is always true. Increasing $\beta$ away from zero activates the transient structure and progressively tightens the constraint.

**Why it's surprising:** One might expect that the permanent-impact limit imposes the strongest constraint (price effects never decay, so manipulation should be hardest). In fact, the opposite is true: permanent impact is the *most degenerate* case, where round trips are always costless.

---

:::theorem{id="prop:largeN" label="Large-$N$ Scaling"}
For $N$ assets with unit self-impact $c_{ii}=1$, uniform exponent $\beta$, and uniform cross-impact $c_{ij}=c$ for $i\neq j$, the Gamma-weighted matrix
$$\widetilde{C} = \gamma(\beta)\bigl[(1-c)I + c\,\mathbf{1}\mathbf{1}^\top\bigr]$$
is nonneg.\ definite if and only if
$$-\frac{1}{N-1} \;\le\; c \;\le\; 1.$$
:::

In a large homogeneous market, the admissible range for cross-impact is highly asymmetric in $N$. Positive cross-impact can be as large as $c = 1$ (full correlation) regardless of how many assets there are; this bound is independent of $N$. By contrast, negative cross-impact must satisfy $|c| \le \tfrac{1}{N-1}$, which vanishes as $N \to \infty$. Economically: correlated positive cross-impact (assets moving together) is structurally robust, while negative cross-impact (assets moving in opposite directions) is increasingly constrained as the universe of assets grows.

**Why it's surprising:** The positive and negative directions are treated completely differently by the no-manipulation geometry, despite appearing symmetrically in the matrix. The asymmetry reflects the fact that adding more assets tightens the Perron–Frobenius constraint on the most negative eigenvalue but leaves the largest eigenvalue free.

## Proof Sketches {#proofs}

:::proof-sketch{for="thm:main"}
1. **Symmetrisation of the Volterra form.** The causal cost form $\mathcal{C}(u) = \int_0^T\!\int_0^t u_t^\top H(t-s)u_s\,ds\,dt$ is symmetrised using the symmetry $H(t) = H(t)^\top$ (Assumption (ii)) to obtain $\mathcal{C}(u) = \tfrac{1}{2}\int_\mathbb{R}\!\int_\mathbb{R} f(t)^\top H(|t-s|)f(s)\,ds\,dt$, converting the triangular domain into a full convolution with the *even* kernel $K(t) = H(|t|)$. This enables Fourier methods.

2. **Matrix-valued Bochner–Schwartz.** Applying the Bochner–Schwartz lemma (Lemma `lem:BS`) to the symmetric convolution form shows that $\mathcal{C}(u) \ge 0$ for all $u$ if and only if $\widehat{K}(\omega) = \widehat{H}(\omega) \ge 0$ (as a matrix) for almost every $\omega$. Since each entry $\widehat{K}_{ij}(\omega) = c_{ij}\gamma(\beta_{ij})|\omega|^{\beta_{ij}-1}$ is locally integrable ($\beta_{ij}-1 \in (-1,0)$), the pointwise version of the lemma applies and gives the equivalence (i)$\Leftrightarrow$(ii).

3. **Exponential divergence argument for necessity (N=2).** Writing $\omega = e^\lambda$, the determinant of the $2\times 2$ spectral matrix is $e^{(\beta_{11}+\beta_{22}-2)\lambda}[c_{11}\gamma(\beta_{11})c_{22}\gamma(\beta_{22}) - c_{12}^2\gamma(\beta_{12})^2 e^{\delta\lambda}]$ with $\delta = 2\beta_{12}-\beta_{11}-\beta_{22}$. For $c_{12}\neq 0$ and $\delta \neq 0$, the bracket diverges to $-\infty$ as $|\lambda| \to \infty$, so positive-definiteness fails for some $\omega$. This forces $\delta = 0$ (mean-exponent condition) as a necessity.

4. **Diagonal factorisation for sufficiency (general N).** Under the mean-exponent condition, $\beta_{ij} = (b_i+b_j)/2$, so $|\omega|^{\beta_{ij}-1} = |\omega|^{(b_i-1)/2}|\omega|^{(b_j-1)/2}$. Setting $D(\omega) = \mathrm{diag}(|\omega|^{(b_i-1)/2})$, the spectral matrix factorises as $\widehat{H}(\omega) = D(\omega)\,\widetilde{C}\,D(\omega)$. Since $D(\omega)$ is a positive diagonal matrix and $\widetilde{C} \ge 0$ by assumption, this gives $\widehat{H}(\omega) \ge 0$ for all $\omega > 0$.

5. **Necessity for general N via principal minors.** If $\widehat{H}(\omega) \ge 0$ for all $\omega > 0$, every $2\times 2$ principal submatrix is also $\ge 0$ for all $\omega$. The pair $(i,j)$ submatrix is precisely the $N=2$ case in Step 3, which forces $\beta_{ij} = (\beta_{ii}+\beta_{jj})/2$ for each pair with $c_{ij}\neq 0$. With the mean-exponent condition established, the factorisation $\widehat{H}(\omega) = D(\omega)\widetilde{C}D(\omega)$ and the invertibility of $D(\omega)$ give $\widetilde{C} \ge 0$ by congruence.
:::

:::proof-sketch{for="prop:reg_necessity"}
1. **Spectral ratio formulation.** The $2\times 2$ PSD condition at frequency $\omega$ reduces to $c_{12}^2 \le R(\omega) := \widehat{\varphi}_{b_1}^{(t_0)}(\omega)\,\widehat{\varphi}_{b_2}^{(t_0)}(\omega)/\widehat{\varphi}_{\beta_{12}}^{(t_0)}(\omega)^2$, where $\widehat{\varphi}_\beta^{(t_0)}$ is the Fourier transform of $(|\cdot|+t_0)^{-\beta}$. Manipulation is precluded iff $c_{12}^2 \le \inf_{\omega>0} R(\omega)$.

2. **Low-frequency asymptotics via Lemma `lem:reg_FT`(ii).** As $\omega \to 0^+$, $\widehat{\varphi}_\beta^{(t_0)}(\omega) \sim \gamma(\beta)\omega^{\beta-1}$, so $R(\omega) \sim \tfrac{\gamma(\beta_{11})\gamma(\beta_{22})}{\gamma(\beta_{12})^2}\omega^{-\delta}$. If $\delta < 0$, then $\omega^{-\delta} = \omega^{|\delta|} \to 0$, forcing $R(\omega) \to 0$, so $\inf R = 0$ and any $c_{12} \neq 0$ violates PSD. This proves necessity when $\delta < 0$.

3. **High-frequency asymptotics via Lemma `lem:reg_FT`(iii).** As $\omega \to \infty$, the DLMF asymptotic expansion of the incomplete Gamma function gives $\widehat{\varphi}_\beta^{(t_0)}(\omega) \sim 2\beta t_0^{-\beta-1}\omega^{-2}$, so $R(\omega) \to \tfrac{\beta_{11}\beta_{22}}{\beta_{12}^2}\,t_0^{\delta}$, a finite positive constant. If $\delta \ge 0$, both the low-frequency limit ($+\infty$) and the high-frequency limit ($>0$) are positive, so $\inf R > 0$ and a non-trivial admissible region for $c_{12}$ exists.

4. **Singular kernel recovery.** As $t_0 \to 0^+$ with $\delta > 0$, the high-frequency constant $\sim t_0^{\delta} \to 0$, so $\inf R \to 0$ and the admissible region collapses to $\{c_{12} = 0\}$, recovering the strict necessity of $\delta = 0$ for the singular kernel.
:::

:::proof-sketch{for="prop:permanent"}
1. **Gamma weight degeneracy.** Using the Taylor expansion $\gamma(\beta) = \pi\beta + O(\beta^2)$ as $\beta \to 0^+$ (which follows from $\Gamma(1-\beta)\to 1$ and $\sin(\pi\beta/2)\sim\pi\beta/2$), the Gamma-weighted matrix $\widetilde{C} = \gamma(\beta)C \to 0$. Since $0 \ge 0$ always, the PSD condition is vacuous.

2. **Direct cost calculation for constant kernel.** For the limiting constant kernel $H(t) \equiv C$, use the symmetry $\int_0^T\!\int_0^t u_t^\top C\,u_s\,ds\,dt = \tfrac12(\int_0^T u_t\,dt)^\top C (\int_0^T u_s\,ds)$. For any round trip with $\int_0^T u_t\,dt = 0$, this gives $\mathcal{C}(u) = 0$ identically, regardless of $C$.
:::

:::proof-sketch{for="prop:singular"}
1. **Homogeneous case: global null direction.** With $b_1 = \cdots = b_N = \beta$, the spectral matrix is $\widehat{H}(\omega) = \gamma(\beta)|\omega|^{\beta-1}C$. If $\widetilde{C}v = 0$ then $Cv = 0$, so $v^\top\widehat{H}(\omega)v = 0$ for all $\omega$. By Parseval's theorem, $\mathcal{C}(f(t)v) = 0$ for all $f$, so $v$ is a genuine zero-cost direction.

2. **Heterogeneous case: frequency-dependent rotation.** The factorisation $\widehat{H}(\omega) = D(\omega)\widetilde{C}D(\omega)$ means $v^\top\widehat{H}(\omega)v = (D(\omega)v)^\top\widetilde{C}(D(\omega)v)$. Since $D(\omega) = \mathrm{diag}(|\omega|^{(b_i-1)/2})$ and the exponents $b_i$ differ, the vector $D(\omega)v$ rotates in $\mathbb{R}^N$ as $\omega$ varies. For it to remain in the null space of $\widetilde{C}$ for all $\omega$, one would need all $b_i$ (for $v_i \neq 0$) to be equal — a contradiction with heterogeneity.

3. **Positive cost for generic strategies.** Since $v^\top\widehat{H}(\omega)v > 0$ for all but finitely many $\omega$, any strategy $f$ with non-finitely-supported Fourier transform satisfies $\mathcal{C}(f(t)v) = \tfrac12\int v^\top\widehat{H}(\omega)v\,|\hat{f}(\omega)|^2\,d\omega > 0$, confirming the structural safety margin from exponent heterogeneity.
:::

## Numerical Illustration {#numerics}

The numerical experiments are organised into five subsections (Sections 8.1–8.5) and serve both to validate the analytical results and to build intuition for the parameter sensitivity.

**Two-asset and three-asset singular kernel (Sections 8.1–8.2).** For $N=2$ with self-impact exponents $b_1, b_2$ ranging over $(0, 0.5)^2$, the paper plots the admissible region for $(c_{12}/\sqrt{c_{11}c_{22}})$ as a function of the exponent gap $b_1 - b_2$, confirming that the admissible cross-impact is exactly $|c_{12}| \le \sqrt{c_{11}c_{22}}$ (the $\widetilde{C}\ge 0$ condition) once the mean-exponent condition is imposed. For $N=3$, the admissible region in $(c_{12}, c_{13}, c_{23})$-space is a convex cone, and the numerical experiments verify that its boundary corresponds precisely to $\widetilde{C}$ being rank-deficient, consistent with Theorem `thm:main`.

**Parameter sensitivity (Section 8.3).** Sensitivity to self-impact exponents (Section 8.3.1) shows that the Gamma weights $\gamma(\beta_i)$ modulate the effective strength of the no-manipulation constraint: assets with larger $\beta_i$ (faster decay) receive more spectral weight, tightening the constraint for cross-impact involving them. The sensitivity to $N$ (Section 8.3.2) confirms the large-$N$ scaling of Proposition `prop:largeN`: for a uniform portfolio with cross-impact $c$, the admissible range is $[-1/(N-1), 1]$, and numerical experiments show this bound tight by constructing explicit manipulation strategies at $c = -1/(N-1) - \varepsilon$.

**Regularised kernel: admissible region and $t_0$ dependence (Sections 8.4–8.5).** For the regularised kernel with $\delta > 0$ (cross-impact decaying slower than the mean), the admissible region for $c_{12}$ is plotted as a function of $t_0$. The numerical results confirm Proposition `prop:reg_necessity`(ii)–(iii): the admissible region shrinks monotonically as $t_0 \to 0^+$ and collapses to $\{c_{12}=0\}$ in the limit, validating the spectral asymptotic analysis. The asymptotic formula for the high-frequency limit $R(\infty) = (\beta_{11}\beta_{22}/\beta_{12}^2)\,t_0^{\delta}$ is verified numerically to 5 significant digits against the exact Fourier representation involving incomplete Gamma functions, as noted in Remark 5.7 of the paper.

## Connections {#connections}

- [Discrete vs. Rough](/papers/discrete_vs_rough): Both papers work with power-law propagator kernels and the $L^2$ theory of Volterra operators; the rough-path / discrete-time correspondence