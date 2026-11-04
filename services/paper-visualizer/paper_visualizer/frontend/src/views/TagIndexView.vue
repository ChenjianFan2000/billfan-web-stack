<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import PaperCard from '@/components/PaperCard.vue'
import { usePapersStore } from '@/stores/papers'
import { useLangStore } from '@/stores/lang'

const props = defineProps<{ kind: 'domain' | 'tool'; tag?: string }>()
const papers = usePapersStore()
const lang = useLangStore()

onMounted(() => papers.load())

const bucket = computed(() =>
  props.kind === 'domain' ? papers.tags.domains : papers.tags.math_tools,
)

const selectedPapers = computed(() => {
  if (!props.tag) return []
  const slugs = bucket.value[props.tag]?.papers ?? []
  return papers.papers.filter((p) => slugs.includes(p.slug))
})
</script>

<template>
  <div class="max-w-7xl mx-auto p-6">
    <h2 class="text-2xl font-semibold mb-4">
      {{ props.kind === 'domain' ? (lang.current === 'zh' ? '按领域浏览' : 'By domain') : (lang.current === 'zh' ? '按数学工具浏览' : 'By math tool') }}
    </h2>
    <div class="flex flex-wrap gap-2 mb-6">
      <RouterLink
        v-for="[key, entry] in Object.entries(bucket)"
        :key="key"
        :to="`/tags/${props.kind}/${key}`"
        class="px-3 py-1.5 text-sm rounded border transition"
        :class="props.tag === key ? 'bg-brand-500 text-white border-brand-500' : 'bg-slate-800 border-slate-700 hover:border-brand-500'"
      >
        {{ entry.label[lang.current] || key.replace(/_/g, ' ') }}
        <span class="text-xs opacity-70 ml-1">{{ entry.papers.length }}</span>
      </RouterLink>
    </div>
    <div
      v-if="props.tag && selectedPapers.length"
      class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"
    >
      <PaperCard v-for="p in selectedPapers" :key="p.slug" :paper="p" />
    </div>
    <div v-else-if="props.tag" class="text-slate-500 italic">—</div>
  </div>
</template>
