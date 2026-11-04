import { useMemo } from "react"
import ReactMarkdown from "react-markdown"
import rehypeKatex from "rehype-katex"
import remarkBreaks from "remark-breaks"
import remarkGfm from "remark-gfm"
import remarkMath from "remark-math"

type Props = {
  content: string
}

function normalizeLatexDelimiters(input: string): string {
  if (!input) {
    return ""
  }
  return input
    .replace(/\\\[((?:.|\n)*?)\\\]/g, (_match, expr: string) => `\n$$${expr}$$\n`)
    .replace(/\\\(((?:.|\n)*?)\\\)/g, (_match, expr: string) => `$${expr}$`)
}

export function MarkdownContent({ content }: Props) {
  const normalized = useMemo(() => normalizeLatexDelimiters(content || ""), [content])

  return (
    <div className="markdown-content">
      <ReactMarkdown rehypePlugins={[rehypeKatex]} remarkPlugins={[remarkGfm, remarkMath, remarkBreaks]}>
        {normalized}
      </ReactMarkdown>
    </div>
  )
}
