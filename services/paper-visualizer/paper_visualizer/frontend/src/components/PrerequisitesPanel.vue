<script setup lang="ts">
import type { Prerequisite } from '@/api'

defineProps<{ prereqs: Prerequisite[] }>()

const levelColor: Record<string, string> = {
  basic: 'bg-emerald-500/20 text-emerald-400',
  intermediate: 'bg-brand-500/20 text-brand-500',
  advanced: 'bg-amber-500/20 text-amber-400',
}
</script>

<template>
  <div v-if="prereqs && prereqs.length" class="flex flex-wrap gap-1.5">
    <span
      v-for="p in prereqs"
      :key="p.topic_id"
      :title="p.why"
      class="text-[11px] px-2 py-0.5 rounded font-medium cursor-help"
      :class="levelColor[p.level] ?? 'bg-slate-700/40 text-slate-300'"
    >{{ p.topic_id.replace(/_/g, ' ') }}</span>
  </div>
  <div v-else class="text-xs text-slate-500 italic">—</div>
</template>
