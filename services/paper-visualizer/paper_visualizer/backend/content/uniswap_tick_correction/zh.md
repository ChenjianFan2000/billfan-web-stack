---
paper_slug: uniswap_tick_correction
lang: zh
sections:
  - id: context
    title: 背景与动机
  - id: objects
    title: 核心数学对象
  - id: main-results
    title: 主要结论
  - id: proofs
    title: 证明思路
  - id: numerics
    title: 数值验证
  - id: connections
    title: 与相关工作的联系
---

## 背景与动机 {#context}

去中心化交易所 Uniswap v3 引入了**集中流动性**机制：流动性提供者（LP）将资本集中配置在自选价格区间 $[p_\ell, p_u]$ 内，只有在市价落于该区间时才赚取手续费。价格空间被离散化为以 $(1+\gamma)$ 为公比的等比数列——称为"Tick 格点"，其中 $\gamma$ 由费率档位决定，从稳定币池的 $0.01\%$ 到高波动品种的 $2.02\%$ 不等。集中流动性在提高资本效率的同时，也使 LP 的收益精确计算变得非平凡，因为手续费仅在价格穿越格点时才被触发。

**EGM 渐近框架**（Echenim, Gobet, Maurice 2025）是该领域的基础性工作：他们证明当 $\gamma \to 0$ 时，归一化手续费收入依概率收敛至对数价格过程局部时间的积分，并在几何布朗运动（GBM）下给出了显式期望收益公式。然而，在实际中 $\gamma$ 是由费率档位固定的有限值——对于 $1\%$ 档位，$\gamma \approx 0.02$；对于包含 20 个 Tick 的 LP 仓位，有限 $\gamma$ 效应可超过总手续费收入的 $1.5\%$。

本文填补了这一空白，系统研究**有限 Tick 修正**的三个层面：（1）一般常漂移扩散下一阶修正系数 $\kappa_1$ 的**非普适性**；（2）LP 区间边界与 Tick 格点不对齐时的**错位修正**；（3）考虑有限 Tick 效应后**最优区间宽度**的重新设计。核心发现是：EGM 框架中所谓"普适"的 $\kappa_1 = 1/4$ 不过是风险中性 GBM 漂移的一个精确代数特例，在物理测度或任意其他漂移下，该系数将发生本质性改变。

## 核心数学对象 {#objects}

**对数价格过程与漂移参数**

$$dX_t = \mu\,dt + \sigma\,dW_t, \qquad \alpha \coloneqq -\frac{2\mu}{\sigma^2}.$$

风险中性 GBM 对应 $\alpha = 1$（即 $\mu = -\sigma^2/2$），ABM 对应 $\alpha = 0$。参数 $\alpha$ 是统一描述各种测度的关键枢纽。

**Tick 格点与 LP 区间**

格点间距为 $h = \log(1+\gamma)$，格点为 $\{kh : k \in \mathbb{Z}\}$。LP 持仓覆盖以 $X_0 = 0$ 为中心的 $N$ 个 Tick，在对数价格空间中构成区间 $[-Nh/2,\, Nh/2]$。参数 $N$ 为偶数。

**尺度函数与穿越概率**

$$S(x) = \frac{1}{\alpha}\bigl(e^{\alpha x} - 1\bigr), \qquad p_\uparrow(h) = \frac{S(h)}{S(2h)} = \frac{1}{1+e^{\alpha h}} = \frac{1}{2} - \frac{\alpha h}{4} + O(h^2).$$

尺度函数将连续扩散的穿越概率化为纯代数表达式，是后续一切展开的基础。

**穿越权重函数 $f$ 与渐近权重函数 $g$**

$$f(x) \coloneqq e^{x/2}\,\mathbb{E}[L^x_T], \qquad g(x) \coloneqq e^{-3x/2}\,\mathbb{E}[L^x_T].$$

$f$ 出现在离散求和 $\Psi(\gamma)$ 中（手续费收入），$g$ 出现在 EGM 连续积分 $F_0^Y(\gamma)$ 中。两者之差 $f(x)-g(x) = (e^{x/2}-e^{-3x/2})\mathbb{E}[L^x_T]$ 在 $x=0$ 附近为 $2x\,\mathbb{E}[L^x_T]+O(x^2)$，是二阶修正项的来源。

**归一化预因子 $\psi(h)$**

$$c(h) \coloneqq \frac{\gamma}{h}\cdot\frac{e^{h/2}-1}{1+e^{\alpha h}}, \qquad \psi(h) \coloneqq \frac{4c(h)}{h}.$$

$c(h)$ 是每次穿越所对应的手续费系数，其关于 $h$ 的展开给出了"预因子修正"$\kappa_1^\psi$，是 $\kappa_1$ 的两个来源之一。

**期望归一化手续费与 EGM 渐近值**

$$\Psi(\gamma) = \frac{\phi}{1-\phi}\sum_{k=-N/2}^{N/2-1} c(h)\cdot e^{kh/2}\cdot\mathbb{E}[L^{kh}_T], \qquad F_0^Y(\gamma) = \frac{\phi}{4(1-\phi)}\int_{-Nh/2}^{Nh/2} e^{-3x/2}\,\mathbb{E}[L^x_T]\,dx.$$

本文的核心目标是精确计算比值 $\Psi(\gamma)/F_0^Y(\gamma)$ 关于 $\gamma$ 的展开式。

## 主要结论 {#main-results}

:::theorem{id=thm:general_kappa1 label="定理：一般一阶修正系数"}
设对数价格满足 $dX_t = \mu\,dt + \sigma\,dW_t$，$\mu \in \mathbb{R}$，$\sigma > 0$。对以 $X_0 = 0$ 为中心的 $N$-Tick LP 区间，期望归一化手续费满足
$$\frac{\Psi(\gamma)}{F_0^Y(\gamma)} = 1 + \kappa_1(\mu,\sigma)\,\gamma + O(\gamma^2),$$
其中
$$\kappa_1(\mu,\sigma) = \frac{1}{2} + \frac{\mu}{2\sigma^2}.$$
:::

该定理揭示：在常漂移扩散框架下，有限 Tick 效应的一阶修正系数是漂移率与波动率平方之比的线性函数。对于零漂移（ABM），$\kappa_1 = 1/2$；对于风险中性 GBM（$\mu = -\sigma^2/2$），$\kappa_1 = 1/4$；对于具有正期望收益的物理测度（$\mu = r - \sigma^2/2$，$r>0$），修正系数更大。该结果与 $\sigma$、$T$、$N$ 均无关，仅通过 $\mu/\sigma^2$ 依赖于漂移-波动率比。

**为何令人意外：** $\kappa_1 = 1/4$ 并非普适常数，而是仅在 $\mu = -\sigma^2/2$ 这一精确代数条件下成立；对于实际加密资产在物理测度下（如比特币 $r \approx 0.5$, $\sigma \approx 0.8$），修正系数约为风险中性值的 $2.5$ 倍。

---

:::theorem{id=cor:physical label="推论：物理测度下的修正"}
在物理测度下，期望对数收益漂移为 $\mu_P = r - \sigma^2/2$，则
$$\kappa_1^P = \frac{1}{2} + \frac{r - \sigma^2/2}{2\sigma^2} = \frac{1}{4} + \frac{r}{2\sigma^2}.$$
对于具有正期望收益（$r > 0$）的资产，一阶修正严格大于风险中性值 $1/4$。
:::

该推论对于使用 LP 优化工具的实践者至关重要：绝大多数 LP 分析工具基于风险中性 GBM，而 LP 的实际收益由物理测度决定。在物理测度下，有限 Tick 效应显著放大——对于以太坊（$r \approx 0.3$, $\sigma \approx 0.7$），$\kappa_1^P \approx 0.56$，是风险中性值的 $2.2$ 倍。

**为何令人意外：** 即使波动率参数相同，仅因测度变换（物理测度 vs. 风险中性测度），有限 Tick 修正就可相差 $2$—$3$ 倍，这在实操层面有直接的经济意义。

---

:::theorem{id=thm:main label="定理：GBM 下的完整二阶展开"}
在风险中性 GBM 下，$\sigma > 0$，$T > 0$，$N$ 为偶数，则
$$\frac{\Psi(\gamma)}{F_0^Y(\gamma)} = 1 + \frac{1}{4}\,\gamma - \frac{N^2}{6}\,\gamma^2 + O(\gamma^3).$$
特别地，$\kappa_1 = \lim_{\gamma\to 0}[\Psi/F_0^Y - 1]/\gamma = 1/4$，与 $\sigma$、$T$、$N$ 均无关。
:::

二阶项 $-N^2\gamma^2/6$ 量化了离散求和相对于 EGM 连续积分的系统性偏差：它随区间宽度 $N$ 的平方增长，并且始终为负。这意味着对于足够宽的区间，EGM 公式将**高估**手续费收入。由此得到一个符号转换阈值（推论）：

$$\gamma^* = \frac{3}{2N^2}.$$

当 $\gamma < \gamma^*$ 时 EGM 低估手续费；当 $\gamma > \gamma^*$ 时则高估。

**为何令人意外：** 即使一阶系数 $1/4$ 是"普适"的（在风险中性 GBM 下），二阶系数却明确依赖于 $N$，使宽区间的 LP 面临更大的系统误差。

---

:::theorem{id=thm:misaligned label="定理：错位边界修正"}
对于下边界分数偏移为 $\delta$、上边界为 $\delta'$ 的 LP 区间（各含 $N$ 个内部 Tick），手续费修正为
$$\frac{\Psi_{\mathrm{mis}}}{\Psi_{\mathrm{align}}} = 1 - \frac{1}{N}\Bigl[\frac{\delta}{2-\delta} + \frac{\delta'}{2-\delta'}\Bigr] + O(N^{-2}),$$
其中 $\Psi_{\mathrm{align}}$ 是对齐情形下的手续费（由定理 thm:main 给出）。修正项恒为非正，当且仅当 $\delta = \delta' = 0$（两端均对齐）时取等。
:::

该定理来自边界 Tick 效率函数 $R(\delta) = 2(1-\delta)/(2-\delta)$：边界 Tick 仅能赚取内部 Tick 手续费的 $R(\delta)$ 比例。当偏移量 $\delta = 1/2$（半 Tick 错位）时，边界 Tick 效率降至 $2/3$；当 $\delta \to 1$ 时效率趋于零。对于含 $N$ 个 Tick 的区间，每个错位边界带来约 $1/N$ 量级的相对损失。

**为何令人意外：** 与经典 Broadie-Glasserman-Kou（BGK）离散时间障碍期权修正不同，此处的修正是 $\delta$ 的**有理函数**，完全不含 Wiener-Hopf 常数 $\zeta(1/2)/\sqrt{2\pi}$。根本原因是连续价格路径必然以概率一穿越每个空间格点，不存在"跳过"问题，故 Spitzer-Baxter 机制不适用。

---

:::theorem{id=prop:optimal_N label="命题：最优区间宽度的修正"}
在修正公式下，最大化手续费的 Tick 数满足
$$N^*_{\mathrm{corr}} = N^*_{\mathrm{EGM}}\Bigl(1 - \frac{(N^*_{\mathrm{EGM}})^2\,\gamma^2}{2} + O(\gamma)\Bigr).$$
修正项恒为负：有限 Tick 效应使最优区间宽度收窄。
:::

有限 Tick 修正的第二阶项 $-N^2\gamma^2/6$ 对宽区间施加了额外惩罚，从而将最优 Tick 数相对 EGM 渐近结果下移 $1$—$2$ 个 Tick。对于 $0.05\%$ 费率档位（$\gamma = 0.001$，最优区间最宽），修正幅度最大；对于 $1\%$ 档位（$\gamma = 0.02$），最优区间仅有约 $9$ 个 Tick，修正效果可忽略不计。

**为何令人意外：** LP 通常认为更宽的区间意味着更高的费率覆盖，但二阶修正揭示了一个与宽度的**凸性惩罚**，使实际最优宽度系统性地窄于连续极限预测。

## 证明思路 {#proofs}

:::proof-sketch{for=thm:general_kappa1}
1. **分解比值**：将 $\Psi/F_0^Y$ 写成三因子之积：预因子 $\psi(h)$、离散和与积分之比 $\sum h f(kh)/I_f(h)$、以及权重函数积分比 $I_f(h)/I_g(h)$。

2. **预因子展开**（引理 lem:prefactor_general）：对 $c(h) = (\gamma/h)(e^{h/2}-1)/(1+e^{\alpha h})$ 的每个因子分别 Taylor 展开至 $O(h^2)$，乘积整理后得 $\psi(h) = 1 + h(3/4 - \alpha/2) + O(h^2)$，即 $\kappa_1^\psi = 3/4 + \mu/\sigma^2$。

3. **Euler-Maclaurin 边界项**（引理 lem:EM 与 lem:f_prime）：左端点 Riemann 和的 Euler-Maclaurin 公式给出 $\sum h f(kh) = I_f(h) - Nh^2 f'(0)/2 + O(h^3)$；利用 $\partial_x\mathbb{E}[L^x_T]|_{x=0} = (\mu/\sigma^2)\mathbb{E}[L^0_T]$ 计算得 $f'(0) = (1/2 + \mu/\sigma^2)\mathbb{E}[L^0_T]$，从而 $\kappa_1^{EM} = -1/4 - \mu/(2\sigma^2)$。

4. **权重函数比**：利用 $f(x) - g(x) = 2x\,\mathbb{E}[L^x_T] + O(x^2)$ 及奇函数积分为零，证明 $I_f/I_g = 1 + O(h^2)$，即该比值对一阶修正无贡献。

5. **合并**：$\kappa_1 = \kappa_1^\psi + \kappa_1^{EM} = (3/4 + \mu/\sigma^2) + (-1/4 - \mu/(2\sigma^2)) = 1/2 + \mu/(2\sigma^2)$。
:::

---

:::proof-sketch{for=thm:main}
1. **GBM 预因子**（引理 lem:prefactor_gbm）：在 $\alpha=1$ 下代入 $\kappa_1^\psi = 3/4 - 1/2 = 1/4$，得 $\psi(h) = 1 + h/4 + O(h^2)$。

2. **Euler-Maclaurin 消去**（引理 lem:EM_gbm）：在 $\alpha=1$ 下 $f'(0) = 0$（风险中性 GBM 漂移的代数特殊性），一阶 Euler-Maclaurin 边界项恰好消失，$\sum h f(kh)/I_f(h) = 1 + O(h^2)$。

3. **权重函数二阶差异**（引理 lem:weight_discrep）：计算 $f''(0) - g''(0) = -4\lambda_0$（其中 $\lambda_0 = \mathbb{E}[L^0_T]$），利用 $\int_{-a}^a x^2\,dx = 2a^3/3$ 得 $I_f - I_g = -4\lambda_0 a^3/3 + O(a^5)$，从而 $I_f/I_g = 1 - N^2h^2/6 + O(h^4)$，其中 $a = Nh/2$。

4. **组合三因子**：$\Psi/F_0^Y = (1+h/4)(1+O(h^2))(1-N^2h^2/6) = 1 + h/4 - N^2h^2/6 + O(h^3)$；利用 $h = \gamma + O(\gamma^2)$ 转换为 $\gamma$ 的展开式。
:::

---

:::proof-sketch{for=thm:misaligned}
1. **边界 Tick 的非对称退出问题**：错位时，边界 Tick $x_b$ 位于宽度为 $(2-\delta)h$ 的非对称区间 $[a_\ell, x_b+h]$ 内，而非标准的宽度 $2h$ 的对称区间。利用尺度函数给出向上穿越概率 $p_b = S((1-\delta)h)/S((2-\delta)h)$。

2. **效率比的极限**：当 $h \to 0$ 时 $S(x) \approx x$，故 $R(\delta) = p_b/p_\uparrow \to 2(1-\delta)/(2-\delta)$，这是 $\delta$ 的有理函数，与 $\alpha$（即漂移）无关（$\alpha$ 依赖仅进入 $O(h^2)$ 项）。

3. **整体费收入修正**：区间共 $N$ 个 Tick，两个边界 Tick 各贡献 $R(\delta)$ 和 $R(\delta')$ 倍的内部 Tick 收益，其余 $N-2$ 个 Tick 贡献正常。加权平均得 $\Psi_{\mathrm{mis}}/\Psi_{\mathrm{align}} = 1 - (1/N)[\delta/(2-\delta) + \delta'/(2-\delta')] + O(N^{-2})$。
:::

---

:::proof-sketch{for=prop:optimal_N}
1. **建立目标函数**：将修正后的手续费 $\mathrm{Fee}(N,\gamma) \approx C_{\mathrm{fee}} N\gamma(1+\gamma/4 - N^2\gamma^2/6)$ 与二次型非永久损失 $\mathrm{IL} \approx C_{\mathrm{IL}}N^2\gamma^2$ 相减，得净收益关于 $N$ 的三次多项式。

2. **一阶条件与摄动分析**：对 $N$ 求导并令其为零，写 $N = N^*_{\mathrm{EGM}}(1+\epsilon)$，在 $|\epsilon| \ll 1$ 处线性化。利用无修正最优条件 $2C_{\mathrm{IL}}N^*_{\mathrm{EGM}}\gamma = C_{\mathrm{fee}}$ 化简，得到修正量 $\epsilon \approx \gamma/4 - (N^*_{\mathrm{EGM}})^2\gamma^2/2$。

3. **主导项分析**：由于 $N^*_{\mathrm{EGM}} = O(\gamma^{-1})$，乘积 $(N^*_{\mathrm{EGM}})^2\gamma^2 = O(1)$，故主导修正为 $-(N^*_{\mathrm{EGM}})^2\gamma^2/2 < 0$，即最优区间宽度总是收窄。
:::

## 数值验证 {#numerics}

数值实验采用**半解析方法**：期望局部时间 $\mathbb{E}[L^x_T]$ 通过对 Gauss 转移密度的数值积分精确计算，$\Psi(\gamma)$ 和 $F_0^Y(\gamma)$ 的离散求和与积分则直接数值评估，无需 Monte Carlo 模拟。

**一般 $\kappa_1$ 的验证**（表 tab:general_kappa1）：在参数 $\sigma=0.4$，$T=1$，$N=20$ 下，对五种漂移值（包含 $\mu > 0$，$\mu = 0$，风险中性 GBM，以及 $\mu < -\sigma^2/2$ 等极端情形）计算数值 $\kappa_1$。当 $\gamma = 10^{-4}$ 时，数值结果与理论预测 $\kappa_1 = 1/2 + \mu/(2\sigma^2)$ 的残差约为 $0.01$，与 $O(\gamma)$ 项的量级一致；特别是 $\mu = -0.20$ 时 $\kappa_1 \approx -0.125$，数值实验确认修正系数可为负值。

**GBM 二阶展开的验证**（表 tab:main）：固定 $\sigma=0.4$，$T=1$，$\phi=0.01$，$N=20$，在不同 $\gamma$ 值下计算相对修正 $\Psi/F_0^Y - 1$。数值结果精确拟合 $\gamma/4 - N^2\gamma^2/6$ 的二次形式，与 $O(\gamma^3)$ 项误差相符。符号转换点 $\gamma^* = 3/(2N^2) = 0.00375$ 在数值上得到验证。

**错位修正的验证**（第 8.5 节）：对不同偏移量 $\delta \in \{0, 0.25, 0.5, 0.75\}$ 的边界 Tick 情形，数值计算 $\Psi_{\mathrm{mis}}/\Psi_{\mathrm{align}}$，结果与公式 $1-(1/N)\delta/(2-\delta)$ 高度吻合，确认修正为有理函数且不含 $\zeta(1/2)$ 相关常数。此外，对比特币（$r=0.5$，$\sigma=0.8$）等加密资产的物理测度参数进行了专项灵敏度分析，证实 $\kappa_1^P \approx 0.64$，与理论值一致。

## 与相关工作的联系 {#connections}

- [variance_options](/papers/variance_options)：局部时间积分表示是波动率衍生品定价的核心工具，本文对 $\mathbb{E}[L^x_T]$ 的精确 Taylor 展开技术与方差互换分析中的占据时间分解方法高度相关。

- [discrete_vs_rough](/papers/discrete_vs_rough)：离散时间监控与连续时间模型之间的系统误差是共同主题；本文揭示空间离散化（Tick 格点）产生有理型代数修正，而该项目中时间离散化产生的修正含 Wiener-Hopf 常数——两种离散化的本质差异在此得到清晰对比。

- [var_ratio](/papers/var_ratio)：Euler-Maclaurin 公式在离散求和与连续积分之间的误差控制是共用的分析工具；本文的第二阶修正 $-N^2\gamma^2/6$ 与波动率比率研究中类似的 Riemann 和误差结构存在方法论上的联系。

- [mv_games](/papers/mv_games)：物理测度与风险中性测度下的策略差异是连接点；本文证明 LP 在物理测度下面临显著更大的有限 Tick 修正（$\kappa_1^P$ 可达 $\kappa_1^{Q}$ 的 $2$—$3$ 倍），与均值-方差博弈文献中测度变换对最优策略的非线性影响相互呼应。