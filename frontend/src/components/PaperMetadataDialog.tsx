import { useEffect, useMemo, useState } from "react"
import type { Paper } from "../lib/types"
import { Modal } from "./ui/Modal"
import { Spinner } from "./ui/Spinner"

type Props = {
  paper: Paper | null
  submitting: boolean
  onClose: () => void
  onSubmit: (paperId: number, payload: {
    title: string
    authors: string[]
    year: number | null
    publisher: string
    doi: string
    summary_one_line: string
    abstract_original: string
    abstract_zh: string
  }) => Promise<void>
}

type FormState = {
  title: string
  authors: string
  year: string
  publisher: string
  doi: string
  summary: string
  abstractOriginal: string
  abstractZh: string
}

const EMPTY_FORM: FormState = {
  title: "",
  authors: "",
  year: "",
  publisher: "",
  doi: "",
  summary: "",
  abstractOriginal: "",
  abstractZh: "",
}

function buildForm(paper: Paper | null): FormState {
  if (!paper) {
    return EMPTY_FORM
  }
  return {
    title: paper.title || "",
    authors: (paper.authors || []).join(", "),
    year: paper.year == null ? "" : String(paper.year),
    publisher: paper.publisher || "",
    doi: paper.doi || "",
    summary: paper.summary_one_line || "",
    abstractOriginal: paper.abstract_original || "",
    abstractZh: paper.abstract_zh || "",
  }
}

export function PaperMetadataDialog({ paper, submitting, onClose, onSubmit }: Props) {
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [error, setError] = useState("")

  useEffect(() => {
    setForm(buildForm(paper))
    setError("")
  }, [paper])

  const open = !!paper

  const footer = useMemo(
    () => (
      <>
        <button
          className="rounded border border-slate-600 px-3 py-1 text-sm text-slate-200 hover:border-slate-400 disabled:opacity-40"
          disabled={submitting}
          onClick={onClose}
          type="button"
        >
          取消
        </button>
        <button
          className="inline-flex items-center gap-2 rounded bg-cyan/20 px-3 py-1 text-sm text-cyan hover:bg-cyan/30 disabled:cursor-not-allowed disabled:opacity-40"
          disabled={submitting}
          onClick={() => {
            if (!paper) {
              return
            }

            const rawYear = form.year.trim()
            const parsedYear = rawYear === "" ? null : Number(rawYear)
            if (rawYear !== "" && Number.isNaN(parsedYear)) {
              setError("年份格式不正确，请输入数字或留空。")
              return
            }

            setError("")
            onSubmit(paper.id, {
              title: form.title.trim(),
              authors: form.authors
                .split(",")
                .map((item) => item.trim())
                .filter(Boolean),
              year: parsedYear,
              publisher: form.publisher.trim(),
              doi: form.doi.trim(),
              summary_one_line: form.summary.trim(),
              abstract_original: form.abstractOriginal.trim(),
              abstract_zh: form.abstractZh.trim(),
            }).catch(() => undefined)
          }}
          type="button"
        >
          {submitting ? <Spinner /> : null}
          保存修改
        </button>
      </>
    ),
    [form, onClose, onSubmit, paper, submitting],
  )

  return (
    <Modal
      description={paper ? `编辑论文 #${paper.id} 的元数据信息` : undefined}
      footer={footer}
      onClose={() => {
        if (!submitting) {
          onClose()
        }
      }}
      open={open}
      title="编辑论文元数据"
    >
      <div className="space-y-3">
        <label className="block">
          <span className="mb-1 block text-xs text-slate-400">标题</span>
          <input
            className="w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm"
            onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
            value={form.title}
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-xs text-slate-400">作者（英文逗号分隔）</span>
          <input
            className="w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm"
            onChange={(event) => setForm((prev) => ({ ...prev, authors: event.target.value }))}
            value={form.authors}
          />
        </label>

        <div className="grid gap-3 sm:grid-cols-3">
          <label className="block">
            <span className="mb-1 block text-xs text-slate-400">年份</span>
            <input
              className="w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm"
              onChange={(event) => setForm((prev) => ({ ...prev, year: event.target.value }))}
              placeholder="可留空"
              value={form.year}
            />
          </label>

          <label className="block sm:col-span-2">
            <span className="mb-1 block text-xs text-slate-400">出版方</span>
            <input
              className="w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm"
              onChange={(event) => setForm((prev) => ({ ...prev, publisher: event.target.value }))}
              value={form.publisher}
            />
          </label>
        </div>

        <label className="block">
          <span className="mb-1 block text-xs text-slate-400">DOI</span>
          <input
            className="w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm"
            onChange={(event) => setForm((prev) => ({ ...prev, doi: event.target.value }))}
            value={form.doi}
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-xs text-slate-400">一句话总结</span>
          <textarea
            className="h-16 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm"
            onChange={(event) => setForm((prev) => ({ ...prev, summary: event.target.value }))}
            value={form.summary}
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-xs text-slate-400">摘要原文</span>
          <textarea
            className="h-28 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm"
            onChange={(event) => setForm((prev) => ({ ...prev, abstractOriginal: event.target.value }))}
            value={form.abstractOriginal}
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-xs text-slate-400">摘要中文</span>
          <textarea
            className="h-28 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm"
            onChange={(event) => setForm((prev) => ({ ...prev, abstractZh: event.target.value }))}
            value={form.abstractZh}
          />
        </label>

        {error ? <p className="text-sm text-red-400">{error}</p> : null}
      </div>
    </Modal>
  )
}
