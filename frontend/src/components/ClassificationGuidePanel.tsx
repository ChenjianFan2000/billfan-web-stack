import { useEffect, useMemo, useState } from "react"
import { Spinner } from "./ui/Spinner"

type Props = {
  value: string
  loading: boolean
  saving: boolean
  onSave: (content: string) => Promise<void>
}

export function ClassificationGuidePanel({ value, loading, saving, onSave }: Props) {
  const [draft, setDraft] = useState(value)

  useEffect(() => {
    setDraft(value)
  }, [value])

  const dirty = useMemo(() => draft !== value, [draft, value])

  return (
    <section className="rounded-xl border border-slate-700/60 bg-panel p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-cyan">分类指导</h3>
        <span className="text-[11px] text-slate-400">{draft.length}/12000</span>
      </div>
      <textarea
        className="h-40 w-full resize-y rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs text-slate-200 disabled:opacity-40"
        disabled={loading || saving}
        onChange={(event) => setDraft(event.target.value)}
        placeholder="在这里维护分类规则，上传与AI分类都会参考它。"
        value={draft}
      />
      <div className="mt-2 flex items-center justify-between gap-2">
        <p className="text-[11px] text-slate-400">上传处理与分类推荐会优先遵循该指导文本。</p>
        <button
          className="inline-flex items-center gap-1 rounded bg-cyan/20 px-3 py-1 text-xs text-cyan hover:bg-cyan/30 disabled:cursor-not-allowed disabled:opacity-40"
          disabled={loading || saving || !dirty}
          onClick={() => {
            onSave(draft).catch(() => undefined)
          }}
          type="button"
        >
          {saving ? <Spinner /> : null}
          保存指导
        </button>
      </div>
    </section>
  )
}
