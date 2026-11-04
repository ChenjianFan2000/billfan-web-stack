<script setup lang="ts">
import { computed } from 'vue'
import type { QualityFull } from '@/api'
import { useLangStore } from '@/stores/lang'

const props = defineProps<{ quality: QualityFull | undefined }>()
const lang = useLangStore()

const dims = computed(() => {
  const d = props.quality?.dimensions ?? {}
  return Object.entries(d)
})

const dimColor: Record<string, string> = {
  strong: 'bg-emerald-500/20 text-emerald-400',
  acceptable: 'bg-brand-500/20 text-brand-500',
  weak: 'bg-amber-500/20 text-amber-400',
}

const tierLabel: Record<string, Record<string, string>> = {
  A: { zh: '课程级', en: 'Coursework' },
  B: { zh: '专刊级', en: 'Specialized Journal' },
  C: { zh: '顶刊级', en: 'Top Venue' },
}

const sigScore = computed(() => props.quality?.significance_score ?? null)
const sigMax = computed(() => props.quality?.significance_max ?? 16)
const sigPct = computed(() =>
  sigScore.value !== null ? Math.round((sigScore.value / sigMax.value) * 100) : 0,
)
const tier = computed(() => props.quality?.tier ?? null)
</script>

<template>
  <div v-if="quality">
    <!-- Tier -->
    <div v-if="tier" class="mb-3">
      <div class="flex items-center gap-2 mb-1">
        <span
          class="text-sm font-bold px-2.5 py-0.5 rounded border"
          :class="{
            'bg-slate-500/20 text-slate-300 border-slate-500/30': tier === 'A',
            'bg-emerald-500/20 text-emerald-400 border-emerald-500/30': tier === 'B',
            'bg-amber-500/20 text-amber-400 border-amber-500/30': tier === 'C',
          }"
        >Tier {{ tier }}</span>
        <span class="text-xs text-slate-500">{{ tierLabel[tier]?.[lang.current] ?? '' }}</span>
      </div>
    </div>

    <!-- Significance bar -->
    <div v-if="sigScore !== null" class="mb-3">
      <div class="flex justify-between text-xs mb-1">
        <span class="text-slate-400">{{ lang.current === 'zh' ? '显著性' : 'Significance' }}</span>
        <span class="font-semibold" :class="sigPct >= 80 ? 'text-emerald-400' : sigPct >= 60 ? 'text-amber-400' : 'text-slate-400'">
          {{ sigScore }} / {{ sigMax }}
        </span>
      </div>
      <div class="w-full h-2 rounded-full bg-slate-700 overflow-hidden">
        <div
          class="h-full rounded-full transition-all"
          :class="sigPct >= 80 ? 'bg-emerald-400' : sigPct >= 60 ? 'bg-amber-400' : 'bg-slate-400'"
          :style="`width: ${sigPct}%`"
        />
      </div>
    </div>

    <!-- Dimension badges -->
    <div v-if="dims.length" class="mb-3">
      <div class="text-[11px] text-slate-500 mb-1">{{ lang.current === 'zh' ? '五维评估' : '5-Dimension Assessment' }}</div>
      <div class="flex flex-wrap gap-1">
        <span
          v-for="[name, level] in dims"
          :key="name"
          class="text-[10px] px-1.5 py-0.5 rounded font-medium"
          :class="dimColor[level] ?? 'bg-slate-700/40 text-slate-300'"
          :title="`${name}: ${level}`"
        >{{ name }}</span>
      </div>
    </div>

    <!-- Critic / Coherence verdict -->
    <div v-if="quality.critic_verdict || quality.coherence_verdict" class="mb-3 text-xs space-y-1">
      <div v-if="quality.critic_verdict" class="flex justify-between">
        <span class="text-slate-500">Critic</span>
        <span
          class="font-medium"
          :class="quality.critic_verdict?.includes('PASS') ? 'text-emerald-400' : 'text-amber-400'"
        >{{ quality.critic_verdict }}</span>
      </div>
      <div v-if="quality.coherence_verdict" class="flex justify-between">
        <span class="text-slate-500">Coherence</span>
        <span
          class="font-medium"
          :class="quality.coherence_verdict === 'COHERENT' ? 'text-emerald-400' : 'text-amber-400'"
        >{{ quality.coherence_verdict }}</span>
      </div>
    </div>

    <!-- Target venues -->
    <div v-if="quality.target_venues?.length" class="text-xs text-slate-500">
      <span>{{ lang.current === 'zh' ? '目标期刊' : 'Target venues' }}: </span>
      <span class="text-slate-300">{{ quality.target_venues.join(', ') }}</span>
    </div>
  </div>
  <div v-else class="text-xs text-slate-500 italic">
    {{ lang.current === 'zh' ? '暂无评估数据' : 'No evaluation data' }}
  </div>
</template>
