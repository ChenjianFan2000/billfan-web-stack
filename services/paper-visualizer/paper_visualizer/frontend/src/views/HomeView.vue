<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PaperCard from '@/components/PaperCard.vue'
import FilterSidebar from '@/components/FilterSidebar.vue'
import { usePapersStore } from '@/stores/papers'
import { useLangStore } from '@/stores/lang'
import { useT } from '@/i18n'

const papers = usePapersStore()
const lang = useLangStore()
const t = useT()
const error = ref<string | null>(null)

async function loadPapers() {
  error.value = null
  try {
    await papers.load()
  } catch (e) {
    error.value = (e as Error).message || 'Failed to connect'
  }
}

onMounted(loadPapers)
</script>

<template>
  <div class="max-w-7xl mx-auto flex">
    <FilterSidebar />
    <section class="flex-1 p-5">
      <div v-if="error" class="py-10">
        <div class="bg-rose-500/10 border border-rose-500/30 rounded-lg p-6 text-center max-w-lg mx-auto">
          <p class="text-rose-400 mb-3">{{ lang.current === 'zh' ? '无法连接后端' : 'Cannot connect to backend' }}</p>
          <p class="text-sm text-slate-400 mb-4">{{ lang.current === 'zh' ? '请在终端运行：' : 'Run in terminal:' }} <code class="bg-slate-800 px-2 py-0.5 rounded">bash paper_visualizer/scripts/run_dev.sh</code></p>
          <button class="px-4 py-2 rounded bg-brand-500 hover:bg-brand-600 text-white text-sm" @click="loadPapers()">{{ lang.current === 'zh' ? '重试' : 'Retry' }}</button>
        </div>
      </div>
      <div v-else-if="!papers.loaded" class="text-slate-400 py-10 text-center">{{ t('loading') }}</div>
      <div
        v-else-if="papers.filtered.length === 0"
        class="text-slate-400 py-10 text-center"
      >{{ t('noResults') }}</div>
      <div
        v-else
        class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"
      >
        <PaperCard v-for="p in papers.filtered" :key="p.slug" :paper="p" />
      </div>
    </section>
  </div>
</template>
