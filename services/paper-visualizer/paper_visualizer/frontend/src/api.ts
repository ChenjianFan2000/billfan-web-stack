export interface LocalizedStr {
  zh: string
  en: string
}

export interface QualitySummary {
  tier: string | null
  significance_score: number | null
  significance_max: number
}

export interface QualityFull {
  tier?: string
  tier_confidence?: string
  significance_score?: number
  significance_max?: number
  critic_verdict?: string
  coherence_verdict?: string
  dimensions?: Record<string, string>
  target_venues?: string[]
  phase?: string
  project_status?: string
}

export interface PaperSummary {
  slug: string
  short_title: LocalizedStr
  status: string
  domain: string[]
  math_tools: string[]
  one_liner: LocalizedStr | string
  repo?: string
  quality?: QualitySummary | null
}

export interface PaperIndex {
  generated_at: string
  papers: PaperSummary[]
}

export interface TheoremBlock {
  id: string
  env: string
  statement_tex: string
  section_number: string | null
  label: LocalizedStr
  key_ideas: { zh: string[]; en: string[] }
}

export interface Prerequisite {
  topic_id: string
  level: string
  why: string
}

export interface RelatedPaper {
  slug: string
  relation: string
  note: string
}

export interface PaperMeta {
  slug: string
  title: LocalizedStr
  short_title: LocalizedStr
  author: string
  date: string
  status: string
  abstract: { tex: string; zh: string; en: string }
  domain: string[]
  math_tools: string[]
  prerequisites: Prerequisite[]
  main_theorems: TheoremBlock[]
  sections: Array<{ number: string; title_tex: string }>
  related_papers: RelatedPaper[]
  figures: Array<{ path: string; caption_tex: string }>
  source: { tex_path: string; pdf_path: string | null; source_hash?: string; ingested_at?: string }
  repo?: string
  project_id?: string | null
  quality?: QualityFull
}

export interface PaperDetail {
  meta: PaperMeta
  content: { zh: string; en: string }
}

export interface TagEntry {
  label: LocalizedStr
  papers: string[]
}

export interface TagIndex {
  domains: Record<string, TagEntry>
  math_tools: Record<string, TagEntry>
}

const API = '/api'

export async function fetchPapers(): Promise<PaperIndex> {
  const r = await fetch(`${API}/papers`)
  if (!r.ok) throw new Error(`fetchPapers ${r.status}`)
  return r.json()
}

export async function fetchPaper(slug: string): Promise<PaperDetail> {
  const r = await fetch(`${API}/papers/${encodeURIComponent(slug)}`)
  if (!r.ok) throw new Error(`fetchPaper ${r.status}`)
  return r.json()
}

export async function fetchTags(): Promise<TagIndex> {
  const r = await fetch(`${API}/tags`)
  if (!r.ok) throw new Error(`fetchTags ${r.status}`)
  return r.json()
}

export interface ChatRequest {
  paper_slug: string
  message: string
  history: { role: 'user' | 'assistant'; content: string }[]
  lang: 'zh' | 'en'
  current_section?: string
}

export async function streamChat(
  req: ChatRequest,
  onToken: (text: string) => void,
  onDone: () => void,
  onError: (msg: string) => void,
): Promise<void> {
  let response: Response
  try {
    response = await fetch(`${API}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    })
  } catch (e) {
    onError((e as Error).message)
    return
  }
  if (!response.ok || !response.body) {
    onError(`chat ${response.status}`)
    return
  }
  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buf = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    const events = buf.split('\n\n')
    buf = events.pop() ?? ''
    for (const ev of events) {
      const lines = ev.split('\n')
      const evLine = lines.find((l) => l.startsWith('event: '))
      const dataLine = lines.find((l) => l.startsWith('data: '))
      if (!evLine || !dataLine) continue
      const kind = evLine.slice(7).trim()
      const payload = dataLine.slice(6)
      try {
        const obj = JSON.parse(payload)
        if (kind === 'token' && obj.text) onToken(obj.text)
        if (kind === 'done') {
          onDone()
          return
        }
        if (kind === 'error') {
          onError(obj.message ?? 'unknown')
          return
        }
      } catch {
        /* partial frame, keep accumulating */
      }
    }
  }
  onDone()
}
