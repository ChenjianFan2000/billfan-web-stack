import { useMemo, useState } from "react"
import type { CategoryNode, Paper } from "../lib/types"
import { flattenCategories } from "../lib/tree"
import { Modal } from "./ui/Modal"
import { Spinner } from "./ui/Spinner"

type Props = {
  papers: Paper[]
  categories: CategoryNode[]
  onUpdate: (paperId: number, payload: Partial<Paper>) => Promise<void>
  onDelete: (paperId: number) => Promise<void>
}

export function PaperManager({ papers, categories, onUpdate, onDelete }: Props) {
  const [editingPaperId, setEditingPaperId] = useState<number | null>(null)
  const [draftTitle, setDraftTitle] = useState("")
  const [draftSummary, setDraftSummary] = useState("")
  const [busyPaperId, setBusyPaperId] = useState<number | null>(null)
  const [deletePaperId, setDeletePaperId] = useState<number | null>(null)

  const categoryOptions = useMemo(() => flattenCategories(categories), [categories])
  const deletePaper = papers.find((item) => item.id === deletePaperId) ?? null

  return (
    <section className="rounded-xl border border-slate-700/60 bg-panel p-3">
      <h3 className="mb-2 text-sm font-semibold text-cyan">论文管理</h3>
      <div className="max-h-52 overflow-auto scrollbar-thin">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr className="text-left text-slate-400">
              <th className="pb-2">标题</th>
              <th className="pb-2">年份</th>
              <th className="pb-2">分类</th>
              <th className="pb-2">操作</th>
            </tr>
          </thead>
          <tbody>
            {papers.map((paper) => {
              const editing = editingPaperId === paper.id
              const busy = busyPaperId === paper.id
              return (
                <tr key={paper.id} className="border-t border-slate-700/40 align-top">
                  <td className="py-2 pr-2">
                    {editing ? (
                      <input
                        className="w-full rounded border border-slate-600 bg-slate-950 px-1 py-0.5"
                        onChange={(event) => setDraftTitle(event.target.value)}
                        value={draftTitle}
                      />
                    ) : (
                      <div className="max-w-56 truncate">{paper.title || `未命名 #${paper.id}`}</div>
                    )}
                  </td>
                  <td className="py-2 pr-2">{paper.year ?? "-"}</td>
                  <td className="py-2 pr-2">
                    <select
                      className="rounded border border-slate-600 bg-slate-950 px-1 py-0.5"
                      defaultValue={paper.category_id ?? ""}
                      disabled={busy}
                      onChange={(event) => {
                        const value = event.target.value
                        onUpdate(paper.id, { category_id: value ? Number(value) : null }).catch(() => {
                          event.target.value = paper.category_id == null ? "" : String(paper.category_id)
                        })
                      }}
                    >
                      <option value="">未分类</option>
                      {categoryOptions.map((item) => (
                        <option key={item.id} value={item.id}>
                          {"--".repeat(item.depth)} {item.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="py-2">
                    <div className="flex gap-1">
                      {editing ? (
                        <>
                          <input
                            className="w-40 rounded border border-slate-600 bg-slate-950 px-1 py-0.5"
                            onChange={(event) => setDraftSummary(event.target.value)}
                            value={draftSummary}
                          />
                          <button
                            className="inline-flex items-center gap-1 rounded border border-cyan/60 px-2 py-0.5 text-cyan disabled:opacity-40"
                            disabled={busy}
                            onClick={async () => {
                              setBusyPaperId(paper.id)
                              try {
                                await onUpdate(paper.id, {
                                  title: draftTitle,
                                  summary_one_line: draftSummary,
                                })
                                setEditingPaperId(null)
                              } finally {
                                setBusyPaperId(null)
                              }
                            }}
                            type="button"
                          >
                            {busy ? <Spinner /> : null}
                            保存
                          </button>
                          <button
                            className="rounded border border-slate-600 px-2 py-0.5"
                            disabled={busy}
                            onClick={() => setEditingPaperId(null)}
                            type="button"
                          >
                            取消
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            className="rounded border border-slate-600 px-2 py-0.5 hover:border-violet hover:text-violet"
                            onClick={() => {
                              setEditingPaperId(paper.id)
                              setDraftTitle(paper.title || "")
                              setDraftSummary(paper.summary_one_line || "")
                            }}
                            type="button"
                          >
                            编辑
                          </button>
                          <button
                            className="rounded border border-red-500/60 px-2 py-0.5 text-red-300 hover:bg-red-500/20"
                            onClick={() => setDeletePaperId(paper.id)}
                            type="button"
                          >
                            删除
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {papers.length === 0 ? <p className="text-xs text-slate-400">暂无论文</p> : null}
      </div>

      <Modal
        footer={
          <>
            <button
              className="rounded border border-slate-600 px-3 py-1 text-sm"
              disabled={busyPaperId === deletePaperId}
              onClick={() => setDeletePaperId(null)}
              type="button"
            >
              取消
            </button>
            <button
              className="inline-flex items-center gap-2 rounded bg-red-500/20 px-3 py-1 text-sm text-red-200 disabled:opacity-40"
              disabled={!deletePaperId || busyPaperId === deletePaperId}
              onClick={async () => {
                if (!deletePaperId) {
                  return
                }
                setBusyPaperId(deletePaperId)
                try {
                  await onDelete(deletePaperId)
                  setDeletePaperId(null)
                } finally {
                  setBusyPaperId(null)
                }
              }}
              type="button"
            >
              {busyPaperId === deletePaperId ? <Spinner /> : null}
              确认删除
            </button>
          </>
        }
        onClose={() => setDeletePaperId(null)}
        open={!!deletePaperId}
        title="删除论文"
      >
        <p className="text-sm text-slate-300">确认删除论文 “{deletePaper?.title || deletePaperId}”？</p>
      </Modal>
    </section>
  )
}
