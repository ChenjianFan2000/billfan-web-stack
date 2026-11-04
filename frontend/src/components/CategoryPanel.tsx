import { useMemo, useState } from "react"
import type { CategoryNode } from "../lib/types"
import { flattenCategories } from "../lib/tree"
import { Modal } from "./ui/Modal"
import { Spinner } from "./ui/Spinner"

type Props = {
  categories: CategoryNode[]
  onCreate: (payload: { name: string; parent_id?: number | null }) => Promise<void>
  onUpdate: (categoryId: number, payload: { name?: string; parent_id?: number | null; order_index?: number }) => Promise<void>
  onDelete: (categoryId: number) => Promise<void>
}

export function CategoryPanel({ categories, onCreate, onUpdate, onDelete }: Props) {
  const [name, setName] = useState("")
  const [parentId, setParentId] = useState<string>("")
  const [busyCreate, setBusyCreate] = useState(false)
  const [busyActionId, setBusyActionId] = useState<number | null>(null)
  const [renameTarget, setRenameTarget] = useState<{ id: number; name: string } | null>(null)
  const [renameInput, setRenameInput] = useState("")
  const [deleteTarget, setDeleteTarget] = useState<{ id: number; name: string } | null>(null)

  const flat = useMemo(() => flattenCategories(categories), [categories])

  return (
    <section className="rounded-xl border border-slate-700/60 bg-panel p-3">
      <h3 className="mb-2 text-sm font-semibold text-cyan">类目管理</h3>
      <div className="mb-3 space-y-2 rounded border border-slate-700/40 bg-slate-900/60 p-2">
        <input
          className="w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs"
          disabled={busyCreate}
          onChange={(event) => setName(event.target.value)}
          placeholder="新分类名称"
          value={name}
        />
        <select
          className="w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs"
          disabled={busyCreate}
          onChange={(event) => setParentId(event.target.value)}
          value={parentId}
        >
          <option value="">根分类</option>
          {flat
            .filter((item) => item.depth === 0)
            .map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
        </select>
        <button
          className="inline-flex w-full items-center justify-center gap-2 rounded bg-cyan/20 px-2 py-1 text-xs text-cyan hover:bg-cyan/30 disabled:cursor-not-allowed disabled:opacity-40"
          disabled={busyCreate}
          onClick={async () => {
            const finalName = name.trim()
            if (!finalName) {
              return
            }
            setBusyCreate(true)
            try {
              await onCreate({ name: finalName, parent_id: parentId ? Number(parentId) : null })
              setName("")
              setParentId("")
            } finally {
              setBusyCreate(false)
            }
          }}
          type="button"
        >
          {busyCreate ? <Spinner /> : null}
          新建分类
        </button>
      </div>

      <div className="max-h-40 space-y-1 overflow-auto pr-1 text-xs scrollbar-thin">
        {flat.length === 0 ? <p className="text-slate-400">暂无分类</p> : null}
        {flat.map((item) => (
          <div key={item.id} className="flex items-center justify-between rounded border border-slate-700/50 bg-slate-900/70 px-2 py-1">
            <span style={{ paddingLeft: item.depth * 12 }}>
              {item.depth > 0 ? "└ " : ""}
              {item.name}
            </span>
            <div className="flex gap-1">
              <button
                className="rounded border border-slate-600 px-2 py-0.5 text-[11px] hover:border-violet hover:text-violet disabled:opacity-40"
                disabled={busyActionId === item.id}
                onClick={() => {
                  setRenameTarget({ id: item.id, name: item.name })
                  setRenameInput(item.name)
                }}
                type="button"
              >
                改名
              </button>
              <button
                className="rounded border border-red-500/60 px-2 py-0.5 text-[11px] text-red-300 hover:bg-red-500/20 disabled:opacity-40"
                disabled={busyActionId === item.id}
                onClick={() => setDeleteTarget({ id: item.id, name: item.name })}
                type="button"
              >
                删除
              </button>
            </div>
          </div>
        ))}
      </div>

      <Modal
        footer={
          <>
            <button
              className="rounded border border-slate-600 px-3 py-1 text-sm"
              disabled={busyActionId === renameTarget?.id}
              onClick={() => setRenameTarget(null)}
              type="button"
            >
              取消
            </button>
            <button
              className="inline-flex items-center gap-2 rounded bg-violet/20 px-3 py-1 text-sm text-violet-100 disabled:opacity-40"
              disabled={!renameTarget || !renameInput.trim() || busyActionId === renameTarget.id}
              onClick={async () => {
                if (!renameTarget) {
                  return
                }
                setBusyActionId(renameTarget.id)
                try {
                  await onUpdate(renameTarget.id, { name: renameInput.trim() })
                  setRenameTarget(null)
                } finally {
                  setBusyActionId(null)
                }
              }}
              type="button"
            >
              {renameTarget && busyActionId === renameTarget.id ? <Spinner /> : null}
              保存
            </button>
          </>
        }
        onClose={() => setRenameTarget(null)}
        open={!!renameTarget}
        title="重命名分类"
      >
        <input
          className="w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm"
          onChange={(event) => setRenameInput(event.target.value)}
          value={renameInput}
        />
      </Modal>

      <Modal
        footer={
          <>
            <button
              className="rounded border border-slate-600 px-3 py-1 text-sm"
              disabled={busyActionId === deleteTarget?.id}
              onClick={() => setDeleteTarget(null)}
              type="button"
            >
              取消
            </button>
            <button
              className="inline-flex items-center gap-2 rounded bg-red-500/20 px-3 py-1 text-sm text-red-200 disabled:opacity-40"
              disabled={!deleteTarget || busyActionId === deleteTarget.id}
              onClick={async () => {
                if (!deleteTarget) {
                  return
                }
                setBusyActionId(deleteTarget.id)
                try {
                  await onDelete(deleteTarget.id)
                  setDeleteTarget(null)
                } finally {
                  setBusyActionId(null)
                }
              }}
              type="button"
            >
              {deleteTarget && busyActionId === deleteTarget.id ? <Spinner /> : null}
              确认删除
            </button>
          </>
        }
        onClose={() => setDeleteTarget(null)}
        open={!!deleteTarget}
        title="删除分类"
      >
        <p className="text-sm text-slate-300">确认删除分类 “{deleteTarget?.name}”？此操作不可撤销。</p>
      </Modal>
    </section>
  )
}
