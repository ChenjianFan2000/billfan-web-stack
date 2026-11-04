<script setup lang="ts">
import { RouterLink } from 'vue-router'
import type { RelatedPaper } from '@/api'

defineProps<{ related: RelatedPaper[] }>()
</script>

<template>
  <div v-if="related && related.length" class="flex flex-col gap-1.5">
    <RouterLink
      v-for="r in related"
      :key="r.slug"
      :to="`/papers/${r.slug}`"
      class="text-sm px-3 py-2 rounded bg-slate-800/60 hover:bg-slate-800 border border-slate-700 block"
    >
      <span class="text-slate-200">→ {{ r.slug }}</span>
      <span class="block text-[11px] text-slate-500 mt-0.5">{{ r.note }}</span>
    </RouterLink>
  </div>
  <div v-else class="text-xs text-slate-500 italic">—</div>
</template>
