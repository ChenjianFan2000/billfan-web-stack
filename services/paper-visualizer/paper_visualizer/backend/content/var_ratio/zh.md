---
paper_slug: var_ratio
lang: zh
sections:
  - id: context
    title: 背景与动机
  - id: objects
    title: 核心数学对象
  - id: main-results
    title: 主要结果
  - id: proofs
    title: 证明梗概
  - id: numerics
    title: 数值实验
  - id: connections
    title: 关联文献
---

## 背景与动机 {#context}

大型信贷组合的尾部风险度量是量化风险管理的核心问题。以巴塞尔内部评级法（IRB）为代表的监管框架要求银行在极高置信水平（通常 $\alpha = 99.9\%$）下持有资本缓冲。该资本要求对违约事件之间的**依赖结构**高度敏感：边际违约概率（PD）可以从历史数据中较可靠地估计，但联合尾部依赖结构则难以刻画，尤其在极端情景下更是如此。巴塞尔框架采用 Vasicek 单因子高斯 Copula 模型，在封闭形式下计算组合 VaR，但该模型对尾部依赖的低估在 2008 年金融危机中暴露无遗。

**依赖不确定性**下的风险聚合研究试图在仅知道部分依赖信息时计算最坏情形风险度量。该领域早期贡献包括 Makarov、Rüschendorf 和 Embrechts 等人的工作，核心发现是：在**完全依赖不确定性**下，VaR 上界可等于各个体 VaR 之和。真正令人震惊的是 De Vecchi、Nendel 和 Streicher（2026，以下记为 DVNs）的最新结果：即便个体损失之间存在**任意小**的正相关（用 Pearson 相关、Spearman $\rho$ 或 Kendall $\tau$ 均可度量），仍然与**完全共单调的尾部**相容——这意味着组合 VaR 可被严重低估。DVNs 通过一个比值 $r_\alpha(n)$（真实最坏情形 VaR 与从"正常"机制估计的 VaR 之比）量化这一效应，并建立了同质边际情形下的渐近下界，但未证明下界是否精确、未推广至异质组合，也未说明所构造的耦合是否最优。

本文在五个方向上对 DVNs 的分析进行了**根本性的深化与推广**：（1）证明渐近比值的精确极限；（2）推广至异质信贷组合；（3）建立 $O(n^{-1/2})$ 的 Berry–Esseen 收敛速率；（4）证明上共单调耦合在所有满足配对相关约束的可交换 Bernoulli 耦合中**渐近最优**，其证明将 de Finetti 定理与经典矩问题相结合；（5）将整个框架推广至连续随机损失给定违约（LGD）分布，揭示相变现象，并证明 LGD 不确定性严格放大最坏情形比值。作为应用，本文表明巴塞尔 IRB 模型在各评级类别和 LGD 假设下存在 3 至 29 倍的资本低估。

## 核心数学对象 {#objects}

**上共单调耦合（Upper Comonotonic Coupling）**

$$
X_i^\gamma \;:=\; F_{\mu_i}^{-1}\!\bigl(\gamma V_i\,\mathbf{1}_{\{U \leq \gamma\}} + U\,\mathbf{1}_{\{U > \gamma\}}\bigr), \qquad i = 1, \ldots, n,
$$

其中 $U \sim \mathrm{Uniform}(0,1)$ 为公共系统性因子，$V_1, \ldots, V_n$ 为独立于 $U$ 的 i.i.d. 均匀随机变量，$\gamma \in (0,1)$ 为**尾部阈值**。其非平凡之处在于：该耦合同时满足正确的边际分布、任意小的配对相关约束，以及在事件 $\{U > \gamma\}$ 上的**完全共单调尾部**——三者看似矛盾，却能共存。

**VaR 低估比值**

$$
r_\alpha(n) \;:=\; \frac{\operatorname{VaR}_\alpha^{\mathbb{P}}\!\bigl(\sum_{i=1}^n \lambda_i X_i^\gamma\bigr)}{\operatorname{VaR}_\alpha^{\mathbb{P}}\!\bigl(\sum_{i=1}^n \lambda_i X_i^\gamma \,\big|\, U \leq \gamma\bigr)},
$$

分子为真实（无条件）组合 VaR，分母为仅观测到"正常"机制 $\{U \leq \gamma\}$ 时所估计的 VaR。$r_\alpha(n) \gg 1$ 意味着若从未目睹极端尾部事件，风险管理者将系统性地低估组合损失。

**条件违约概率（Conditional PD）**

$$
\tilde{p}_i \;:=\; \mathbb{P}(X_i^\gamma = 1 \mid U \leq \gamma) \;=\; \frac{\gamma - 1 + p_i}{\gamma}.
$$

正常机制下的条件 PD 满足 $\tilde{p}_i < p_i$，因为部分违约概率质量被"集中"到了尾部事件中。这一关系是分子与分母之间比值精确极限的核心。

**de Finetti 混合分布与矩约束集**

对于均值为 $p$、方差约束为 $\delta p(1-p)$ 的概率测度集合：

$$
\mathcal{V}(p,\delta) \;:=\; \bigl\{\nu \in \mathcal{P}([0,1]) : \mathbb{E}_\nu[\theta] = p,\; \operatorname{Var}_\nu(\theta) \leq \delta\,p(1-p)\bigr\}.
$$

由 de Finetti 定理，任意可交换 Bernoulli 序列等价于某个混合分布 $\nu \in \mathcal{P}([0,1])$，而配对 Pearson 相关约束 $\leq \delta$ 恰好等价于 $\operatorname{Var}_\nu(\theta) \leq \delta p(1-p)$。这将无限维耦合问题化归为关于 $\nu$ 的一维矩优化问题。

**复合损失边际 CDF（含连续 LGD）**

$$
F_i(x) = \begin{cases}
1 - p_i, & x = 0, \\
(1 - p_i) + p_i\,G_i(x), & x \in (0, 1],
\end{cases}
$$

其中 $G_i$ 为第 $i$ 个债务人的 LGD 分布。相应分位数函数为 $F_i^{-1}(u) = G_i^{-1}((u-(1-p_i))/p_i)$（当 $u \geq 1-p_i$），此对象将二元违约框架推广至连续损失设定。

**相变阈值 $\gamma = 1 - p_{\min}$**

在同质组合中，当 $\gamma \downarrow (1-p)$ 时，比值 $r_\alpha(\infty;\gamma)$ 发散（一阶极点）；而在异质组合中，同样的极限却保持有限。这一**定性差异**标志着一个相变边界，是本文揭示的核心几何现象之一。

## 主要结果 {#main-results}

:::theorem{id=thm:sharp_identical label="同质边际的精确比值"}
设 $\mu_i = B(1,p)$ 对所有 $i \in \mathbb{N}$，$\gamma \in (1-p, 1)$，$\alpha \in [\gamma, 1)$，且 $(\lambda_i)_{i \in \mathbb{N}} \subset [0, \infty)$ 满足权重条件。则 $r_\alpha(n)$ 收敛且

$$\lim_{n \to \infty} r_\alpha(n) \;=\; \frac{\gamma}{\gamma - 1 + p} \;=\; \frac{1}{\tilde{p}},$$

其中 $\tilde{p} = (\gamma - 1 + p)/\gamma$ 为正常机制下的条件 PD。特别地，DVNs 下界精确当且仅当 $\alpha = \gamma$。
:::

该定理给出了 DVNs 仅通过下界刻画的渐近比值的**精确极限**。分子 $\operatorname{VaR}_\alpha(S_n) = L_n$（总敞口）成立因为尾部事件 $\{U > \gamma\}$ 触发全体同时违约；分母 $\operatorname{VaR}_\alpha(S_n^{\mathrm{ind}})/L_n \to \tilde{p}$ 由条件独立损失的大数定律给出。因此比值精确等于 $1/\tilde{p}$，与组合规模和权重结构均无关。

**为何令人惊讶：** 对于 $p = 1\%$、Pearson 相关 $\delta = 10\%$ 的典型情形，精确极限约为 $111$，而 DVNs 数值实验中 $n=1000$ 时仅观测到约 $50$——表明有限组合规模效应显著，但极限本身远比直觉预期更为极端。

---

:::theorem{id=thm:wc_optimality label="上共单调耦合的最坏情形最优性"}
设 $p \in (0,1)$，$\delta \in (0,1)$，$\alpha \in (0,1)$。定义 $\gamma = (1-p)/((1-p) + \delta p)$。

(a) 若 $\gamma \geq \alpha$（小 $\delta$ 情形）：

$$\lim_{n \to \infty} \frac{1}{n}\sup_{F \in \mathcal{M}_n^{\mathrm{exch}}(p,\delta)} \operatorname{VaR}_\alpha(S_n) \;=\; p(1-\delta) \;=\; \tilde{p},$$

其中上确界渐近由阈值为 $\gamma$ 的上共单调耦合实现。

(b) 若 $\gamma < \alpha$（大 $\delta$ 情形）：

$$\sup_{F \in \mathcal{M}_n^{\mathrm{exch}}(p,\delta)} \operatorname{VaR}_\alpha(S_n) \;=\; n$$

对所有足够大的 $n$ 成立，且上共单调耦合精确实现此上确界。
:::

该定理将上共单调耦合从一个"能产生大 VaR 比值的特定构造"提升为**所有满足约束的可交换耦合中的真正最坏情形**。其核心洞察是：最坏情形耦合必然将所有依赖集中在单一灾难性事件（混合分布在 $\theta = 1$ 处的原子），其余概率质量则以尽可能低的速率产生独立违约——这正是上共单调耦合的精确结构。

**为何令人惊讶：** 最优性的证明路径出人意料：它将无限维耦合优化问题化归为关于混合分布的一维矩问题，而该矩问题的两点最优解与上共单调耦合的 de Finetti 表示**精确重合**——这一代数巧合揭示了深刻的结构性原因。

---

:::theorem{id=thm:lgd_ratio label="随机 LGD 下的 VaR 比值"}
考虑 $n$ 个同质债务人，PD 为 $p$，LGD i.i.d. 分布为 $G$（支撑在 $[0,1]$）。在阈值为 $\gamma \in (1-p, 1)$ 的上共单调耦合下，对 $\alpha \in [\gamma, 1)$：

$$\lim_{n \to \infty} r_\alpha(n) \;=\; \frac{G^{-1}\!\left(\dfrac{\alpha - 1 + p}{p}\right)}{\dfrac{1}{\gamma}\displaystyle\int_0^\gamma F^{-1}(u)\,\mathrm{d}u},$$

其中 $F$ 为复合 CDF。
:::

分子 $G^{-1}((\alpha-1+p)/p)$ 是 LGD 分布在高分位点处的值，衡量尾部事件下的损失强度；分母是正常机制下条件平均损失，由 $F^{-1}$ 在 $[0,\gamma]$ 上的截断均值给出。当 LGD 退化为 $1$（纯 Bernoulli 情形）时，公式恰好还原为定理 $r_\alpha(\infty) = \gamma/(\gamma-1+p)$。

**为何令人惊讶：** 推论 `cor:lgd_amplification` 证明任何非退化 LGD 分布都**严格放大**最坏情形比值——LGD 不确定性不仅不能分散尾部风险，反而加剧了 VaR 低估。对于均匀 LGD，放大因子恰为 $2$（当 $\alpha = \gamma$ 时）。

---

:::theorem{id=thm:phase_transition label="阈值处的相变"}
将 $r_\alpha(\infty;\gamma)$ 视为 $\gamma$ 的函数。

(a) **同质情形**（$p_i = p$ 对所有 $i$）。当 $\gamma \downarrow (1-p)$ 时：

$$r_\alpha(\infty; \gamma) = \frac{\gamma}{\gamma - 1 + p} \;\sim\; \frac{1-p}{\gamma - (1-p)} \;\to\; +\infty.$$

发散速率为一阶极点。

(b) **异质情形**（$p_{\min} < \bar{p}$）。当 $\gamma \downarrow (1-p_{\min})$ 时，比值趋于有限极限：

$$r_\alpha(\infty; \gamma) \;\to\; \frac{\bar{F}^{-1}(\alpha)}{\bar{\tilde{\mu}}_{\gamma \downarrow (1-p_{\min})}},$$

其中分子分母均保持有界。
:::

该定理揭示了组合异质性在依赖不确定性下的一个根本性保护机制：同质组合在"几乎无相关性"极限下比值趋于无穷，而异质组合却保持有限。这是因为异质组合中，当 $\gamma$ 接近 $1-p_{\min}$ 时，部分 PD 较低的债务人在尾部事件中**不再必然违约**，从而为分母提供了正的贡献下界。

**为何令人惊讶：** 风险管理者通常认为组合异质性会增加复杂性但对尾部风险影响中性；该定理表明在依赖不确定性语境下，异质性提供了一个**定量的缓冲**，完全改变了 VaR 比值的定性行为。

---

:::theorem{id=thm:berry_esseen label="Berry–Esseen 收敛速率"}
在定理 `thm:sharp_hetero` 的条件下，额外假设 $\lambda_i = 1$，$\alpha \in (\gamma,1)$，$z_\alpha := \Phi^{-1}(\alpha) > 0$。定义

$$\sigma_n^2 := \sum_{i=1}^n \tilde{p}_i(1-\tilde{p}_i), \qquad \rho_n := \sum_{i=1}^n \tilde{p}_i(1-\tilde{p}_i)\bigl(\tilde{p}_i^2 + (1-\tilde{p}_i)^2\bigr).$$

则对所有足够大的 $n$：

$$\left|r_\alpha(n) - \frac{n}{n\tilde{\bar{p}}_n + z_\alpha \sigma_n}\right| \;\leq\; \left(1 + \frac{C_0\,\rho_n}{\phi(z_\alpha)\,\sigma_n^2}\right) \cdot \frac{n}{(n\tilde{\bar{p}}_n)^2},$$

其中 $C_0 \leq 0.5600$（Shevtsova 2011 的 Berry–Esseen 常数）。特别地，$|r_\alpha(n) - \gamma/(\gamma-1+\bar{p}_n)| = O(n^{-1/2})$。
:::

该定理给出了带显式常数的 $O(n^{-1/2})$ 收敛速率，并揭示异质组合收敛**至少与同质情形一样快**（因 Jensen 不等式保证异质情形下 $\sigma_n^2/n$ 更小）。中间量 $n/(n\tilde{\bar{p}}_n + z_\alpha\sigma_n)$ 提供了对任意有限 $n$ 的精确近似。

**为何令人惊讶：** 对于典型信用参数（$p=1\%$，$\gamma=0.999$），修正项系数约为 $3605$，说明即便组合规模 $n$ 高达数千，有限样本效应仍然显著——这解释了为何 DVNs 的 $n=1000$ 数值实验中观测到的比值（约 50）远低于精确极限（约 111）。

## 证明梗概 {#proofs}

:::proof-sketch{for=thm:sharp_identical}
1. **分子计算**：在事件 $\{U > \gamma\}$ 上（概率 $1-\gamma \geq 1-\alpha > 0$），全体债务人同时违约，$S_n = L_n$；对任意 $t < L_n$ 有 $\mathbb{P}(S_n > t) \geq 1-\gamma \geq 1-\alpha$，故 $\operatorname{VaR}_\alpha(S_n) = L_n$。
2. **分母的大数定律**：在条件 $\{U \leq \gamma\}$ 下，$X_i^\gamma$ 为 i.i.d. $B(1,\tilde{p})$，由 Chebyshev 不等式和权重正则条件 $\sum \lambda_i^2/L_n^2 \to 0$，得 $S_n^{\mathrm{ind}}/L_n \xrightarrow{\mathbb{P}} \tilde{p}$，进而 $\operatorname{VaR}_\alpha(S_n^{\mathrm{ind}})/L_n \to \tilde{p}$。
3. **比值合并**：$r_\alpha(n) = L_n / \operatorname{VaR}_\alpha(S_n^{\mathrm{ind}}) \to 1/\tilde{p} = \gamma/(\gamma-1+p)$。
4. **下界精确性**：DVNs 下界公式在 $\alpha = \gamma$ 时与极限一致，对 $\alpha > \gamma$ 则严格小于极限，因 $\alpha \mapsto \alpha/(\alpha-1+p)$ 在 $(1-p,1)$ 上严格递减。
:::

:::proof-sketch{for=thm:wc_optimality}
1. **de Finetti 化归**：任意可交换 Bernoulli$(p)$ 序列可表示为 $\theta$ 混合，其中 $\mathbb{E}[\theta]=p$；由引理 `lem:cor_mixing`，配对相关约束 $\leq \delta$ 等价于 $\operatorname{Var}_\nu(\theta) \leq \delta p(1-p)$，将问题化归为 $\mathcal{V}(p,\delta)$ 上的矩优化。
2. **矩问题求解（引理 `lem:moment_solution`）**：在均值和方差约束下最大化 $\alpha$-分位数。经典矩问题理论给出极值点为两点分布；参数化为 $\nu = (1-\varepsilon)\delta_a + \varepsilon\delta_b$，在 $b=1$ 和最小 $\varepsilon$ 处取到最优，得 $\nu^* = \gamma\,\delta_{p(1-\delta)} + (1-\gamma)\,\delta_1$，最优分位数为 $p(1-\delta)$。
3. **与上共单调耦合的重合（命题 `prop:match`）**：验证 $\tilde{p} = p(1-\delta)$（代数恒等式），并直接检验上共单调耦合的 de Finetti 混合分布恰为 $\gamma\,\delta_{\tilde{p}} + (1-\gamma)\,\delta_1 = \nu^*$——两点矩最优解与上共单调耦合的 de Finetti 表示**精确重合**。
4. **渐近 VaR 收敛（引理 `lem:var_mixing`）**：对任意 $\nu \in \mathcal{V}(p,\delta)$（无原子假设），条件 LLN 给出 $\operatorname{VaR}_\alpha(S_n)/n \to F_\nu^{-1}(\alpha)$；对两点优化器 $\nu^*$（有原子），直接通过 LLN 验证结论成立。
5. **最优性结论**：综合以上，在所有可交换耦合中渐近 VaR 上确界为 $np(1-\delta)$，由上共单调耦合渐近实现。
:::

:::proof-sketch{for=thm:lgd_ratio}
1. **分子：尾部分位数**：在 $\{U > \gamma\}$ 上，聚合损失为 $S_n/n = G^{-1}((U-(1-p))/p)$，为 $U$ 的单调函数；当 $\alpha \geq \gamma$ 时，$\alpha$-分位数落在共单调尾部，由 $U=\alpha$ 给出 $\operatorname{VaR}_\alpha(S_n)/n \to G^{-1}((\alpha-1+p)/p)$。
2. **分母：条件截断均值**：由引理 `lem:cond_mean_lgd`，$\mathbb{E}[X_i^\gamma \mid U \leq \gamma] = \gamma^{-1}\int_0^\gamma F^{-1}(u)\,\mathrm{d}u =: \tilde{\mu}$；大数定律给出 $S_n^{\mathrm{ind}}/n \xrightarrow{\mathbb{P}} \tilde{\mu}$，从而 $\operatorname{VaR}_\alpha(S_n^{\mathrm{ind}})/n \to \tilde{\mu}$。
3. **放大不等式**：由 $\alpha \geq \gamma$ 和 $G^{-1}$ 的单调性，$G^{-1}(q_\alpha) \cdot q_0 \geq \int_0^{q_0} G^{-1}(v)\,\mathrm{d}v$，证明 $r^{\mathrm{LGD}} \geq r^{\mathrm{Bern}}$；等号当且仅当 $G$ 退化时成立。
:::

:::proof-sketch{for=thm:phase_transition}
1. **同质情形极点**：直接代入 $r_\alpha(\infty;\gamma) = \gamma/(\gamma-1+p)$，当 $\gamma \to (1-p)^+$ 时分母趋于零而分子趋于 $1-p > 0$，构成一阶极点。
2. **异质情形有界性**：当 $\gamma < 1-p_{\min}$ 时，PD 最低的债务人（$p_i < 1-\gamma$）即便在尾部事件中也不违约，其条件损失贡献非零但不等于 $\lambda_i$；分母 $\bar{\tilde{\mu}}$ 因此被上方的平均条件 PD $\bar{p}_{\mathrm{above}}(\gamma)$ 下界所保护，保持远离零。
3. **相图刻画（命题 `prop:phase_diagram`）**：定义 $f(\gamma) = \pi((1-\gamma, p_{\max}])$ 为尾部违约债务人的暴露占比，$\bar{p}_{\mathrm{above}}(\gamma) = \mathbb{E}_\pi[p \mid p > 1-\gamma]$，则 $\gamma > 1-p_{\min}$ 时比值由 $\gamma/(\gamma-1+\bar{p})$ 给出，$\gamma \leq 1-p_{\min}$ 时由 $f(\gamma)$ 和条件均值决定，两者在相变边界处呈现定性不同的行为。
:::

## 数值实验 {#numerics}

数值实验从四个维度验证了上述理论结果。

**收敛速率验证**：对 $p = 0.01$、$\delta = 0.10$（对应 $\gamma \approx 0.999$）、$\alpha = 0.999$，比值 $r_\alpha(n)$ 随 $n$ 的变化表明：$n = 100$ 时约为 40，$n = 1000$ 时约为 50，而精确极限约为 111。这与定理 `thm:berry_esseen` 预测的 $O(n^{-1/2})$ 速率及修正项系数约 3605 完全吻合，说明即便组合规模达到数千，有限样本偏差仍然显著，从业者不应以有限规模的数值低估真实极限。

**LGD 分布效应**：对均匀、Beta 和退化 LGD 分布的比较表明，非退化 LGD 分布严格放大最坏情形比值（推论 `cor:lgd_amplification`）。均匀 LGD 在 $\alpha = \gamma$ 时放大因子精确为 2，与解析公式一致。Beta LGD 的放大因子随参数变化显著，验证了通过正则不完全 Beta 函数数值计算的准确性。

**巴塞尔 IRB 比较**：在各评级类别（PD 从 $0.03\%$ 到 $15\%$）和不同 LGD 假设（$45\%$ 到 $100\%$）下，最坏情形 VaR 与 IRB 资本要求之比覆盖 3 至 29 倍的范围（命题 `prop:irb_comparison` 和 `prop:lgd_capital`）。投资级债务人（低 PD）的低估