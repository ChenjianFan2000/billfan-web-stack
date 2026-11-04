<script setup lang="ts">
import { computed } from 'vue'
import { usePapersStore } from '@/stores/papers'
import { useLangStore } from '@/stores/lang'
import { useT } from '@/i18n'

const papers = usePapersStore()
const lang = useLangStore()
const t = useT()

const domains = computed(() => Object.entries(papers.tags.domains))
const tools = computed(() => Object.entries(papers.tags.math_tools))

const statuses = computed(() => {
  const set = new Set<string>()
  papers.papers.forEach((p) => set.add(p.status))
  return Array.from(set)
})

const repos = computed(() => {
  const counts: Record<string, number> = {}
  papers.papers.forEach((p) => {
    const r = p.repo ?? 'realresearch'
    counts[r] = (counts[r] ?? 0) + 1
  })
  return Object.entries(counts)
})

const repoLabels: Record<string, Record<string, string>> = {
  realresearch: { zh: '计算金融', en: 'Comp. Finance' },
  structural: { zh: '结构研究', en: 'Structural' },
}
</script>

<template>
  <aside class="w-56 shrink-0 border-r border-slate-800 px-4 py-5 text-sm hidden lg:block">
    <div class="text-[11px] uppercase tracking-wider text-slate-500 mb-2">
      {{ t('byDomain') }}
    </div>
    <div class="flex flex-col gap-1 mb-5">
      <label
        v-for="[key, entry] in domains"
        :key="key"
        class="flex items-center gap-2 cursor-pointer hover:text-white"
      >
        <input
          type="checkbox"
          :checked="papers.filterDomains.has(key)"
          @change="papers.toggleDomain(key)"
          class="accent-brand-500"
        />
        <span>{{ entry.label[lang.current] || key.replace(/_/g, ' ') }}</span>
        <span class="text-slate-500 text-xs">({{ entry.papers.length }})</span>
      </label>
    </div>

    <div class="text-[11px] uppercase tracking-wider text-slate-500 mb-2">
      {{ t('byTool') }}
    </div>
    <div class="flex flex-col gap-1 mb-5">
      <label
        v-for="[key, entry] in tools"
        :key="key"
        class="flex items-center gap-2 cursor-pointer hover:text-white"
      >
        <input
          type="checkbox"
          :checked="papers.filterTools.has(key)"
          @change="papers.toggleTool(key)"
          class="accent-brand-500"
        />
        <span>{{ entry.label[lang.current] || key.replace(/_/g, ' ') }}</span>
        <span class="text-slate-500 text-xs">({{ entry.papers.length }})</span>
      </label>
    </div>

    <div class="text-[11px] uppercase tracking-wider text-slate-500 mb-2">
      {{ t('byStatus') }}
    </div>
    <div class="flex flex-col gap-1 mb-5">
      <label
        v-for="s in statuses"
        :key="s"
        class="flex items-center gap-2 cursor-pointer hover:text-white"
      >
        <input
          type="checkbox"
          :checked="papers.filterStatus.has(s)"
          @change="papers.toggleStatus(s)"
          class="accent-brand-500"
        />
        <span>{{ s.replace(/_/g, ' ') }}</span>
      </label>
    </div>

    <div class="text-[11px] uppercase tracking-wider text-slate-500 mb-2">
      {{ t('bySource') }}
    </div>
    <div class="flex flex-col gap-1 mb-5">
      <label
        v-for="[key, count] in repos"
        :key="key"
        class="flex items-center gap-2 cursor-pointer hover:text-white"
      >
        <input
          type="checkbox"
          :checked="papers.filterRepos.has(key)"
          @change="papers.toggleRepo(key)"
          class="accent-brand-500"
        />
        <span>{{ repoLabels[key]?.[lang.current] ?? key }}</span>
        <span class="text-slate-500 text-xs">({{ count }})</span>
      </label>
    </div>

    <button
      class="text-xs text-slate-400 hover:text-slate-200"
      @click="papers.clearFilters()"
    >{{ t('clearFilters') }}</button>
  </aside>
</template>
