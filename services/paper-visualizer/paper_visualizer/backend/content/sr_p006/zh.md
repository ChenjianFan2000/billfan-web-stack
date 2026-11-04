---
paper_slug: sr_p006
lang: zh
sections:
  - id: context
    title: 背景与动机
  - id: objects
    title: 核心数学对象
  - id: main-results
    title: 主要定理
  - id: proofs
    title: 证明思路
  - id: numerics
    title: 数值实验
  - id: connections
    title: 关联工作
---

## 背景与动机 {#context}

考虑 $\mathbb{R}^d$ 上的过阻尼 Langevin 扩散方程
$$dX_t = -\nabla U(X_t)\,dt + \sqrt{2}\,dB_t.$$
这一 SDE 在贝叶斯后验采样、统计力学 Gibbs 测度采样以及机器学习中的惩罚采样目标中无处不在。其不变测度为 $\pi \propto e^{-U}$，而定量刻画初始分布向 $\pi$ 收敛的速度，是连接连续动力学、离散算法误差（ULA）以及平均场传播混沌的核心量。

当势函数 $U$ 本身强凸时，经典 Bakry–Émery 理论给出 $W_2$ 指数收缩，速率恰为强凸常数 $m$。然而实际应用中 $U$ 往往非凸：例如 $U = U_0 + V$，其中 $U_0$ 强凸而 $V$ 带有有界梯度扰动（如有界特征向量对数似然）。此时 Eberle（2016）通过反射耦合与凹距离函数的变分原理，证明了 $W_1$ 型指数收缩的一般存在性，但其速率由 Sturm–Liouville 特征值变分问题给出，通常**不具有显式闭合形式**。

本文填补这一空白：在结构化势函数 $U = U_0 + V$（$U_0$ 是 $m$-强凸的，$\|\nabla V\|_\infty \le K$）以及亚临界条件 $K < \sqrt{m}$ 下，明确构造一族幂律凹距离函数，并得到显式闭合形式收缩速率
$$c^\star = m - K\sqrt{m}.$$
该速率与维数无关，仅通过 $K = \|\nabla V\|_\infty$ 依赖于扰动，而不依赖于 $\|V\|_\infty$——这与 Holley–Stroock 对数 Sobolev 扰动界（其常数随 $\mathrm{osc}(V)$ 指数增长）形成鲜明对比。在此基础上，论文将该速率直接嵌入 ULA 离散化误差分析和平均场粒子系统的传播混沌估计中。

## 核心数学对象 {#objects}

**幂律凹距离函数 $f$**

$$f(r) := \frac{R_0}{1-\beta}\Bigl[\bigl(1 + r/R_0\bigr)^{1-\beta} - 1\Bigr], \qquad r \ge 0,$$

其中参数由势函数参数唯一确定：

$$\beta := \frac{K}{\sqrt{m}} \in [0,1), \qquad R_0 := \frac{2}{\sqrt{m}}, \qquad c^\star := m(1-\beta) = m - K\sqrt{m}.$$

非平凡之处：$f$ 不是欧氏距离，而是严格凹的单调增函数，满足 $f(0)=0$，$f'(0)=1$，且在任意有界区间上与欧氏距离双 Lipschitz 等价。参数 $(\beta, R_0)$ 由对两参数族的最优化唯一确定（见命题 \ref{prop:sharpness}）。

**$W_{1,f}$ Kantorovich 距离**

$$W_{1,f}(\mu, \nu) := \inf_{\pi} \int f(|x - y|)\, d\pi(x,y),$$

即以 $f(|x-y|)$ 为代价函数的最优输运距离。由于 $f(r) \le r$，有 $W_{1,f} \le W_1$，故它是比标准 $W_1$ 更精细的度量。

**Eberle 反射耦合**

给定 $(X_t)$ 满足 Langevin SDE，伴随过程 $(X'_t)$ 定义为

$$dX'_t = -\nabla U(X'_t)\,dt + \sqrt{2}(I - 2e_t e_t^\top)\,dB_t, \qquad e_t := \frac{X_t - X'_t}{|X_t - X'_t|},$$

直到耦合时刻 $\tau := \inf\{t: X_t = X'_t\}$，之后令 $X'_t \equiv X_t$。非平凡之处：噪声幅度相同，但沿方向 $e_t$ 的分量被翻转，使得距离过程 $r_t = |X_t - X'_t|$ 满足一维 SDE，噪声系数为常数 $2\sqrt{2}$（由 Itô 公式中 Itô 修正项恰好相消所致）。

**距离过程的一维 SDE**

$$dr_t = -e_t \cdot (\nabla U(X_t) - \nabla U(X'_t))\,dt + 2\sqrt{2}\,dW_t, \qquad t < \tau,$$

漂移上界为 $2K - m r_t$。这将 $d$ 维耦合问题约化为含有界漂移的一维扩散问题。

**关键代数不等式（超鞅条件）**

$$\forall r \ge 0: \quad (2K - mr)\,f'(r) + 4\,f''(r) + c^\star\,f(r) \le 0.$$

非平凡之处：将 Itô 公式对 $f(r_t)$ 应用后，此不等式直接推出 $\mathbb{E}[f(r_t)]$ 的指数衰减——整个论证的核心代数步骤。

## 主要定理 {#main-results}

:::theorem{id=lem:key label="关键代数引理"}
在假设 A1–A3 下，以 $f$、$\beta$、$c^\star$、$R_0$ 如式 \eqref{eq:params}–\eqref{eq:fdef} 定义，函数 $f$ 对所有 $r \ge 0$ 满足
$$( 2K - mr)\,f'(r) + 4\,f''(r) + c^\star\,f(r) \le 0,$$
当且仅当 $r = 0$ 时等号成立。
:::

此引理是全文的代数核心。令 $y = 1 + r/R_0 \in [1,\infty)$，不等式等价于 $h(y) \le \sqrt{m}$，其中 $h(y) := y^{-\beta-1}[(K+\sqrt{m})y - K]$。验证分三步：$h(1) = \sqrt{m}$（等号恰在 $r=0$ 处成立），$h'(1) = 0$，以及 $h'(y) < 0$ 对所有 $y > 1$ 成立（漂移系数的线性因子为负）。**令人惊讶之处：** 参数 $R_0 = 2/\sqrt{m}$ 和 $\beta = K/\sqrt{m}$ 的选取使得两个代数切线条件 $h(1) = \sqrt{m}$ 与 $h'(1) = 0$ 同时成立，这并非显然，而是最优性的精确表现。

---

:::theorem{id=thm:main label="连续时间主定理"}
假设 A1–A3。设 $(X_t)_{t\ge 0}$、$(X'_t)_{t\ge 0}$ 是通过 Eberle 反射耦合所得的两条解，初始分布分别为 $\mu_0, \nu_0$。则对所有 $t \ge 0$，
$$\mathbb{E}\bigl[f(|X_t - X'_t|)\bigr] \le e^{-c^\star t}\,\mathbb{E}\bigl[f(|X_0 - X'_0|)\bigr],$$
其中 $c^\star = m - K\sqrt{m}$。从而
$$W_{1,f}\bigl(\mathrm{Law}(X_t),\mathrm{Law}(X'_t)\bigr) \le e^{-c^\star t}\,W_{1,f}(\mu_0,\nu_0).$$
:::

该定理断言：在 $f$-Wasserstein 意义下，任意两条 Langevin 解之间的距离以速率 $c^\star$ 指数衰减——无论维数 $d$ 为何，无论 $\|V\|_\infty$ 大小。速率 $c^\star = m - K\sqrt{m}$ 在 $K=0$ 时退化为强凸速率 $m$，在 $K \to \sqrt{m}$ 时趋于零，刻画了临界阈值的行为。**令人惊讶之处：** 速率完全不依赖于 $\|V\|_\infty$，仅通过梯度模 $K$ 感知扰动，与基于振幅的函数不等式扰动界形成鲜明对比。

---

:::theorem{id=thm:ula label="ULA 离散时间收缩定理"}
假设 A1–A4。存在绝对常数 $C_1 > 0$，使得对每个满足
$$h \le h_0 := \min\!\left(\frac{m}{2L^2},\,\frac{1}{L},\,\frac{1}{c^\star}\right)$$
的步长 $h$，每个初始分布 $\nu_0$（满足 $M_0 := \mathbb{E}_{\nu_0}[|X - x^\star|^2] < \infty$），以及每个 $N \ge 1$，有
$$W_{1,f}\bigl(\nu_0 P_h^N, \pi\bigr) \le e^{-c^\star N h/2}\,W_{1,f}(\nu_0, \pi) + \frac{C_1\,L^2\,\sqrt{M^\star + d}\,\sqrt{h}}{c^\star},$$
其中 $M^\star = M_0 + 4(2K^2 + md)/m^2$，$c^\star = m - K\sqrt{m}$。
:::

该定理为 ULA 迭代提供了"几何衰减 $+$ 加性偏差"形式的界：第一项以连续时间速率 $c^\star/2$ 几何衰减（折半来自步长余量），第二项为量级 $O(\sqrt{h})$ 的渐近偏差，控制 ULA 在凹距离下的均衡误差。$\sqrt{M^\star + d}$ 的出现源于 Euler–Maruyama 一步强误差中对梯度模的控制。**令人惊讶之处：** 离散化速率与连续时间速率相同（仅差因子 $1/2$），离散化代价仅以加性 $O(\sqrt{h})$ 项进入，不改变指数衰减速率。

---

:::theorem{id=thm:poc label="均匀时间传播混沌定理"}
假设 A1、A5，且 $K < \sqrt{m}$。设初始数据独立同分布：$X^{i,N}_0 \sim \mu_0$ i.i.d.，$Y^i_t$ 为对应 McKean–Vlasov 解。则存在绝对常数 $C_2 > 0$，使得对所有 $N \ge 2$，所有 $t \ge 0$，所有 $i \in \{1,\dots,N\}$，
$$W_{1,f}\bigl(\mathrm{Law}(X^{i,N}_t),\,\mu_t\bigr) \le \frac{C_2\,K}{\sqrt{N-1}\cdot c^\star}, \qquad c^\star = m - K\sqrt{m}.$$
特别地，该界**关于时间一致**且**与维数无关**。
:::

经典 Sznitman 型耦合论证给出的界形如 $C(t)/\sqrt{N}$，其中 $C(t) \sim e^{Lt}$ 随时间指数增长，仅对有限时间区间有效。本定理以收缩速率 $c^\star > 0$ 取代发散因子，得到对所有时间均匀的 $O(1/\sqrt{N})$ 界，且常数显式。**令人惊讶之处：** 界与维数 $d$ 完全无关——这源于 $\|\nabla_1 W\|_\infty \le K$ 控制的是梯度的范数而非分量，避免了 $\sqrt{d}$ 因子的出现。

---

:::theorem{id=prop:sharpness label="指数最优性命题"}
考虑两参数族
$$f_{R,\beta}(r) := \frac{R}{1-\beta}\bigl[(1+r/R)^{1-\beta}-1\bigr], \quad R>0,\ \beta\in[0,1),$$
及对应的超鞅收缩速率 $c(R,\beta)$。在假设 A3（$K < \sqrt{m}$）下，
$$\sup_{R>0,\,\beta\in[0,1)} c(R,\beta) = m - K\sqrt{m},$$
且上确界唯一在 $(R,\beta) = (2/\sqrt{m},\,K/\sqrt{m})$ 处取得。
:::

在幂律凹距离族中，本文所构造的 $f$ 是**唯一最优选择**：没有其他参数组合能给出更大的收缩速率。**令人惊讶之处：** 最优性证明完全代数化——通过分析 $c(R,\beta) \le m(1-\beta)$（由 $y^{1-\beta}$ 项的发散性推出）和切线约束 $\beta \ge K/\sqrt{m}$（由 $H'(1)=0$ 条件推出），两个不等式同时在且仅在 $(\beta, R) = (K/\sqrt{m}, 2/\sqrt{m})$ 处饱和。

## 证明思路 {#proofs}

:::proof-sketch{for=lem:key}
1. **变量替换化简**：令 $y = 1 + r/R_0 \in [1,\infty)$，将左端化为 $2(h(y) - \sqrt{m})$，其中 $h(y) = y^{-\beta-1}[(K+\sqrt{m})y - K]$。
2. **验证端点等号**：直接计算 $h(1) = (K+\sqrt{m}) - K = \sqrt{m}$，故 $r=0$ 处等号成立。
3. **单调性论证**：计算 $h'(y) = y^{-\beta-2}[(\beta+1)K - \beta(K+\sqrt{m})y]$；其中括号在 $y=1$ 处为零（利用 $\beta = K/\sqrt{m}$），斜率 $-\beta(K+\sqrt{m}) < 0$，故对所有 $y > 1$ 有 $h'(y) < 0$，即 $h$ 在 $[1,\infty)$ 严格递减，从而 $h(y) < \sqrt{m}$。
:::

:::proof-sketch{for=thm:main}
1. **反射耦合约化**：由引理 \ref{lem:rt-sde}，距离过程 $r_t = |X_t - X'_t|$ 满足一维 SDE，漂移有界于 $2K - mr_t$；将 $d$ 维问题约化为一维问题。
2. **Itô 公式 $+$ 超鞅不等式**：对停止过程 $r_{t\wedge\tau}$ 应用 Itô 公式得 $df(r_t) = [\cdot]\,dt + \text{鞅}$；由引理 \ref{lem:key}，漂移项满足 $\le -c^\star f(r_t)$；由 $f' \le 1$ 知随机积分为 $L^2$-鞅。
3. **Grönwall 引理**：取期望后得 $\frac{d}{dt}\mathbb{E}[f(r_{t\wedge\tau})] \le -c^\star \mathbb{E}[f(r_{t\wedge\tau})]$，由 Grönwall 引理立得指数衰减；再通过最优初始耦合的下确界转化为 $W_{1,f}$ 语言。
:::

:::proof-sketch{for=thm:ula}
1. **半群三角分解**：将一步误差分解为"连续流收缩"与"离散化偏差"两项：$W_{1,f}(\mu_{k+1},\pi) \le W_{1,f}(\mu_k P_h, \mu_k T_h) + W_{1,f}(\mu_k T_h, \pi T_h)$；第二项由定理 \ref{thm:main} 给出 $e^{-c^\star h}$ 收缩。
2. **Euler–Maruyama 一步强误差**：利用引理 \ref{lem:onestep-strong}，通过 Lipschitz 条件和 Grönwall 引理对 $\mathbb{E}[|X_h - \bar{X}_1|^2]$ 建立 $O(h^3)$ 强误差界；由 $f(r) \le r$ 转化为 $W_{1,f}$ 的 $O(\sqrt{h})$ 界。
3. **矩控制与迭代几何级数求和**：引理 \ref{lem:ula-moment} 给出 ULA 迭代的均匀二阶矩界；将一步误差关于 $k$ 求和得几何级数，收敛于加性偏差项 $C_1 L^2 \sqrt{M^\star+d}\,\sqrt{h}/c^\star$。
:::

:::proof-sketch{for=thm:poc}
1. **粒子差过程的 Itô 公式**：令 $\Delta^i_t = X^{i,N}_t - Y^i_t$，对 $f(|\Delta^i_t|)$ 应用 Itô 公式；利用有效势 $U^{\mathrm{eff}}_t$ 满足 A1–A3（关于 $t$ 一致），得到 $-c^\star$ 收缩漂移项加上经验均场波动项 $\mathcal{F}^i_t$。
2. **波动项的维数无关界**：将 $\mathcal{F}^i_t$ 分解为"经验波动"与"漂移修正"两部分；前者由 i.i.d. 有界随机变量的方差界给出 $\mathbb{E}[|\mathcal{F}^{i,\mathrm{fluct}}_t|] \le 2K/\sqrt{N-1}$（无维数因子）；后者由 $L_W$-Lipschitz 条件控制。
3. **Grönwall 闭合与均匀界**：通过 $|\Delta^i_t|^2$ 的 Itô 计算得到均匀二阶矩界，代入 $\mathcal{F}^{i,\mathrm{drift}}$ 估计，最终得到常系数 ODE $\phi'(t) \le -c^\star \phi(t) + C_2 K/\sqrt{N-1}$；由 $\phi(0)=0$ 和 Grönwall 引理直接得到关于 $t$ 一致的 $O(1/\sqrt{N})$ 界。
:::

## 数值实验 {#numerics}

论文第 10 节报告了五组数值实验，系统验证理论结果。**实验 E1** 在不同维数下固定 $m$ 并变化 $K$，通过模拟两条 Langevin 轨道并追踪耦合距离的经验收缩速率，与理论预测 $c^\star = m - K\sqrt{m}$ 进行比较；结果显示经验速率与理论值吻合良好，相对误差通常在 $5\%$ 以内。**实验 E2** 固定 $(m, K)$ 并将维数 $d$ 从 $1$ 变化至 $500$，验证收缩速率确实与维数无关（经验速率相对 $d$ 的曲线近乎水平）。**实验 E3** 验证 ULA 离散化偏差的 $O(\sqrt{h})$ 标度律，通过对数-对数回归确认斜率接近 $1/2$。**实验 E4** 将理论框架应用于贝叶斯逻辑回归后验——一个真实的非凸统计问题——验证反射耦合和理论速率在实际模型中的有效性。**实验 E5** 研究临界行为：随 $K \uparrow \sqrt{m}$，经验半衰期与理论预测的 $\Theta(\varepsilon^{-1})$（其中 $\varepsilon = \sqrt{m} - K$）一致，定量验证了命题 \ref{prop:critical} 中线性消失的结论。整体而言，数值实验覆盖了理论的所有主要方面，并通过可复现代码（`code/` 目录）加以支持。

## 关联工作 {#connections}

- [sr_p005](/papers/sr_p005)：若该项目研究离散 Langevin 或 MCMC 的收缩性，则与本文共享"反射耦合 $+$ 凹距离函数"的超鞅论证框架，以及 Euler–Maruyama 一步强误差对离散化偏差的控制技术。
- [sr_p001](/papers/sr_p001)：若涉及平均场或 McKean–Vlasov 方程，则与本文定理 \ref{thm:poc} 共享均匀时间传播混沌的 Grönwall 闭合机制，以及经验波动项的维数无关方差界。
- [mv_games](/papers/mv_games)：平均场博弈中的 McKean–Vlasov 动力学通常具有与本文相同的结构（强凸基础势 $+$ 有界相互作用），本文的显式收缩速率 $c^\star$ 可直接为均衡唯一性和收敛速率分析提供定量输入。
- [project7](/papers/project7)：若涉及 Wasserstein 梯度流或函数不等式（Poincaré、对数 Sobolev），则与本文共享"势函数分解 $U = U_0 + V$"的扰动框架，以及收缩速率与谱间隙之间的对应关系。
- [discrete_vs_rough](/papers/discrete_vs_rough)：若研究粗糙势或非光滑漂移下的离散化误差，则与本文第 6 节共享 ULA 的"连续流 $+$ 离散化偏差"分解方法及步长条件 $h \le m/(2L^2)$ 的来源。