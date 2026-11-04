<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import MarkdownIt from 'markdown-it'
import katex from 'katex'

const props = defineProps<{ source: string }>()

const md = new MarkdownIt({ html: true, linkify: true, breaks: false })

/**
 * Clean LaTeX artifacts that the AI copied verbatim from the paper source.
 * Runs BEFORE math pre-rendering so math-internal commands are handled too.
 */
function cleanLatexArtifacts(src: string): string {
  let out = src

  // --- Outside math: LaTeX text commands → Markdown equivalents ---
  // \emph{text} → *text*
  out = out.replace(/\\emph\{([^}]+)\}/g, '*$1*')
  // \textbf{text} → **text**
  out = out.replace(/\\textbf\{([^}]+)\}/g, '**$1**')
  // \textit{text} → *text*
  out = out.replace(/\\textit\{([^}]+)\}/g, '*$1*')
  // \underline{text} → text (no markdown equivalent, just strip)
  out = out.replace(/\\underline\{([^}]+)\}/g, '$1')

  // --- Cross-references → plain label text ---
  // \Cref{label}, \cref{label} → "label" (cleaned)
  out = out.replace(/\\[Cc]ref\{([^}]+)\}/g, (_, label) => {
    // thm:main → Theorem main, lem:x → Lemma x, sec:y → Section y
    const cleaned = label
      .replace(/^thm:/, 'Theorem ')
      .replace(/^lem:/, 'Lemma ')
      .replace(/^prop:/, 'Proposition ')
      .replace(/^cor:/, 'Corollary ')
      .replace(/^def:/, 'Definition ')
      .replace(/^sec:/, 'Section ')
      .replace(/^eq:/, 'Eq. ')
      .replace(/^fig:/, 'Figure ')
    return cleaned
  })
  // \eqref{label} → (label)
  out = out.replace(/\\eqref\{([^}]+)\}/g, '($1)')
  // \ref{label} → label
  out = out.replace(/\\ref\{([^}]+)\}/g, (_, label) => {
    return label
      .replace(/^thm:/, 'Theorem ')
      .replace(/^lem:/, 'Lemma ')
      .replace(/^prop:/, 'Proposition ')
      .replace(/^cor:/, 'Corollary ')
      .replace(/^sec:/, 'Section ')
      .replace(/^eq:/, 'Eq. ')
  })
  // \cite{key} or \cite{key1,key2} → [key]
  out = out.replace(/\\cite\{([^}]+)\}/g, '[$1]')
  // \label{...} → remove entirely (stray labels in prose)
  out = out.replace(/\\label\{[^}]*\}/g, '')

  // --- Inside $...$ math: fix commands KaTeX doesn't know ---
  // \d → \mathrm{d} (differential d) — only when followed by space or letter
  out = out.replace(/(\$[^$]*)\bd\s/g, (match) =>
    match.replace(/\\d\s/g, '\\mathrm{d}\\,'),
  )

  // \P → \mathbb{P} (probability), \E → \mathbb{E} (expectation)
  // Only replace when these are standalone commands (not part of longer command)
  // These are tricky because they're valid LaTeX but KaTeX handles them differently
  // Skip for safety — KaTeX handles \mathbb{P} etc. natively

  return out
}

function parseDirectiveAttrs(body: string): Record<string, string> {
  const attrs: Record<string, string> = {}
  const re = /(\w+)\s*=\s*(?:"([^"]*)"|([^\s"}]+))/g
  let mm: RegExpExecArray | null
  while ((mm = re.exec(body)) !== null) {
    attrs[mm[1]] = mm[2] ?? mm[3] ?? ''
  }
  return attrs
}

function preprocessDirectives(src: string): string {
  // Match `:::theorem{...}\n...body...\n:::` blocks and convert to
  // <div class="thm-marker" data-id="..." data-label="...">body</div>
  src = src.replace(
    /:::theorem\{([^}]*)\}\n([\s\S]*?)\n:::/g,
    (_, attrBody, body) => {
      const attrs = parseDirectiveAttrs(attrBody)
      const id = attrs.id ?? ''
      const label = (attrs.label ?? '').replace(/"/g, '&quot;')
      return `<div class="thm-marker" data-id="${id}" data-label="${label}">\n\n${body}\n\n</div>`
    },
  )
  src = src.replace(
    /:::proof-sketch\{([^}]*)\}\n([\s\S]*?)\n:::/g,
    (_, attrBody, body) => {
      const attrs = parseDirectiveAttrs(attrBody)
      const forId = attrs.for ?? ''
      return `<div class="proof-marker" data-for="${forId}">\n\n${body}\n\n</div>`
    },
  )
  return src
}

function stripFrontmatter(src: string): string {
  if (!src.startsWith('---')) return src
  const end = src.indexOf('\n---', 3)
  if (end === -1) return src
  const after = src.slice(end + 4)
  return after.startsWith('\n') ? after.slice(1) : after
}

function renderMathToHtml(tex: string, display: boolean): string {
  try {
    return katex.renderToString(tex, {
      displayMode: display,
      throwOnError: false,
      output: 'html',
    })
  } catch {
    const escaped = tex
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
    return `<code class="text-rose-400">${escaped}</code>`
  }
}

interface MathPlaceholder {
  html: string
  tex: string
}

function renderWithMath(src: string): string {
  const placeholders: MathPlaceholder[] = []
  const token = (i: number) => `zzXmathXzz${i}zzXendXzz`

  let out = src.replace(/\$\$([\s\S]+?)\$\$/g, (_, tex) => {
    placeholders.push({
      html: `<div class="my-4 overflow-x-auto">${renderMathToHtml(tex.trim(), true)}</div>`,
      tex: tex.trim(),
    })
    return token(placeholders.length - 1)
  })

  out = out.replace(/\$([^\n$]+?)\$/g, (_, tex) => {
    placeholders.push({
      html: renderMathToHtml(tex.trim(), false),
      tex: tex.trim(),
    })
    return token(placeholders.length - 1)
  })

  const rendered = md.render(out)

  // Parse into a detached DOM so we can substitute tokens inside attribute
  // values as plain text, and tokens inside text nodes as HTML.
  const tmp = document.createElement('div')
  tmp.innerHTML = rendered

  const tokenRe = /zzXmathXzz(\d+)zzXendXzz/g

  // Substitute tokens in attribute values with plain-text LaTeX.
  const walkerEls = document.createNodeIterator(tmp, NodeFilter.SHOW_ELEMENT)
  let elNode: Node | null
  while ((elNode = walkerEls.nextNode())) {
    const el = elNode as Element
    for (const attr of Array.from(el.attributes)) {
      if (attr.value.includes('zzXmathXzz')) {
        const replaced = attr.value.replace(tokenRe, (_, n) => placeholders[Number(n)]?.tex ?? '')
        el.setAttribute(attr.name, replaced)
      }
    }
  }

  // Substitute tokens in text nodes with inline HTML (KaTeX).
  const walkerTx = document.createNodeIterator(tmp, NodeFilter.SHOW_TEXT)
  const textNodes: Text[] = []
  let txNode: Node | null
  while ((txNode = walkerTx.nextNode())) {
    if ((txNode as Text).data.includes('zzXmathXzz')) {
      textNodes.push(txNode as Text)
    }
  }
  for (const text of textNodes) {
    const data = text.data
    const frag = document.createDocumentFragment()
    let last = 0
    let m: RegExpExecArray | null
    const re = /zzXmathXzz(\d+)zzXendXzz/g
    while ((m = re.exec(data)) !== null) {
      if (m.index > last) frag.appendChild(document.createTextNode(data.slice(last, m.index)))
      const span = document.createElement('span')
      span.innerHTML = placeholders[Number(m[1])]?.html ?? ''
      // Hoist children out of the wrapper span
      while (span.firstChild) frag.appendChild(span.firstChild)
      last = re.lastIndex
    }
    if (last < data.length) frag.appendChild(document.createTextNode(data.slice(last)))
    text.parentNode?.replaceChild(frag, text)
  }

  return tmp.innerHTML
}

const rawHtml = computed(() => {
  const stripped = stripFrontmatter(props.source)
  const cleaned = cleanLatexArtifacts(stripped)
  const withDirectives = preprocessDirectives(cleaned)
  return renderWithMath(withDirectives)
})

const host = ref<HTMLElement | null>(null)

function upgradeHost(el: HTMLElement) {
  el.querySelectorAll('.thm-marker').forEach((node) => {
    const id = node.getAttribute('data-id') || ''
    const label = node.getAttribute('data-label') || ''
    const inner = node.innerHTML
    const wrapper = document.createElement('div')
    wrapper.className =
      'my-5 border-l-4 border-brand-500 bg-brand-500/5 rounded-r px-5 py-4'
    wrapper.innerHTML = `
      <div class="text-[11px] uppercase tracking-wider text-brand-500 font-semibold mb-2">
        ${label} <span class="text-slate-500 font-normal">· ${id}</span>
      </div>
      <div class="text-slate-100 theorem-body">${inner}</div>
    `
    node.replaceWith(wrapper)
  })

  el.querySelectorAll('.proof-marker').forEach((node) => {
    const forId = node.getAttribute('data-for') || ''
    const inner = node.innerHTML
    const details = document.createElement('details')
    details.className =
      'my-4 border-l-4 border-slate-600 bg-slate-900/60 rounded-r px-5 py-3'
    details.innerHTML = `
      <summary class="cursor-pointer text-sm font-semibold text-slate-200 select-none">
        ▸ Proof sketch · ${forId}
      </summary>
      <div class="mt-3 text-sm text-slate-300 leading-relaxed">${inner}</div>
    `
    node.replaceWith(details)
  })
}

async function upgrade() {
  await nextTick()
  if (!host.value) return
  upgradeHost(host.value)
}

onMounted(upgrade)
watch(() => props.source, upgrade)
</script>

<template>
  <div ref="host" class="prose-math" v-html="rawHtml" />
</template>
