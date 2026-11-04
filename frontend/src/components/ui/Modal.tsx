import type { ReactNode } from "react"

type Props = {
  open: boolean
  title: string
  description?: string
  children?: ReactNode
  onClose: () => void
  footer?: ReactNode
}

export function Modal({ open, title, description, children, onClose, footer }: Props) {
  if (!open) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm" role="dialog" aria-modal>
      <div className="w-full max-w-2xl rounded-2xl border border-slate-700/60 bg-slate-900/95 shadow-2xl shadow-cyan/10">
        <div className="flex items-start justify-between gap-3 border-b border-slate-700/50 px-5 py-4">
          <div>
            <h3 className="text-base font-semibold text-slate-100">{title}</h3>
            {description ? <p className="mt-1 text-xs text-slate-400">{description}</p> : null}
          </div>
          <button
            className="rounded border border-slate-600 px-2 py-1 text-xs text-slate-300 hover:border-cyan/70 hover:text-cyan"
            onClick={onClose}
            type="button"
          >
            关闭
          </button>
        </div>

        <div className="max-h-[70vh] overflow-auto px-5 py-4 scrollbar-thin">{children}</div>

        {footer ? <div className="flex justify-end gap-2 border-t border-slate-700/50 px-5 py-4">{footer}</div> : null}
      </div>
    </div>
  )
}
