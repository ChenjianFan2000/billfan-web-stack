---
paper_slug: project8
lang: zh
sections:
  - id: context
    title: 背景与动机
  - id: objects
    title: 核心数学对象
  - id: main-results
    title: 主要定理
  - id: proofs
    title: 证明概要
  - id: numerics
    title: 数值验证
  - id: connections
    title: 关联工作
---

## 背景与动机 {#context}

**金融网络清算模型的随机矩阵视角。** Eisenberg–Noe（2001）清算模型是系统性风险分析的核心工具：给定 $N$ 家银行组成的互持负债网络，以及外部冲击向量，清算向量 $p^\ast_N$ 是一个单调映射的最小不动点，它决定了哪些银行违约以及违约缺口有多大。传统研究将网络视为固定的确定性图，分析其在给定拓扑下的清算结果。然而，在现实中，银行间敞口矩阵包含大量随机性，其统计特性比网络拓扑更为稳定且可观测。**本文的根本问题是**：当敞口矩阵 $L_N$ 从 i.i.d. 非负随机矩阵集成中采样时，聚合缺口 $\Sigma_N$ 的大 $N$ 波动服从什么分布？

**经典出发点：线性谱统计量的中心极限定理。** 对于样本协方差矩阵 $W_N$ 的线性谱统计量 $\mathcal{L}_g(W_N) = N^{-1}\sum_k g(\lambda_k)$，Bai–Yao（2005）和 Bai–Silverstein（2010）在检验函数 $g$ 解析的条件下证明了 $N$ 速率中心极限定理，方差由 Chebyshev 系数公式给出。这一结果是随机矩阵理论在金融中的标准工具箱，例如用于投资组合协方差矩阵的清洁。**但已有工作的局限在于**：（1）检验函数必须解析，而 Eisenberg–Noe 清算映射中的正部算子 $(\cdot)^+$ 在零点具有导数跳跃；（2）外部负债的异质性 $b_i$ 会打破矩阵的对称结构，令人担忧 $N$ 速率是否还能保持。

**本文填补的空白。** 本文建立了处理上述两个障碍的完整框架。核心贡献是：（i）将线性谱统计量 CLT 推广到分段 $C^1$ 检验函数（**清算线性谱统计量**，cLSS），正式论证导数跳跃点不产生额外方差贡献；（ii）发现一个**自对偶消去恒等式**（Lemma \ref{lem:self-dual}），它证明在异质性外部负债网络中 $N$ 速率依然保持；（iii）刻画临界窗口处 $N^{-1/2}$ 阶确定性偏移的精确常数，该常数由一个超越方程的正根唯一决定，具有普适性；（iv）为最大奇异值建立 Tracy–Widom GOE 边缘普适性，以及关于异质性具有去稳定效应的精确临界冲击公式。

---

## 核心数学对象 {#objects}

**1. 相对负债矩阵与清算映射。** 设 $L_{N,ij} = \xi_{ij}/N$（$i \neq j$，对角元为零），其中 $\xi_{ij}$ i.i.d. 非负，均值 $\mu$，方差 $\sigma^2$，四阶矩有限。银行 $i$ 的名义总负债为 $\bar{p}_{N,i} = \sum_j L_{N,ij} + b_{N,i}$，其中 $b_{N,i} > 0$ 是外部负债。**行次随机相对负债矩阵**为

$$\widetilde{\Pi}_{N,ij} = \frac{L_{N,ij}}{\bar{p}_{N,i}},$$

其行和严格小于 1（因为 $b_{N,i} > 0$）。Eisenberg–Noe 清算向量 $p^\ast_N$ 是单调映射 $\Phi(p) = \bar{p}_N \wedge (c_N - \eta_N + \widetilde{\Pi}_N^\top p)$ 的最小不动点。非平凡性在于：这是一个非光滑不动点问题，正部运算 $(\cdot)^+$ 和取极小 $\wedge$ 使得对矩阵参数的 Fréchet 导数在违约集边界上不连续。

**2. 聚合缺口与压力向量。** 违约集为 $\mathcal{D}_N = \{i : p^\ast_{N,i} < \bar{p}_{N,i}\}$，**聚合缺口**为

$$\Sigma_N = \frac{1}{N} \sum_{i \in \mathcal{D}_N} (\bar{p}_{N,i} - p^\ast_{N,i}).$$

令**压力向量** $\mathbf{s}_N = \bar{p}_N - c_N + \eta_N - \widetilde{\Pi}_N^\top \bar{p}_N$，则 $\Sigma_N = N^{-1} \mathbf{1}^\top (I - \widetilde{\Pi}_N^\top)^{-1} (\mathbf{s}_N)^+$。非平凡性在于：正部算子 $(\cdot)^+$ 的存在，使得 $\Sigma_N$ 不是矩阵项的线性泛函，需要精细的 Fréchet 展开才能将其化归为谱统计量。

**3. 中心化样本协方差矩阵与 Marchenko–Pastur 律。** 定义**中心化样本协方差矩阵**

$$\mathcal{W}_N^{\mathrm{ctr}} = N(L_N - \mathbb{E}L_N)(L_N - \mathbb{E}L_N)^\top.$$

在假设 (H1)、(H6) 下（$q=1$ 方阵情形），其经验谱分布几乎必然收敛到参数 $q=1$ 的 Marchenko–Pastur 分布 $\mu_{\mathrm{MP}}$，支撑为 $[0, 4\sigma^2]$。非平凡性在于：原始矩阵 $L_N$ 有秩-1 均值尖峰 $\mathbb{E}L_N$（奇异值约 $\mu$），远远分离于中心化矩阵的体谱边 $2\sigma/\sqrt{N}$，因此需仔细处理中心化操作。

**4. 清算线性谱统计量（cLSS）类。** 一个**cLSS 检验函数** $g: [0, 4\sigma^2] \to \mathbb{R}$ 是在 $[0, 4\sigma^2]$ 上连续、在有限个内部断点 $\mathcal{B} = \{c_1, \ldots, c_{m-1}\} \subset (0, 4\sigma^2)$ 两侧分段解析的函数，导数在断点处允许跳跃（但函数本身连续）。对应的 **cLSS** 为 $\mathcal{L}_g(W_N) = N^{-1} \sum_k g(\lambda_k(W_N))$。非平凡性在于：导数跳跃使得检验函数仅属于 Sobolev 类 $H^{3/2-\epsilon}$，但本文证明这仍在 Bai–Silverstein 方差公式的适用范围之内，无需额外的断点方差修正项。

**5. Perron 特征值与 LCP 抑制因子。** $\widetilde{\Pi}_N^\top$ 的 Perron 特征值（谱半径）的极限为

$$\rho_\infty^\ast = \mu \int \frac{d\mu_\beta(b)}{\mu + b} \in (0,1),$$

其中 $\mu_\beta$ 是外部负债的经验测度。**LCP 抑制因子** $1 + \theta_\infty(0)$ 由超越方程

$$\varphi(u) - u\Phi(-u) = \frac{\beta}{\mu} u$$

的唯一正根 $u^\ast = u^\ast(\beta/\mu)$ 决定，其中 $\varphi, \Phi$ 分别是标准正态的密度和分布函数。非平凡性在于：这个常数完全由无量纲比 $\beta/\mu$ 决定，与 $\sigma, \gamma$ 无关，体现了普适性；而其来源是一个低维 Schur 补不动点分析，而非拟合参数。

---

## 主要定理 {#main-results}

:::theorem{id="thm:thm51" label="定理 5.1：$\widetilde{\Pi}_N$ 的谱分解"}
在假设 (H1)、(H4)、(H6)、(H7) 下，当 $N \to \infty$ 时：

1. **(行和集中)** 以概率 $\geq 1 - 2N^{-10}$，
$$\max_{1 \leq i \leq N} \left|\bar{p}_{N,i} - (\mu + b_{N,i})\right| \leq C\sigma\sqrt{\frac{\log N}{N}},$$
其中 $C$ 为绝对常数。

2. **(Perron 集中)** $\widetilde{\Pi}_N^\top$ 的 Perron 特征值满足
$$\rho^\ast(\widetilde{\Pi}_N^\top) = \rho_\infty^\ast + O_p\!\left(\sqrt{\frac{\log N}{N}}\right), \quad \text{其中} \quad \rho_\infty^\ast = \mu \int \frac{d\mu_\beta(b)}{\mu + b} \in (0,1).$$

3. **(Neumann 收缩)** 以概率 $\geq 1 - 2N^{-10}$，对所有 $y \in \mathbb{R}^N$，
$$\|(I - \widetilde{\Pi}_N^\top)^{-1} y\|_\infty \leq (1 - \rho^\ast)^{-1} \|y\|_\infty \cdot (1 + o_p(1)).$$
:::

**直觉解释：** 定理 5.1 是整个证明体系的基础。第一部分说明每家银行的名义总负债 $\bar{p}_{N,i}$ 以极高概率集中在其确定性极限 $\mu + b_{N,i}$ 附近，误差仅为 $O(\sqrt{\log N/N})$。第二部分给出了行次随机矩阵 Perron 特征值的精确极限，它是一个关于 $\mu_\beta$ 的 Jensen 泛函，在异质情形下严格大于同质情形的值 $\mu/(\mu+\beta)$。第三部分保证了 Neumann 级数的收敛性，从而使清算核的 Lipschitz 界和 Fréchet 展开都有效。

**为什么令人惊讶：** Perron 特征值极限 $\rho_\infty^\ast$ 由 $\mu_\beta$ 的调和型 Jensen 泛函决定，而非简单地由均值 $\beta$ 决定。由 $b \mapsto 1/(\mu+b)$ 的严格凸性，异质情形的 $\rho_\infty^\ast$ 严格大于同质情形，这正是异质性去稳定效应的谱根源。

---

:::theorem{id="thm:thm52" label="定理 5.2：异质 $N$ 速率 CLT"}
在假设 (H1)、(H4)、(H5a)、(H6)、(H7) 下，存在显式确定性泛函
$$\Sigma_\infty(s;\mu,\sigma^2,\mu_\beta,\gamma) \in \mathbb{R}, \qquad V(s;\mu,\sigma^2,\mu_\beta,\gamma) \geq 0,$$
各自关于 $s$ 连续且分段光滑，使得对每个 $s \neq s_c$ 的超临界区间中，
$$\boxed{N\!\left(\Sigma_N - \Sigma_\infty(s)\right) \xrightarrow{\mathcal{L}} \mathcal{N}(0, V(s)).}$$
函数 $s \mapsto \Sigma_\infty(s)$ 连续非减，$s < s_c$ 时 $\Sigma_\infty(s) = 0$；当 $s \downarrow s_c$ 时，$\Sigma_\infty(s) = A_+(s-s_c) + O((s-s_c)^2)$，其中显式斜率 $A_+ > 0$。
:::

**直觉解释：** 这是本文的核心结果。在随机网络中，聚合缺口 $\Sigma_N$ 以 $N$ 速率（而非更慢的 $\sqrt{N}$ 速率）波动，这意味着网络的随机性被大量平均，使得波动远比单个银行的波动更小。序参量 $\Sigma_\infty(s)$ 在临界冲击 $s_c$ 处从零出发，以线性斜率 $A_+$ 增长，表现出连续相变特征。方差 $V(s)$ 由 cLSS 框架的 Chebyshev 系数公式给出，其中断点 $c(s)$ 对应清算激活阈值。

**为什么令人惊讶：** 在外部负债完全异质（$b_{N,i}$ 各不相同）的情形下，$N$ 速率 CLT 依然成立，这并不显然。关键是自对偶消去引理（引理 \ref{lem:self-dual}）：$\widetilde{\Pi}_{N,ij}$ 中的 $(\mu+b_i)^{-1}$ 权重与 $\bar{p}_{\infty,i} = \mu+b_i$ 精确抵消，使加权列和退化为 $\Delta L$ 的无权列和，从而恢复了 i.i.d. 结构所需的对称性。

---

:::theorem{id="thm:thm52star" label="定理 5.2*：临界窗口精化"}
在定理 5.2 的假设及同质基准 $b_{N,i} \equiv \beta$ 下，令 $s_c^{(0)} = \gamma - \beta$，$A_+ = (\mu+\beta)/\beta$，$\sigma_\tau = \sigma\sqrt{2}$。定义普适 LCP 抑制因子
$$1 + \theta_\infty(0) := \frac{\sqrt{2\pi}\,\beta}{\mu} \cdot u^\ast,$$
其中 $u^\ast = u^\ast(\beta/\mu)$ 是超越方程
$$\varphi(u) - u\,\Phi(-u) = \frac{\beta}{\mu}\,u$$
的唯一正根。则当 $N \to \infty$ 时：

1. **(导出的确定性偏移)**
$$\sqrt{N} \cdot \mathbb{E}[\Sigma_N(s_c^{(0)})] \longrightarrow c_0 = \sigma\sqrt{2} \cdot \frac{\mu+\beta}{\mu} \cdot u^\ast.$$

2. **(普适性)** 抑制因子 $1+\theta_\infty(0)$ 仅依赖无量纲比 $\beta/\mu$，与 $\sigma$ 和 $\gamma$ 无关。

3. **(Gauss 波动)**
$$N\!\left(\Sigma_N(s_c^{(0)}) - \frac{c_0}{\sqrt{N}}\right) \xrightarrow{\mathcal{L}} \mathcal{N}(0, V^\ast(0)).$$

4. **(临界指数)** 临界指数为 $\alpha = 1/2$，而非朴素 Tracy–Widom 边缘尺度 $\alpha = 2/3$。
:::

**直觉解释：** 在临界点 $s = s_c^{(0)}$ 处，压力向量的期望为零，但 Gauss 波动产生了 $O(N^{-1/2})$ 阶的正部期望，对应确定性偏移 $c_0/\sqrt{N}$。这个常数 $c_0$ 完全由一个一维超越方程的正根决定，无需任何拟合，且只依赖无量纲比 $\beta/\mu$。在去掉这个确定性偏移之后，剩余波动仍是 $N$ 速率 Gauss 分布。

**为什么令人惊讶：** 临界窗口的尺度是 $N^{-1/2}$，而非人们可能预期的 Tracy–Widom 边缘尺度 $N^{-2/3}$。这是因为决定 $\Sigma_N$ 波动的机制来自压力向量的中心极限定理（$N^{-1/2}$ 尺度），而非矩阵最大特征值的边缘涨落（$N^{-2/3}$ 尺度）。LCP 内生违约集选择产生的抑制因子 $1+\theta_\infty(0) \approx 0.433$ 在数值上被精确验证（相对误差 $0.66\%$）。

---

:::theorem{id="thm:thm53" label="定理 5.3：Tracy–Widom GOE 边缘普适性"}
在假设 (H1)、(H2)、(H4)、(H6)、(H7) 下，令 $\widetilde{L}_N = L_N - \mathbb{E}L_N$，$s_1(\sqrt{N}\widetilde{L}_N)$ 为 $\sqrt{N}\widetilde{L}_N$ 的最大奇异值。则
$$N^{2/3} \cdot \frac{s_1(\sqrt{N}\widetilde{L}_N) - 2\sigma}{2^{-2/3}\sigma} \xrightarrow{\mathcal{L}} F_1^{\mathrm{GOE}},$$
其中 $F_1^{\mathrm{GOE}}$ 为 Tracy–Widom GOE 分布。显式预因子 $2^{-2/3}\sigma$ 来自映射 $\lambda \mapsto \sqrt{\lambda}$ 在 $\lambda = 4\sigma^2$ 处的 Jacobian，应用于 Pillai–Yin 的特征值形式边缘涨落尺度 $2^{4/3}\sigma^2$（$q=1$ 情形）。
:::

**直觉解释：** 中心化负债矩阵 $\sqrt{N}\widetilde{L}_N$ 的最大奇异值在 Marchenko–Pastur 谱边 $2\sigma$ 处以 Tracy–Widom GOE 律涨落，这是随机矩阵理论中经典的边缘普适性结果。预因子 $2^{-2/3}\sigma$ 由奇异值与特征值之间的 Jacobian 变换精确给出，是完全可计算的。

**为什么令人惊讶：** 原始矩阵 $L_N$ 的对角元为零（而非 i.i.d.），且有秩-1 均值尖峰 $\mu\mathbf{1}\mathbf{1}^\top/N$（奇异值约 $\mu$）远离体谱边。需要用 Weyl 不等式和 Lee–Schnelli 鲁棒性定理来证明这两个修正（对角零修正和均值尖峰）均不影响 Tracy–Widom 极限，其中对角修正（算子范数 $O(N^{-1/2})$）作为标量偏移被吸收，均值尖峰（$\Theta(\sqrt{N})$ 量级）与体谱边完全分离。

---

:::theorem{id="thm:atom-dichotomy" label="定理：原子-连续两分性"}
令 $b_{\max} = \operatorname{ess\,sup}\mu_\beta$，$A_{\mathrm{top}} = \mu_\beta(\{b_{\max}\}) \in [0,1]$。在定理 5.2 的假设下，在 $s = s_c^{\mathrm{HET}} = \gamma - b_{\max}$ 处：

1. **(原子情形，$A_{\mathrm{top}} > 0$)** 定理 5.2* 的临界窗口分析适用，带修正确定性偏移
$$c_0^{\mathrm{HET}}(\mu_\beta) = A_{\mathrm{top}} \cdot A_+^{\mathrm{HET}} \cdot \sigma_\tau \varphi(0) \cdot (1 + \theta_\infty^{\mathrm{HET}}(0;\mu_\beta)),$$
其中 $A_+^{\mathrm{HET}} = 1/(1 - \rho_\infty^{\ast,\mathrm{HET}})$。

2. **(无原子情形，$A_{\mathrm{top}} = 0$)** $\mu_\beta$ 顶部的连续性将 HOM 情形的折点**抹平**：
$$\sqrt{N} \cdot \mathbb{E}[\Sigma_N(s_c^{\mathrm{HET}})] \longrightarrow 0,$$
且序参量 $s \mapsto \Sigma_\infty(s)$ 在 $s = s_c^{\mathrm{HET}}$ 处是 $C^1$ 的。$N^{-1}$ 速率 Gauss 波动（定理 5.2 的 CLT）仍然成立，但确定性 $N^{-1/2}$ 偏移消失。
:::

**直觉解释：** 异质外部负债的临界冲击由**最大外部负债 $b_{\max}$** 决定，而非均值 $\beta$，因为最高负债的银行最先违约。当 $\mu_\beta$ 在 $b_{\max}$ 处有正原子时，恰好有 $A_{\mathrm{top}} \cdot N$ 家银行同时处于违约边界，产生类 HOM 的 $\sqrt{N}$ 偏移；当 $\mu_\beta$ 在顶部连续时，没有银行同时精确处于边界，偏移消失，序参量变为 $C^1$。

**为什么令人惊讶：** 临界窗口的结构在 $\mu_\beta$ 于 $b_{\max}$ 处的原子质量上是**不连续**的——这是一个刀刃型现象。在实践中，连续分布的外部负债（无原子）可能导致实证研究者误以为 Eisenberg–Noe 网络在临界附近行为"光滑"，但这恰恰是因为 $\sqrt{N}$ 偏移已消失，而非因为没有相变。

---

:::theorem{id="thm:cLSS-CLT" label="定理：cLSS 中心极限定理（Chebyshev 方差公式）"}
在假设 (H1)、(H4)、(H5a)、(H6)、(H7) 下，令 $W_N = \mathcal{W}_N^{\mathrm{ctr}}$，设 $g:[0,4\sigma^2]\to\mathbb{R}$ 为带断点集 $\mathcal{B} = \{c_1,\ldots,c_{m-1}\} \subset (0,4\sigma^2)$ 的 cLSS 检验函数。则
$$N\!\left(\mathcal{L}_g(W_N) - \int g\,d\mu_{\mathrm{MP}}\right) \xrightarrow{\mathcal{L}} \mathcal{N}(0, V(g)),$$
其中
$$V(g) = 2\sum_{k=1}^\infty k\, a_k(g)^2,$$
$a_k(g)$ 为变量替换 $\theta \mapsto g(2\sigma^2(1-\cos\theta))$ 在 $[0,\pi]$ 上的 Chebyshev 系数：
$$a_k(g) = \frac{2}{\pi}\int_0^\pi g(2\sigma^2(1-\cos\theta))\cos(k\theta)\,d\theta, \quad k \geq 1.$$
当 $\mathcal{B} = \emptyset$ 时，退化为 Bai–Silverstein 解析检验函数 CLT。当 $\mathcal{B} \neq \emptyset$ 时，导数跳跃断点**不产生任何额外方差贡献**。
:::

**直觉解释：** 这是 cLSS 框架的技术核心。分段 $C^1$ 检验函数（Sobolev 类 $H^{3/2-\epsilon}$）处于 Sosoe–Wong 正则性阈值之内，因此标准 Bai–Silverstein 方差公式逐字继承，无需修正。方差完全由 Chebyshev 系数决定，而 Chebyshev 系数对导数跳跃点（级别 $H^{3/2-\epsilon}$）以平方可积方式衰减，不产生额外贡献。

**为什么令人惊讶：** 一个朴素的尺度论启发式推断认为，断点 $c_j$ 处导数跳跃 $|\Delta g'_j|$ 应贡献 $|\Delta g'_j|^2/\rho_{\mathrm{MP}}(c_j)$ 的附加方差（除以局部谱密度）。数值实验在 $N = 400$ 至 $1600$ 上明确否定了这一预测：方差关于 $c_j$ 的变化在 $\rho_{\mathrm{MP}}(c_j)$ 变化因子 9 时仅波动约 $7\%$，远小于 $1/\rho_{\mathrm{MP}}$ 预测的数量级差异。

---

:::theorem{id="cor:destab" label="推论：异质性去稳定——精确支撑级公式"}
固定均值外部负债 $\beta = \int b\,d\mu_\beta$，令 $b_{\max} = \operatorname{ess\,sup}\mu_\beta$。则
$$s_c^{\mathrm{HET}}(\mu_\beta) = \gamma - b_{\max} \leq \gamma - \beta = s_c^{\mathrm{HOM}}(\beta),$$
当且仅当 $\mu_\beta$ 不是点质量时严格不等。即，在保均值展开的情形下，外部负债分布的任意均值保持扩散**严格降低**聚合缺口正增