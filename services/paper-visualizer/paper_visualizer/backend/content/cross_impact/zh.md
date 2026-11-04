---
paper_slug: cross_impact
lang: zh
sections:
  - id: context
    title: 背景与动机
  - id: objects
    title: 核心数学对象
  - id: main-results
    title: 主要结果
  - id: proofs
    title: 证明概要
  - id: numerics
    title: 数值实验
  - id: connections
    title: 关联论文
---

## 背景与动机 {#context}

在多资产市场中，大额订单的执行会移动价格——不仅影响被交易资产本身，还会波及其他资产，这一现象称为**交叉冲击（cross-impact）**。Bouchaud 等人提出的传播算子模型（propagator model）通过卷积核 $G(t,s)$ 刻画历史交易如何传播至当前价格：资产价格在时刻 $t$ 的扭曲量为 $D_t^u = \int_0^t G(t,s)\,u_s\,ds$。经济一致性要求模型排除**价格操纵**——即通过价格扭曲本身获利的往返策略（round-trip strategy）。Huberman–Stanzl 和 Gatheral–Schied–Slynko 的经典工作将无操纵条件归结为积分算子的**非负定性**。

对于单资产情形，无操纵理论已相当完善：幂律传播算子 $H(t) = c\,t^{-\beta}$（$\beta \in (0,\tfrac12)$）的无操纵条件仅为 $c \ge 0$。对于多资产情形，Abi Jaber、Neuman 和 Tuschmann 建立了矩阵值卷积核的充分条件，其推论覆盖了**因子化**情形 $H(t) = C\,\varphi(t)$——即所有资产对共享同一标量衰减函数 $\varphi$。然而，实证研究（Hey–Neuman–Tuschmann 等）持续发现不同资产对具有**不同的衰减指数** $\beta_{ij}$，因子化模型因此过于限制。

本文填补这一空白：对于**异质幂律交叉冲击核** $H_{ij}(t) = c_{ij}\,t^{-\beta_{ij}}$（$\beta_{ij} \in (0,\tfrac12)$），给出无操纵的**充要条件**。结果揭示出两个相互独立的结构约束：一是关于指数矩阵的**均值指数条件**（mean-exponent condition），二是关于系数矩阵的 **Gamma 加权正定性**。此外，论文还分析了正则化核（regularized kernel）的不对称必要性结构，以及参数空间边界处的退化行为，为多资产市场的模型校准和操纵检测提供了可操作的理论基础。

## 核心数学对象 {#objects}

**交易策略与价格扭曲。** 交易策略为 $u \in \mathcal{U} := L^2([0,T], \mathbb{R}^N)$，价格扭曲由 Volterra 核 $G(t,s) = \mathbf{1}_{t \ge s}\,H(t-s)$ 给出：
$$D_t^u = \int_0^t H(t-s)\,u_s\,ds.$$
非标准之处在于核是矩阵值的，且各分量可具有不同的奇异性指数。

**瞬态冲击成本。** 策略 $u$ 的瞬态冲击成本定义为
$$\mathcal{C}(u) := \int_0^T u_t^\top D_t^u\,dt = \int_0^T\!\int_0^T u_t^\top G(t,s)\,u_s\,ds\,dt.$$
这是交易者对抗自身价格冲击所付出的总成本；无操纵等价于对所有往返策略 $\mathcal{C}(u) \ge 0$。

**异质幂律核（核假设）。** 核的各分量为
$$H_{ij}(t) = c_{ij}\,t^{-\beta_{ij}}, \quad \beta_{ij} \in \left(0,\tfrac{1}{2}\right),$$
并满足对称性 $c_{ij}=c_{ji}$、$\beta_{ij}=\beta_{ji}$，以及非负自冲击 $c_{ii} \ge 0$。条件 $\beta_{ij} < \tfrac12$ 保证 $G \in L^2([0,T]^2)$；异质性 $\beta_{ij} \neq \beta_{kl}$ 使得因子化方法失效。

**Gamma 权重函数。** 定义
$$\gamma(\beta) := 2\,\Gamma(1-\beta)\sin\!\left(\frac{\pi\beta}{2}\right), \quad \beta \in (0,1).$$
此函数在 $(0,1)$ 上严格正，满足 $\gamma(\beta) \to 0^+$（$\beta \to 0^+$）和 $\gamma(\beta) \to +\infty$（$\beta \to 1^-$），且有展开式 $\gamma(\beta) = \pi\beta + O(\beta^2)$。它是幂律分布 $|t|^{-\beta}$ 的 Fourier 变换中出现的自然常数。

**Gamma 加权矩阵。** 定义
$$\widetilde{C} := \left[c_{ij}\,\gamma(\beta_{ij})\right]_{i,j=1}^N.$$
这是系数矩阵 $C = [c_{ij}]$ 与 Gamma 权重矩阵 $[\gamma(\beta_{ij})]$ 的 Schur（逐元素）乘积。其非负定性是无操纵的核心条件之一，非平凡之处在于权重 $\gamma(\beta_{ij})$ 依赖于指数，使得 $\widetilde{C} \ge 0$ 与 $C \ge 0$ 一般并不等价。

**谱矩阵。** 对 $\omega > 0$，定义
$$\widehat{H}(\omega) := \left[c_{ij}\,\gamma(\beta_{ij})\,|\omega|^{\beta_{ij}-1}\right]_{i,j}.$$
这是核 $H(|t|)$（视为 $\mathbb{R}$ 上的偶函数）的 Fourier 变换，由引理 [lem:FT] 给出。无操纵等价于对所有 $\omega > 0$ 均有 $\widehat{H}(\omega) \ge 0$（矩阵意义下）。

## 主要结果 {#main-results}

:::theorem{id=thm:main label="无操纵刻画定理（主定理）"}
在核假设（Assumption 2.4）下，以下三条等价：

**(i)** $G(t,s)=\mathbf{1}_{t\ge s}\,H(t-s)$ 对所有 $T>0$ 均排除价格操纵。

**(ii)** 谱矩阵 $\widehat{H}(\omega) = \left[c_{ij}\,\gamma(\beta_{ij})\,|\omega|^{\beta_{ij}-1}\right]_{i,j}$ 对所有 $\omega>0$ 均非负定。

**(iii)** 以下两个条件同时成立：
- **(a) 均值指数条件：** 对所有满足 $c_{ij}\neq 0$ 的 $(i,j)$，有 $\beta_{ij} = \dfrac{\beta_{ii}+\beta_{jj}}{2}$；
- **(b) Gamma 加权正定性：** $\widetilde{C} := \left[c_{ij}\,\gamma(\beta_{ij})\right]_{i,j}$ 非负定。
:::

**直觉解释：** 主定理将时域的无操纵条件完全转化为频域的矩阵正定性，再进一步分解为两个独立的结构约束。均值指数条件 (a) 是纯粹的**指数结构约束**：交叉冲击的衰减速率必须恰好是两个自冲击衰减速率的算术平均值。这一条件保证谱矩阵 $\widehat{H}(\omega)$ 可以对角分解为 $D(\omega)\,\widetilde{C}\,D(\omega)$，其中 $D(\omega) = \mathrm{diag}(|\omega|^{(b_i-1)/2})$ 是正对角矩阵。条件 (b) 则是**系数结构约束**：在指数结构正确的前提下，加权系数矩阵须正半定。两个条件缺一不可，且均为充要条件。

**为何令人惊讶：** 经典结果（如 Abi Jaber–Neuman–Tuschmann 的因子化推论）仅要求 $C \ge 0$；本定理揭示，一旦允许异质指数，**指数本身**（而非仅系数）就携带了无操纵的本质结构信息——即使系数矩阵 $C$ 正定，若指数不满足均值条件，操纵机会依然存在。

---

:::theorem{id=prop:reg_necessity label="正则化核的不对称必要性（命题）"}
设 $N=2$，$t_0>0$，$\beta_{11},\beta_{22}\in(0,1)$，$c_{11},c_{22}>0$。令 $\delta := 2\beta_{12}-\beta_{11}-\beta_{22}$。

**(i)** 若 $\delta < 0$ 且 $c_{12}\neq 0$，则 $G^{(t_0)}$ 对某个 $T>0$ 存在价格操纵。特别地，均值指数条件 $\delta=0$ 在 $\beta_{12} < (\beta_{11}+\beta_{22})/2$ 时是必要的。

**(ii)** 若 $\delta \ge 0$，均值指数条件**不是**必要的：正则化核在以下条件下对所有 $T>0$ 排除操纵：
$$c_{12}^2 \;\le\; t_0^{\delta}\, \frac{\Gamma(1-\beta_{11})\,\Gamma(1-\beta_{22})}{\Gamma(1-\beta_{12})^2}.$$

**(iii)** 当 $t_0\to 0^+$（$\delta>0$）时，上式右端趋于零，恢复奇异核的必要性。
:::

**直觉解释：** 正则化核 $H_{ij}^{(t_0)}(t) = c_{ij}(t+t_0)^{-\beta_{ij}}$ 的 Fourier 变换不再是纯幂律，而涉及不完全 Gamma 函数，低频行为与奇异核相同（$\sim \gamma(\beta)\omega^{\beta-1}$），高频行为则快速衰减（$O(\omega^{-2})$）。当交叉冲击衰减**快于**均值（$\delta < 0$）时，谱比率 $R(\omega)$ 在低频趋于零，正则化无法补救，均值指数条件仍是必要的。当交叉冲击衰减**慢于**均值（$\delta > 0$）时，低频谱比率趋于无穷，约束来自高频，存在一个依赖 $t_0$ 的容许区域。

**为何令人惊讶：** 这是首个在必要性层面区分正则化核与奇异核的结果，揭示了不完全 Gamma 函数谱结构中的**方向不对称性**——同样是偏离均值指数条件，偏离方向不同导致截然不同的操纵可能性。

---

:::theorem{id=prop:singular label="奇异 $\widetilde{C}$ 与零成本组合（命题）"}
假设均值指数条件成立，$\widetilde{C} \ge 0$ 且存在 $v \neq 0$ 使得 $\widetilde{C}v = 0$。

**(i) 同质指数**（$b_1=\cdots=b_N=\beta$）：组合方向 $v$ 的瞬态冲击成本恒为零。任何满足 $\int_0^T f(t)\,dt=0$ 的往返策略 $u(t)=f(t)\,v$ 均有 $\mathcal{C}(u)=0$。

**(ii) 异质指数**（某些 $b_i \neq b_j$）：策略 $u(t)=f(t)\,v$ 的成本仅对特定频率匹配的交易模式为零，对一般往返策略有 $\mathcal{C}(u)>0$。
:::

**直觉解释：** 在正半定边界上，零向量 $v$ 的经济含义取决于指数是否同质。同质情形下，谱矩阵 $\widehat{H}(\omega) = \gamma(\beta)|\omega|^{\beta-1}C$ 中 $Cv=0$ 对所有频率成立，整个子空间的往返交易成本为零，构成市场完整性的严重隐患。异质情形下，对角矩阵 $D(\omega)$ 随频率旋转零向量方向，使得零成本条件在几乎所有频率处均不满足。

**为何令人惊讶：** 异质指数在正半定边界处提供了一种**结构性安全边际**——即使模型处于无操纵条件的临界状态，异质性也能防止出现整个方向上的零成本往返交易，这一保护机制在同质模型中完全缺失。

---

:::theorem{id=prop:largeN label="大 $N$ 缩放（命题）"}
对于 $N$ 个资产、单位自冲击（$c_{ii}=1$）、均匀指数 $\beta$、均匀交叉冲击 $c_{ij}=c$（$i\neq j$）的情形，矩阵 $\widetilde{C} = \gamma(\beta)\left[(1-c)I + c\,\mathbf{1}\mathbf{1}^\top\right]$ 非负定当且仅当
$$-\frac{1}{N-1} \;\le\; c \;\le\; 1.$$
:::

**直觉解释：** 正交叉冲击的上界 $c \le 1$ 与资产数量 $N$ 无关，可以任意扩展；而负交叉冲击的下界 $|c| \le 1/(N-1) \to 0$ 随 $N$ 增大而趋于零。这一不对称性源于矩阵 $\mathbf{1}\mathbf{1}^\top$ 的最小特征值为零（对应均匀方向），而最大特征值为 $N$（对应均匀方向），使得负相关性在大市场中受到严格限制。

**为何令人惊讶：** 正负交叉冲击在大市场中的**可扩展性完全不对称**：正交叉冲击是可扩展的（$c_{\max}=1$ 与 $N$ 无关），而负交叉冲击必须以 $O(1/(N-1))$ 的速率趋于零，这对多资产对冲策略的设计有直接约束。

## 证明概要 {#proofs}

:::proof-sketch{for=thm:main}
1. **Volterra 核到卷积形式的对称化。** 利用核的对称性 $H(t)=H(t)^\top$，将因果二次型 $\int_0^T\!\int_0^t u_t^\top H(t-s)u_s\,ds\,dt$ 对称化为 $\frac{1}{2}\int_\mathbb{R}\!\int_\mathbb{R} f(t)^\top H(|t-s|)f(s)\,ds\,dt$，从而将有限区间上的非负定性问题转化为全实轴上偶函数卷积核的非负定性问题。

2. **矩阵值 Bochner–Schwartz 定理（频域刻画）。** 应用矩阵值 Bochner–Schwartz 引理（引理 [lem:BS]），将时域非负定性等价于谱矩阵 $\widehat{H}(\omega) = [c_{ij}\gamma(\beta_{ij})|\omega|^{\beta_{ij}-1}]$ 对几乎所有 $\omega > 0$ 的非负定性；关键工具是引理 [lem:FT]：$\widehat{|t|^{-\beta}}(\omega) = \gamma(\beta)|\omega|^{\beta-1}$。

3. **$2\times 2$ 主子式的指数分析（必要性）。** 对任意 $i\neq j$，考察 $\{i,j\}$ 主子矩阵的行列式：令 $\lambda = \ln\omega$，行列式中出现因子 $e^{\delta\lambda}$（$\delta = 2\beta_{ij}-\beta_{ii}-\beta_{jj}$）。若 $\delta \neq 0$，则当 $|\lambda| \to \infty$ 时行列式趋于 $-\infty$，故 $\delta = 0$ 是必要的，即均值指数条件。

4. **对角分解（充分性）。** 在均值指数条件下，令 $D(\omega) = \mathrm{diag}(|\omega|^{(b_i-1)/2})$，则谱矩阵分解为 $\widehat{H}(\omega) = D(\omega)\,\widetilde{C}\,D(\omega)$。由于 $D(\omega)$ 正定且 $\widetilde{C} \ge 0$，合同变换保持非负定性，充分性得证。

5. **一般 $N$ 的必要性归约。** 对一般 $N$，若 $\widehat{H}(\omega) \ge 0$ 对所有 $\omega > 0$ 成立，则其每个 $2\times 2$ 主子矩阵亦非负定，由步骤 3 得均值指数条件对所有对 $(i,j)$ 成立；再由步骤 4 的分解和 $D(\omega)$ 的可逆性得 $\widetilde{C} \ge 0$。
:::

:::proof-sketch{for=prop:reg_necessity}
1. **正则化核的 Fourier 变换精确表示。** 通过换元 $u = t+t_0$ 和围道旋转，将 $\int_0^\infty (t+t_0)^{-\beta}e^{i\omega t}\,dt$ 表示为 $e^{-it_0\omega}(-i\omega)^{\beta-1}\Gamma(1-\beta,-it_0\omega)$，其中 $\Gamma(s,z)$ 为上不完全 Gamma 函数。

2. **低频与高频渐近分析。** 利用 $\omega \to 0^+$ 时 $\Gamma(1-\beta,-it_0\omega) \to \Gamma(1-\beta)$ 得低频行为 $\sim \gamma(\beta)\omega^{\beta-1}$（与奇异核相同）；利用 DLMF 渐近公式 $\Gamma(a,z) \sim z^{a-1}e^{-z}$（$|z|\to\infty$）得高频行为 $O(\omega^{-2})$。

3. **谱比率 $R(\omega)$ 的单调性分析。** 定义谱比率 $R(\omega) = \widehat{\varphi}_{b_1}^{(t_0)}(\omega)\widehat{\varphi}_{b_2}^{(t_0)}(\omega)/[\widehat{\varphi}_{\beta_{12}}^{(t_0)}(\omega)]^2$；当 $\delta < 0$ 时低频 $R(\omega) \sim \mathrm{const}\cdot\omega^{|\delta|} \to 0$，故任意 $c_{12}\neq 0$ 在低频处违反正定性；当 $\delta \ge 0$ 时 $R(\omega)$ 在低频趋于 $+\infty$，约束来自高频极限 $R(\infty) = (\beta_{11}\beta_{22}/\beta_{12}^2)t_0^\delta$，给出容许区域 \eqref{eq:reg_bound}。
:::

:::proof-sketch{for=prop:singular}
1. **同质情形的谱零化。** 同质指数下 $\widehat{H}(\omega) = \gamma(\beta)|\omega|^{\beta-1}C$；由 $\widetilde{C}v = \gamma(\beta)Cv = 0$ 得 $v^\top\widehat{H}(\omega)v = 0$ 对所有 $\omega > 0$ 成立；由 Parseval 定理得时域成本为零。

2. **异质情形的频率旋转论证。** 异质指数下分解 $\widehat{H}(\omega) = D(\omega)\widetilde{C}D(\omega)$；$v^\top\widehat{H}(\omega)v = 0$ 等价于 $D(\omega)v$ 落入 $\widetilde{C}$ 的零空间；由于 $D(\omega)v$ 的方向随 $\omega$ 变化（各分量以不同幂次缩放），此条件仅在有限个 $\omega$ 处成立，故对一般 $f$ 有 $\mathcal{C}(u) > 0$。
:::

:::proof-sketch{for=prop:largeN}
1. **特征值计算。** 矩阵 $(1-c)I + c\mathbf{1}\mathbf{1}^\top$ 有两个不同特征值：$1-c$（重数 $N-1$，对应与 $\mathbf{1}$ 正交的方向）和 $1+(N-1)c$（重数 $1$，对应均匀方向 $\mathbf{1}$）。

2. **非负定性条件。** 非负定性等价于两个特征值均非负：$1-c \ge 0$ 给出 $c \le 1$；$1+(N-1)c \ge 0$ 给出 $c \ge -1/(N-1)$，合并得 $-1/(N-1) \le c \le 1$。
:::

## 数值实验 {#numerics}

数值实验分为五个部分，系统验证了主定理及其推论的各个方面。

**两资产奇异核（第 8.1 节）。** 对 $N=2$，通过扫描参数空间 $(c_{12}, \beta_{12})$ 绘制无操纵容许区域，验证均值指数条件的必要性：当 $\beta_{12} \neq (\beta_{11}+\beta_{22})/2$ 时，无论 $c_{12}$ 多小（只要非零），均存在操纵机会；容许区域的边界精确对应 $\widetilde{C}$ 的最小特征值为零的曲线。三资产情形（第 8.2 节）验证了一般 $N$ 下主定理的正确性，所有 $2\times 2$ 主子矩阵的均值指数条件均需同时满足。

**参数敏感性（第 8.3 节）。** 对自冲击指数 $b_i$ 的敏感性分析（表格 `tab:sensitivity_beta`）表明：对于实证典型值 $b_i \in [0.2, 0.5]$，奇异核的 $\widetilde{C} \ge 0$ 边界与正则化核的谱边界之差不超过 $1\%$，验证了推论 [cor:regularised] 的近似充分性。大 $N$ 缩放实验（第 8.3.2 节）数值确认了命题 [prop:largeN] 的界 $-1/(N-1) \le c \le 1$，并展示了负交叉冲击容许范围随 $N$ 增大而线性收缩的现象。

**正则化核的容许区域（第 8.4–8.5 节）。** 对 $N=2$，固定 $\delta > 0$，数值计算谱比率 $R(\omega)$ 的全局最小值，验证了命题 [prop:reg_necessity](ii) 中容许区域 \eqref{eq:reg_bound} 的精确性；$t_0$ 依赖性实验（第 8.5 节）展示了容许区域随 $t_0 \to 0^+$ 单调收缩至零的过程，定量验证了 $t_0^\delta$ 的幂律收缩速率，与不完全 Gamma 函数的高频渐近分析完全吻合。

## 关联论文 {#connections}

- [discrete_vs_rough](/papers/discrete_vs_rough)：共享幂律传播算子的谱分析框架；离散时间与连续时间无操纵条件的对应关系，以及 $\beta \approx 0.5$ 边界情形的处理方式。

- [mv_games](/papers/mv_games)：共享多资产市场冲击模型的基础设定；均衡策略的存在性依赖于冲击核的非负定性，本文的充要条件直接为均衡分析提供可验证的参数约束。

- [var_ratio](/papers/var_ratio)：共享幂律核的 Fourier 分析工具，特别是分布意义下 $|t|^{-\beta}$ 的 Fourier 变换公式（引理 [lem:FT]）及其在方差比统计量渐近理论中的应用。