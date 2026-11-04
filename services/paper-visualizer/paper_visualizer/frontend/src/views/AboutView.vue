<script setup lang="ts">
import { useLangStore } from '@/stores/lang'
const lang = useLangStore()
</script>

<template>
  <div class="max-w-3xl mx-auto px-6 py-10 text-slate-300 leading-relaxed">
    <template v-if="lang.current === 'zh'">
      <h2 class="text-2xl font-semibold mb-4">关于 Paper Visualizer</h2>
      <p class="mb-4">
        这是 MATHPROVER 项目的论文可视化工具。它用 AI 从每篇论文的 LaTeX 源文件生成
        定理层（30–60 分钟阅读）的教学内容，支持中英双语与 AI 问答。
      </p>
      <h3 class="text-lg font-semibold mt-6 mb-2">目标读者</h3>
      <p class="mb-4">
        具备测度论与随机分析基础的研究生或入门学者。工具默认假设你熟悉 Ito 微积分、
        弱收敛、鞅理论，但不熟悉具体某一篇论文。
      </p>
      <h3 class="text-lg font-semibold mt-6 mb-2">添加新论文</h3>
      <ol class="list-decimal ml-6 mb-4 space-y-1">
        <li>把论文放到 <code class="bg-slate-800 px-1 rounded">output/project9/main.tex</code>（或 main_v2.tex）。</li>
        <li>运行 <code class="bg-slate-800 px-1 rounded">python -m paper_visualizer.backend.ingest</code>。</li>
        <li>运行 <code class="bg-slate-800 px-1 rounded">python -m paper_visualizer.backend.generate</code>。</li>
        <li>刷新浏览器，新论文出现在首页。</li>
      </ol>
      <h3 class="text-lg font-semibold mt-6 mb-2">数据存放位置</h3>
      <p class="mb-4">
        所有 meta.json 和教学 Markdown 保存在 <code class="bg-slate-800 px-1 rounded">paper_visualizer/backend/content/</code>，
        纳入 git，可以手动编辑校对。
      </p>
      <h3 class="text-lg font-semibold mt-6 mb-2">内容 vs AI 问答</h3>
      <p>
        主体教学内容是预生成的（一次性，可缓存），浏览离线也行（除了 AI 问答）。
        每篇论文右上角的"问 Claude"按钮打开侧栏对话，实时流式回答，结合论文全文上下文。
      </p>
    </template>
    <template v-else>
      <h2 class="text-2xl font-semibold mb-4">About Paper Visualizer</h2>
      <p class="mb-4">
        This is the MATHPROVER paper visualization tool. It uses AI to turn each
        paper's LaTeX source into theorem-level teaching content (30–60 minute read)
        in both Chinese and English, with an AI Q&amp;A sidebar.
      </p>
      <h3 class="text-lg font-semibold mt-6 mb-2">Target audience</h3>
      <p class="mb-4">
        Graduate students and early researchers with measure-theoretic probability
        and stochastic calculus background. The tool assumes you know Ito calculus,
        weak convergence, and martingale theory, but not the specific paper.
      </p>
      <h3 class="text-lg font-semibold mt-6 mb-2">Adding a new paper</h3>
      <ol class="list-decimal ml-6 mb-4 space-y-1">
        <li>Place the paper at <code class="bg-slate-800 px-1 rounded">output/project9/main.tex</code> (or main_v2.tex).</li>
        <li>Run <code class="bg-slate-800 px-1 rounded">python -m paper_visualizer.backend.ingest</code>.</li>
        <li>Run <code class="bg-slate-800 px-1 rounded">python -m paper_visualizer.backend.generate</code>.</li>
        <li>Reload the page — the new paper appears on the home grid.</li>
      </ol>
      <h3 class="text-lg font-semibold mt-6 mb-2">Where does the data live</h3>
      <p class="mb-4">
        All meta.json and teaching Markdown files live under
        <code class="bg-slate-800 px-1 rounded">paper_visualizer/backend/content/</code>,
        git-tracked and editable by hand.
      </p>
      <h3 class="text-lg font-semibold mt-6 mb-2">Pre-generated content vs AI Q&amp;A</h3>
      <p>
        Core teaching content is pre-generated (one-time, cached) so reading works offline.
        The "Ask Claude" button on each paper opens a streaming chat sidebar with full
        paper context — online only.
      </p>
    </template>
  </div>
</template>
