---
paper_slug: variance_options
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
    title: 关联工作
---

## 背景与动机 {#context}

已实现方差期权（variance options）是以标的资产在固定期限内的年化已实现方差为结算基准的衍生品。随着2024年9月CBOE标普500方差期货上市，这类产品吸引了学术界与从业者的广泛关注。从定价角度看，一个核心问题是：当期权到期时间 $T \to 0$ 时，价外（OTM）方差看涨期权的价格以何种速率指数衰减？大偏差理论给出答案：

$$\lim_{T \to 0} T \log C(T) = -I_\rho(S_0, V_0, K),$$

其中**速率函数** $I_\rho$ 控制着短期渐近行为。Pirjol、Wang与Zhu（PWZ，2025）将 $I_\rho$ 刻画为一个以资产价格路径 $g$ 和波动率路径 $h$ 为变量的**有约束变分问题**的解。他们在相关系数 $\rho = 0$ 时给出了精确解，并对一般 $\rho$ 证明了上下界

$$\frac{1}{1+|\rho|} I_0 \leq I_\rho \leq \frac{1}{1-|\rho|} I_0,$$

但指出对 $\rho \neq 0$ 的欧拉–拉格朗日方程"看起来不可能有显式解"。

本文填补了这一缺口：通过将 $\rho$ 视为扰动参数，建立 $I_\rho$ 关于 $\rho = 0$ 的严格摄动展开，并证明其实解析性（real-analyticity）。关键工具是**Banach空间中的解析隐函数定理**，将欧拉–拉格朗日方程组视为算子方程并在 $\rho = 0$ 处验证可逆性。与此同时，对于纯随机波动率模型（局部波动率函数 $\eta$ 为常数），本文证明了一个远比渐近展开更强的结果：速率函数完全与相关系数无关，即 $I_\rho = I_0$ 对所有 $\rho \in (-1,1)$ 精确成立。

在Heston模型中，$\rho = 0$ 的变分问题进一步化归为经典的**Ermakov–Pinney方程** $u'' = -\lambda/u^3$，从而得到仅涉及初等函数的完全显式解。最终，本文还建立了速率函数扰动展开与**Alòs分解**之间的深层联系：两者被同一个截面相关泛函 $C[g,h]$ 控制，但分别作用于价格分布的"尾部"（极端行权价）和"主体"（温和行权价），形成一种"体–尾对偶"结构。

## 核心数学对象 {#objects}

**1. 局部-随机波动率（LSV）模型**

在风险中性测度 $\mathbb{Q}$ 下，资产价格 $S_t$ 与方差过程 $V_t$ 满足：

$$\frac{\mathrm{d}S_t}{S_t} = \eta(S_t)\sqrt{V_t}\bigl(\rho\,\mathrm{d}Z_t + \sqrt{1-\rho^2}\,\mathrm{d}W_t\bigr), \quad \frac{\mathrm{d}V_t}{V_t} = \mu(V_t)\,\mathrm{d}t + \sigma(V_t)\,\mathrm{d}Z_t,$$

其中 $W_t, Z_t$ 相互独立，$\rho \in (-1,1)$ 为资产–波动率相关系数，$\eta(\cdot)$ 为局部波动率函数。非平凡之处在于 $\eta$ 的存在使资产动态与波动率过程通过变分约束发生耦合，令 $\rho \neq 0$ 时的变分问题不可分离。

**2. 作用泛函与三个基本二次型**

对路径 $(g,h) \in \mathrm{AC}[0,1]^2$（分别表示 $\log S_t$ 与 $\log V_t$ 的时间缩放路径），作用泛函分解为：

$$\Lambda_\rho[g,h] = \frac{1}{2(1-\rho^2)}\bigl(A[g,h] + B[g,h] - 2\rho\,C[g,h]\bigr),$$

其中三个基本泛函为：
$$A[g,h] := \int_0^1 \frac{(g')^2}{\eta^2(e^g)\,e^h}\,\mathrm{d}t, \quad B[g,h] := \int_0^1 \frac{(h')^2}{\sigma^2(e^h)}\,\mathrm{d}t, \quad C[g,h] := \int_0^1 \frac{g'\,h'}{\eta(e^g)\,e^{h/2}\,\sigma(e^h)}\,\mathrm{d}t.$$

$A$ 称为**资产作用量**，$B$ 称为**波动率作用量**，$C$ 称为**截面相关泛函**。非平凡之处在于 $C$ 的符号不定，且恰好是连接扰动展开与Alòs分解的核心对象。

**3. 速率函数（有约束变分问题）**

$$I_\rho(S_0, V_0, K) = \inf_{\substack{g(0)=\log S_0,\;h(0)=\log V_0\\ \int_0^1 e^{h(t)}\eta^2(e^{g(t)})\,\mathrm{d}t = K}} \Lambda_\rho[g,h].$$

边界条件在 $t=1$ 处为横截性条件 $g'(1) = h'(1) = 0$（自由端点）。非平凡之处在于 $\eta$ 非常数时，约束将 $g$ 与 $h$ 耦合，使问题不可分离。

**4. 截面相关泛函 $C[g,h]$ 的Cauchy–Schwarz界**

由Cauchy–Schwarz不等式：$|C[g,h]| \leq \sqrt{A[g,h] \cdot B[g,h]} \leq \Lambda_0[g,h]$，这保证了展开系数 $|I_1| \leq I_0$，与PWZ界在一阶处相容。

**5. Ermakov–Pinney方程（Heston模型的化归）**

在Heston模型中令 $u = 1/\sqrt{v}$（$v = e^h$ 为方差路径），$\rho = 0$ 的变分问题等价于最小化 $\int_0^1 (u')^2\,\mathrm{d}t$ 约束 $\int_0^1 u^{-2}\,\mathrm{d}t = K$。欧拉–拉格朗日方程为：

$$u''(t) = -\frac{\lambda}{u(t)^3},$$

即经典的Ermakov–Pinney方程，其通解为 $u(t) = \sqrt{A + Bt + Ct^2}$，具有完全初等的显式解。这在方差期权定价中是首次出现。

**6. 边界算子与可逆性**

对欧拉–拉格朗日映射 $F: \mathcal{X} \times (-1,1) \to \mathcal{Y}$，其在 $\rho=0$ 处的Fréchet导数具有**加边结构**（bordered structure）：

$$D_{(g,h,\lambda)}F\big|_0 = \begin{pmatrix} \delta^2\mathcal{L}_0 & \delta\Phi^T \\ \delta\Phi & 0 \end{pmatrix}.$$

该算子的可逆性（由变分问题的正定二次型保证）是应用解析隐函数定理的关键前提。

## 主要结果 {#main-results}

:::theorem{id=thm_analyticity label="定理：速率函数的实解析性"}
在假设（正则性、严格正性、非退化性）下，存在 $r > 0$ 使得：

(i) 极小元 $(g^*(\rho), h^*(\rho), \lambda^*(\rho))$ 作为映射 $(-r,r) \to H^1[0,1]^2 \times \mathbb{R}$ 是实解析的。

(ii) 速率函数 $I_\rho = \Lambda_\rho[g^*(\rho), h^*(\rho)]$ 在 $(-r,r)$ 上实解析，并有收敛的Taylor展开：

$$I_\rho = \sum_{k=0}^{N} I_k\,\rho^k + R_{N+1}(\rho), \qquad |R_{N+1}(\rho)| \leq \frac{M\,|\rho|^{N+1}}{r - |\rho|}.$$

(iii) 收敛半径满足 $r \geq \alpha / \|D_\rho F|_0\|$，其中 $\alpha$ 为二次型的强制性常数。
:::

本定理表明 $I_\rho$ 不仅有形式幂级数展开，而且在 $|\rho| < r$ 的区间内**严格收敛**，并给出了余项的显式Cauchy型误差界。证明的核心是将欧拉–拉格朗日方程组写成Banach空间上的算子方程 $F(g,h,\lambda;\rho) = 0$，然后验证 $F$ 关于所有变量实解析且在 $\rho = 0$ 处 $D_{(g,h,\lambda)}F$ 可逆，从而对 $\rho$ 应用解析隐函数定理。

**为何令人意外：** 尽管作用泛函 $\Lambda_\rho$ 在 $\rho = \pm 1$ 有极点，收敛半径 $r$ 可能严格小于1，但对纯随机波动率模型，该极点被完全吸收，$I_\rho$ 实际上在整个 $(-1,1)$ 上为常数——这比任何有限收敛半径的结论都强得多。

---

:::theorem{id=thm_main label="定理：一阶扰动修正"}
在正则性与非退化性假设下，速率函数满足：

$$I_\rho = I_0 - \rho\, C[g_0, h_0] + O(\rho^2),$$

其中 $C[g_0,h_0]$ 为截面相关泛函在 $\rho=0$ 最优路径处的值。等价地，

$$I_1 := \left.\frac{\mathrm{d} I_\rho}{\mathrm{d}\rho}\right|_{\rho=0} = -\int_0^1 \frac{g_0'(t)\,h_0'(t)}{\eta\bigl(e^{g_0(t)}\bigr)\,e^{h_0(t)/2}\,\sigma\bigl(e^{h_0(t)}\bigr)}\,\mathrm{d}t = -C_0.$$
:::

一阶修正 $I_1 = -C_0$ 具有清晰的金融含义：它度量了沿 $\rho = 0$ 最优路径，**资产价格最优波动** $g_0'/(\eta e^{h_0/2})$ 与**波动率最优波动** $h_0'/\sigma(e^{h_0})$ 之间的相关性。当这两个波动正相关（$C_0 > 0$）时，引入正相关系数 $\rho > 0$ 会降低速率函数，使价外方差期权的短期价格指数衰减减慢，这正是资产–波动率正相关增大大方差实现概率的直觉。

**为何令人意外：** 利用包络定理（Danskin定理），最优路径在 $\rho$ 方向上的变化对 $I_\rho$ 的一阶导数**无贡献**，从而将 $I_1$ 化简为一个在已知 $\rho=0$ 最优路径上的单积分，无需求解 $\rho \neq 0$ 的欧拉–拉格朗日方程。

---

:::theorem{id=cor_SV label="推论：纯随机波动率模型的相关不变性"}
当 $\eta(\cdot) \equiv \eta_0$ 为常数时（纯随机波动率模型），速率函数与相关系数无关：

$$I_\rho = I_0 \qquad \text{对所有 } \rho \in (-1,1).$$

即 $I_k = 0$ 对所有 $k \geq 1$ 成立。等价地，$I_\rho$ 连续延拓至 $\rho = \pm 1$，且 $I_{\pm 1} = I_0$。
:::

这一结果揭示了纯随机波动率模型的一种结构刚性：**方差期权的短期速率函数完全不受资产–波动率相关系数影响**。机制是：当 $\eta$ 为常数时，约束 $\int_0^1 \eta_0^2 e^{h}\,\mathrm{d}t = K$ 完全不依赖于资产路径 $g$，从而 $g$ 可以自由地"吸收"相关系数，通过选取 $g_\rho'(t) = \rho\,e^{h/2}\,h'/\sigma(e^h)$ 使作用泛函中的相关项恰好抵消，而不影响约束。这与股票期权的情形形成鲜明对比：股票期权中，$\rho$ 通过偏度直接影响隐含波动率。

**为何令人意外：** Heston模型（及所有常数 $\eta$ 的随机波动率模型）中，$\rho$ 对方差期权短期速率函数的影响为**精确零**，而非"小"或"高阶小"——这意味着 $\rho=0$ 的显式公式即为精确答案，无需任何修正。

---

:::theorem{id=thm_heston label="定理：Heston模型的显式解"}
在Heston模型中（$\eta \equiv 1$，$\sigma(V) = \xi\sqrt{V}$），$\rho=0$ 的最优方差路径和速率函数由如下显式公式给出。

**(i) 最优方差路径。** 由约束方程

$$\frac{\arctan\!\left(\sqrt{p/(1-p)}\right)}{\sqrt{p\,(1-p)}} = \frac{K}{V_0}$$

隐式确定 $p \in (0,1)$，则最优方差路径为

$$v^*(t) = \frac{V_0}{1 - p + p(t-1)^2}, \qquad t \in [0,1].$$

**(ii) 速率函数。**

$$I_0(K) = \frac{2p}{\xi^2 V_0}\left[1 - \sqrt{\frac{1-p}{p}}\,\arctan\!\left(\sqrt{\frac{p}{1-p}}\right)\right].$$

**(iii)** Lagrange乘子为 $\lambda_0 = I_0/K$。
:::

该定理将Heston模型 $\rho=0$ 的变分问题化归为Ermakov–Pinney方程并完全显式求解，获得仅含反正切和初等运算的闭合公式。最优路径 $v^*(t)$ 是一个关于 $(t-1)^2$ 的有理函数，在 $t=0$ 处取值 $V_0$，在 $t=1$ 处达到最大值 $V_0/(1-p)$（对价外看涨期权 $K > V_0$）。

**为何令人意外：** Ermakov–Pinney方程首次出现在量子力学和宇宙学中，本文是其在方差期权定价中的首次应用。更重要的是，结合推论（相关不变性），该公式不仅是 $\rho=0$ 的近似，而是**对所有 $\rho \in (-1,1)$ 精确成立**的Heston方差期权速率函数。

---

:::theorem{id=prop_saturation label="命题：Heston模型的远翼饱和"}
在Heston模型中，当 $K \to \infty$ 时：

$$I_0(K) \;\to\; I_0^{\max} := \frac{2}{\xi^2 V_0}.$$

更精确地，当 $p \to 1^-$ 时：

$$I_0(K) = \frac{2}{\xi^2 V_0}\left[1 - \sqrt{\frac{1-p}{p}}\,\frac{\pi}{2} + O(1-p)\right] \to \frac{2}{\xi^2 V_0}.$$
:::

速率函数在行权价 $K \to \infty$ 时趋向有限上界 $2/(\xi^2 V_0)$，这直接预言了方差期权深度价外看涨期权的**隐含波动率微笑趋于平坦**（而非发散）。具体地，深度价外的隐含波动率满足 $\Sigma_V(K) \sim |\log(K/F_V)| / \sqrt{2 I_0^{\max}}$，即隐含波动率仅以 $\log K$ 的速率增长，远慢于股票期权。

**为何令人意外：** 对股票期权，大偏差速率函数随行权价趋于无穷而无限增大（Lee矩公式）。方差期权的"饱和"现象源于方差过程本身的对数正态结构——波动率路径在有限作用代价下可以任意抬升。

## 证明梗概 {#proofs}

:::proof-sketch{for=thm_analyticity}
1. **构造算子方程**：将欧拉–拉格朗日方程组（含横截性条件和约束）写成Banach空间之间的映射 $F(g,h,\lambda;\rho) = 0$，其中 $F: H^1[0,1]^2 \times \mathbb{R} \times (-1,1) \to (H^{-1}[0,1])^2 \times \mathbb{R}^3$。
2. **验证联合解析性**：利用 $\eta, \sigma$ 的实解析性和 $1/(1-\rho^2)$ 的解析性，证明 $F$ 关于 $(g,h,\lambda,\rho)$ 联合实解析（Banach空间上解析函数的复合规则）。
3. **验证加边算子可逆性**：在 $\rho=0$ 处，Fr\'echet导数 $D_{(g,h,\lambda)}F$ 具有加边结构；利用非退化假设（二次型在约束切空间上正定）和约束满射性，验证其作为有界线性算子可逆。
4. **应用解析隐函数定理**：由Banach空间版本的解析隐函数定理（Deimling, Zeidler），零集在 $\rho=0$ 邻域内由实解析曲线参数化，得到极小元和速率函数的解析性。
5. **Cauchy误差界**：由解析函数的Cauchy积分公式直接得到截断误差的几何级数界 $M|\rho|^{N+1}/(r-|\rho|)$。
:::

:::proof-sketch{for=thm_main}
1. **包络定理（Danskin定理）**：由于极小元 $(g^*(\rho), h^*(\rho))$ 在 $\rho$ 上光滑，$\mathrm{d}I_\rho/\mathrm{d}\rho = \partial\Lambda_\rho/\partial\rho$ 在最优路径处求值，路径对 $\rho$ 的导数不出现（一阶无贡献）。
2. **计算 $\partial\Lambda_\rho/\partial\rho$**：对分解式 $\Lambda_\rho = (A+B-2\rho C)/(2(1-\rho^2))$ 关于 $\rho$ 求偏导，得 $\partial\Lambda_\rho/\partial\rho\big|_{\rho=0} = -C[g,h]$。
3. **代入最优路径**：将 $(g,h) = (g_0, h_0)$ 代入，直接得到 $I_1 = -C[g_0,h_0] = -C_0$，完成一阶展开。
:::

:::proof-sketch{for=cor_SV}
1. **构造可行路径族**：对任意满足约束的波动率路径 $h$，定义资产路径 $g_\rho(t) := \log S_0 + \rho\int_0^t e^{h/2}h'/\sigma(e^h)\,\mathrm{d}s$，其中利用 $h'(1)=0$ 验证横截性条件 $g_\rho'(1) = 0$ 自动满足。
2. **精确消去相关项**：将 $g_\rho$ 代入作用泛函，发现 $g_\rho'/(\eta_0 e^{h/2}) = \rho h'/\sigma(e^h)$，使得 $A+B-2\rho C = A+B-2\rho C$ 中分子为零（$A$ 项与 $2\rho C$ 项恰好抵消），从而 $\Lambda_\rho[g_\rho,h] = B[h]/2$。
3. **上下界合并**：一方面 $I_\rho \leq \inf_h B[h]/2 = I_0$（由上述构造）；另一方面 $\Lambda_\rho[g,h] \geq B[h]/2 \geq I_0$（作用泛函第一项非负），故 $I_\rho \geq I_0$，两者相等。
:::

:::proof-sketch{for=thm_heston}
1. **换元 $u = 1/\sqrt{v}$**：令 $u(t) = v(t)^{-1/2}$，将变分问题化为 $\min \int (u')^2\,\mathrm{d}t$ 约束 $\int u^{-2}\,\mathrm{d}t = K$，欧拉–拉格朗日方程化为Ermakov–Pinney方程 $u'' = -\lambda/u^3$。
2. **显式求解Ermakov–Pinney方程**：其通解为 $u(t) = \sqrt{A+Bt+Ct^2}$，利用初始条件 $u(0) = 1/\sqrt{V_0}$ 和横截性条件 $u'(1) = 0$ 确定参数，得 $v^*(t) = V_0/(1-p+p(t-1)^2)$。
3. **约束方程确定参数 $p$**：将 $v^*$ 代入约束 $\int_0^1 v^*\,\mathrm{d}t = K$，利用 $\int_0^1 \mathrm{d}s/((1-p)+ps^2)$ 的反正切公式得到关于 $p$ 的隐式方程。
4. **计算速率函数**：将 $u' = C(t-1)/u(t)$ 代入 $I_0 = (2/\xi^2)\int(u')^2\,\mathrm{d}t$，化简为含参数 $p$ 的初等函数表达式。
:::

## 数值实验 {#numerics}

数值实验分为两大类，分别验证本文的两个核心结论。

**第一类：Tanh LSV模型的扰动展开验证。** 选取非常数局部波动率函数 $\eta(S) = \tanh(\cdot)$，参数设置涵盖多种行权价水平和相关系数 $\rho \in [-0.7, 0.7]$。通过蒙特卡洛模拟（短期限 $T = 0.01$，路径数 $10^7$）直接估计速率函数，然后与一阶近似 $I_0 - \rho C_0$ 和二阶近似（需数值求解线性化边值问题得到 $(g_1, h_1)$）进行比较。结果表明，对于 $|\rho| \leq 0.5$，一阶近似的相对误差低于3%，二阶近似则进一步将误差降至0.5%以内；当 $|\rho|$ 接近0.7时，展开精度有所下降，与收敛半径 $r < 1$ 的理论预测一致。

**第二类：Heston模型的相关不变性验证。** 通过对变分问题进行全数值优化（离散化欧拉–拉格朗日方程组的有限差分求解），在参数空间 $(\xi, V_0, K)$ 的网格上，对 $\rho \in \{-0.9, -0.7, \ldots, 0.7, 0.9\}$ 分别求解变分问题，所得 $I_\rho$ 与 $I_0$ 的差值均在机器精度（$\approx 10^{-14}$）范围内，完美验证了 $I_\rho = I_0$ 的精确等式。同时，将定理中 $I_0$ 的闭合公式与PWZ的近ATM渐近公式 $I_0 \approx (3/(2\xi^2 V_0)) x^2$（$x = \log(K/V_0)$）进行交叉验证，两者在 $|x| \leq 0.2$ 范围内高度吻合（相对误差 $<1\%$），确认了两种方法的一致性。敏感性分析还验证了 $I_0 \propto 1/\xi^2$（命题~\ref{prop:xi_limits}）和 $I_0 \propto 1/V_0$（命题~\ref{prop:V0_limits}）的理论预测。

## 关联工作 {#connections}

- [project7](/papers/project7)：PWZ（2025）对LSV模型中方差期权速率函数的变分问题给出了 $\rho=0$ 的基础解，本文以其最优路径 $(g_0