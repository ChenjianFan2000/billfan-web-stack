---
paper_slug: mv_games
lang: zh
sections:
  - id: context
    title: 背景与动机
  - id: objects
    title: 核心数学对象
  - id: main-results
    title: 主要定理
  - id: proofs
    title: 证明草图
  - id: numerics
    title: 数值实验
  - id: connections
    title: 相关工作联系
---

## 背景与动机 {#context}

现代金融市场中，机构投资者不仅关注绝对收益，更被迫与同行比较相对表现。这种竞争压力催生了基准跟踪与羊群行为。与此同时，资产预期回报率等关键参数往往无法直接观测，基金经理需实时从价格数据中学习，在**部分信息**下做出投资决策。当竞争压力与信息不完全相互叠加时，投资组合的尾部风险会产生何种微妙效应？这正是本文研究的核心问题。

Huang 与 Sun（2025）（以下简称 HS2025）将均值-方差博弈与 Bayes 滤波框架结合，显式求解了常数漂移设定下 $N$ 人对称均值-方差博弈在全信息（FI）与部分信息（PI）两种情形的 Nash 均衡。他们的数值实验揭示了一个引人注目的现象：在部分信息下，相对绩效竞争显著放大了投资者财富的**向下风险**，而全信息情形下此效应几乎不存在。HS2025 将"部分信息的向下放大效应是否可以从理论上严格刻画"列为公开问题。

本文正面回应了这一公开问题，并给出了比原始猜想更精确、更令人惊讶的结论——**风险反转**（risk reversal）：FI 与 PI 投资者之间首次穿越时间的大小关系，取决于未观测到的真实漂移状态。在**好状态**（高漂移 $\mu_1$）下，PI 投资者因低估漂移而保守投资，其破产概率显著低于 FI；在**坏状态**（低漂移 $\mu_2$）下，PI 投资者因过度乐观而超额投资，破产概率可高达 FI 的 $300$ 倍。论文通过四个严格定理——指数上鞅界、鞅测度下的 Dubins–Schwarz 二次变差比较、$L^2$ 耦合坏状态放大不等式、$\lambda$-敏感性比较——以及全面的 Monte Carlo 分析，精确刻画了这一"无知悖论"。

---

## 核心数学对象 {#objects}

**1. 金融市场与财富过程**

股票价格满足
$$\frac{dS(t)}{S(t)} = \mu\,dt + \sigma\,dW(t),\qquad S(0)=s_0>0,$$
其中 $\sigma>0$ 已知，漂移 $\mu\in\{\mu_1,\mu_2\}$（$\mu_1>\mu_2>0$）固定但未知。投资者 $i$ 的财富过程为
$$dX_i(t) = \pi_i(t)\,\mu\,dt + \pi_i(t)\,\sigma\,dW(t),\qquad X_i(0)=x>0.$$
非平凡之处：漂移 $\mu$ 的二值性使得 Bayes 滤波在 $[0,1]$ 上诱导出扩散过程，而非一般的无穷维滤波。

**2. Nash 均衡策略**

在对称假设（所有投资者共享风险厌恶系数 $\gamma>0$，竞争权重 $\lambda\in[0,1)$，初始财富 $x$）下：

- **全信息均衡**：当真实漂移为 $\mu_k$ 时，FI Nash 均衡为确定性常数
$$\pi_k^{\mathrm{FI}} := \frac{\mu_k}{\sigma^2\,\gamma(1-\lambda)}.$$

- **部分信息均衡**：PI Nash 均衡为
$$\pi^*(t,q) = \frac{g(t,q)}{\gamma(1-\lambda)},$$
其中 $g(t,q) = \underbrace{\theta(q)/\sigma^2}_{\text{近视项}} - \underbrace{(\beta(q)/\sigma)\,\partial_q c(t,q)/\kappa}_{\text{对冲项}}$，$c(t,q)$ 满足 Cauchy 问题（见下文滤波方程）。**关键结构性质**：在对称均衡中，$g(t,q)$ 与 $\lambda$ 无关，竞争参数仅通过显式因子 $1/(1-\lambda)$ 进入策略。

**3. Bayes 后验滤波过程**

后验概率 $P(t):=\mathrm{Prob}(\mu=\mu_1\mid\mathcal{F}^S_t)$ 满足滤波 SDE
$$dP(t) = \beta(P(t))\,d\widehat{W}(t),\qquad P(0)=p,$$
其中
$$\theta(q):=\delta q+\mu_2,\qquad \beta(q):=\frac{\delta}{\sigma}q(1-q),\quad \delta:=\mu_1-\mu_2,$$
$\widehat{W}$ 为新息 Brownian 运动。非平凡之处：$P(t)$ 在 $\Prob_{\mu_1}$ 下为下鞅（收敛至 $1$），在 $\Prob_{\mu_2}$ 下为上鞅（收敛至 $0$），同一策略 $\pi^*$ 在两种真实状态下产生截然不同的风险特征。

**4. 首次穿越时间与安全边际**

$$\tau := \inf\{t\ge 0: X(t)\le D\},\qquad a:=x-D>0.$$
分别记 $\tau_k^{\mathrm{FI}}$（FI 破产时刻，状态 $k$）与 $\tau^{\mathrm{PI}}$（PI 破产时刻）。

**5. 鞅测度 $Q$**

由 Radon–Nikodym 密度定义：
$$\frac{dQ}{d\Prob_{\mu_1}}\bigg|_{\mathcal{F}_T} = \exp\!\biggl(-\frac{\mu_1}{\sigma}W(T)-\frac{\mu_1^2}{2\sigma^2}T\biggr).$$
在 $Q$ 下，$\widetilde{W}(t):=W(t)+(\mu_1/\sigma)t$ 为标准 Brownian 运动，两类财富过程均为连续局部鞅——这是进行 Dubins–Schwarz 比较的基础。

**6. 期望财富缺口**

$$G(\lambda,T):=\mathbb{E}_{\mu_1}[X^{\mathrm{FI}}(T)]-\mathbb{E}_{\mu_1}[X^{\mathrm{PI}}(T)]\ge 0.$$
此量衡量 PI 策略在好状态下的均值损失，但它无法反映尾部风险的方向性反转，这正是首次穿越分析的必要性所在。

---

## 主要定理 {#main-results}

### 好状态安全性

:::theorem{id=thm:expo_bound label="定理（指数安全界）"}
在 $\Prob_{\mu_1}$ 下，对任意 $T>0$：
$$\Prob_{\mu_1}\!\bigl(\tau^{\mathrm{PI}}\le T\bigr) \;\le\; \exp\!\biggl(-\frac{2\mu_1\,a}{\pi_1^{\mathrm{FI}}\,\sigma^2}\biggr) \;=\; \Prob_{\mu_1}\!\bigl(\tau_1^{\mathrm{FI}}<\infty\bigr).$$
即：PI 投资者的**有限时域**破产概率，有界于 FI 投资者的**无限时域**破产概率。
:::

在好状态下，PI 投资者因不知晓漂移处于高位而低估期望收益，投资量低于 FI 最优值：$\pi^*(t)\le\pi_1^{\mathrm{FI}}$。较低的仓位减少了组合波动，使得财富过程更难跌破警戒线。定理的核心结论是：PI 的任意有限期破产概率，不超过 FI 的无限期破产概率这一更宽松的界，从而说明 PI 投资者在好状态下享有指数量级的安全优势，其 Lundberg 指数比 FI 高出约 $5$–$6$ 倍（见数值结果）。

**Why it's surprising:** 人们通常认为信息不完全会带来劣势，但此定理表明：在好状态下，正是"无知"引发的保守行为使 PI 投资者**比全知的 FI 投资者更难破产**，且有限期风险甚至低于 FI 的无限期风险。

---

:::theorem{id=thm:Q_comparison label="定理（鞅测度二次变差比较）"}
定义 $Q$ 如上。在 $Q$ 下，FI 与 PI 财富过程均为连续局部鞅，$\widetilde{W}(t):=W(t)+(\mu_1/\sigma)t$ 为标准 $Q$-Brownian 运动。则：
$$Q\!\bigl(\tau^{\mathrm{PI}}\le T\bigr)\;\le\; Q\!\bigl(\tau_1^{\mathrm{FI}}\le T\bigr),$$
等号成立当且仅当 $\pi^*(t,P(t))=\pi_1^{\mathrm{FI}}$ 对 Lebesgue-a.e. $t\in[0,T]$，$Q$-a.s.。
:::

在鞅测度 $Q$ 下，两类财富过程均无漂移，区别仅在于二次变差：FI 过程的二次变差为确定性线性函数 $U(T)=(\pi_1^{\mathrm{FI}}\sigma)^2 T$，而 PI 过程的二次变差 $V(T)=\sigma^2\int_0^T[\pi^*(s)]^2\,ds\le U(T)$ 随机且更小。由 Dubins–Schwarz 定理，二次变差越小意味着时钟走得越慢，从而穿越障碍的概率越低。

**Why it's surprising:** 从测度变换角度，这一比较在 $Q$ 下是严格的，但由于 Girsanov 密度与破产事件的相关性，能否直接转化为物理测度 $\Prob_{\mu_1}$ 下的结论存在技术障碍（Girsanov obstruction），论文将其列为公开猜想，并辅以 20 万条路径的 Monte Carlo 模拟加以验证。

---

### 坏状态放大

:::theorem{id=thm:bad_state label="定理（坏状态破产放大）"}
在 $\Prob_{\mu_2}$ 下，令 $\bar{\pi}:=\pi^*(0)=\theta(p)/[\sigma^2\gamma(1-\lambda)]$。则：

**(i)（无限时域比较）** 对所有 $a>0$ 与 $p\in(0,1)$：
$$\Prob_{\mu_2}\!\bigl(\tau^{\mathrm{PI}}<\infty\bigr)>\Prob_{\mu_2}\!\bigl(\tau_2^{\mathrm{FI}}<\infty\bigr).$$

**(ii)（定量界）** 对任意 $\epsilon\in(0,\,\delta p/\mu_2)$ 与 $h>0$：
$$\Prob_{\mu_2}\!\bigl(\tau^{\mathrm{PI}}\le h\bigr)\;\ge\;\mathfrak{p}\!\bigl((1+\epsilon)a,\;\bar{\pi}\mu_2,\;\bar{\pi}\sigma,\;h\bigr)-\frac{K\,h^2}{\epsilon^2\,a^2},$$
其中 $\mathfrak{p}(a',b,c,T)$ 为漂移 $b$、扩散 $c$ 的 Bachelier–Lévy 破产概率，常数
$$K=\frac{2\delta^4p^2(1-p)^2}{\sigma^6\gamma^2(1-\lambda)^2}(4\sigma^2+\mu_2^2).$$
:::

在坏状态下，PI 投资者因先验赋予好状态正概率而高估漂移，初始投资量为 FI 最优值的 $\bar{\pi}/\pi_2^{\mathrm{FI}}=1+\delta p/\mu_2$ 倍（在 HS2025 参数下为 $5.5$ 倍）。更高的仓位极大增加了破产概率。定理 (i) 从无限时域给出定性比较，定理 (ii) 通过 $L^2$ 耦合技术，将 PI 过程的初始常数仓位段与一个参考 Brownian 运动耦合，给出有限时域的定量下界。

**Why it's surprising:** 坏状态下的破产概率放大比是**指数量级**的——在 HS2025 参数下约为 $307$ 倍——而好状态下的抑制比趋向于 $0$。两个方向的效应极度不对称，说明"无知悖论"在坏状态下的代价远超好状态下的红利。

---

### 敏感性放大

:::theorem{id=thm:sensitivity label="定理（$\lambda$-敏感性比较）"}
FI 破产概率满足：
$$-\log\Prob_{\mu_k}\!\bigl(\tau_k^{\mathrm{FI}}<\infty\bigr)=2\gamma(1-\lambda)\,a,$$
故 $\frac{d}{d\lambda}[-\log\Prob_{\mu_k}(\tau_k^{\mathrm{FI}}<\infty)]=-2\gamma a$。

由于 $g(t,q)$ 与 $\lambda$ 无关（对称均衡结构），PI 策略 $\pi^*(t)=g(t,P(t))/[\gamma(1-\lambda)]$ 的 Lundberg 指数满足
$$\psi^{\mathrm{PI}}(\lambda)=\psi^{\mathrm{PI}}(0)\cdot(1-\lambda),\qquad \frac{d\psi^{\mathrm{PI}}}{d\lambda}=-\psi^{\mathrm{PI}}(0).$$
由于 $\psi^{\mathrm{PI}}(0)\gg\psi^{\mathrm{FI}}(0)=2\gamma$，对数破产概率对 $\lambda$ 的绝对敏感性在 PI 下更大：
$$\frac{d/d\lambda\,[-\log\Prob(\tau^{\mathrm{PI}}\le T)]}{d/d\lambda\,[-\log\Prob(\tau_k^{\mathrm{FI}}<\infty)]}\;\approx\;\frac{\psi^{\mathrm{PI}}(0)}{\psi^{\mathrm{FI}}(0)}\;\approx\;5\text{–}6.$$
:::

此定理精确刻画了 HS2025 所猜测的"向下放大"机制：PI 投资者虽然在好状态下绝对更安全，但其安全边际对竞争强度 $\lambda$ 的侵蚀速率是 FI 的 $5$–$7$ 倍。随着 $\lambda$ 增大（即竞争加剧），PI 投资者的 Lundberg 指数下降更快，协同回撤（co-drawdown）的可能性以更高的速率攀升。

**Why it's surprising:** PI 投资者同时享有"绝对更安全"与"相对更脆弱"两种特性——她的破产缓冲区更厚，但竞争每增加一分，缓冲区受到的侵蚀也成比例地更大。这是部分信息与竞争交互作用的精确数学表述。

---

## 证明草图 {#proofs}

:::proof-sketch{for=thm:expo_bound}
1. **构造指数上鞅**：取倾斜参数 $\vartheta:=-2\mu_1/(\pi_1^{\mathrm{FI}}\sigma^2)<0$，定义指数过程 $Z(t):=\exp\!\bigl(\vartheta(X^{\mathrm{PI}}(t)-x)-\int_0^t\psi(s)\,ds\bigr)$，其中 $\psi(s):=\vartheta\pi^*(s)\mu_1+\tfrac{\vartheta^2}{2}(\pi^*(s))^2\sigma^2$。由 Itô 公式，$Z$ 的 $dt$ 项恰好抵消，$Z$ 为非负局部鞅，从而为上鞅。
2. **验证补偿项非正**：利用 $\pi^*(s)\le\pi_1^{\mathrm{FI}}$，分解 $\psi(s)=\pi^*(s)\cdot(-2\mu_1^2/(\pi_{\max}\sigma^2))\cdot[1-\pi^*(s)/\pi_{\max}]\le 0$，故 $\exp(-\int_0^t\psi(s)\,ds)\ge 1$。
3. **可选停时定理**：在停时 $\tau^{\mathrm{PI}}\wedge T$ 处，利用 $Z(0)=1\ge\mathbb{E}[Z(\tau\wedge T)]$，以及在 $\{\tau\le T\}$ 上 $Z(\tau)\ge e^{2\mu_1 a/(\pi_{\max}\sigma^2)}$，直接得到破产概率上界；再与经典 FI 无限期破产公式对比，完成等号识别。
:::

:::proof-sketch{for=thm:Q_comparison}
1. **Girsanov 变换**：通过 Radon–Nikodym 密度将 $\Prob_{\mu_1}$ 变为 $Q$，使两类财富过程均成为连续 $Q$-局部鞅，消除漂移，为比较创造对称基础。
2. **Dubins–Schwarz 表示**：对两类局部鞅分别应用 Dambis–Dubins–Schwarz 定理，表示为时变 Brownian 运动 $B_k(\cdot)$；FI 的时钟 $U(T)=(\pi_1^{\mathrm{FI}}\sigma)^2 T$ 为确定性线性函数，PI 的时钟 $V(T)=\sigma^2\int_0^T[\pi^*(s)]^2\,ds\le U(T)$ 随机且更小。
3. **单调性集合包含**：由 $V(T)\le U(T)$ 推出集合包含关系 $\{\inf_{v\le V(T)}B_2(v)\le -a\}\subseteq\{\inf_{v\le U(T)}B_2(v)\le -a\}$；再利用 $B_1,B_2$ 在 $Q$ 下同分布，取概率得 $Q(\tau^{\mathrm{PI}}\le T)\le Q(\tau_1^{\mathrm{FI}}\le T)$。
:::

:::proof-sketch{for=thm:bad_state}
1. **精确 FI 破产公式**：在 $\Prob_{\mu_2}$ 下，FI 财富偏差为常数漂移正向 Brownian 运动，由经典首次穿越公式得 $\Prob_{\mu_2}(\tau_2^{\mathrm{FI}}<\infty)=\exp(-2\gamma(1-\lambda)a)$。
2. **$L^2$ 耦合下界**：将 PI 策略在短时段 $[0,h]$ 近似为初始常数仓位 $\bar{\pi}=\pi^*(0)>\pi_2^{\mathrm{FI}}$；利用滤波连续性引理（$\mathbb{E}[\sup_{s\in[0,h]}|P(s)-p|^2]\le\delta^2 h/(4\sigma^2)$）量化近似误差，得到形如 $\Prob_{\mu_2}(\tau^{\mathrm{PI}}\le h)\ge\mathfrak{p}((1+\epsilon)a,\bar{\pi}\mu_2,\bar{\pi}\sigma,h)-Kh^2/(\epsilon^2 a^2)$ 的下界。
3. **Bachelier–Lévy 单调性与放大比**：引理 \ref{lem:BL_mono} 保证对常数仓位 $\pi>\pi_2^{\mathrm{FI}}$，破产概率严格增大；结合 $\bar{\pi}/\pi_2^{\mathrm{FI}}=1+\delta p/\mu_2$ 的显式超投资比，推导出指数放大比 $C\exp(2\gamma(1-\lambda)a\cdot\delta p/(\delta p+\mu_2))$，在 HS2025 参数下约为 $307$。
:::

:::proof-sketch{for=thm:sensitivity}
1. **FI Lundberg 指数的精确公式**：由常数仓位 FI 策略的经典无限期破产公式，$-\log\Prob_{\mu_k}(\tau_k^{\mathrm{FI}}<\infty)=2\gamma(1-\lambda)a$，对 $\lambda$ 求导得敏感性 $-2\gamma a$。
2. **利用 $g$ 的 $\lambda$-无关性**：在对称均衡中，$g(t,q)$ 与 $\lambda$ 无关（Remark 2.3），故 PI 策略整体以 $1/(1-\lambda)$ 缩放；PI Lundberg 指数因此满足 $\psi^{\mathrm{PI}}(\lambda)=\psi^{\mathrm{PI}}(0)(1-\lambda)$，其对 $\lambda$ 的导数为 $-\psi^{\mathrm{PI}}(0)$。
3. **敏感性比率**：由定理 \ref{thm:expo_bound} 提供的 PI Lundberg 指数下界 $\psi^{\mathrm{PI}}(0)\ge 2\gamma\mu_1/\theta(p)$（在 HS2025 参数下约为 $1.82\times 2\gamma$，而 Monte Carlo 估计约为 $5$–$6\times 2\gamma$），得到绝对敏感性之比 $\psi^{\mathrm{PI}}(0)/\psi^{\mathrm{FI}}(0)\approx 5$–$6$。
:::

---

## 数值实验 {#numerics}

数值分析基于 HS2025 校准参数：$\mu_1=0.2$，$\mu_2=0.02$，$\sigma=0.1$，$\gamma=5$，$x=3$，先验 $p=0.5$，并在警戒线 $D\in[1.5,2.5]$ 与竞争参数 $\lambda\in[0,0.9]$ 的完整参数网格上进行，每组参数使用 $200{,}000$ 条模拟路径。

**好状态安全性验证**：在所有测试的 $(D,\lambda)$ 参数组合下，Monte Carlo 均一致地给出 $\Prob_{\mu_1}(\tau^{\mathrm{PI}}\le T)<\Prob_{\mu_1}(\tau_1^{\mathrm{FI}}\le T)$，从而为猜想（Conjecture 3.5）提供了强数值支撑。有效 PI Lundberg 指数的估计值约为 FI 理论下界的 $5$–$6$ 倍，差距归因于 PI 策略中的对冲分量（hedging demand）进一步压低了实际仓位。有效指数表展示了跨越不同 $\lambda$ 值的一致性。

**坏状态放大验证**：在坏状态下，数值结果证实了定理 \ref{thm:bad_state} 的定性结论。无限期破产概率之比 $\Prob_{\mu_2}(\tau^{\mathrm{PI}}<\infty)/\Prob_{\mu_2}(\tau_2^{\mathrm{FI}}<\infty)$ 在基准参数下约为 $307$，与理论预测吻合；随着安全边际 $a=x-D$ 增大，此比率呈指数增长。临界先验 $p^*$（混合测度下 FI 与 PI 破产概率相等的先验值）在所有测试参数组合下均满足 $p^*<0.07$，说明对几乎任何非退化先验，PI 在混合意义下都更安全。

**敏感性与相图**：$\lambda$-敏感性分析表明，$\log\Prob(\tau^{\mathrm{PI}}\le T)$ 对 $\lambda$ 的斜率约为 $\log\Prob(\tau^{\mathrm{FI}}<\infty)$ 对 $\lambda$ 斜率的 $5$–$7$ 倍，与定理 \ref{thm:sensitivity} 的预测精确匹配。相图分析在 $(D,\lambda)$ 平面上清晰展示了"好状态 PI 更安全"与"坏状态 PI 更危险"的分界区域，以及在不同参数校准下结论的稳健性。

---

## 相关工作联系 {#connections}

- [variance_options](/papers/variance_options)：两篇论文均涉及随机过程的二次变差结构；本文中 Dubins–Schwarz 定理利用二次变差排序比较破产概率，与方差期权定价中二次变差的核心角色形成方法论呼应。

- [var_ratio](/papers/var_ratio)：方差比统计量的分析依赖于信息结构对波动率估计的影响；本文对 FI 与 PI 投资者波动率暴露差异的精确刻画（仓位上界 $\pi^*(t)\le\pi_1^{\mathrm{FI}}$）与信息不完全下波动率比较的框架共享技术基础。

- [cross_impact](/papers/cross_impact)：交叉冲击（cross impact）模型研究多资产/多参与者情形下的策略相互依赖；本文 $N$ 人均值-方差博弈中竞争参数 $\lambda$ 对个体策略的放大机制，与交叉冲击引起的系统性风险传导机制在数学结构上相互呼应。