import { useState } from "react"
import { exportPdfs, exportReferences, exportTexts } from "../api/paperAssistant"
import type { CategoryNode } from "../lib/types"
import { flattenCategories } from "../lib/tree"
import { Spinner } from "./ui/Spinner"

type Props = {
  categories: CategoryNode[]
}

export function ExportPanel({ categories }: Props) {
  const [selectedCategoryIds, setSelectedCategoryIds] = useState<number[]>([])
  const [refFormat, setRefFormat] = useState<"apa" | "bibtex">("apa")
  const [refOutput, setRefOutput] = useState<"text" | "pdf">("text")
  const [textOutput, setTextOutput] = useState("")
  const [busy, setBusy] = useState<"none" | "pdf" | "txt" | "ref">("none")

  const flattened = flattenCategories(categories)

  const toggleCategory = (id: number) => {
    setSelectedCategoryIds((prev) => (prev.includes(id) ? prev.filter((v) => v !== id) : [...prev, id]))
  }

  const payload = selectedCategoryIds.length ? { category_ids: selectedCategoryIds } : {}

  return (
    <section className="rounded-xl border border-slate-700/60 bg-panel p-3">
      <h3 className="mb-2 text-sm font-semibold text-cyan">导出</h3>

      <div className="mb-2 max-h-20 overflow-auto rounded border border-slate-700/40 bg-slate-900/60 p-2 text-xs scrollbar-thin">
        {flattened.length === 0 ? <p className="text-slate-400">暂无分类，默认导出全部</p> : null}
        {flattened.map((item) => (
          <label key={item.id} className="mb-1 flex items-center gap-2">
            <input
              checked={selectedCategoryIds.includes(item.id)}
              disabled={busy !== "none"}
              onChange={() => toggleCategory(item.id)}
              type="checkbox"
            />
            <span>
              {"--".repeat(item.depth)} {item.name}
            </span>
          </label>
        ))}
      </div>

      <div className="mb-2 flex gap-2">
        <button
          className="inline-flex items-center gap-2 rounded bg-cyan/20 px-2 py-1 text-xs text-cyan disabled:opacity-40"
          disabled={busy !== "none"}
          onClick={async () => {
            setBusy("pdf")
            try {
              const result = await exportPdfs(payload)
              window.open(result.download_url, "_blank")
            } finally {
              setBusy("none")
            }
          }}
          type="button"
        >
          {busy === "pdf" ? <Spinner /> : null}
          导出 PDF 压缩包
        </button>
        <button
          className="inline-flex items-center gap-2 rounded bg-emerald-500/20 px-2 py-1 text-xs text-emerald-200 disabled:opacity-40"
          disabled={busy !== "none"}
          onClick={async () => {
            setBusy("txt")
            try {
              const result = await exportTexts(payload)
              window.open(result.download_url, "_blank")
            } finally {
              setBusy("none")
            }
          }}
          type="button"
        >
          {busy === "txt" ? <Spinner /> : null}
          导出 TXT 压缩包
        </button>
      </div>

      <div className="mb-2 flex gap-2">
        <select
          className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs"
          disabled={busy !== "none"}
          onChange={(event) => setRefFormat(event.target.value as "apa" | "bibtex")}
          value={refFormat}
        >
          <option value="apa">APA</option>
          <option value="bibtex">BibTeX</option>
        </select>
        <select
          className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs"
          disabled={busy !== "none"}
          onChange={(event) => setRefOutput(event.target.value as "text" | "pdf")}
          value={refOutput}
        >
          <option value="text">文本</option>
          <option value="pdf">PDF</option>
        </select>
        <button
          className="inline-flex items-center gap-2 rounded bg-violet/20 px-2 py-1 text-xs text-violet-200 disabled:opacity-40"
          disabled={busy !== "none"}
          onClick={async () => {
            setBusy("ref")
            try {
              const result = await exportReferences({
                format: refFormat,
                output: refOutput,
                ...payload,
              })
              if (result.output === "pdf") {
                window.open(result.download_url, "_blank")
              } else {
                setTextOutput(result.content)
              }
            } finally {
              setBusy("none")
            }
          }}
          type="button"
        >
          {busy === "ref" ? <Spinner /> : null}
          导出参考文献
        </button>
      </div>

      {busy !== "none" ? <p className="mb-2 text-[11px] text-slate-400">正在生成导出文件，请稍候...</p> : null}

      {textOutput ? (
        <textarea
          className="h-24 w-full rounded border border-slate-600 bg-slate-950 p-2 font-mono text-[11px]"
          readOnly
          value={textOutput}
        />
      ) : null}
    </section>
  )
}
