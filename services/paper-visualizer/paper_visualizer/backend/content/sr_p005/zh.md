---
paper_slug: sr_p005
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
    title: 关联文献
---

## 背景与动机 {#context}

方差期权（options on realized variance）是以标的资产已实现方差为标的的衍生品，近年来随着 CBOE S&P 500 方差期货（代码 VA）于 2024 年 9 月上线，对此类工具定价方法的需求显著增加。在局部随机波动率（LSV）框架下，资产价格 $S_t$ 与方差过程 $V_t$ 之间的噪声存在相关性参数 $\rho$，该相关性（杠杆效应）对期权定价有本质影响，但也使分析大幅复杂化。

Pirjol、Wang 与 Zhu（2025，以下简称 PWZ2025）证明了价外方差期权的短到期渐近行为由一个二维变分问题的"速率函数" $I_\rho$ 控制：

$$\lim_{T\to 0} T\log C(T) = -I_\rho(S_0, V_0, K).$$

对于 $\rho=0$ 以及 $\rho=\pm 1$ 两种极端情形，该变分问题均可显式求解，分别退化为与亚式期权速率函数相关的一维问题。然而，对于一般的 $\rho\in(-1,1)\setminus\{0\}$，变分问题涉及资产路径 $g(t)=\log S_t$ 与方差路径 $h(t)=\log V_t$ 之间的非平凡耦合，PWZ2025 仅给出了上下界，未能完整求解。

本文在常数波动率之波动率假设 $\sigma(v)\equiv\sigma_0$ 下，从三个互补角度推进对上述开放问题的求解：Hamiltonian 守恒律、$\alpha$-参数化上界族、以及关于 $\rho$ 的扰动展开。这三种方法各有侧重：守恒律揭示最优轨迹的几何结构，参数化上界提供可计算的实用近似（对杠杆区间 $\rho<0$ 改进可达 75%），扰动展开给出小 $|\rho|$ 时的显式公式及金融解释。

## 核心数学对象 {#objects}

**速率函数（变分问题）**

$$I_\rho(S_0,V_0,K) = \inf_{\substack{g(0)=\log S_0,\;h(0)=\log V_0 \\ \int_0^1 e^{h(t)}\eta^2(e^{g(t)})\,\mathrm{d}t = K}} \Lambda_\rho[g,h],$$

其中作用量泛函为

$$\Lambda_\rho[g,h] = \frac{1}{2(1-\rho^2)}\int_0^1 \bigl(a(t)-\rho\,b(t)\bigr)^2\,\mathrm{d}t + \frac{1}{2}\int_0^1 b(t)^2\,\mathrm{d}t.$$

非平凡之处：这是一个**等周约束**下的无穷维变分问题，当 $\rho\neq 0$ 时两个路径变量深度耦合，无法逐分量分离。

**速度变量**

$$a(t) = \frac{g'(t)}{\eta(e^{g(t)})\sqrt{e^{h(t)}}}, \qquad b(t) = \frac{h'(t)}{\sigma_0}.$$

这是对原始路径导数的规范化，使得作用量在 $\rho=0$ 时成为 $\frac{1}{2}\int(a^2+b^2)\,\mathrm{d}t$，从而具有欧氏度量结构。

**$\alpha$-耦合函数 $F_\alpha$**

$$\int_{S_0}^{F_\alpha(x)}\frac{\mathrm{d}y}{y\,\eta(y)} = \frac{2\alpha}{\sigma_0}\bigl(\sqrt{x}-\sqrt{V_0}\bigr), \qquad F_\alpha(V_0)=S_0.$$

这是一个将方差路径映射到资产路径的"平方根耦合"，通过比例约束 $a(t)=\alpha\,b(t)$ 自然导出。与 PWZ2025 中的对数耦合相比，该平方根形式能生成可优化的上界族。

**有效支付函数**

$$G_\alpha(x) = x\,\eta^2(F_\alpha(x)).$$

将二维约束 $\int e^h \eta^2(e^g)\,\mathrm{d}t=K$ 化为关于 $h$ 单独的约束 $\int G_\alpha(e^h)\,\mathrm{d}t=K$，从而实现维度约化。

**一维速率函数 $J_\alpha$**

$$J_\alpha(V_0,K) = \inf_{\substack{h(0)=\log V_0 \\ \int_0^1 G_\alpha(e^{h(t)})\,\mathrm{d}t = K}} \frac{1}{2\sigma_0^2}\int_0^1 \bigl(h'(t)\bigr)^2\,\mathrm{d}t.$$

本质上是以修正局部波动率 $G_\alpha$ 为参数的亚式期权速率函数，可借助 Pirjol-Zhu（2023）的方法显式计算。

**Hamiltonian**

$$\mathcal{H}(t) = \frac{1}{2(1-\rho^2)}\bigl(a(t)^2 - 2\rho\,a(t)\,b(t) + b(t)^2\bigr) - \lambda\,e^{h(t)}\eta^2(e^{g(t)}).$$

这是 Euler-Lagrange 系统的第一积分（守恒量），其守恒性来自 Lagrangian 对时间参数 $t$ 的自主性。

## 主要结果 {#main-results}

:::theorem{id="thm:hamiltonian" label="命题：Hamiltonian 守恒律"}
假设 $\sigma(v)\equiv\sigma_0$。设 $(g,h)$ 是约束变分问题的光滑临界点，定义 Hamiltonian

$$\mathcal{H}(t) = \frac{1}{2(1-\rho^2)}\bigl(a(t)^2 - 2\rho\,a(t)\,b(t) + b(t)^2\bigr) - \lambda\,e^{h(t)}\eta^2(e^{g(t)}).$$

则对所有 $t\in[0,1]$，$\mathcal{H}(t)=E$ 为常数，$E$ 由边界条件确定。
:::

该命题表明，沿最优轨迹，"动能" $\frac{1}{2(1-\rho^2)}\|w(t)\|^2$（其中 $w=(a-\rho b,\sqrt{1-\rho^2}\,b)$）与"势能" $\lambda e^h\eta^2(e^g)$ 之和守恒。这将四维相空间 $(g,h,g',h')$ 中的最优轨迹约束在水平集 $\mathcal{H}=E$ 上，从而将有效自由度从二维降为一维。**令人意外之处：** 尽管变分问题包含等周约束（而非标准 Euler-Lagrange 问题），时间自主性仍给出干净的守恒律，且其形式与经典力学中的"能量守恒"完全平行。

:::theorem{id="thm:alpha" label="定理：$\alpha$-参数化上界"}
假设 $\sigma(v)\equiv\sigma_0$。对任意 $\rho\in(-1,1)$，

$$I_\rho(S_0,V_0,K) \leq \inf_{\alpha\in\mathbb{R}}\,C(\alpha,\rho)\cdot J_\alpha(V_0,K),$$

其中

$$C(\alpha,\rho) = \frac{\alpha^2 - 2\alpha\rho + 1}{1-\rho^2},$$

$J_\alpha(V_0,K)$ 是由 $G_\alpha$ 定义的一维速率函数（见上文）。
:::

该定理将困难的二维变分问题化为关于单参数 $\alpha\in\mathbb{R}$ 的一维优化：对每个 $\alpha$，上界 $C(\alpha,\rho)\cdot J_\alpha$ 均可通过亚式期权方法高效计算，再对 $\alpha$ 做数值最优化即得最紧上界。特别地，$\alpha=\rho$ 时 $C(\rho,\rho)=1$，退化为单位系数界；而对一般 $\alpha$，可利用 $C$ 与 $J_\alpha$ 之间的权衡获得更紧的界。**令人意外之处：** 仅通过"比例路径"这一简单 ansatz，就能将二维问题完全化为一维，且在 $\eta$ 为常数时给出**精确值**。

:::theorem{id="cor:exactconst" label="推论：常数局部波动率时的精确性"}
当 $\eta(x)\equiv\eta_0$ 为常数时，$\alpha$-参数化上界精确：

$$I_\rho(S_0,V_0,K) = J\!\left(V_0,\,\frac{K}{\eta_0^2}\right),$$

该值与 $\rho$ 无关，其中 $J(V_0,z)$ 是 Pirjol-Zhu（2023）中的亚式期权速率函数。
:::

这说明在常数局部波动率模型中，相关性 $\rho$ 对方差期权价格（在短到期渐近意义下）**没有影响**。直觉上，当 $\eta$ 为常数时，已实现方差 $\int V_s\eta_0^2\,\mathrm{d}s$ 仅取决于方差路径 $V$，资产路径可被"积掉"，最优 $g$ 由 $a=\rho b$ 给出。**令人意外之处：** $\rho$ 完全消失于最终答案，尽管它深嵌于作用量泛函的结构中。

:::theorem{id="thm:perturb" label="定理：一阶扰动展开"}
在正则性假设下，设 $\sigma(v)\equiv\sigma_0$，则速率函数关于 $\rho$ 在零点的展开为

$$I_\rho(S_0,V_0,K) = I_0(S_0,V_0,K) - \rho\int_0^1 a_0(t)\,b_0(t)\,\mathrm{d}t + O(\rho^2),$$

其中 $I_0=I_{\rho=0}$ 是 PWZ2025 中的无相关速率函数，$(a_0,b_0)$ 是 $\rho=0$ 时最优轨迹处的速度变量。$O(\rho^2)$ 中的隐含常数依赖于 $V_0,K,\sigma_0$ 及 $\eta$ 的 $C^2$ 范数。
:::

一阶修正项 $-\rho\int_0^1 a_0 b_0\,\mathrm{d}t$ 具有明确金融含义：对价外方差看涨期权（$K>V_0\eta^2(S_0)$），最优 $\rho=0$ 轨迹满足 $a_0>0,b_0>0$，故一阶项为负，说明正相关 $\rho>0$ 使速率函数减小（期权价格提升），负相关 $\rho<0$ 则相反——这与杠杆效应对方差期权的已知定性影响完全一致。**令人意外之处：** 一阶系数完全由已知的 $\rho=0$ 最优解决定，无需额外求解新的变分问题。

## 证明概要 {#proofs}

:::proof-sketch{for="thm:hamiltonian"}
1. **时间自主性（Noether 定理）**：$\sigma\equiv\sigma_0$ 使 Lagrangian 密度不显含时间参数 $t$，由经典变分原理，Hamiltonian $\mathcal{H}=p_g g'+p_h h'-\mathcal{L}$ 沿 Euler-Lagrange 方程的解守恒。
2. **计算共轭动量**：直接对 $\mathcal{L}$ 关于 $g',h'$ 求偏导，得 $p_g=(a-\rho b)/[(1-\rho^2)\eta(e^g)\sqrt{e^h}]$，$p_h=(b-\rho a)/[(1-\rho^2)\sigma_0]$。
3. **代入化简**：计算 $p_g g'+p_h h'=(a^2-2\rho ab+b^2)/(1-\rho^2)$，减去 $\mathcal{L}$ 后得到命题中的 $\mathcal{H}$，验证其等于常数 $E$。
:::

:::proof-sketch{for="thm:alpha"}
1. **路径限制（上界原理）**：将变分问题限制到满足比例约束 $a(t)=\alpha\,b(t)$ 的路径子集，其上的下确界构成全集上下确界的上界。
2. **路径约化**：由 $a=\alpha b$ 及 $F_\alpha$ 的定义，资产路径 $g$ 完全由方差路径 $h$ 决定：$e^{g(t)}=F_\alpha(e^{h(t)})$。
3. **作用量分解**：代入 $a=\alpha b$ 到展开后的作用量，得 $\Lambda_\rho[g,h]=C(\alpha,\rho)\cdot\frac{1}{2\sigma_0^2}\int(h')^2\,\mathrm{d}t$，等周约束变为 $\int G_\alpha(e^h)\,\mathrm{d}t=K$，从而下确界恰为 $C(\alpha,\rho)\cdot J_\alpha$。
4. **对 $\alpha$ 优化**：对所有 $\alpha$ 取最小即得最紧上界。
:::

:::proof-sketch{for="thm:perturb"}
1. **包络定理**：速率函数 $I_\rho$ 是光滑优化问题的值函数，由包络定理 $\frac{\mathrm{d}I_\rho}{\mathrm{d}\rho}\big|_{\rho=0}=\frac{\partial\Lambda_\rho}{\partial\rho}\big|_{(g_0,h_0),\rho=0}$。
2. **计算偏导**：对展开后的作用量求 $\partial/\partial\rho$，在 $\rho=0$ 处得 $\frac{\partial\Lambda_\rho}{\partial\rho}\big|_{\rho=0}=-\int_0^1 a_0(t)b_0(t)\,\mathrm{d}t$（$\rho$ 项系数在 $\rho=0$ 处消去）。
3. **Taylor 展开**：将上述一阶导数代入，给出定理中的 $O(\rho^2)$ 展开式；余项的界依赖于正则性假设（最优解对 $\rho$ 的 $C^1$ 依赖）。
:::

## 数值实验 {#numerics}

数值实验在 Tanh 局部波动率模型 $\eta(S)=f_0+f_1\tanh(\log(S/S_0)-x_0)$（参数 $V_0=1.0,\sigma_0=2.0,f_0=1,f_1=-0.5,x_0=0$）中进行，与 PWZ2025 保持一致，便于对比。实验通过以下步骤计算 $\alpha$-最优上界：数值求解耦合方程 $F_\alpha$，构造有效支付 $G_\alpha$，调用 Pirjol-Zhu（2023）方法计算 $J_\alpha$，再对 $\alpha$ 做一维数值最优化。

主要结果汇总于论文表 1：在杠杆区间 $\rho<0$ 的价外看涨期权场景下，$\alpha$-最优界相比 PWZ2025 的 Proposition 13 上界改进幅度高达 **75%**（例如 $\rho=-0.7,K=2.0$ 时，P13 给出 0.3119，$\alpha$-最优界给出 0.0765）。改进幅度关于 $\rho$ 不对称：负相关改进显著，正相关改进较小（部分场景接近 0%）。最优耦合参数 $\alpha^*$ 始终偏向负值（相对于 $\rho$），反映了 Tanh 模型中 $\eta$ 单调递减的杠杆效应。同时，$\rho=0$ 附近的扰动展开在数值上也与精确上界吻合良好，验证了一阶修正项的实用精度。

## 关联文献 {#connections}

- [variance_options](/papers/variance_options)：本文直接延续 PWZ2025 的工作，求解其遗留的 $\rho\neq 0$ 开放问题；速率函数定义、$\rho=0$ 及 $\rho=\pm 1$ 的已知结果、以及对数耦合上界（Proposition 13, 17）均来自该文。
- [sr_p001](/papers/sr_p001)：Pirjol-Zhu（2023）的亚式期权速率函数 $J(V_0,z)$ 是本文一维化约的核心工具；$J_\alpha$ 的计算方法直接借用该文框架。
- [sr_p006](/papers/sr_p006)：Pirjol-Zhu（2024）在 LSV 模型亚式期权中引入对数耦合技术，与本文的平方根耦合 ansatz 在方法论上互补；两种耦合均属"路径比例约束"思路，但适用区间不同。