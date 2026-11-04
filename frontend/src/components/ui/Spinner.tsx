export function Spinner({ size = "sm" }: { size?: "sm" | "md" }) {
  const cls = size === "md" ? "h-5 w-5 border-2" : "h-4 w-4 border-2"
  return <span aria-hidden className={`${cls} inline-block animate-spin rounded-full border-slate-500 border-t-cyan`} />
}
