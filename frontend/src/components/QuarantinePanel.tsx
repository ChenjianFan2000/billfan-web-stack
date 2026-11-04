import type { QuarantinePaper } from "../lib/types"

type Props = {
  items: QuarantinePaper[]
}

function shortText(value: string, limit: number) {
  const text = (value || "").trim()
  if (!text) {
    return ""
  }
  if (text.length <= limit) {
    return text
  }
  return `${text.slice(0, limit)}...`
}

export function QuarantinePanel({ items }: Props) {
  return (
    <section className="rounded-xl border border-red-500/35 bg-red-500/10 p-3">
      <h3 className="mb-2 text-sm font-semibold text-red-200">坏 PDF 隔离列表</h3>
      <p className="mb-2 text-[11px] text-red-100/80">解析失败文件会保留在这里，不会混入正常论文库。</p>
      {items.length === 0 ? <p className="text-xs text-slate-300">当前无隔离文件</p> : null}
      <div className="max-h-56 space-y-2 overflow-auto text-xs scrollbar-thin">
        {items.map((item) => (
          <article key={item.id} className="rounded border border-red-400/30 bg-slate-900/60 p-2">
            <div className="text-red-100">#{item.id} {item.title || "未命名文件"}</div>
            <div className="mt-1 text-red-200/80">
              原因：{shortText(item.quarantine_reason || item.latest_job_error || item.latest_job_status || "unknown", 180)}
            </div>
            {item.file_path ? <div className="mt-1 text-[10px] text-slate-300">{shortText(item.file_path, 130)}</div> : null}
          </article>
        ))}
      </div>
    </section>
  )
}
