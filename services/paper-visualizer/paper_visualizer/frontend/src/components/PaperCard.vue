<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import type { PaperSummary } from '@/api'
import { useLangStore } from '@/stores/lang'
import { useT } from '@/i18n'

const props = defineProps<{ paper: PaperSummary }>()
const lang = useLangStore()
const t = useT()

const tierColor: Record<string, string> = {
  A: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
  B: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  C: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
}

const repoLabel = computed(() => {
  const r = props.paper.repo ?? 'realresearch'
  return r === 'structural' ? t('repoStructural') : t('repoRealresearch')
})
const repoColor = computed(() =>
  (props.paper.repo ?? 'realresearch') === 'structural'
    ? 'bg-violet-500/15 text-violet-400 border-violet-500/30'
    : 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
)
const tier = computed(() => props.paper.quality?.tier ?? null)
const sigScore = computed(() => props.paper.quality?.significance_score ?? null)
const sigMax = computed(() => props.paper.quality?.significance_max ?? 16)
const sigPct = computed(() =>
  sigScore.value !== null ? Math.round((sigScore.value / sigMax.value) * 100) : 0,
)
</script>

<template>
  <div
    class="rounded-lg border border-slate-800 bg-slate-900/60 hover:border-brand-500/60 transition p-4 flex flex-col gap-3"
  >
    <div class="flex flex-wrap gap-1.5 items-center">
      <!-- Source repo badge -->
      <span
        class="text-[10px] px-1.5 py-0.5 rounded border font-medium"
        :class="repoColor"
      >{{ repoLabel }}</span>
      <!-- Tier badge -->
      <span
        v-if="tier"
        class="text-[11px] px-2 py-0.5 rounded font-bold uppercase tracking-wide border"
        :class="tierColor[tier] ?? 'bg-slate-600/30 text-slate-300 border-slate-600'"
      >Tier {{ tier }}</span>
      <!-- Significance mini-bar -->
      <span
        v-if="sigScore !== null"
        class="text-[11px] flex items-center gap-1"
        :title="`Significance: ${sigScore}/${sigMax}`"
      >
        <span class="inline-block w-12 h-1.5 rounded-full bg-slate-700 overflow-hidden">
          <span
            class="block h-full rounded-full transition-all"
            :class="sigPct >= 80 ? 'bg-emerald-400' : sigPct >= 60 ? 'bg-amber-400' : 'bg-slate-400'"
            :style="`width: ${sigPct}%`"
          />
        </span>
        <span class="text-slate-400">{{ sigScore }}/{{ sigMax }}</span>
      </span>
      <!-- Domain chips -->
      <span
        v-for="d in paper.domain.slice(0, 2)"
        :key="d"
        class="text-[11px] px-2 py-0.5 rounded bg-brand-500/15 text-brand-500 font-medium"
      >{{ d.replace(/_/g, ' ') }}</span>
    </div>
    <RouterLink :to="`/papers/${paper.slug}`" class="block">
      <h3 class="text-base font-semibold leading-snug hover:text-brand-500 transition">
        {{ paper.short_title[lang.current] || paper.short_title.en || paper.slug }}
      </h3>
    </RouterLink>
    <p class="text-sm text-slate-400 line-clamp-3 min-h-[3.5em]">{{
      typeof paper.one_liner === 'string'
        ? paper.one_liner
        : (paper.one_liner[lang.current] || paper.one_liner.en || '')
    }}</p>
    <div class="flex gap-2 mt-1">
      <RouterLink
        :to="`/papers/${paper.slug}`"
        class="text-xs px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700"
      >{{ t('read') }}</RouterLink>
      <RouterLink
        :to="`/papers/${paper.slug}?chat=1`"
        class="text-xs px-3 py-1.5 rounded bg-brand-500/20 hover:bg-brand-500/30 text-brand-500 border border-brand-500/30"
      >{{ t('askAi') }}</RouterLink>
    </div>
  </div>
</template>
