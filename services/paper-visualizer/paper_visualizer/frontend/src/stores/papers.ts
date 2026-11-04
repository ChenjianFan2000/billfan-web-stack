import { defineStore } from 'pinia'
import { fetchPapers, fetchTags, type PaperSummary, type TagIndex } from '@/api'

interface State {
  papers: PaperSummary[]
  tags: TagIndex
  loaded: boolean
  filterDomains: Set<string>
  filterTools: Set<string>
  filterStatus: Set<string>
  filterRepos: Set<string>
  search: string
}

export const usePapersStore = defineStore('papers', {
  state: (): State => ({
    papers: [],
    tags: { domains: {}, math_tools: {} },
    loaded: false,
    filterDomains: new Set(),
    filterTools: new Set(),
    filterStatus: new Set(),
    filterRepos: new Set(),
    search: '',
  }),
  getters: {
    filtered(state): PaperSummary[] {
      return state.papers.filter((p) => {
        if (state.filterDomains.size && !p.domain.some((d) => state.filterDomains.has(d)))
          return false
        if (state.filterTools.size && !p.math_tools.some((t) => state.filterTools.has(t)))
          return false
        if (state.filterStatus.size && !state.filterStatus.has(p.status)) return false
        if (state.filterRepos.size && !state.filterRepos.has(p.repo ?? 'realresearch')) return false
        if (state.search) {
          const q = state.search.toLowerCase()
          const liner = typeof p.one_liner === 'string' ? p.one_liner : `${p.one_liner.zh} ${p.one_liner.en}`
          const hay = `${p.short_title.zh} ${p.short_title.en} ${liner}`.toLowerCase()
          if (!hay.includes(q)) return false
        }
        return true
      })
    },
  },
  actions: {
    async load() {
      if (this.loaded) return
      const [idx, tags] = await Promise.all([fetchPapers(), fetchTags()])
      this.papers = idx.papers
      this.tags = tags
      this.loaded = true
    },
    toggleDomain(d: string) {
      if (this.filterDomains.has(d)) this.filterDomains.delete(d)
      else this.filterDomains.add(d)
    },
    toggleTool(t: string) {
      if (this.filterTools.has(t)) this.filterTools.delete(t)
      else this.filterTools.add(t)
    },
    toggleStatus(s: string) {
      if (this.filterStatus.has(s)) this.filterStatus.delete(s)
      else this.filterStatus.add(s)
    },
    toggleRepo(r: string) {
      if (this.filterRepos.has(r)) this.filterRepos.delete(r)
      else this.filterRepos.add(r)
    },
    clearFilters() {
      this.filterDomains.clear()
      this.filterTools.clear()
      this.filterStatus.clear()
      this.filterRepos.clear()
      this.search = ''
    },
  },
})
