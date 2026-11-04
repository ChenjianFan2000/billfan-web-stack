import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  createConversation,
  deleteConversation,
  listConversationMessages,
  listConversations,
  renameConversation,
  streamAgentChat,
  uploadChatAttachment,
} from "../api/paperAssistant"
import type { AgentStreamEvent, ChatAttachment, ChatMessage, Conversation } from "../lib/types"
import { MarkdownContent } from "./ui/MarkdownContent"
import { Modal } from "./ui/Modal"
import { Spinner } from "./ui/Spinner"

type ToolEvent = {
  id: number
  name: string
  status?: string
  error?: string
  durationMs?: number
}

type Props = {
  queuedQuestion?: { id: number; content: string; paperIds?: number[] } | null
  onQueuedQuestionConsumed?: (id: number) => void
}

const MIN_CHAT_ZOOM = 0.85
const MAX_CHAT_ZOOM = 1.8
const CHAT_ZOOM_STEP = 0.1

function toErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof Error && err.message) {
    return err.message
  }
  return fallback
}

function toolStatusLabel(status?: string, error?: string): string {
  if (error) {
    return "失败"
  }
  const value = (status || "").toLowerCase()
  if (value === "start" || value === "running" || value === "in_progress" || value === "pending") {
    return "执行中"
  }
  if (value === "success" || value === "done" || value === "completed" || value === "ok") {
    return "完成"
  }
  if (value === "error" || value === "failed") {
    return "失败"
  }
  return status || "执行中"
}

function toolStatusClass(status?: string, error?: string): string {
  const label = toolStatusLabel(status, error)
  if (label === "失败") {
    return "border-red-500/50 bg-red-500/10 text-red-200"
  }
  if (label === "完成") {
    return "border-emerald-500/50 bg-emerald-500/10 text-emerald-200"
  }
  return "border-cyan/40 bg-cyan/10 text-cyan-100"
}

export function AgentPanel({ queuedQuestion, onQueuedQuestionConsumed }: Props) {
  const [loading, setLoading] = useState(true)
  const [conversationLoading, setConversationLoading] = useState(false)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const [attachments, setAttachments] = useState<ChatAttachment[]>([])
  const [attachmentUploading, setAttachmentUploading] = useState(false)
  const [toolEvents, setToolEvents] = useState<ToolEvent[]>([])
  const [statusText, setStatusText] = useState("准备就绪")
  const [error, setError] = useState("")
  const [conversationAction, setConversationAction] = useState<"none" | "create" | "rename" | "delete">("none")
  const [renameDialogOpen, setRenameDialogOpen] = useState(false)
  const [renameDraft, setRenameDraft] = useState("")
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [fullscreen, setFullscreen] = useState(false)
  const [chatZoom, setChatZoom] = useState(1)
  const [linkedPaperIds, setLinkedPaperIds] = useState<number[]>([])
  const consumedQueuedIdRef = useRef<number | null>(null)
  const toolEventIdRef = useRef(1)
  const panelRef = useRef<HTMLElement | null>(null)

  const loadConversations = useCallback(async () => {
    const rows = await listConversations()
    setConversations(rows)
    if (!rows.length) {
      setConversationId(null)
      setMessages([])
      setToolEvents([])
      return
    }
    setConversationId((prev) => (prev && rows.some((item) => item.id === prev) ? prev : rows[0].id))
  }, [])

  useEffect(() => {
    loadConversations()
      .catch(() => {
        setError("会话加载失败，请稍后重试。")
      })
      .finally(() => setLoading(false))
  }, [loadConversations])

  useEffect(() => {
    if (!conversationId) {
      setMessages([])
      setToolEvents([])
      return
    }
    setToolEvents([])
    setConversationLoading(true)
    listConversationMessages(conversationId)
      .then((next) => {
        setMessages(next)
      })
      .catch(() => {
        setMessages([])
        setError("消息加载失败，请稍后重试。")
      })
      .finally(() => setConversationLoading(false))
  }, [conversationId])

  const currentConversation = useMemo(
    () => conversations.find((item) => item.id === conversationId) ?? null,
    [conversations, conversationId],
  )

  const handleCreateConversation = async () => {
    setConversationAction("create")
    setError("")
    try {
      const created = await createConversation()
      setConversations((prev) => [created, ...prev])
      setConversationId(created.id)
      setMessages([])
      setStatusText("已创建新会话")
    } catch {
      setError("新建会话失败，请稍后重试。")
    } finally {
      setConversationAction("none")
    }
  }

  const ensureConversation = useCallback(async (): Promise<number | null> => {
    if (conversationId) {
      return conversationId
    }
    if (conversations.length) {
      setConversationId(conversations[0].id)
      return conversations[0].id
    }
    const created = await createConversation()
    setConversations((prev) => [created, ...prev])
    setConversationId(created.id)
    setMessages([])
    return created.id
  }, [conversationId, conversations])

  const sendContent = useCallback(
    async (targetConversationId: number, content: string, attachmentIds: number[], paperIds: number[]) => {
      setSending(true)
      setToolEvents([])
      setError("")
      setStatusText("正在提交问题...")

      const localUser: ChatMessage = {
        id: Date.now(),
        role: "user",
        content,
        attachments: attachmentIds,
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, localUser])

      let assistantContent = ""
      try {
        await streamAgentChat(
          targetConversationId,
          {
            content,
            attachment_ids: attachmentIds,
            paper_ids: paperIds,
          },
          (event: AgentStreamEvent) => {
            if (event.type === "status") {
              setStatusText(event.status || event.content || "处理中...")
              return
            }
            if (event.type === "tool_call") {
              const eventName = event.name || "unknown"
              const nextStatus = event.status || "start"
              const nextError = event.error
              const statusText = toolStatusLabel(nextStatus, nextError)
              setStatusText(`工具调用：${eventName} · ${statusText}`)
              setToolEvents((prev) => {
                if (nextStatus === "start") {
                  return [
                    ...prev,
                    {
                      id: toolEventIdRef.current++,
                      name: eventName,
                      status: nextStatus,
                    },
                  ]
                }
                const runningIndex = [...prev]
                  .reverse()
                  .findIndex(
                    (item) =>
                      item.name === eventName &&
                      ["start", "running", "in_progress", "pending"].includes((item.status || "").toLowerCase()) &&
                      !item.error,
                  )
                if (runningIndex >= 0) {
                  const target = prev.length - 1 - runningIndex
                  const merged = {
                    ...prev[target],
                    status: nextStatus,
                    error: nextError,
                    durationMs: event.duration_ms,
                  }
                  const next = [...prev]
                  next[target] = merged
                  return next
                }
                return [
                  ...prev,
                  {
                    id: toolEventIdRef.current++,
                    name: eventName,
                    status: nextStatus,
                    error: nextError,
                    durationMs: event.duration_ms,
                  },
                ]
              })
              return
            }
            if (event.type === "chunk" && event.content) {
              setStatusText("AI 正在回复...")
              assistantContent += event.content
              setMessages((prev) => {
                const next = [...prev]
                const last = next[next.length - 1]
                if (last?.role === "assistant" && last.id === -1) {
                  last.content = assistantContent
                  return [...next]
                }
                return [
                  ...next,
                  {
                    id: -1,
                    role: "assistant",
                    content: assistantContent,
                    attachments: [],
                    created_at: new Date().toISOString(),
                  },
                ]
              })
              return
            }
            if (event.type === "done" && event.content) {
              assistantContent = event.content
              setStatusText("回复完成")
              return
            }
            if (event.type === "error") {
              setStatusText(event.error || "对话失败")
            }
          },
        )

        const latest = await listConversationMessages(targetConversationId)
        setMessages(latest)
        const list = await listConversations()
        setConversations(list)
      } catch (err) {
        setError(toErrorMessage(err, "发送失败，请稍后重试。"))
        setStatusText("发送失败")
      } finally {
        setSending(false)
        setAttachments([])
      }
    },
    [],
  )

  const handleSend = useCallback(async () => {
    const content = input.trim()
    if (!content || sending || attachmentUploading) {
      return
    }

    const targetConversationId = await ensureConversation()
    if (!targetConversationId) {
      return
    }

    setInput("")
    await sendContent(
      targetConversationId,
      content,
      attachments.map((item) => item.attachment_id),
      linkedPaperIds,
    )
  }, [attachments, attachmentUploading, ensureConversation, input, linkedPaperIds, sendContent, sending])

  useEffect(() => {
    if (!queuedQuestion || sending) {
      return
    }
    if (consumedQueuedIdRef.current === queuedQuestion.id) {
      return
    }

    const content = queuedQuestion.content.trim()
    if (!content) {
      consumedQueuedIdRef.current = queuedQuestion.id
      onQueuedQuestionConsumed?.(queuedQuestion.id)
      return
    }
    consumedQueuedIdRef.current = queuedQuestion.id

    ;(async () => {
      const targetConversationId = await ensureConversation()
      if (!targetConversationId) {
        return
      }
      const nextPaperIds = (queuedQuestion.paperIds || []).filter((item) => Number.isInteger(item) && item > 0)
      if (nextPaperIds.length) {
        setLinkedPaperIds(nextPaperIds)
      }
      setInput("")
      await sendContent(targetConversationId, content, [], nextPaperIds.length ? nextPaperIds : linkedPaperIds)
      onQueuedQuestionConsumed?.(queuedQuestion.id)
    })().catch(() => undefined)
  }, [ensureConversation, linkedPaperIds, onQueuedQuestionConsumed, queuedQuestion, sendContent, sending])

  const hasBusyState = loading || conversationLoading || sending || attachmentUploading
  const zoomPercent = Math.round(chatZoom * 100)

  const updateChatZoom = useCallback((direction: "in" | "out") => {
    setChatZoom((current) => {
      const next = direction === "in" ? current + CHAT_ZOOM_STEP : current - CHAT_ZOOM_STEP
      return Math.min(MAX_CHAT_ZOOM, Math.max(MIN_CHAT_ZOOM, Number(next.toFixed(2))))
    })
  }, [])

  const resetChatZoom = useCallback(() => {
    setChatZoom(1)
  }, [])

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setFullscreen(false)
        return
      }
      const panelFocused = panelRef.current ? panelRef.current.contains(document.activeElement) : false
      if (!(event.ctrlKey || event.metaKey) || (!fullscreen && !panelFocused)) {
        return
      }
      const key = event.key
      if (key === "+" || key === "=") {
        event.preventDefault()
        updateChatZoom("in")
        return
      }
      if (key === "-" || key === "_") {
        event.preventDefault()
        updateChatZoom("out")
        return
      }
      if (key === "0") {
        event.preventDefault()
        resetChatZoom()
      }
    }
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  }, [fullscreen, resetChatZoom, updateChatZoom])

  useEffect(() => {
    const { body } = document
    const previous = body.style.overflow
    if (fullscreen) {
      body.style.overflow = "hidden"
    }
    return () => {
      body.style.overflow = previous
    }
  }, [fullscreen])

  useEffect(() => {
    const panel = panelRef.current
    if (!panel) {
      return
    }
    const onWheel = (event: WheelEvent) => {
      if (!(event.ctrlKey || event.metaKey)) {
        return
      }
      event.preventDefault()
      if (event.deltaY < 0) {
        updateChatZoom("in")
      } else {
        updateChatZoom("out")
      }
    }
    panel.addEventListener("wheel", onWheel, { passive: false })
    return () => {
      panel.removeEventListener("wheel", onWheel)
    }
  }, [fullscreen, updateChatZoom])

  return (
    <section
      ref={panelRef}
      className={`min-w-0 rounded-xl border border-slate-700/60 bg-panel p-3 ${
        fullscreen ? "fixed inset-2 z-[80] flex h-[calc(100vh-1rem)] flex-col overflow-hidden p-0 shadow-2xl" : ""
      }`}
    >
      <div className={`flex flex-wrap items-center justify-between gap-2 ${fullscreen ? "border-b border-slate-700/60 px-3 py-2.5" : "mb-2"}`}>
        <h3 className="min-w-0 text-sm font-semibold text-cyan">Agent 对话</h3>
        <div className="flex shrink-0 items-center gap-2">
          <div className="hidden items-center gap-1 rounded border border-slate-600/70 bg-slate-900/70 px-1 py-0.5 text-[11px] text-slate-200 sm:inline-flex">
            <button
              className="rounded px-1 hover:bg-slate-700/80"
              onClick={() => updateChatZoom("out")}
              type="button"
            >
              A-
            </button>
            <button className="rounded px-1 text-cyan hover:bg-slate-700/80" onClick={resetChatZoom} type="button">
              {zoomPercent}%
            </button>
            <button
              className="rounded px-1 hover:bg-slate-700/80"
              onClick={() => updateChatZoom("in")}
              type="button"
            >
              A+
            </button>
          </div>
          <button
            className="inline-flex items-center gap-1 rounded border border-cyan/60 bg-cyan/15 px-2 py-1 text-xs font-semibold text-cyan hover:bg-cyan/25"
            onClick={() => setFullscreen((value) => !value)}
            title={fullscreen ? "退出全屏（Esc）" : "进入全屏"}
            type="button"
          >
            {fullscreen ? "退出全屏" : "全屏"}
          </button>
          <button
            className="inline-flex items-center gap-1 rounded border border-cyan/60 px-2 py-1 text-xs text-cyan disabled:opacity-40"
            disabled={conversationAction !== "none" || sending}
            onClick={() => {
              handleCreateConversation().catch(() => undefined)
            }}
            type="button"
          >
            {conversationAction === "create" ? <Spinner /> : null}
            + 新建
          </button>
        </div>
      </div>

      <div className={fullscreen ? "flex min-h-0 flex-1 flex-col p-3" : ""}>
        <div className="mb-2 rounded border border-slate-700/40 bg-slate-900/60 px-2 py-1 text-[11px] text-slate-300">
          <div className="inline-flex items-center gap-2">
            {hasBusyState ? <Spinner /> : null}
            {statusText}
          </div>
        </div>
        {linkedPaperIds.length ? (
          <div className="mb-2 flex items-center justify-between rounded border border-cyan/30 bg-cyan/5 px-2 py-1 text-[11px] text-cyan-100">
            <span>已关联论文上下文：{linkedPaperIds.map((id) => `#${id}`).join(", ")}</span>
            <button
              className="rounded border border-cyan/50 px-2 py-0.5 text-[10px] hover:bg-cyan/10"
              disabled={sending}
              onClick={() => setLinkedPaperIds([])}
              type="button"
            >
              清除关联
            </button>
          </div>
        ) : null}

        {error ? <div className="mb-2 rounded border border-red-500/40 bg-red-500/10 px-2 py-1 text-xs text-red-300">{error}</div> : null}

        <div className="mb-2 flex gap-2">
          <select
            className="min-w-0 flex-1 rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs disabled:opacity-50"
            disabled={loading || !conversations.length || sending}
            onChange={(event) => setConversationId(Number(event.target.value))}
            value={conversationId ?? ""}
          >
            {conversations.map((conversation) => (
              <option key={conversation.id} value={conversation.id}>
                {conversation.title}
              </option>
            ))}
          </select>
          {currentConversation ? (
            <>
              <button
                className="rounded border border-slate-600 px-2 py-1 text-xs disabled:opacity-40"
                disabled={conversationAction !== "none" || sending}
                onClick={() => {
                  setRenameDraft(currentConversation.title)
                  setRenameDialogOpen(true)
                }}
                type="button"
              >
                改名
              </button>
              <button
                className="rounded border border-red-500/60 px-2 py-1 text-xs text-red-300 disabled:opacity-40"
                disabled={conversationAction !== "none" || sending}
                onClick={() => {
                  setDeleteDialogOpen(true)
                }}
                type="button"
              >
                删除
              </button>
            </>
          ) : null}
        </div>

        <div
          className={`mb-2 overflow-auto rounded border border-slate-700/50 bg-slate-950/70 p-2 scrollbar-thin ${
            fullscreen ? "min-h-0 flex-1" : "h-52"
          }`}
        >
          <div style={{ fontSize: `${(0.78 * chatZoom).toFixed(3)}rem` }}>
            {conversationLoading ? <p className="text-slate-400">会话加载中...</p> : null}
            {!conversationLoading && !messages.length ? <p className="text-slate-400">开始一段新对话吧。</p> : null}
            {messages.map((message) => (
              <div key={`${message.id}-${message.created_at}`} className="mb-2">
                <div className="mb-1 text-[0.72em] text-slate-400">{message.role === "user" ? "你" : "助手"}</div>
                <div className="rounded border border-slate-700/50 bg-slate-900/80 p-2 text-slate-200">
                  {message.role === "assistant" ? (
                    <MarkdownContent content={message.content || ""} />
                  ) : (
                    <div className="whitespace-pre-wrap">{message.content}</div>
                  )}
                </div>
              </div>
            ))}
            {toolEvents.map((event) => (
              <div key={event.id} className="mb-2">
                <div className="mb-1 text-[0.72em] text-slate-400">工具</div>
                <div className="rounded border border-slate-700/50 bg-slate-900/80 p-2">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 text-[0.72em] text-slate-200">
                      <span className="text-cyan">调用 {event.name}</span>
                      {event.durationMs != null ? <span className="ml-2 text-slate-400">{event.durationMs}ms</span> : null}
                    </div>
                    <span className={`shrink-0 rounded border px-1.5 py-0.5 text-[0.68em] ${toolStatusClass(event.status, event.error)}`}>
                      {toolStatusLabel(event.status, event.error)}
                    </span>
                  </div>
                  {event.error ? <div className="mt-1 text-[0.72em] text-red-300">{event.error}</div> : null}
                </div>
              </div>
            ))}
            {sending && (!messages.length || messages[messages.length - 1]?.role !== "assistant") ? (
              <div className="mb-2">
                <div className="mb-1 text-[0.72em] text-slate-400">助手</div>
                <div className="inline-flex items-center gap-2 rounded border border-slate-700/50 bg-slate-900/80 p-2 text-slate-300">
                  <Spinner />
                  正在思考...
                </div>
              </div>
            ) : null}
          </div>
        </div>

        <div className={`${fullscreen ? "shrink-0 border-t border-cyan/30 bg-slate-950/90 pt-3" : ""}`}>
          <div className="mb-2 flex flex-wrap gap-2">
            <input
              accept=".pdf,image/*"
              className="block min-w-0 flex-1 cursor-pointer rounded border border-slate-600 bg-slate-900 px-2 py-1 text-xs disabled:opacity-40"
              disabled={sending || attachmentUploading}
              onChange={async (event) => {
                const files = Array.from(event.target.files || [])
                if (!files.length) {
                  return
                }
                setAttachmentUploading(true)
                setError("")
                setStatusText("正在上传附件...")
                try {
                  const uploaded: ChatAttachment[] = []
                  for (const file of files) {
                    const attachment = await uploadChatAttachment(file)
                    uploaded.push(attachment)
                  }
                  setAttachments((prev) => [...prev, ...uploaded])
                  setStatusText(`附件上传完成（${uploaded.length} 个）`)
                  event.target.value = ""
                } catch (err) {
                  setError(toErrorMessage(err, "附件上传失败，请稍后重试。"))
                  setStatusText("附件上传失败")
                } finally {
                  setAttachmentUploading(false)
                }
              }}
              type="file"
            />
          </div>

          {attachments.length ? (
            <div className="mb-2 max-h-20 overflow-auto rounded border border-slate-700/40 bg-slate-900/60 p-2 text-[11px] text-slate-300 scrollbar-thin">
              {attachments.map((attachment) => (
                <div key={attachment.attachment_id} className="mb-1 flex items-center justify-between gap-2">
                  <span>
                    #{attachment.attachment_id} · {attachment.type}
                  </span>
                  <button
                    className="rounded border border-slate-600 px-1 py-0.5 text-[10px] hover:border-red-400 hover:text-red-300"
                    disabled={sending}
                    onClick={() => {
                      setAttachments((prev) => prev.filter((item) => item.attachment_id !== attachment.attachment_id))
                    }}
                    type="button"
                  >
                    移除
                  </button>
                </div>
              ))}
            </div>
          ) : null}

          <div className="flex gap-2">
            <textarea
              className={`min-w-0 flex-1 resize-none rounded border bg-slate-950 px-3 py-2 disabled:opacity-40 ${
                fullscreen ? "h-24 border-cyan/70 text-sm shadow-[inset_0_0_0_1px_rgba(34,211,238,0.15)]" : "h-16 border-slate-600 text-xs"
              }`}
              disabled={sending}
              onChange={(event) => setInput(event.target.value)}
              placeholder="输入你的问题，例如：帮我重排 CV 分类中的论文..."
              value={input}
            />
            <button
              className={`inline-flex items-center justify-center gap-2 rounded disabled:cursor-not-allowed disabled:opacity-40 ${
                fullscreen
                  ? "min-w-24 bg-cyan px-5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan/80"
                  : "bg-cyan/20 px-3 py-1 text-xs text-cyan hover:bg-cyan/30"
              }`}
              disabled={sending || attachmentUploading || !input.trim()}
              onClick={() => {
                handleSend().catch(() => undefined)
              }}
              type="button"
            >
              {sending ? <Spinner /> : null}
              {sending ? "发送中" : "发送"}
            </button>
          </div>
        </div>
      </div>

      <Modal
        footer={
          <>
            <button
              className="rounded border border-slate-600 px-3 py-1 text-sm"
              disabled={conversationAction === "rename"}
              onClick={() => setRenameDialogOpen(false)}
              type="button"
            >
              取消
            </button>
            <button
              className="inline-flex items-center gap-2 rounded bg-cyan/20 px-3 py-1 text-sm text-cyan disabled:opacity-40"
              disabled={!renameDraft.trim() || conversationAction === "rename" || !currentConversation}
              onClick={async () => {
                if (!currentConversation) {
                  return
                }
                setConversationAction("rename")
                setError("")
                try {
                  const updated = await renameConversation(currentConversation.id, renameDraft.trim())
                  setConversations((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
                  setRenameDialogOpen(false)
                  setStatusText("会话名称已更新")
                } catch (err) {
                  setError(toErrorMessage(err, "重命名失败，请稍后重试。"))
                } finally {
                  setConversationAction("none")
                }
              }}
              type="button"
            >
              {conversationAction === "rename" ? <Spinner /> : null}
              保存
            </button>
          </>
        }
        onClose={() => setRenameDialogOpen(false)}
        open={renameDialogOpen}
        title="重命名会话"
      >
        <input
          className="w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm"
          onChange={(event) => setRenameDraft(event.target.value)}
          value={renameDraft}
        />
      </Modal>

      <Modal
        footer={
          <>
            <button
              className="rounded border border-slate-600 px-3 py-1 text-sm"
              disabled={conversationAction === "delete"}
              onClick={() => setDeleteDialogOpen(false)}
              type="button"
            >
              取消
            </button>
            <button
              className="inline-flex items-center gap-2 rounded bg-red-500/20 px-3 py-1 text-sm text-red-200 disabled:opacity-40"
              disabled={conversationAction === "delete" || !currentConversation}
              onClick={async () => {
                if (!currentConversation) {
                  return
                }
                setConversationAction("delete")
                setError("")
                try {
                  await deleteConversation(currentConversation.id)
                  await loadConversations()
                  setDeleteDialogOpen(false)
                  setStatusText("会话已删除")
                } catch (err) {
                  setError(toErrorMessage(err, "删除会话失败，请稍后重试。"))
                } finally {
                  setConversationAction("none")
                }
              }}
              type="button"
            >
              {conversationAction === "delete" ? <Spinner /> : null}
              确认删除
            </button>
          </>
        }
        onClose={() => setDeleteDialogOpen(false)}
        open={deleteDialogOpen}
        title="删除会话"
      >
        <p className="text-sm text-slate-300">确认删除当前会话 “{currentConversation?.title || "未命名会话"}”？</p>
      </Modal>
    </section>
  )
}
