import { useEffect, useMemo, useState, useTransition, type JSX } from "react"
import { getPaperFileUrl } from "../api/paperAssistant"
import type { CategoryNode, Paper } from "../lib/types"
import { formatAuthors, mapPapersByCategory } from "../lib/tree"
import { Spinner } from "./ui/Spinner"

type Props = {
  categories: CategoryNode[]
  papers: Paper[]
  onSetPaperCategories: (paperId: number, categoryIds: number[]) => Promise<void>
  onEditPaperMetadata: (paper: Paper) => Promise<void>
  onAskAgentAboutPaper: (paper: Paper) => void
  onDeletePaper: (paper: Paper) => Promise<void>
  paperActionState?: { id: number; action: "move" | "edit" | "delete" } | null
}

export function PaperLibrary({
  categories,
  papers,
  onSetPaperCategories,
  onEditPaperMetadata,
  onAskAgentAboutPaper,
  onDeletePaper,
  paperActionState,
}: Props) {
  const [expandedPaperIds, setExpandedPaperIds] = useState<Record<number, boolean>>({})
  const [expandedCategoryIds, setExpandedCategoryIds] = useState<Record<number, boolean>>({})
  const [categorySelections, setCategorySelections] = useState<Record<number, number[]>>({})
  const [toggleTarget, setToggleTarget] = useState<{ kind: "paper" | "category"; id: number } | null>(null)
  const [isPending, startTransition] = useTransition()

  useEffect(() => {
    if (!isPending) {
      setToggleTarget(null)
    }
  }, [isPending])

  useEffect(() => {
    // Keep checkbox draft in sync with latest server data after refresh/actions.
    setCategorySelections({})
  }, [papers])

  const papersByCategory = useMemo(() => mapPapersByCategory(papers), [papers])

  const allCategoryOptions = useMemo(() => {
    const out: Array<{ id: number; name: string }> = []
    const walk = (nodes: CategoryNode[], prefix = "") => {
      nodes.forEach((node) => {
        const label = prefix ? `${prefix} / ${node.name}` : node.name
        out.push({ id: node.id, name: label })
        walk(node.children ?? [], label)
      })
    }
    walk(categories)
    return out
  }, [categories])

  const togglePaper = (paperId: number) => {
    setToggleTarget({ kind: "paper", id: paperId })
    startTransition(() => {
      setExpandedPaperIds((prev) => ({ ...prev, [paperId]: !prev[paperId] }))
    })
  }

  const toggleCategory = (categoryId: number) => {
    setToggleTarget({ kind: "category", id: categoryId })
    startTransition(() => {
      setExpandedCategoryIds((prev) => ({ ...prev, [categoryId]: !prev[categoryId] }))
    })
  }

  const renderPaper = (paper: Paper) => {
    const expanded = !!expandedPaperIds[paper.id]
    const selectedCategoryIds =
      categorySelections[paper.id] ??
      (paper.category_ids?.length ? paper.category_ids : paper.category_id == null ? [] : [paper.category_id])
    const isToggling = isPending && toggleTarget?.kind === "paper" && toggleTarget.id === paper.id
    const paperBusyAction = paperActionState?.id === paper.id ? paperActionState.action : null

    return (
      <div key={`paper-${paper.id}`} className="rounded-lg border border-slate-700/60 bg-slate-900/70 p-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h4 className="truncate text-sm font-semibold text-slate-100">{paper.title || `未命名论文 #${paper.id}`}</h4>
            <p className="truncate text-xs text-slate-400">
              {formatAuthors(paper.authors)} · {paper.year ?? "n.d."}
            </p>
            <p className="mt-1 text-xs text-slate-300">{paper.summary_one_line || "暂无一句话概括"}</p>
          </div>
          <div className="flex shrink-0 gap-2">
            <button
              className="inline-flex items-center gap-1 rounded border border-slate-600 px-2 py-1 text-xs hover:border-cyan hover:text-cyan"
              onClick={() => togglePaper(paper.id)}
              type="button"
            >
              {isToggling ? <Spinner /> : null}
              {expanded ? "收起" : "展开"}
            </button>
          </div>
        </div>
        {expanded ? (
          <div className="mt-3 space-y-2 animate-fade-in-fast">
            <div className="space-y-1 rounded border border-slate-700/60 bg-slate-950/60 p-2">
              <p className="text-xs text-slate-400">设置分类（可多选）</p>
              <div className="max-h-36 space-y-1 overflow-auto pr-1 scrollbar-thin">
                {allCategoryOptions.map((opt) => (
                  <label key={opt.id} className="flex cursor-pointer items-center gap-2 text-xs text-slate-200">
                    <input
                      checked={selectedCategoryIds.includes(opt.id)}
                      disabled={paperBusyAction !== null}
                      onChange={(event) => {
                        const checked = event.target.checked
                        setCategorySelections((prev) => {
                          const base =
                            prev[paper.id] ??
                            (paper.category_ids?.length ? paper.category_ids : paper.category_id == null ? [] : [paper.category_id])
                          const current = new Set(base)
                          if (checked) {
                            current.add(opt.id)
                          } else {
                            current.delete(opt.id)
                          }
                          const next = allCategoryOptions.map((item) => item.id).filter((id) => current.has(id))
                          return { ...prev, [paper.id]: next }
                        })
                      }}
                      type="checkbox"
                    />
                    <span>{opt.name}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                className="inline-flex items-center gap-1 rounded border border-slate-600 px-2 py-1 text-xs hover:border-cyan hover:text-cyan disabled:opacity-40"
                disabled={paperBusyAction !== null}
                onClick={() => {
                  onSetPaperCategories(paper.id, selectedCategoryIds).catch(() => undefined)
                }}
                type="button"
              >
                {paperBusyAction === "move" ? <Spinner /> : null}
                设置分类
              </button>
              <button
                className="rounded border border-slate-600 px-2 py-1 text-xs hover:border-slate-400 disabled:opacity-40"
                disabled={paperBusyAction !== null}
                onClick={() => {
                  setCategorySelections((prev) => ({ ...prev, [paper.id]: [] }))
                }}
                type="button"
              >
                清空分类
              </button>
              <button
                className="inline-flex items-center gap-1 rounded border border-slate-600 px-2 py-1 text-xs hover:border-violet hover:text-violet disabled:opacity-40"
                disabled={paperBusyAction !== null}
                onClick={() => {
                  onEditPaperMetadata(paper).catch(() => undefined)
                }}
                type="button"
              >
                {paperBusyAction === "edit" ? <Spinner /> : null}
                编辑元数据
              </button>
              <button
                className="rounded border border-slate-600 px-2 py-1 text-xs hover:border-emerald-400 hover:text-emerald-200 disabled:cursor-not-allowed disabled:opacity-40"
                disabled={!paper.file_path}
                onClick={() => {
                  window.open(getPaperFileUrl(paper.id, "preview"), "_blank", "noopener,noreferrer")
                }}
                type="button"
              >
                预览
              </button>
              <button
                className="rounded border border-slate-600 px-2 py-1 text-xs hover:border-indigo-400 hover:text-indigo-200 disabled:cursor-not-allowed disabled:opacity-40"
                disabled={!paper.file_path}
                onClick={() => {
                  window.open(getPaperFileUrl(paper.id, "download"), "_blank", "noopener,noreferrer")
                }}
                type="button"
              >
                下载
              </button>
              <button
                className="rounded border border-cyan/60 px-2 py-1 text-xs text-cyan hover:bg-cyan/10"
                onClick={() => {
                  onAskAgentAboutPaper(paper)
                }}
                type="button"
              >
                向 AI 提问
              </button>
              <button
                className="inline-flex items-center gap-1 rounded border border-red-500/60 px-2 py-1 text-xs text-red-300 hover:bg-red-500/20 disabled:opacity-40"
                disabled={paperBusyAction !== null}
                onClick={() => {
                  void onDeletePaper(paper)
                }}
                type="button"
              >
                {paperBusyAction === "delete" ? <Spinner /> : null}
                删除
              </button>
            </div>
            <div className="grid gap-2 md:grid-cols-2">
              <div className="rounded border border-slate-700/50 bg-slate-950/70 p-2">
                <p className="mb-1 text-xs text-slate-400">摘要原文</p>
                <p className="max-h-52 overflow-auto whitespace-pre-wrap text-xs text-slate-200 scrollbar-thin">
                  {paper.abstract_original || "暂无"}
                </p>
              </div>
              <div className="rounded border border-slate-700/50 bg-slate-950/70 p-2">
                <p className="mb-1 text-xs text-slate-400">摘要中文</p>
                <p className="max-h-52 overflow-auto whitespace-pre-wrap text-xs text-slate-200 scrollbar-thin">
                  {paper.abstract_zh || "暂无"}
                </p>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    )
  }

  const renderCategory = (category: CategoryNode, depth = 0): JSX.Element => {
    const open = expandedCategoryIds[category.id] ?? true
    const children = category.children ?? []
    const categoryPapers = papersByCategory[String(category.id)] ?? []
    const isToggling = isPending && toggleTarget?.kind === "category" && toggleTarget.id === category.id

    return (
      <div key={`cat-${category.id}`} className="space-y-2">
        <button
          className="flex w-full items-center justify-between rounded-lg border border-slate-700/50 bg-slate-900/60 px-3 py-2 text-left hover:border-cyan/60"
          onClick={() => toggleCategory(category.id)}
          style={{ marginLeft: depth * 12 }}
          type="button"
        >
          <span className="inline-flex min-w-0 items-center gap-2 truncate text-sm">
            {isToggling ? <Spinner /> : null}
            {open ? "▼" : "▶"} {category.name}
          </span>
          <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-300">{category.count}</span>
        </button>
        {open ? (
          <div className="space-y-2 animate-fade-in-fast" style={{ marginLeft: depth * 12 }}>
            {categoryPapers.map(renderPaper)}
            {children.map((child) => renderCategory(child, depth + 1))}
          </div>
        ) : null}
      </div>
    )
  }

  const uncategorized = papersByCategory.uncategorized ?? []

  return (
    <section className="flex h-full min-w-0 flex-col rounded-xl border border-slate-700/60 bg-panel p-4 shadow-panel">
      <h3 className="mb-3 text-lg font-semibold text-cyan">论文库</h3>
      {isPending ? <p className="mb-2 text-[11px] text-slate-400">正在更新视图...</p> : null}
      <div className="flex-1 space-y-3 overflow-auto pr-1 scrollbar-thin">
        {categories.map((category) => renderCategory(category))}
        {uncategorized.length ? (
          <div className="space-y-2">
            <h4 className="rounded-lg border border-slate-700/50 bg-slate-900/60 px-3 py-2 text-sm">未分类</h4>
            {uncategorized.map(renderPaper)}
          </div>
        ) : null}
        {!categories.length && !papers.length ? <p className="text-sm text-slate-400">暂无数据</p> : null}
      </div>
    </section>
  )
}
