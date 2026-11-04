import { useMemo, useRef, useState } from "react"
import { getJobStatus, uploadPaper } from "../api/paperAssistant"
import { Spinner } from "./ui/Spinner"

type UploadJobState = {
  localId: number
  queueNo: number
  fileName: string
  jobId?: number
  status: "queued" | "requesting" | "pending" | "processing" | "done" | "skipped" | "error"
  error?: string
}

type Props = {
  onUploaded: () => Promise<void>
}

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

function statusLabel(status: string) {
  if (status === "queued") {
    return "等待中"
  }
  if (status === "requesting") {
    return "上传请求中"
  }
  if (status === "pending") {
    return "排队中"
  }
  if (status === "processing") {
    return "处理中"
  }
  if (status === "done") {
    return "完成"
  }
  if (status === "skipped") {
    return "已跳过"
  }
  if (status === "error") {
    return "失败"
  }
  return status
}

function statusTone(status: UploadJobState["status"]): string {
  if (status === "done") {
    return "border-emerald-500/40 bg-emerald-500/10 text-emerald-200"
  }
  if (status === "error") {
    return "border-red-500/40 bg-red-500/10 text-red-200"
  }
  if (status === "skipped") {
    return "border-amber-500/40 bg-amber-500/10 text-amber-200"
  }
  return "border-cyan/40 bg-cyan/10 text-cyan-100"
}

function queueHint(job: UploadJobState, jobs: UploadJobState[]): string {
  const active = jobs.find((item) => ["requesting", "pending", "processing"].includes(item.status))
  if (!active) {
    return job.status === "queued" ? "待调度" : "已出队"
  }
  if (job.queueNo < active.queueNo) {
    return "已出队"
  }
  if (job.queueNo === active.queueNo && ["requesting", "pending", "processing"].includes(job.status)) {
    return "当前处理"
  }
  if (job.queueNo > active.queueNo) {
    return `前方剩余 ${job.queueNo - active.queueNo} 个`
  }
  return ""
}

function toErrorMessage(err: unknown): string {
  if (err instanceof Error && err.message) {
    return err.message
  }
  return "上传失败，请稍后重试"
}

export function UploadPanel({ onUploaded }: Props) {
  const [jobs, setJobs] = useState<UploadJobState[]>([])
  const [busy, setBusy] = useState(false)
  const jobSeedRef = useRef(1)

  const runUpload = async (localId: number, file: File): Promise<boolean> => {
    setJobs((prev) =>
      prev.map((item) => (item.localId === localId ? { ...item, status: "requesting", error: undefined } : item)),
    )
    const uploaded = await uploadPaper(file)
    setJobs((prev) =>
      prev.map((item) => (item.localId === localId ? { ...item, jobId: uploaded.job_id, status: "pending" } : item)),
    )

    for (let i = 0; i < 300; i += 1) {
      await sleep(2000)
      const status = await getJobStatus(uploaded.job_id)
      setJobs((prev) =>
        prev.map((item) =>
          item.localId === localId
            ? { ...item, status: status.status, error: status.error_msg }
            : item,
        ),
      )
      if (status.status === "done" || status.status === "skipped") {
        return true
      }
      if (status.status === "error") {
        return false
      }
    }

    setJobs((prev) =>
      prev.map((item) =>
        item.localId === localId
          ? {
              ...item,
              status: "error",
              error: item.error || "任务轮询超时",
            }
          : item,
      ),
    )
    return false
  }

  const progress = useMemo(() => {
    const total = jobs.length
    const finished = jobs.filter((item) => ["done", "skipped", "error"].includes(item.status)).length
    const failed = jobs.filter((item) => item.status === "error").length
    const running = jobs.find((item) => ["requesting", "pending", "processing"].includes(item.status))
    return {
      total,
      finished,
      failed,
      runningQueueNo: running?.queueNo ?? null,
      percent: total ? Math.round((finished / total) * 100) : 0,
    }
  }, [jobs])

  return (
    <section className="rounded-xl border border-slate-700/60 bg-panel p-3">
      <h3 className="mb-2 text-sm font-semibold text-cyan">上传论文</h3>
      <input
        accept="application/pdf,.pdf"
        className="mb-2 block w-full cursor-pointer rounded border border-slate-600 bg-slate-900 p-2 text-xs disabled:opacity-40"
        disabled={busy}
        multiple
        onChange={async (event) => {
          const files = event.target.files
          if (!files?.length) {
            return
          }

          const filesArray = Array.from(files)
          const incoming = filesArray.map((file, index) => ({
            localId: jobSeedRef.current + index,
            queueNo: index + 1,
            fileName: file.name,
            status: "queued" as const,
          }))
          jobSeedRef.current += incoming.length
          setJobs(incoming)
          setBusy(true)
          try {
            let completedCount = 0
            for (const job of incoming) {
              try {
                const file = filesArray[job.queueNo - 1]
                if (!file) {
                  continue
                }
                const finished = await runUpload(job.localId, file)
                if (finished) {
                  completedCount += 1
                }
              } catch (err) {
                setJobs((prev) =>
                  prev.map((item) =>
                    item.localId === job.localId
                      ? { ...item, status: "error", error: toErrorMessage(err) }
                      : item,
                  ),
                )
              }
            }
            if (completedCount > 0) {
              await onUploaded()
            }
          } finally {
            setBusy(false)
            event.target.value = ""
          }
        }}
        type="file"
      />
      {jobs.length ? (
        <div className="mb-2 rounded border border-slate-700/50 bg-slate-900/60 p-2 text-[11px] text-slate-300">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span>
              共 {progress.total} 个任务 · 已完成 {progress.finished} · 失败 {progress.failed}
              {progress.runningQueueNo ? ` · 当前处理队列 #${progress.runningQueueNo}` : ""}
            </span>
            <span>{progress.percent}%</span>
          </div>
          <div className="mt-1 h-1.5 overflow-hidden rounded bg-slate-800">
            <div className="h-full rounded bg-cyan transition-all" style={{ width: `${progress.percent}%` }} />
          </div>
        </div>
      ) : null}
      {busy ? <p className="mb-2 text-[11px] text-slate-400">上传已开始，系统正在按队列顺序处理 PDF...</p> : null}
      <div className="max-h-64 space-y-1 overflow-auto text-xs scrollbar-thin">
        {jobs.length === 0 ? <p className="text-slate-400">暂无上传任务</p> : null}
        {[...jobs].sort((a, b) => a.queueNo - b.queueNo).map((job) => {
          const isWorking = ["requesting", "pending", "processing"].includes(job.status)
          return (
            <div key={job.localId} className="rounded border border-slate-700/50 bg-slate-900/70 p-2">
              <div className="flex items-start justify-between gap-2">
                <div className="truncate text-slate-100">
                  <span className="mr-1 text-slate-400">#{job.queueNo}</span>
                  {job.fileName}
                </div>
                <div className="flex flex-col items-end gap-1">
                  {job.jobId ? <span className="shrink-0 text-[10px] text-slate-400">job#{job.jobId}</span> : null}
                  <span className="shrink-0 text-[10px] text-slate-500">{queueHint(job, jobs)}</span>
                </div>
              </div>
              <div className="mt-1 inline-flex items-center gap-2 text-slate-300">
                <span className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] ${statusTone(job.status)}`}>
                  {isWorking ? <Spinner /> : null}
                  {statusLabel(job.status)}
                </span>
              </div>
              {job.error ? (
                <div className={`mt-1 ${job.status === "skipped" ? "text-amber-300" : "text-red-400"}`}>{job.error}</div>
              ) : null}
            </div>
          )
        })}
      </div>
    </section>
  )
}
