import { useCallback, useEffect, useMemo, useState } from "react"
import {
  createCategory,
  deleteCategory,
  deletePaper,
  getClassificationGuidance,
  listQuarantinedPapers,
  getStats,
  listCategories,
  listPapers,
  logout,
  updateClassificationGuidance,
  updateCategory,
  updatePaper,
} from "../api/paperAssistant"
import { ApiError } from "../api/client"
import { AgentPanel } from "../components/AgentPanel"
import { CategoryPanel } from "../components/CategoryPanel"
import { ClassificationGuidePanel } from "../components/ClassificationGuidePanel"
import { ExportPanel } from "../components/ExportPanel"
import { PaperLibrary } from "../components/PaperLibrary"
import { PaperMetadataDialog } from "../components/PaperMetadataDialog"
import { QuarantinePanel } from "../components/QuarantinePanel"
import { StatsBar } from "../components/StatsBar"
import { UploadPanel } from "../components/UploadPanel"
import { Modal } from "../components/ui/Modal"
import { Spinner } from "../components/ui/Spinner"
import { ToastViewport, type ToastItem } from "../components/ui/ToastViewport"
import type { CategoryNode, Paper, QuarantinePaper, StatsPayload } from "../lib/types"

type Props = {
  username: string
  onLoggedOut: () => void
}

const EMPTY_STATS: StatsPayload = { total: 0, categories: [] }

function toErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof ApiError && err.message) {
    return err.message
  }
  if (err instanceof Error && err.message) {
    return err.message
  }
  return fallback
}

export function AppPage({ username, onLoggedOut }: Props) {
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)
  const [error, setError] = useState("")
  const [categories, setCategories] = useState<CategoryNode[]>([])
  const [papers, setPapers] = useState<Paper[]>([])
  const [stats, setStats] = useState<StatsPayload>(EMPTY_STATS)
  const [classificationGuidance, setClassificationGuidance] = useState("")
  const [quarantinedPapers, setQuarantinedPapers] = useState<QuarantinePaper[]>([])
  const [guidanceSaving, setGuidanceSaving] = useState(false)
  const [queuedAgentQuestion, setQueuedAgentQuestion] = useState<{ id: number; content: string; paperIds?: number[] } | null>(null)
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const [paperActionState, setPaperActionState] = useState<{ id: number; action: "move" | "edit" | "delete" } | null>(null)
  const [editingPaper, setEditingPaper] = useState<Paper | null>(null)
  const [metadataSubmitting, setMetadataSubmitting] = useState(false)
  const [deletePaperTarget, setDeletePaperTarget] = useState<Paper | null>(null)
  const [deleteSubmitting, setDeleteSubmitting] = useState(false)

  const pushToast = useCallback((tone: ToastItem["tone"], message: string) => {
    const id = Date.now() + Math.floor(Math.random() * 1000)
    setToasts((prev) => [...prev, { id, tone, message }])
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((item) => item.id !== id))
    }, 2800)
  }, [])

  const refreshAll = useCallback(async () => {
    const [categoriesData, papersData, statsData, guidanceData, quarantineData] = await Promise.all([
      listCategories(),
      listPapers(),
      getStats(),
      getClassificationGuidance(),
      listQuarantinedPapers(),
    ])
    setCategories(categoriesData)
    setPapers(papersData)
    setStats(statsData)
    setClassificationGuidance(guidanceData.content || "")
    setQuarantinedPapers(quarantineData)
  }, [])

  useEffect(() => {
    refreshAll()
      .catch((err) => {
        console.error(err)
        setError(toErrorMessage(err, "加载数据失败"))
      })
      .finally(() => setLoading(false))
  }, [refreshAll])

  const runAction = useCallback(
    async (task: () => Promise<void>, options: { success?: string; fallbackError: string; refresh?: boolean }) => {
      setError("")
      setRefreshing(true)
      try {
        await task()
        if (options.refresh !== false) {
          await refreshAll()
        }
        if (options.success) {
          pushToast("success", options.success)
        }
      } catch (err) {
        const message = toErrorMessage(err, options.fallbackError)
        setError(message)
        pushToast("error", message)
        throw err
      } finally {
        setRefreshing(false)
      }
    },
    [pushToast, refreshAll],
  )

  const headerStateText = useMemo(() => {
    if (loading) {
      return "系统初始化中"
    }
    if (loggingOut) {
      return "正在退出登录"
    }
    if (refreshing) {
      return "数据同步中"
    }
    return "实时在线"
  }, [loading, loggingOut, refreshing])

  return (
    <main className="min-h-screen overflow-x-scroll overflow-y-auto bg-bg p-4 text-slate-100">
      <div className="mx-auto w-full min-w-0 max-w-[1500px] space-y-4">
        <header className="relative overflow-hidden rounded-xl border border-slate-700/60 bg-panel px-4 py-3 shadow-panel">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(0,212,255,0.14),transparent_48%)]" />
          <div className="relative z-10 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-xl font-semibold text-cyan">其华的论文管理小助手</h1>
              <p className="text-xs text-slate-400">Research Terminal · {headerStateText}</p>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="rounded bg-slate-800 px-2 py-1">{username}</span>
              <button
                className="inline-flex items-center gap-2 rounded border border-slate-600 px-3 py-1 hover:border-red-400 hover:text-red-300 disabled:opacity-40"
                disabled={loggingOut}
                onClick={async () => {
                  setLoggingOut(true)
                  try {
                    await logout()
                    onLoggedOut()
                  } finally {
                    setLoggingOut(false)
                  }
                }}
                type="button"
              >
                {loggingOut ? <Spinner /> : null}
                登出
              </button>
            </div>
          </div>
          {refreshing ? <div className="mt-3 h-1 w-full overflow-hidden rounded bg-slate-800"><div className="h-full w-1/3 animate-loading-bar rounded bg-cyan" /></div> : null}
        </header>

        <StatsBar stats={stats} />

        {error ? <div className="rounded border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">{error}</div> : null}

        {loading ? (
          <div className="rounded-xl border border-slate-700/60 bg-panel p-6 text-center text-sm text-slate-300">
            <span className="inline-flex items-center gap-2">
              <Spinner />
              加载中...
            </span>
          </div>
        ) : (
          <div className="grid min-w-0 gap-4 lg:grid-cols-[minmax(0,1.9fr)_minmax(0,1fr)]">
            <div className="min-w-0">
              <PaperLibrary
                categories={categories}
                onAskAgentAboutPaper={(paper) => {
                  const prompt = [
                    `请基于这篇论文回答我的问题。`,
                    `论文ID：${paper.id}`,
                    `论文标题：${paper.title || `未命名论文 #${paper.id}`}`,
                    paper.authors.length ? `作者：${paper.authors.join(", ")}` : "",
                    paper.year ? `年份：${paper.year}` : "",
                    paper.doi ? `DOI：${paper.doi}` : "",
                    paper.summary_one_line ? `一句话概括：${paper.summary_one_line}` : "",
                    paper.abstract_zh ? `摘要中文：${paper.abstract_zh}` : "",
                    `请先简要概括论文，然后告诉我它的研究对象、方法、主要结论和可借鉴点。`,
                  ]
                    .filter(Boolean)
                    .join("\n")
                  setQueuedAgentQuestion({ id: Date.now(), content: prompt, paperIds: [paper.id] })
                  pushToast("info", `问题已注入 AI 对话区，并关联论文 #${paper.id} 全文`)
                }}
                onDeletePaper={async (paper) => {
                  setDeletePaperTarget(paper)
                }}
                onEditPaperMetadata={async (paper) => {
                  setEditingPaper(paper)
                  setPaperActionState({ id: paper.id, action: "edit" })
                }}
                onSetPaperCategories={async (paperId, categoryIds) => {
                  const previous = papers.find((item) => item.id === paperId)
                  const normalized = Array.from(new Set(categoryIds.map((id) => Number(id)).filter((id) => Number.isInteger(id) && id > 0)))
                  setPaperActionState({ id: paperId, action: "move" })
                  setPapers((prev) =>
                    prev.map((item) =>
                      item.id === paperId
                        ? {
                            ...item,
                            category_ids: normalized,
                            category_id: normalized.length ? normalized[0] : null,
                          }
                        : item,
                    ),
                  )
                  try {
                    await runAction(
                      async () => {
                        await updatePaper(paperId, { category_ids: normalized })
                      },
                      { success: "论文分类已更新", fallbackError: "设置分类失败" },
                    )
                  } catch {
                    setPapers((prev) =>
                      prev.map((item) =>
                        item.id === paperId
                          ? {
                              ...item,
                              category_ids: previous?.category_ids ?? [],
                              category_id: previous?.category_id ?? null,
                            }
                          : item,
                      ),
                    )
                  } finally {
                    setPaperActionState(null)
                  }
                }}
                paperActionState={paperActionState}
                papers={papers}
              />
            </div>

            <aside className="min-w-0 space-y-3">
              <UploadPanel
                onUploaded={async () => {
                  await runAction(async () => undefined, {
                    success: "上传任务完成，数据已同步",
                    fallbackError: "上传完成后刷新失败",
                  }).catch(() => undefined)
                }}
              />
              <QuarantinePanel items={quarantinedPapers} />
              <CategoryPanel
                categories={categories}
                onCreate={async (payload) => {
                  await runAction(
                    async () => {
                      await createCategory(payload)
                    },
                    { success: "分类创建成功", fallbackError: "创建分类失败" },
                  ).catch(() => undefined)
                }}
                onDelete={async (categoryId) => {
                  await runAction(
                    async () => {
                      await deleteCategory(categoryId)
                    },
                    { success: "分类删除成功", fallbackError: "删除分类失败" },
                  ).catch(() => undefined)
                }}
                onUpdate={async (categoryId, payload) => {
                  await runAction(
                    async () => {
                      await updateCategory(categoryId, payload)
                    },
                    { success: "分类更新成功", fallbackError: "更新分类失败" },
                  ).catch(() => undefined)
                }}
              />
              <ClassificationGuidePanel
                loading={loading}
                onSave={async (content) => {
                  setGuidanceSaving(true)
                  setError("")
                  try {
                    const saved = await updateClassificationGuidance(content)
                    setClassificationGuidance(saved.content || "")
                    pushToast("success", "分类指导已保存")
                  } catch (err) {
                    const message = toErrorMessage(err, "保存分类指导失败")
                    setError(message)
                    pushToast("error", message)
                  } finally {
                    setGuidanceSaving(false)
                  }
                }}
                saving={guidanceSaving}
                value={classificationGuidance}
              />
              <AgentPanel
                onQueuedQuestionConsumed={(id) => {
                  setQueuedAgentQuestion((prev) => (prev && prev.id === id ? null : prev))
                }}
                queuedQuestion={queuedAgentQuestion}
              />
              <ExportPanel categories={categories} />
            </aside>
          </div>
        )}
      </div>

      <PaperMetadataDialog
        onClose={() => {
          if (!metadataSubmitting) {
            setEditingPaper(null)
            setPaperActionState(null)
          }
        }}
        onSubmit={async (paperId, payload) => {
          setMetadataSubmitting(true)
          setPaperActionState({ id: paperId, action: "edit" })
          try {
            await runAction(
              async () => {
                await updatePaper(paperId, payload)
              },
              { success: "元数据已更新", fallbackError: "更新元数据失败" },
            )
            setEditingPaper(null)
          } finally {
            setMetadataSubmitting(false)
            setPaperActionState(null)
          }
        }}
        paper={editingPaper}
        submitting={metadataSubmitting}
      />

      <Modal
        footer={
          <>
            <button
              className="rounded border border-slate-600 px-3 py-1 text-sm"
              disabled={deleteSubmitting}
              onClick={() => setDeletePaperTarget(null)}
              type="button"
            >
              取消
            </button>
            <button
              className="inline-flex items-center gap-2 rounded bg-red-500/20 px-3 py-1 text-sm text-red-100 disabled:opacity-40"
              disabled={deleteSubmitting || !deletePaperTarget}
              onClick={async () => {
                if (!deletePaperTarget) {
                  return
                }
                setDeleteSubmitting(true)
                setPaperActionState({ id: deletePaperTarget.id, action: "delete" })
                let deleted = false
                try {
                  await runAction(
                    async () => {
                      await deletePaper(deletePaperTarget.id)
                    },
                    { success: "论文已删除", fallbackError: "删除论文失败" },
                  )
                  deleted = true
                } catch {
                  deleted = false
                } finally {
                  if (deleted) {
                    setDeletePaperTarget(null)
                  }
                  setDeleteSubmitting(false)
                  setPaperActionState(null)
                }
              }}
              type="button"
            >
              {deleteSubmitting ? <Spinner /> : null}
              确认删除
            </button>
          </>
        }
        onClose={() => setDeletePaperTarget(null)}
        open={!!deletePaperTarget}
        title="删除论文"
      >
        <p className="text-sm text-slate-300">确认删除论文 “{deletePaperTarget?.title || deletePaperTarget?.id}”？删除后不可恢复。</p>
      </Modal>

      <ToastViewport toasts={toasts} />
    </main>
  )
}
