export type ToastItem = {
  id: number
  tone: "success" | "error" | "info"
  message: string
}

const toneClass: Record<ToastItem["tone"], string> = {
  success: "border-emerald-500/50 bg-emerald-500/15 text-emerald-100",
  error: "border-red-500/50 bg-red-500/15 text-red-100",
  info: "border-cyan/50 bg-cyan/15 text-cyan-100",
}

export function ToastViewport({ toasts }: { toasts: ToastItem[] }) {
  if (!toasts.length) {
    return null
  }

  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-[min(92vw,360px)] flex-col gap-2">
      {toasts.map((toast) => (
        <div key={toast.id} className={`rounded-xl border px-3 py-2 text-sm shadow-xl backdrop-blur ${toneClass[toast.tone]}`}>
          {toast.message}
        </div>
      ))}
    </div>
  )
}
