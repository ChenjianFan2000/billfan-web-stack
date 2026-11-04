---
paper_slug: project7
lang: zh
sections:
  - id: context
    title: 背景与动机
  - id: objects
    title: 关键数学对象
  - id: main-results
    title: 主要定理
  - id: proofs
    title: 证明思路
  - id: numerics
    title: 数值验证
  - id: connections
    title: 与相关工作的联系
---

## 背景与动机 {#context}

储备支持型稳定币（reserve-backed stablecoin）通过持有抵押品并承诺1:1赎回来维持与美元的挂钩。以USDC和USDT为代表，此类稳定币的总市值已超3000亿美元，日结算量超过Visa，在加密市场中扮演着类似货币市场基金的角色。尽管有储备支撑，稳定币仍会周期性地发生"脱锚"（depeg）事件——2023年3月，硅谷银行倒闭导致USDC短暂跌至0.878美元；2022年5月，USDT在TerraUSD崩溃期间跌至0.953美元。这类事件提出了一个数学上精确的问题：**在小噪声极限下，储备支持型稳定币在给定时间窗口内脱锚的概率是多少？**

经典的Freidlin-Wentzell（FW）大偏差理论为此提供了自然框架：在噪声强度 $\varepsilon \to 0$ 时，通过速率函数 $I(T,\lambda)$ 精确刻画脱锚概率的指数衰减速率，以及沿"最优路径"（instanton）的精确前置因子（Eyring-Kramers预因子）。对于最简单的"线性流出"模型（常数漂移、常数波动率），速率函数是初等二次型，脱锚概率可化归为经典反正态分布首达时密度。

然而，当稳定币设计的确定性极限在某临界赎回压力 $\lambda_c$ 处发生**鞍结分岔**（saddle-node bifurcation）时，问题变得深刻：随着控制参数趋近 $\lambda_c$，激活势垒以 $(\lambda_c-\lambda)^{3/2}$ 的速率消失——这是鞍结逃逸的**普适3/2临界指数**，在统计物理文献中早已确立，但此前从未被引入金融数学。恰在临界点 $\lambda = \lambda_c$ 处，Eyring-Kramers公式退化（前置因子发散、指数趋零），正确的渐近由2021年Hathcock-Sethna利用重整化群方法推导的**Airy标度函数** $\mathcal{T}_{HS}(\eta)$ 给出，它在亚稳态、临界态与超临界态三个区间统一插值。本文的核心贡献在于：将这一物理学结果严格移植到随机金融稳定币模型，建立精确误差估计，并推导出若干新的特殊函数恒等式。

## 关键数学对象 {#objects}

**1. 储备过程 $V_t^\varepsilon$（Reserve SDE）**

$$\d V_t^\varepsilon = b(V_t^\varepsilon;\,\lambda)\,\d t + \varepsilon\,\sigma(V_t^\varepsilon)\,\d W_t,\qquad V_0^\varepsilon = V_0,$$

其中 $\lambda \geq 0$ 为赎回压力，$\varepsilon > 0$ 为小噪声参数，$b$ 编码了发行方的设计机制（套利反馈、赎回响应等）。脱锚时刻为 $\tau_\varepsilon = \inf\{t \geq 0 : V_t^\varepsilon \leq p^*L\}$，其中 $p^* \in (0,1]$ 为锚定阈值比率，$L$ 为固定负债总额。非平凡之处在于：$b$ 对 $\lambda$ 的依赖决定了脱锚动力学属于哪种分岔类型。

**2. Freidlin-Wentzell作用泛函 $S_T(\phi;\lambda)$**

$$S_T(\phi;\lambda) = \frac{1}{2}\int_0^T \frac{\bigl(\dot\phi(t) - b(\phi(t);\lambda)\bigr)^2}{\sigma(\phi(t))^2}\,\d t,$$

定义在路径空间 $C([0,T],\mathbb{R})$ 上。速率函数 $I(T,\lambda) = \inf_{\phi \in \mathcal{A}_T} S_T(\phi;\lambda)$，其中 $\mathcal{A}_T$ 是所有在 $[0,T]$ 内至少触碰脱锚边界一次的路径集合。最优路径（instanton）的作用量等于速率函数，几何上对应"花费最小代价"到达脱锚集的轨迹。

**3. 鞍结分岔假设下的临界参数 $(v_*, \lambda_c, A, B)$**

在 $\Cref{assump:saddle}$ 下，漂移在 $(v_*, \lambda_c)$ 附近满足局部正规形展开：

$$b(v_* + u;\, \lambda_c - \nu) = A\nu - Bu^2 + R(u,\nu),\qquad |R| \leq C(|u|^3+\nu^2+u^2|\nu|),$$

其中 $A,B>0$。常数 $A=-\partial_\lambda b(v_*;\lambda_c)$（赎回压力对漂移的灵敏度）和 $B = -\frac{1}{2}\partial_v^2 b(v_*;\lambda_c)$（曲率）共同决定了3/2指数的系数及Eyring-Kramers预因子中的 $\sqrt{A}$ 因子（此因子在前期草稿中缺失，经SymPy验证才得以修正）。

**4. Hathcock-Sethna Airy标度函数 $\mathcal{T}_{HS}(\eta)$**

$$\mathcal{T}_{HS}(\eta) = 2^{1/3}\pi^2\Bigl[\operatorname{Ai}^2(2^{2/3}\eta) + \operatorname{Bi}^2(2^{2/3}\eta)\Bigr],$$

其中 $\operatorname{Ai},\operatorname{Bi}$ 为第一、二类Airy函数，$\eta$ 为无量纲临界参数（见下方定理4的重标度公式）。这是连接亚稳态Eyring-Kramers渐近（$\eta\to+\infty$）、临界有限值（$\eta=0$，$\mathcal{T}_{HS}(0)\approx6.27$）与超临界确定性穿越时间（$\eta\to-\infty$）的统一公式。非平凡之处在于：Airy函数出现在首达时问题中，而非量子力学，源于鞍结正规形SDE的谱分析。

**5. 有限边界Hathcock-Sethna函数 $\mathcal{T}_+(\eta,\chi_+)$**

$$\mathcal{T}_+(\eta,\chi_+) := 2\int_{\chi_+}^\infty \d y\int_{-\infty}^y \d z\,\exp\!\bigl(2\eta(y-z) - \tfrac{2}{3}(y^3-z^3)\bigr),$$

它是规范鞍结SDE $\d y = (\eta - y^2)\d\tau + \d W_\tau$ 从 $y_0=+\infty$ 出发、以 $\chi_+$ 为吸收边界的平均首达时的精确表达（相差指数小修正项）。$\chi_+\to-\infty$ 时趋向 $\mathcal{T}_{HS}(\eta)$。本文将此双重积分化为精确一维积分，并给出新的Airy平方积分恒等式。

**6. Pontryagin均值首达时公式**

对非退化一维扩散，从 $V_0 > p^*L$ 出发、以 $p^*L$ 为吸收边界的均值首达时为：

$$\mathbb{E}[\tau_\varepsilon] = \int_{p^*L}^{V_0}\frac{2}{\varepsilon^2\sigma(y)^2}\,e^{\Phi_\varepsilon(y)}\int_y^{+\infty}e^{-\Phi_\varepsilon(z)}\,\d z\,\d y,$$

其中 $\Phi_\varepsilon(v) = -\int_{v_*}^v \frac{2b(v';\lambda)}{(\varepsilon\sigma(v'))^2}\d v'$。全文证明的核心技术步骤是将此公式在 $\varepsilon\to0$ 下局部化并重标度，化为 $\mathcal{T}_{HS}$ 的计算。

## 主要定理 {#main-results}

:::theorem{id=thm:LDP label="定理（FW大偏差原理，第3节）"}
在假设H1-H4（Assumption 3.1）下，脱锚时刻 $\tau_\varepsilon = \inf\{t\geq 0: V_t^\varepsilon \leq p^*L\}$ 满足

$$\lim_{\varepsilon\to0^+} -\varepsilon^2\log\mathbb{P}(\tau_\varepsilon \leq T) = I(T,\lambda) := \inf_{\phi\in\mathcal{A}_T} S_T(\phi;\lambda),$$

其中Freidlin-Wentzell作用泛函为

$$S_T(\phi;\lambda) = \frac{1}{2}\int_0^T \frac{(\dot\phi(t)-b(\phi(t);\lambda))^2}{\sigma(\phi(t))^2}\,\d t,$$

$\mathcal{A}_T = \{\phi\in C([0,T],\mathbb{R}): \phi(0)=V_0,\ \exists\,t\in[0,T]\ \text{使得}\ \phi(t)\leq p^*L\}$。
:::

该定理将稳定币脱锚概率的指数衰减精确化为一个变分问题：速率函数 $I(T,\lambda)$ 等于使系统在 $[0,T]$ 内触碰脱锚边界的最优路径（instanton）所需的"最小代价"。当 $I>0$ 时，脱锚是指数罕见事件；当 $I=0$ 时（超临界），脱锚以概率1发生。定理的前提是温和正则性条件和漂移在边界处的非特征条件（$b(p^*L;\lambda)>0$），确保边界可达性分析有效。

**为何令人惊讶：** 大偏差框架将一个复杂的随机首达时问题完全化归为确定性变分问题——脱锚路径的"形状"（instanton的轨迹）完全由速率函数的极值问题决定，而与噪声的具体分布（高斯与否）无关，只要满足非退化性条件即可。

---

:::theorem{id=thm:linear label="定理（线性流出模型，第4节）"}
对SDE $\d V_t^\varepsilon = -\lambda\,\d t + \varepsilon\sigma_0\,\d W_t$，设 $a = V_0 - p^*L > 0$，$\lambda_c = a/T$：

1. 对 $\lambda \in [0,\lambda_c)$（亚临界），

$$\lim_{\varepsilon\to0^+} -\varepsilon^2\log\mathbb{P}(\tau_\varepsilon\leq T) = \frac{T(\lambda_c-\lambda)^2}{2\sigma_0^2}.$$

2. 精确Eyring-Kramers预因子：

$$\mathbb{P}(\tau_\varepsilon\leq T) = \frac{2\lambda_c\,\varepsilon\sigma_0}{\sqrt{2\pi T}\,(\lambda_c^2-\lambda^2)}\exp\!\Bigl(-\frac{T(\lambda_c-\lambda)^2}{2\varepsilon^2\sigma_0^2}\Bigr)(1+O(\varepsilon^2)).$$

3. 在 $\lambda=\lambda_c$ 处（临界）：$\lim_{\varepsilon\to0^+}\mathbb{P}(\tau_\varepsilon\leq T) = 1/2$。

4. 对 $\lambda>\lambda_c$（超临界）：$\lim_{\varepsilon\to0^+}\mathbb{P}(\tau_\varepsilon\leq T) = 1$（指数收敛）。
:::

这个定理给出了最简单模型的完整三区间图景。速率函数 $I = T(\lambda_c-\lambda)^2/(2\sigma_0^2)$ 是关于"超出临界值的距离"的二次型，临界点处概率精确为1/2——噪声使系统"恰好处于临界线上"。Eyring-Kramers预因子中出现的 $\lambda_c^2-\lambda^2 = (\lambda_c-\lambda)(\lambda_c+\lambda)$ 反映了两端贡献的非对称性。

**为何令人惊讶：** 临界处 $\mathbb{P}\to1/2$ 是一个精确、模型无关的结果：它直接来自反正态分布首达时的对称性，而非近似。

---

:::theorem{id=thm:saddle label="定理（鞍结节普适3/2指数与Eyring-Kramers预因子，第5节）"}
设假设H1-H4（Assumption 3.1）与鞍结假设（Assumption 5.1）成立。

**(i) 临界渐近。** 当 $\lambda\to\lambda_c^-$ 时，

$$I(T,\lambda) = \frac{8\,A^{3/2}}{3\sqrt{B}\,\sigma(v_*)^2}\,(\lambda_c-\lambda)^{3/2}\,(1+o(1)),$$

条件为 $T > T_{\min}(\lambda) = O((\lambda_c-\lambda)^{-1/2}\log(1/(\lambda_c-\lambda)))$。

**(ii) Eyring-Kramers预因子（远离临界）。** 对 $\lambda_c-\lambda\geq c_0>0$，

$$\mathbb{E}[\tau_\varepsilon] = \frac{\pi}{\sqrt{AB(\lambda_c-\lambda)}}\exp\!\Bigl(\frac{8A^{3/2}(\lambda_c-\lambda)^{3/2}}{3\sqrt{B}\,\sigma(v_*)^2\,\varepsilon^2}\Bigr)(1+O(\varepsilon)).$$
:::

这是本文的核心代数结果。速率函数以 $(\lambda_c-\lambda)^{3/2}$ 趋于零（而非线性模型的 $(\lambda_c-\lambda)^2$），揭示了鞍结分岔处势垒消失的普适速率。预因子 $\pi/\sqrt{AB(\lambda_c-\lambda)}$ 中的 $\sqrt{A}$ 因子（来自Berglund 2013鞍点退出公式的规范转化）在初稿中被遗漏，经SymPy验证后得到修正，体现了精确前置因子计算中规范选取的细节性重要性。

**为何令人惊讶：** 3/2指数是普适的——无论具体的非线性函数 $f(v)$ 形式如何，只要满足鞍结正规形假设，指数就是3/2，系数由 $A, B, \sigma(v_*)$ 完全决定。这是金融数学中鲜见的普适性结果，此前仅在统计物理和化学动力学文献中出现。

---

:::theorem{id=thm:airy label="定理（普适Airy过渡，第6节）"}
在假设H1-H4与鞍结假设下，进一步设 $\sigma$ 在 $v_*$ 邻域 $C^2$，定义重标度常数

$$\alpha = (\varepsilon\sigma(v_*))^{2/3}B^{-1/3},\quad \beta = (\varepsilon\sigma(v_*))^{-2/3}B^{-2/3},\quad \eta = A\,B^{-1/3}(\lambda_c-\lambda)(\varepsilon\sigma(v_*))^{-4/3}.$$

设 $K\subset\mathbb{R}$ 为有界集。则当 $\varepsilon\to0^+$，沿满足 $\eta_n\in K$ 的序列 $(\varepsilon_n,\nu_n)$，均值脱锚时刻满足

$$\mathbb{E}[\tau_{\varepsilon_n}] = \beta_n\,\mathcal{T}_{HS}(\eta_n)\bigl(1 + O(\varepsilon_n^{2/3}\log(1/\varepsilon_n))\bigr),$$

对 $\eta\in K$ 一致成立，其中Hathcock-Sethna Airy标度函数为

$$\mathcal{T}_{HS}(\eta) = 2^{1/3}\pi^2\Bigl[\operatorname{Ai}^2(2^{2/3}\eta) + \operatorname{Bi}^2(2^{2/3}\eta)\Bigr].$$
:::

这是本文最深刻的结果。单一公式 $\beta\cdot\mathcal{T}_{HS}(\eta)$ 在三个区间统一插值：当 $\eta\gg1$ 时退化为 $\text{Eyring-Kramers}$ 预因子（对应定理3(ii)）；在 $\eta=0$ 处给出有限普适值 $\mathcal{T}_{HS}(0)\approx6.27$；当 $\eta\to-\infty$ 时渐近于 $\pi/\sqrt{|\eta|}$，即确定性穿越时间。误差率 $O(\varepsilon^{2/3}\log(1/\varepsilon))$ 是严格的，并在联合极限 $(\varepsilon,\nu)\to0$（$\eta$ 有界）意义下一致成立。

**为何令人惊讶：** Airy函数在金融首达时问题中的出现完全出乎意料——它源于鞍结正规形SDE的谱结构，而非量子散射或光学衍射问题。这是Airy标度函数首次被严格引入金融大偏差领域。

---

:::theorem{id=thm:airy-integral label="定理（$\mathcal{T}_{HS}$的一维积分表示与新Airy平方恒等式，第6.2节）"}
Hathcock-Sethna标度函数具有以下一维积分表示，对所有 $\eta\in\mathbb{R}$ 成立：

$$\mathcal{T}_{HS}(\eta) = \sqrt{2\pi}\int_0^\infty t^{-1/2}\,e^{2\eta t - t^3/6}\,\d t = 2^{1/3}\pi^2\Bigl[\operatorname{Ai}^2(2^{2/3}\eta) + \operatorname{Bi}^2(2^{2/3}\eta)\Bigr].$$

两个封闭形式相等给出Airy平方积分恒等式：

$$\int_0^\infty t^{-1/2}\,e^{2\eta t - t^3/6}\,\d t = 2^{-1/6}\,\pi^{3/2}\,\Bigl[\operatorname{Ai}^2(2^{2/3}\eta) + \operatorname{Bi}^2(2^{2/3}\eta)\Bigr],\quad \eta\in\mathbb{R}.$$
:::

这个定理有两重意义。其一，一维积分表示提供了计算 $\mathcal{T}_{HS}(\eta)$ 的初等替代路径，完全绕过Hathcock-Sethna原文中的Schrödinger谱分析；其二，Airy平方恒等式本身经检索未见于Abramowitz-Stegun、DLMF或Gradshteyn-Ryzhik积分表，是一个新的特殊函数结果。此外，令 $\eta\to-\infty$ 时通过Watson引理恢复 $\pi/\sqrt{|\eta|}$，令 $\eta\to+\infty$ 时通过Laplace法恢复Eyring-Kramers，三个区间的行为从同一积分自然涌现。

**为何令人惊讶：** 如此简洁的一维积分（被积函数仅含 $t^{-1/2}$ 和立方指数 $e^{2\eta t-t^3/6}$）能够精确等于Airy函数平方之和，这一联系在标准参考文献中从未被记录。

## 证明思路 {#proofs}

:::proof-sketch{for=thm:LDP}
1. **样本路径大偏差原理**：在紧集 $[p^*L-\delta, V_{\max}]$ 上，利用Dembo-Zeitouni《大偏差技术与应用》定理5.6.3，在Lipschitz条件（H1）和非退化扩散条件（H2）下建立 $\{V_\varepsilon\}$ 在 $C([0,T],\mathbb{R})$ 上的样本路径LDP，速率函数为 $S_T(\phi;\lambda)$。
2. **退出时LDP化归**：利用非特征边界条件（H3）（即 $b(p^*L;\lambda)>0$），由Freidlin-Wentzell《随机扰动动力系统》第4章定理4.2.1，将样本路径LDP转化为首达时LDP，得到 $\lim_{\varepsilon\to0^+}-\varepsilon^2\log\mathbb{P}(\tau_\varepsilon\leq T) = \inf_{\phi\in\mathcal{A}_T}S_T(\phi;\lambda)$。
3. **变分问题适定性**：利用作用泛函 $S_T$ 的下半连续性与路径集合 $\mathcal{A}_T$ 的闭性，确认下确界可达（或通过极小化序列取极限），得到速率函数 $I(T,\lambda)$ 的良定义性。
:::

:::proof-sketch{for=thm:linear}
1. **Cauchy-Schwarz变分**：对直线路径 $\phi(t) = V_0 - ct$（常数斜率），通过Cauchy-Schwarz不等式将作用泛函下界化为 $(\lambda t^* - a)^2/(2\sigma_0^2 t^*)$，对 $t^*\in(0,T]$ 最小化（函数在 $\lambda<\lambda_c$ 时于 $t^*=T$ 取最小），得到封闭速率函数 $I=T(\lambda_c-\lambda)^2/(2\sigma_0^2)$。
2. **精确首达时公式**：对算术布朗运动，利用Karatzas-Shreve经典反正态首达时公式写出 $\mathbb{P}(\tau_\varepsilon\leq T)$ 的精确表达，含两个正态分布累积函数 $\Phi(z_1)+e^{2\lambda a/(\varepsilon\sigma_0)^2}\Phi(z_2)$。
3. **Mills比渐近展开**：对两项分别应用Mill比 $\Phi(-x)\sim e^{-x^2/2}/(x\sqrt{2\pi})$（$x\to+\infty$），辅以指数恒等式（经SymPy验证），得到精确Eyring-Kramers预因子表达式，误差为 $O(\varepsilon^2)$。
:::

:::proof-sketch{for=thm:saddle}
1. **局部正规形重标度**：令 $u=v-v_*$，$\nu=\lambda_c-\lambda$，利用鞍结假设（H5），将漂移展开为 $b(v_*+u;\lambda)=A\nu-Bu^2+R(u,\nu)$，其中余项 $|R|\leq C(|u|^3+\nu^2+u^2|\nu|)$。
2. **最优逃逸路径的作用量计算**：对主导SDE $\d u=(A\nu-Bu^2)\d t+\varepsilon\sigma_*\d W$，最优逃逸路径满足时间反转方程 $\dot\phi=-b_{\text{normal}}(\phi)$，直接积分给出 $S_{\min}(\nu)=\frac{2}{\sigma_*^2}\int_{u_+}^{u_-}(A\nu-Bu^2)\d u = \frac{8A^{3/2}\nu^{3/2}}{3\sqrt{B}\sigma_*^2}$（经SymPy V2验证）。
3. **余项估计**：沿最优路径 $\phi^{(0)}$ 展开完整作用量 $S_T=S_T^{(0)}+\mathcal{E}_1+\mathcal{E}_2$，利用 $|b_{\text{normal}}|=O(\nu)$、$|R|=O(\nu^{3/2})$、instanton持续时间 $T_{\text{inst}}=O(\nu^{-1/2}\log(1/\nu))$，得 $|\mathcal{E}_1|=O(\nu^2\log(1/\nu))$，相对主项 $O(\nu^{3/2})$ 为高阶小量，证明(i)。
4. **Eyring-Kramers预因子（Berglund公式）**：对部分(ii)，引用Berglund 2013鞍点退出公式，将势函数 $U''(u_\pm)=2\sqrt{AB\nu}$ 代入 $\mathbb{E}[\tau_\varepsilon]\sim\frac{2\pi}{\sqrt{U''(u_+)|U''(u_-)|}}\exp(\ldots)$，并做规范转化（Berglund用 $\sqrt{2}\varepsilon$ 而本文用 $\varepsilon\sigma_*$，经SymPy V3-V4验证得预因子为 $\pi/\sqrt{AB\nu}$）。
:::

:::proof-sketch{for=thm:airy}
1. **Pontryagin公式局部化**：将均值首达时的Pontryagin双重积分分为"局部区域"（$|u|\leq\varepsilon^{1/3-\delta}$）和"非局部补集"两部分；对非局部部分，指数项 $e^{-\Phi_\varepsilon}$ 的立方主导使贡献阶为 $e^{-c\varepsilon^{-1-3\delta}}$，指数小可忽略。
2. **重标度化为规范鞍结SDE**：令 $u=