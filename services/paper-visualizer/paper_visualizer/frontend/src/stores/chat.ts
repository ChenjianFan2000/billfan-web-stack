import { defineStore } from 'pinia'

export interface Msg {
  role: 'user' | 'assistant'
  content: string
}

interface State {
  histories: Record<string, Msg[]>
}

function loadHistory(slug: string): Msg[] {
  if (typeof localStorage === 'undefined') return []
  try {
    const raw = localStorage.getItem(`chat:${slug}`)
    return raw ? (JSON.parse(raw) as Msg[]) : []
  } catch {
    return []
  }
}

export const useChatStore = defineStore('chat', {
  state: (): State => ({ histories: {} }),
  actions: {
    get(slug: string): Msg[] {
      if (!this.histories[slug]) this.histories[slug] = loadHistory(slug)
      return this.histories[slug]
    },
    append(slug: string, msg: Msg) {
      const h = this.get(slug)
      h.push(msg)
      this._persist(slug)
    },
    appendToLast(slug: string, text: string) {
      const h = this.get(slug)
      if (h.length && h[h.length - 1].role === 'assistant') {
        h[h.length - 1].content += text
        this._persist(slug)
      }
    },
    clear(slug: string) {
      this.histories[slug] = []
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem(`chat:${slug}`)
      }
    },
    _persist(slug: string) {
      if (typeof localStorage === 'undefined') return
      const h = this.histories[slug] ?? []
      localStorage.setItem(`chat:${slug}`, JSON.stringify(h.slice(-40)))
    },
  },
})
