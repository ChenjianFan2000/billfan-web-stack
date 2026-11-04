---
paper_slug: sr_p001
lang: zh
sections:
  - id: context
    title: 背景与动机
  - id: objects
    title: 核心数学对象
  - id: main-results
    title: 主要定理
  - id: proofs
    title: 证明梗概
  - id: numerics
    title: 数值实验
  - id: connections
    title: 关联论文
---

## 背景与动机 {#context}

Schrödinger桥问题源于1931年Schrödinger的思想实验：一群独立布朗粒子从初始分布演化至终端分布，最可能的演化路径是什么？现代表述下，给定边际分布 $\mu_0, \mu_T \in \mathcal{P}_2(\mathbb{R}^d)$，问题归结为对半鞅测度关于Wiener测度的相对熵进行最小化，同时满足边际约束。另一个经典范式是Bass鞅输运：通过控制局部鞅的扩散系数，实现两个边际分布之间的鞅插值，漂移项被限制为零。两个框架各有侧重——Schrödinger桥优化漂移，Bass输运优化扩散——此前缺乏统一的插值理论。

Henry-Labordère、Loeper、Mazhar、Pham与Touzi引入了**Schrödinger–Bass桥**（SBB）问题：通过参数 $\beta > 0$ 同时控制漂移 $\alpha_t$ 与扩散系数 $\sigma_t$，代价泛函对漂移施以 $\frac{1}{2}|\alpha_t|^2$ 惩罚，对扩散偏离恒等矩阵施以 $\frac{\beta}{2}\|\sigma_t\sigma_t^\top - I_d\|_F^2$ 惩罚。当 $\beta \to \infty$ 时扩散被迫等于 $I_d$，退化为经典Schrödinger桥；当 $\beta \to 0$ 时漂移惩罚主导，趋向Bass鞅输运。然而，若干基本问题仍悬而未决：Gaussian边际的精确可解性边界是什么？该边界对非Gaussian边际是否仍有意义？边界处的退化结构如何？

本文通过**Pontryagin极大值原理**对Gaussian SBB给出自洽推导，得到伴随方程 $\dot{p} = 2p^2$ 的显式解，将边值问题化简为一个关于标量参数的二次方程。核心贡献包括：识别出临界目标方差 $\gamma_T^* = (\gamma_0 + \beta T^2)/(1+2\beta T)^2$（可解性边界），证明该边界对任意中心化边际均构成**普适下界**，并刻画边界处最优扩散系数退化为零的奇异结构。

## 核心数学对象 {#objects}

**Schrödinger–Bass桥问题（SBB）**

$$\inf_{(\alpha,\sigma)} \int_0^T \mathbb{E}\!\left[\frac{1}{2}|\alpha_t|^2 + \frac{\beta}{2}\|\sigma_t\sigma_t^\top - I_d\|_F^2\right]dt,$$

其中过程满足 $dX_t = \alpha_t\,dt + \sigma_t\,dW_t$，$X_0 \sim \mu_0$，$X_T \sim \mu_T$。非平凡之处：同时控制漂移与扩散，两者代价以 $\beta$ 权衡，使问题严格介于熵输运与鞅输运之间。

**协方差降维后的代价泛函**

在Gaussian假设下，均值与协方差分离，协方差部分化为

$$J = \int_0^T \left[\frac{1}{2}\operatorname{tr}(A_t^2\Gamma_t) + \frac{\beta}{2}\|\Sigma_t\Sigma_t^\top - I_d\|_F^2\right]dt,$$

受协方差动态约束 $\dot{\Gamma} = A_t\Gamma_t + \Gamma_t A_t^\top + \Sigma_t\Sigma_t^\top$。非平凡之处：将无穷维随机控制问题转化为有限维确定性最优控制。

**余状态（costate）过程**

标量情形下，余状态 $p(t)$ 满足伴随方程

$$\dot{p} = 2p^2, \qquad p(t) = \frac{p_0}{1-2p_0 t}.$$

非平凡之处：该Bernoulli方程有爆破结构，可解性要求 $p_0$ 受约束，直接导出可解性边界。

**可解性边界**

$$\gamma_T^* = \frac{\gamma_0 + \beta T^2}{(1+2\beta T)^2}.$$

非平凡之处：这一单一公式统一了两个极端情形——$\beta\to\infty$ 时 $\gamma_T^* \to 0$（所有正方差均可达），$\beta \to 0$ 时 $\gamma_T^* \to \gamma_0$（仅 $\gamma_T > \gamma_0$ 可行）。

**矩阵Riccati方程**

多维情形下余状态矩阵满足

$$\dot{P} = 2P^2, \qquad P(t) = P_0(I - 2P_0 t)^{-1}.$$

非平凡之处：矩阵方程与标量方程形式完全一致，但当 $\Gamma_0$ 与 $\Gamma_T$ 不对易时，$P_0$ 具有非平凡非对角结构，耦合不同坐标方向。

## 主要定理 {#main-results}

:::theorem{id=thm:1d label="一维最优控制定理"}
设 $\gamma_0, \gamma_T > 0$，$\beta > 0$，$T > 0$。定义
$$v = \frac{T + \sqrt{T^2 + 4\bigl(\gamma_T + \tfrac{1}{4\beta}\bigr)\bigl(\gamma_0 + \tfrac{1}{4\beta}\bigr)}}{2\bigl(\gamma_T + \tfrac{1}{4\beta}\bigr)},$$
并令 $p_0 = (v-1)/(2vT)$。则唯一最优控制为
$$\alpha^*(t) = \frac{-2p_0}{1 - 2p_0 t}, \qquad \sigma^{*2}(t) = 1 - \frac{p_0}{\beta(1 - 2p_0 t)}.$$
最优余状态为 $p(t) = p_0/(1 - 2p_0 t)$，守恒Hamiltonian值为
$$H^* = -2p_0^2\gamma_0 + p_0 - \frac{p_0^2}{2\beta}.$$
:::

定理给出了一维Gaussian SBB的全显式解：最优漂移与最优扩散均由单一标量参数 $p_0$ 完全决定，而 $p_0$ 由二次方程唯一确定。最优漂移呈时间变化的均值回复形式，最优扩散系数随时间单调变化。当 $\beta \to \infty$ 时 $\sigma^{*2} \to 1$，退化为Schrödinger桥；当 $\beta \to 0$ 时漂移趋零、扩散趋常数，退化为Bass鞅。

**Why it's surprising:** 将随机控制问题——其状态过程的噪声本身也是控制变量——化简为一个二次方程，解的结构如此简洁是非常出人意料的。

---

:::theorem{id=thm:solvability label="可解性边界定理"}
设 $\beta > 0$，$T > 0$，$\gamma_0 > 0$。定义临界目标方差
$$\gamma_T^* = \frac{\gamma_0 + \beta T^2}{(1 + 2\beta T)^2}.$$
则：
(a) Gaussian SBB关于数据 $(\gamma_0, \gamma_T, \beta, T)$ 可解当且仅当 $\gamma_T \ge \gamma_T^*$。
(b) 在 $\gamma_T = \gamma_T^*$ 处，最优终端波动率退化：$\sigma^*(T) = 0$。
(c) 对所有 $\beta, T > 0$，均有 $\gamma_T^* > 0$。
(d) $\beta \to \infty$ 时：$\gamma_T^* \to 0$。
(e) $\beta \to 0$ 时：$\gamma_T^* \to \gamma_0$。
:::

该定理精确刻画了哪些目标方差对于Gaussian SBB是可达的。可解性条件 $\gamma_T \ge \gamma_T^*$ 是一个锐临界：一旦 $\gamma_T$ 低于此阈值，最优代价从有限值跳跃至 $+\infty$——代价函数在边界处具有跳跃间断性。极限行为揭示：在Schrödinger极限（$\beta \to \infty$）下所有正方差均可达，而在Bass极限（$\beta \to 0$）下仅严格增大的方差可达。

**Why it's surprising:** 即便在 $\beta T > 1$（文献中保证一般可解的条件）成立时，仍存在不可达的目标方差——可解性对具体边际而言更精细，而非仅依赖于参数乘积 $\beta T$。

---

:::theorem{id=thm:nongaussian label="非Gaussian二阶矩下界定理"}
设 $\mu_0, \mu_T \in \mathcal{P}_2(\mathbb{R})$ 为中心化边际（$m_0 = m_T = 0$）。令 $\gamma_0 = \int x^2\,d\mu_0$，$\gamma_T = \int x^2\,d\mu_T$。若
$$\gamma_T < \frac{\gamma_0 + \beta T^2}{(1 + 2\beta T)^2},$$
则 $\mathrm{SBB}(\mu_0, \mu_T) = +\infty$，即无论边际分布的形状如何，Gaussian可解性边界 $\gamma_T^*$ 是任意中心化边际对可达二阶矩的**普适下界**。
:::

该定理将Gaussian分析的结论提升至一般设定：$\gamma_T^*$ 不仅是Gaussian情形的产物，而是对任意半鞅输运计划均成立的基本约束。非Gaussian边际可能有更大的不可解区域，但Gaussian阈值提供了不可解性的普适证书。

**Why it's surprising:** 通过Cauchy–Schwarz不等式与Jensen不等式的巧妙组合，将任意随机控制问题的代价下界化简为确定性Gaussian控制问题，从而将一个关于Gaussian分布的定理转化为普适结果。

---

:::theorem{id=thm:multid label="多维最优控制定理"}
设 $\Gamma_0, \Gamma_T \in S_d^{++}$，$\beta > 0$，$T > 0$。$d$ 维Gaussian SBB的Pontryagin系统给出：
(a) 最优控制为
$$A^*(t) = -2P_0(I - 2P_0 t)^{-1}, \qquad \Sigma^{*2}(t) = I - \frac{P_0}{\beta}(I - 2P_0 t)^{-1},$$
其中 $P_0 \in S_d$ 为初始余状态。
(b) 矩阵伴随方程为 $\dot{P} = 2P^2$，显式解为
$$P(t) = P_0(I - 2P_0 t)^{-1}.$$
(c) 当 $\Gamma_0$ 与 $\Gamma_T$ 对易时，$d$ 维问题分解为 $d$ 个独立的标量问题，每个由定理 thm:1d 求解。
:::

多维情形与一维情形在形式上完全平行，矩阵Riccati方程 $\dot{P} = 2P^2$ 与标量Bernoulli方程具有相同结构。当两个协方差矩阵不对易时，$P_0$ 的非对角元素耦合不同坐标方向，产生各向异性的最优输运结构。

**Why it's surprising:** 矩阵方程 $\dot{P} = 2P^2$ 尽管是非线性的，却有与标量情形完全类比的显式解，关键在于 $P_0$ 与 $(I - 2P_0 t)^{-1}$ 的对易性。

## 证明梗概 {#proofs}

:::proof-sketch{for=thm:1d}
1. **构造Hamiltonian并求一阶条件**：对控制Hamiltonian $H = \frac{1}{2}\alpha^2\gamma + \frac{\beta}{2}(\sigma^2-1)^2 + p(2\alpha\gamma + \sigma^2)$ 分别对 $\alpha$ 和 $\sigma^2$ 求导置零，得 $\alpha^* = -2p$，$\sigma^{*2} = 1 - p/\beta$。
2. **求解伴随方程**：计算 $\dot{p} = -\partial H/\partial\gamma$ 得 $\dot{p} = 2p^2$（Bernoulli方程），显式解为 $p(t) = p_0/(1-2p_0 t)$。
3. **积分因子法求方差轨迹**：令 $\varphi(t) = \gamma(t)/(1-2p_0 t)^2$，计算 $\dot{\varphi}$ 后积分，得到连接 $\gamma_0$ 与 $\gamma_T$ 的方程。
4. **化简为二次方程**：令 $v = 1/(1-2p_0 T)$，方差边值方程化为关于 $v$ 的二次方程，取正根唯一确定 $v$ 进而确定 $p_0$。
5. **Hamiltonian守恒验证**：将 $t=0$ 处的最优控制代入Hamiltonian，利用 $\partial H/\partial t = 0$ 验证守恒值 $H^* = -2p_0^2\gamma_0 + p_0 - p_0^2/(2\beta)$。
:::

:::proof-sketch{for=thm:solvability}
1. **可行性约束**：最优扩散 $\sigma^{*2}(t) = 1 - p_0/(\beta(1-2p_0t))$ 的最小值在 $t=T$ 处取到（$p_0 > 0$ 时 $u(t)$ 递减），约束 $\sigma^{*2}(T) \ge 0$ 等价于 $v \le 1 + 2\beta T$。
2. **临界阈值计算**：将 $v^* = 1+2\beta T$ 代入二次边值方程 \eqref{eq:bvp}，代数化简分子得 $\gamma_0 + \beta T^2$，分母为 $(1+2\beta T)^2$，从而确定 $\gamma_T^*$。
3. **单调性论证**：由隐函数定理，$dv/d\gamma_T < 0$（$v$ 关于 $\gamma_T$ 严格递减），故 $\gamma_T \ge \gamma_T^*$ 当且仅当 $v \le v^*$，完成充要条件的证明。
4. **极限分析**：直接对公式 $\gamma_T^* = (\gamma_0 + \beta T^2)/(1+2\beta T)^2$ 取 $\beta \to \infty$ 和 $\beta \to 0$ 验证渐近行为。
:::

:::proof-sketch{for=thm:nongaussian}
1. **Itô公式建立矩动态**：对任意可行输运计划 $P$，由Itô公式得 $\gamma(T) = \gamma(0) + \int_0^T(2\mathbb{E}[\alpha_t X_t] + \mathbb{E}[\sigma_t^2])\,dt$。
2. **Cauchy–Schwarz降维**：$\mathbb{E}[\alpha_t^2] \ge \mathbb{E}[\alpha_t X_t]^2/\gamma(t)$，将随机代价下界化简为仅依赖 $\bar{\alpha}(t) = \mathbb{E}[\alpha_t X_t]/\gamma(t)$ 的确定性量。
3. **Jensen不等式处理扩散**：$\mathbb{E}[(\sigma_t^2-1)^2] \ge (\mathbb{E}[\sigma_t^2]-1)^2$，将随机扩散代价下界化为确定性扩散 $\bar{\sigma}^2(t) = \mathbb{E}[\sigma_t^2]$ 的代价。
4. **归约至Gaussian问题**：上述两步将任意输运计划的代价下界化为以 $(\bar{\alpha}, \bar{\sigma}^2)$ 为控制的一维确定性问题，正是第3节中的Gaussian最优控制，由定理 thm:solvability 知其在 $\gamma_T < \gamma_T^*$ 时不可解。
:::

## 数值实验 {#numerics}

论文通过三个数值例子验证理论结论。**基线算例**（$\gamma_0=1$，$\gamma_T=2$，$\beta=1$，$T=1$）中，计算得 $v=1$、$p_0=0$，最优控制恰好是标准布朗运动（$\alpha^*=0$，$\sigma^{*2}=1$），代价为零——这是一个"免费"的输运，因为 $\gamma_T = \gamma_0 + T$ 正好由无漂移单位扩散实现，完美验证了公式的自洽性。

**边界算例**（$\gamma_T = \gamma_T^* = 2/9$）中，数值计算给出 $p_0 = 1/3$，最优波动率 $\sigma^{*2}(t) = 1 - 1/(3-2t)$ 在 $t=1$ 处恰好退化为零，最优漂移在终端时刻达到 $\alpha^*(1) = -2$（最大均值回复），验证了命题 prop:boundary 的退化结构。参数 $\beta$ 对可解性阈值影响的表格直观展示了 $\gamma_T^*$ 从 $\beta=0.1$ 时的 $0.764$ 平滑下降至 $\beta=100$ 时的 $0.0025$，定量刻画了 $\beta$ 如何在漂移控制与扩散控制之间权衡。

**非对易多维例子**（$d=2$，$\Gamma_0$ 与 $\Gamma_T$ 不对易）中，通过Python的 `scipy.integrate` 与 `scipy.optimize` 数值求解非线性打靶问题，得到初始余状态

$$P_0 \approx \begin{pmatrix} 0.183 & 0.096 \\ 0.096 & -0.154 \end{pmatrix}.$$

$P_0$ 的非对角元素 $\approx 0.096$ 证明最优余状态耦合两个坐标方向，$P_0$ 的特征值符号相反（$\approx 0.23$ 与 $\approx -0.20$），意味着最优过程同时在一个方向扩张方差、在另一个方向压缩方差——这是一种纯粹的多维各向异性效应，无法通过对易分解捕捉。终端扩散矩阵的特征值均严格正，确认该边际对位于可解区域内部。

## 关联论文 {#connections}

- [variance_options](/papers/variance_options)：方差过程的最优控制结构（余状态方程、Hamiltonian守恒）与本文Gaussian SBB的Pontryagin框架共享相同的随机控制方法论；方差目标约束的可解性分析与本文可解性边界的推导思路平行。
- [mv_games](/papers/mv_games)：均值–方差框架下的均场博弈同样涉及协方差矩阵的动态优化，矩阵Riccati方程 $\dot{P} = 2P^2$ 的结构与线性二次博弈中的Riccati方程具有类比关系。
- [sr_p006](/papers/sr_p006)：作为同一项目中的相关论文，研究SBB问题的PDE方法（Legendre变换与热方程），本文Pontryagin方法与之互补，两者对Gaussian情形给出相同的显式解但证明路径不同。