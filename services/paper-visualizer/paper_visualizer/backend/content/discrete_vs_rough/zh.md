---
paper_slug: discrete_vs_rough
lang: zh
sections:
  - id: context
    title: 背景与动机
  - id: objects
    title: 关键数学对象
  - id: main-results
    title: 主要结论
  - id: proofs
    title: 证明概要
  - id: numerics
    title: 数值实验
  - id: connections
    title: 相关工作联系
---

## 背景与动机 {#context}

方差互换（variance swap）是波动率衍生品市场中流动性最强的工具之一，其收益为某段时期内已实现方差与预设执行价之差。在实践中，已实现方差由离散采样的对数收益率计算（通常为日频），而定价理论则基于连续监控下的二次变差。因此，**离散执行价** $K_d(n)$ 与**连续执行价** $K_c$ 之间存在一个修正项 $\delta(n) = K_d(n) - K_c$，理解这一修正项的渐近行为对于套期保值和模型校准至关重要。

在经典随机波动率模型中，这一差距已被深入研究。Broadie–Jain (2008)、Bernard–Cui (2014) 等人对 Heston 和 Hull–White 模型推导了显式的 $O(n^{-1})$ 展开；Bernard–Cui–McLeish (2014) 将这一 $O(n^{-1})$ 速率推广至一般时齐扩散波动率模型，证明其具有普遍性。Jarrow–Kchhia–Protter (2013) 在一般半鞅框架下建立了 $O(n^{-1/2})$ 上界——该上界对跳跃模型是紧的，但对连续模型则是宽松的。Alòs–Fukasawa (2021) 基于 Malliavin 微积分建立了 Itô 积分离散化误差的 Edgeworth 型展开，但其框架要求波动率过程为半鞅。

**粗糙波动率范式**的兴起彻底改变了上述图景。粗糙 Heston（El Euch–Rosenbaum 2019）、粗糙 Bergomi（Bayer–Friz–Gatheral 2016）等模型以 Volterra 型核 $K(t) = t^{H-1/2}/\Gamma(H+\frac{1}{2})$ 驱动方差过程，Hurst 参数 $H \approx 0.1$，其路径正则性根本不同于经典模型——方差过程**不是**半鞅。这带来了根本性的困难：Alòs–Fukasawa 的框架不再适用，而 $O(n^{-1})$ 的经典速率是否仍然成立完全不明朗。Xi–Wong (2021) 和 Zhuang–Huang (2025) 对粗糙波动率下离散监控方差互换进行了数值计算，但未做渐近分析。

本文填补了这一空白，严格证明：在分数核奇异性的驱动下，收敛速率**退化**为 $O(n^{-(H+1/2)})$，当现货–波动率相关系数 $\rho \neq 0$ 时尤为如此，而且这一**反常标度**（anomalous scaling）是分数核奇异性的普遍性质，与模型的仿射结构无关。论文还修正了早期分析中因粗糙余项估计引入的虚假"相变"——消除了 $H = 1/6$ 处并不存在的相变点——并通过精确的双侧界证明了该速率的**锐利性**。

---

## 关键数学对象 {#objects}

**1. Volterra 随机波动率模型**

$$
\begin{aligned}
\dd S_t &= \sqrt{V_t}\, S_t\bigl(\rho\,\dd W_t + \bar\rho\,\dd B_t\bigr),\\
V_t &= V_0 + \int_0^t K(t-s)\,b(V_s)\,\dd s + \int_0^t K(t-s)\,\sigma_V(V_s)\,\dd W_s,
\end{aligned}
$$

其中 $\bar\rho = \sqrt{1-\rho^2}$，$W$ 与 $B$ 为独立标准 Brown 运动，$\rho \in [-1,1]$ 为杠杆参数。方差过程 $V$ 由**分数核** $K(t) = t^{H-1/2}/\Gamma(H+\frac{1}{2})$（$H \in (0,\frac{1}{2})$）驱动，其路径 Hölder 指数严格小于 $\frac{1}{2}$，使 $V$ **不是**半鞅。粗糙 Heston（$b(v) = \theta-\kappa v$，$\sigma_V(v)=\nu\sqrt{v}$）、粗糙 CIR（$\sigma_V(v)=\nu v^\gamma$）等均为特例。

**2. 离散监控间隙**

等距监控时间 $t_i = iT/n$，$i=0,\ldots,n$，离散执行价为

$$
K_d(n) = \frac{1}{T}\sum_{i=0}^{n-1}\E\!\left[\left(\ln\frac{S_{t_{i+1}}}{S_{t_i}}\right)^{\!2}\right],\qquad K_c = \frac{1}{T}\E\!\left[\int_0^T V_t\,\dd t\right] = \bar V.
$$

**离散监控间隙**定义为 $\delta(n) := K_d(n) - K_c$。其非平凡之处在于：它同时受到对数收益率二阶矩结构（凸性项）和现货–波动率协变量结构（杠杆项）的影响，两者在粗糙模型中表现出本质不同的收敛速率。

**3. 区间内积分量**

在第 $i$ 个监控区间 $[t_i, t_i+\Delta]$（$\Delta = T/n$）上定义

$$
I_i = \int_{t_i}^{t_i+\Delta} V_s\,\dd s,\qquad M_i^W = \int_{t_i}^{t_i+\Delta}\sqrt{V_s}\,\dd W_s,\qquad M_i^B = \int_{t_i}^{t_i+\Delta}\sqrt{V_s}\,\dd B_s.
$$

对数收益率可分解为 $\Delta X_i = -\frac{1}{2}I_i + \rho M_i^W + \bar\rho M_i^B$。非平凡之处在于：$I_i$ 属于 Malliavin Sobolev 空间 $\mathbb{D}^{1,2}$，但对其 Malliavin 导数的估计需要处理分数核的奇异性。

**4. Malliavin 导数与分数核奇异性**

Volterra SDE 的 Malliavin 导数满足线性 Volterra 方程，其**领头阶**为

$$
D_u V_s = K(s-u)\,\sigma_V(V_u) + R(u,s),\qquad s > u,
$$

其中余项满足 $|R(u,s)| \le C\,\sqrt{V_u}\,(s-u)^{2H}$。关键在于：领头阶项 $K(s-u) = (s-u)^{H-1/2}/\Gamma(H+\frac{1}{2})$ 在 $s \to u^+$ 时具有**幂次奇异性**（当 $H < \frac{1}{2}$ 时发散），这一奇异性正是反常标度的根源。

**5. 杠杆敏感性函数 $\bar\varphi$**

$$
\varphi(t) := \E\bigl[\sigma_V(V_t)\sqrt{V_t}\bigr],\qquad \bar\varphi := \frac{1}{T}\int_0^T \varphi(t)\,\dd t.
$$

该量综合了 vol-of-vol 函数 $\sigma_V$ 与现货–波动率协方差结构的相互作用。对于粗糙 Heston，$\bar\varphi = \nu\bar V$；对于粗糙 CIR（$\sigma_V(v)=\nu v^\gamma$），$\bar\varphi = \nu T^{-1}\int_0^T \E[V_t^{\gamma+1/2}]\,\dd t$。非平凡之处在于：**所有 Volterra 模型的反常标度系数仅通过这一个量依赖于模型细节**，体现了结果的普遍性。

**6. Beta 卷积恒等式**

$$
\int_0^t K(t-s)\,K(s)\,\dd s = \frac{t^{2H}}{\Gamma(2H+1)},
$$

这一恒等式来自 Beta 函数积分 $B(H+\frac{1}{2}, H+\frac{1}{2}) = \Gamma(H+\frac{1}{2})^2/\Gamma(2H+1)$，是控制 Malliavin 导数余项（Picard 迭代的第一阶）的核心工具。

---

## 主要结论 {#main-results}

:::theorem{id=thm:general label="定理：一般 Volterra 随机波动率模型的离散监控间隙"}
在假设 (A1)–(A5) 下，离散监控间隙满足

$$
\delta(n) = \frac{C_{\mathrm{lev}}(H)}{n^{H+1/2}} + \frac{C_{\mathrm{eff}}}{n} + o(n^{-1}),
$$

其中

$$
C_{\mathrm{lev}}(H) = \frac{-\rho\,\bar\varphi\, T^{H+1/2}}{\Gamma(H+\tfrac52)},\qquad \bar\varphi = \frac{1}{T}\int_0^T \E\bigl[\sigma_V(V_t)\sqrt{V_t}\bigr]\dd t,
$$

以及 $C_{\mathrm{eff}} = C_{\mathrm{conv}} + C_{\mathrm{drift}}$，其中 $C_{\mathrm{conv}} = (4T)^{-1}\int_0^T \E[V_t]^2\,\dd t$。特别地：

(i) 当 $H < \tfrac12$ 且 $\rho \neq 0$、$\bar\varphi \neq 0$ 时，领头项为 $O(n^{-(H+1/2)})$，且 $H+\tfrac12 < 1$。

(ii) 当 $\rho = 0$ 或 $\bar\varphi = 0$ 时，$\delta(n) = C_{\mathrm{eff}}/n + o(n^{-1})$。
:::

这是本文的核心结论。它说明：在分数核驱动的 Volterra 随机波动率模型下，当存在现货–波动率相关性时，离散监控间隙的收敛速率从经典的 $O(n^{-1})$ **退化**为 $O(n^{-(H+1/2)})$，且领头阶系数 $C_{\mathrm{lev}}(H)$ 对所有 Volterra 模型具有统一的形式——仅通过 $\bar\varphi$ 依赖模型细节。例如，日频监控（$n=252$）下，$H=0.1$、$\rho=-0.7$ 的粗糙 Heston 模型中，间隙约为连续执行价的 $0.6\%$，远大于经典模型的修正量。

**为何令人惊讶：** 尽管不同 Volterra 模型（粗糙 Heston、粗糙 CIR 等）的 vol-of-vol 结构差异显著，反常标度速率 $n^{-(H+1/2)}$ 却完全相同，仿射结构并非关键，而是分数核奇异性单独决定了指数。

---

:::theorem{id=cor:sharpness label="推论：收敛速率的锐利性"}
在定理 \ref{thm:general} 的假设下，若 $\rho \neq 0$ 且 $\bar\varphi \neq 0$，则

$$
\lim_{n\to\infty} n^{H+1/2}\,\delta(n) = C_{\mathrm{lev}}(H) \neq 0.
$$
:::

:::theorem{id=cor:two-sided label="推论：双侧界"}
在相同假设下，存在常数 $0 < c \le C < \infty$ 及 $n_0 \in \mathbb{N}$，使得对所有 $n \ge n_0$：

$$
\frac{c}{n^{H+1/2}} \le |\delta(n)| \le \frac{C}{n^{H+1/2}}.
$$

显式地，可取 $c = |C_{\mathrm{lev}}|/2$，$C = 2|C_{\mathrm{lev}}|$，以及

$$
n_0 = \max\!\left(1,\;\left(\frac{2(|C_{\mathrm{eff}}| + C_R')}{|C_{\mathrm{lev}}|}\right)^{1/(1/2-H)}\right),
$$

其中 $C_R'$ 为展开式中余项的界。
:::

这两个推论共同将定理从渐近上界提升为**精确渐近等价**：间隙在多项式尺度意义下恰好以 $n^{-(H+1/2)}$ 衰减，既不更快也不更慢。对于典型粗糙 Heston 参数（$H=0.1$，$\rho=-0.7$），数值估计给出 $n_0 < 1$，意味着双侧界对**所有** $n \ge 1$ 均成立——杠杆项在任何实际监控频率下均占主导地位。

**为何令人惊讶：** 速率的锐利性并非显而易见——展开式中领头项和次领头项均为正（当 $\rho<0$ 时），因此需要精确控制余项才能排除意外的消去现象。

---

:::theorem{id=prop:tight-remainder label="命题：Malliavin 漂移修正的精确余项估计"}
离散监控间隙中 Malliavin 漂移修正项为

$$
\frac{\rho\,L_b\,\bar\varphi\,T^{2H+1}}{(2H+1)(2H+2)\,\Gamma(2H+1)\,n^{2H+1}} + o(n^{-(2H+1)}).
$$

由于对所有 $H > 0$ 均有 $2H+1 > 1$，该项始终为 $O(n^{-1})$ 或更快的阶，从而总余项为 $o(n^{-1})$，在 $H \in (0,\frac{1}{2})$ 上关于 $H$ 一致成立。
:::

此命题消除了早期分析中的虚假结论。早期研究对 Malliavin 导数余项 $O(\Delta^{2H+2})$ 作了粗糙替换（将其放大为 $O(\Delta^{3H+3/2})$），当 $H < 1/6$ 时使之超过 $O(n^{-1})$，似乎产生了相变；实际上，精确的 Beta 卷积恒等式给出更紧的 $O(n^{-(2H+1)})$，始终次于凸性项 $O(n^{-1})$。

**为何令人惊讶：** 粗糙度越高（$H$ 越小），Malliavin 漂移修正反而**相对更快地**衰减到零（指数 $2H+1$ 虽然更接近 1，但始终大于 1），而非产生相变。

---

:::theorem{id=prop:H-to-0 label="命题：$H \to 0^+$ 的边界行为"}
杠杆系数满足

$$
\lim_{H\to 0^+} C_{\mathrm{lev}}(H) = \frac{-4\rho\,\bar\varphi_0\,\sqrt{T}}{3\sqrt{\pi}},
$$

其中 $\bar\varphi_0 = \lim_{H\to 0^+}\bar\varphi$（假设此极限存在）。收敛速率趋近于 $O(n^{-1/2})$，与 Jarrow–Kchhia–Protter (2013) 对跳跃模型建立的上界吻合。
:::

该命题在连续（粗糙）波动率与不连续（跳跃）波动率之间建立了精确桥梁：随着 $H \to 0^+$，极度粗糙的路径在离散监控修正的尺度上趋近于跳跃过程，速率从 $n^{-(H+1/2)}$ 连续过渡到 $n^{-1/2}$，且系数在极限处保持有限。

**为何令人惊讶：** 尽管 Volterra 模型在 $H \to 0^+$ 时从数学上退化（方差发散，假设 (A1) 失效），杠杆系数本身却连续趋向有限极限，提供了与跳跃模型文献的清晰对应。

---

## 证明概要 {#proofs}

:::proof-sketch{for=thm:general}
1. **间隙分解（Clark–Ocone 对偶）**：将对数收益率 $\Delta X_i = -\frac{1}{2}I_i + \rho M_i^W + \bar\rho M_i^B$ 平方并取期望，利用 Itô 等距和 $W$、$B$ 的独立性，得到间隙分解 $\delta(n) = \frac{1}{T}\sum_{i=0}^{n-1}\left[\frac{1}{4}\E[I_i^2] - \rho\,\E[I_i M_i^W]\right]$，将问题化归为**凸性项**和**杠杆项**两部分的分别估计。

2. **凸性项估计**：将 $\E[I_i^2] = (\E[I_i])^2 + \mathrm{Var}(I_i)$ 分解；前者经 Riemann 和给出 $C_{\mathrm{conv}}/n + O(n^{-2})$；后者利用短程协方差假设 $\mathrm{Cov}(V_s,V_u) = O(|s-u|^{2H})$ 给出 $O(n^{-(1+2H)})$，从而 $\frac{1}{4T}\sum_i \E[I_i^2] = C_{\mathrm{conv}}/n + O(n^{-(1+2H)})$。

3. **Malliavin 导数的领头阶提取**：对一般 Volterra SDE，利用 Clark–Ocone 公式将 $\E[I_i M_i^W]$ 化为关于 $D_u I_i$ 的期望；通过 Picard 迭代分解 $D_u V_s = K(s-u)\sigma_V(V_u) + R(u,s)$，领头阶继承分数核奇异性 $K(s-u) \sim (s-u)^{H-1/2}$。

4. **分数核积分与求和**：对区间内的内层积分 $\int_u^{t_i+\Delta} K(s-u)\,\dd s = (t_i+\Delta-u)^{H+1/2}/\Gamma(H+\frac{3}{2})$，再对外层 $u$ 积分给出每个区间的贡献为 $\varphi(t_i)\Delta^{H+3/2}/\Gamma(H+\frac{5}{2}) + O(\Delta^{H+5/2})$；对 $n$ 个区间求和并利用 Riemann 和 $\sum_i \varphi(t_i) = n\bar\varphi + O(1)$ 及 $n\Delta^{H+3/2} = T^{H+3/2}/n^{H+1/2}$，得到杠杆项 $C_{\mathrm{lev}}(H)/n^{H+1/2} + O(n^{-(2H+1)})$。

5. **余项控制（Beta 卷积恒等式）**：Picard 迭代余项 $R(u,s)$ 的贡献经 Beta 卷积恒等式 $\int_0^t K(t-r)K(r-u)\,\dd r = (t-u)^{2H}/\Gamma(2H+1)$ 精确估计，给出 $O(n^{-(2H+1)})$，始终次于 $O(n^{-1})$，从而总余项为 $o(n^{-1})$。
:::

:::proof-sketch{for=cor:sharpness}
1. **改写为比例形式**：由展开式 $\delta(n) = C_{\mathrm{lev}}/n^{H+1/2} + C_{\mathrm{eff}}/n + o(n^{-1})$，两端乘以 $n^{H+1/2}$，得 $n^{H+1/2}\delta(n) = C_{\mathrm{lev}} + C_{\mathrm{eff}} \cdot n^{H-1/2} + o(n^{H-1/2})$。

2. **指数符号判断**：由 $H < \frac{1}{2}$ 知 $H - \frac{1}{2} < 0$，故 $n^{H-1/2} \to 0$，次领头项消失，极限恰好为 $C_{\mathrm{lev}}$。

3. **非零性验证**：$C_{\mathrm{lev}} = -\rho\bar\varphi T^{H+1/2}/\Gamma(H+\frac{5}{2}) \neq 0$ 源于 $\rho \neq 0$、$\bar\varphi > 0$（$\sigma_V(v)\sqrt{v} > 0$ 对 $v > 0$ 成立且 $V_t > 0$ 有正概率）以及 $\Gamma(\cdot) > 0$。
:::

:::proof-sketch{for=prop:tight-remainder}
1. **Picard 第一阶迭代**：对 Malliavin 导数方程 $D_u V_s = K(s-u)\sigma_V(V_u) + \int_u^s K(s-r)b'(V_r)D_u V_r\,\dd r + \text{（鞅项）}$ 作第一阶 Picard 迭代，漂移修正为 $-L_b\sigma_V(V_u)\int_u^s K(s-r)K(r-u)\,\dd r$。

2. **Beta 卷积恒等式精确化**：利用 $\int_0^{s-u} K(s-u-\tau)K(\tau)\,\dd\tau = (s-u)^{2H}/\Gamma(2H+1)$，将漂移修正化为 $-L_b\sigma_V(V_u)(s-u)^{2H}/\Gamma(2H+1)$，而非粗糙估计 $O((s-u)^{H-1/2} \cdot (s-u)^{H-1/2})$。

3. **精确积分与求和**：对漂移修正项计算 $\int_u^{t_i+\Delta}(s-u)^{2H}\,\dd s = (t_i+\Delta-u)^{2H+1}/(2H+1)$，再对 $u$ 积分并求和，给出贡献 $O(n^{-(2H+1)})$，由 $2H+1 > 1$ 知始终次于 $O(n^{-1})$，从而消除虚假相变。
:::

:::proof-sketch{for=prop:H-to-0}
1. **Gamma 函数极限**：计算 $\Gamma(H+\frac{5}{2})\big|_{H=0} = \Gamma(\frac{5}{2}) = \frac{3}{4}\sqrt{\pi}$，以及 $T^{H+1/2}\big|_{H=0} = \sqrt{T}$，均有有限极限。

2. **系数代入**：将上述极限代入 $C_{\mathrm{lev}}(H) = -\rho\bar\varphi T^{H+1/2}/\Gamma(H+\frac{5}{2})$，得 $C_{\mathrm{lev}}(0^+) = -\rho\bar\varphi_0\sqrt{T}/(\frac{3}{4}\sqrt{\pi}) = -4\rho\bar\varphi_0\sqrt{T}/(3\sqrt{\pi})$。

3. **速率极限与跳跃模型对应**：指数 $H+\frac{1}{2}\to\frac{1}{2}$，使收敛速率趋近于 $O(n^{-1/2})$，与 Jarrow–Kchhia–Protter (2013) 对一般半鞅（含跳跃）模型的上界吻合，为连续粗糙模型与跳跃模型之间提供了精确桥梁。
:::

---

## 数值实验 {#numerics}

数值验证采用粗糙 Heston 的提升 Markov 近似（Abi Jaber–El Euch 2019，$N=20$ 个指数因子），Euler–Maruyama 时间步 $M=2520$，每组参数 $5\times10^5$ 条路径，基准参数为 $\kappa=2$，$\theta=0.08$，$\nu=0.5$，$V_0=0.04$，$T=1$。

**实验一（标度指数）** 对 $n \in \{12, 52, 252, 504\}$ 作 $\log\delta(n)$ 关于 $\log n$ 的线性回归，拟合指数 $\hat\alpha$ 系统性地高于理论值 $H+\frac{1}{2}$ 约 0.07–0.14，与定理预言的两项结构（有限 $n$ 范围内次领头 $O(n^{-1})$ 凸性项抬高有效指数）完全吻合。在 $\rho=0$ 的对照实验中，间隙退化为 Monte Carlo 噪声量级，证实杠杆效应是反常标度的唯一驱动力。

**实验二（系数收敛）** 验证重标化间隙 $n^{H+1/2}\delta(n)$ 随 $n$ 增大趋向理论极限 $C_{\mathrm{lev}}^{\mathrm{rH}}(H)$（推论 \