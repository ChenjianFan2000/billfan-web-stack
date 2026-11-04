import type { StatsPayload } from "../lib/types"

type Props = {
  stats: StatsPayload
}

export function StatsBar({ stats }: Props) {
  return (
    <div className="rounded-xl border border-slate-700/60 bg-panel p-4 shadow-panel">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-cyan">统计信息</h2>
        <span className="rounded-md bg-cyan/10 px-3 py-1 text-sm text-cyan">总论文 {stats.total}</span>
      </div>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
        {stats.categories.map((item) => (
          <div key={item.id} className="rounded-lg border border-slate-700/40 bg-slate-900/70 px-3 py-2">
            <div className="truncate text-xs text-slate-400">{item.name}</div>
            <div className="font-mono text-xl text-slate-100">{item.count}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
