<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { fetchPaper, type PaperDetail } from '@/api'
import { useLangStore } from '@/stores/lang'
import { useT } from '@/i18n'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import TableOfContents from '@/components/TableOfContents.vue'
import PrerequisitesPanel from '@/components/PrerequisitesPanel.vue'
import RelatedPapersPanel from '@/components/RelatedPapersPanel.vue'
import QualityPanel from '@/components/QualityPanel.vue'
import ChatPanel from '@/components/ChatPanel.vue'
import LanguageToggle from '@/components/LanguageToggle.vue'

const props = defineProps<{ slug: string }>()
const route = useRoute()
const lang = useLangStore()
const t = useT()

const detail = ref<PaperDetail | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const chatOpen = ref(false)

async function load() {
  loading.value = true
  error.value = null
  try {
    detail.value = await fetchPaper(props.slug)
  } catch (e) {
    console.error(e)
    error.value = (e as Error).message || 'Failed to load paper'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await load()
  if (route.query.chat === '1') chatOpen.value = true
})

watch(() => props.slug, load)

const source = computed(() => {
  if (!detail.value) return ''
  const content = detail.value.content
  return content[lang.current] || content.en || content.zh || ''
})

const tocItems = computed(() => {
  const src = source.value
  const re = /^##\s+([^\n{]+?)\s*\{#([^}]+)\}/gm
  const items: Array<{ id: string; title: string }> = []
  let m: RegExpExecArray | null
  while ((m = re.exec(src)) !== null) {
    items.push({ title: m[1].trim(), id: m[2] })
  }
  return items
})
</script>

<template>
  <div v-if="loading" class="max-w-7xl mx-auto p-8 text-slate-400">{{ t('loading') }}</div>
  <div v-else-if="error" class="max-w-7xl mx-auto p-8">
    <div class="bg-rose-500/10 border border-rose-500/30 rounded-lg p-6 text-center">
      <p class="text-rose-400 mb-3">{{ lang.current === 'zh' ? '加载失败' : 'Failed to load' }}: {{ error }}</p>
      <p class="text-sm text-slate-400 mb-4">{{ lang.current === 'zh' ? '请确认后端已启动：' : 'Make sure the backend is running:' }} <code class="bg-slate-800 px-2 py-0.5 rounded">bash paper_visualizer/scripts/run_dev.sh</code></p>
      <button class="px-4 py-2 rounded bg-brand-500 hover:bg-brand-600 text-white text-sm" @click="load()">{{ lang.current === 'zh' ? '重试' : 'Retry' }}</button>
    </div>
  </div>
  <div v-else-if="detail" class="max-w-7xl mx-auto">
    <div class="flex items-center justify-between px-5 py-3 border-b border-slate-800 sticky top-[3.3rem] bg-slate-950/80 backdrop-blur z-20">
      <div class="flex items-center gap-3 min-w-0">
        <RouterLink to="/" class="text-slate-400 hover:text-slate-200 shrink-0">
          {{ t('backHome') }}
        </RouterLink>
        <h1 class="text-base md:text-lg font-semibold truncate">
          {{
            detail.meta.short_title[lang.current]
            || detail.meta.title[lang.current]
            || detail.meta.short_title.en
            || detail.meta.title.en
            || detail.meta.slug
          }}
        </h1>
        <span
          v-if="detail.meta.status"
          class="text-[11px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 uppercase shrink-0"
        >{{ detail.meta.status.replace(/_/g, ' ') }}</span>
      </div>
      <div class="flex items-center gap-3 shrink-0">
        <LanguageToggle />
        <button
          class="text-sm px-3 py-1.5 rounded bg-brand-500 hover:bg-brand-600 text-white"
          @click="chatOpen = !chatOpen"
        >💬 {{ t('askClaude') }} →</button>
      </div>
    </div>

    <div class="flex">
      <article class="flex-1 px-6 py-6 min-w-0">
        <MarkdownRenderer :source="source" />
      </article>
      <aside
        class="w-64 shrink-0 px-5 py-6 border-l border-slate-800 sticky top-[7.3rem] self-start max-h-[calc(100vh-7.3rem)] overflow-y-auto hidden md:block"
      >
        <div class="text-[11px] uppercase tracking-wider text-slate-500 mb-2">
          {{ t('tableOfContents') }}
        </div>
        <TableOfContents :items="tocItems" />

        <div class="text-[11px] uppercase tracking-wider text-slate-500 mt-6 mb-2">
          {{ t('prerequisites') }}
        </div>
        <PrerequisitesPanel :prereqs="detail.meta.prerequisites" />

        <div class="text-[11px] uppercase tracking-wider text-slate-500 mt-6 mb-2">
          {{ lang.current === 'zh' ? '质量评估' : 'Quality' }}
        </div>
        <QualityPanel :quality="detail.meta.quality" />

        <div class="text-[11px] uppercase tracking-wider text-slate-500 mt-6 mb-2">
          {{ t('relatedPapers') }}
        </div>
        <RelatedPapersPanel :related="detail.meta.related_papers.filter(r => r.slug !== slug)" />

        <div class="flex gap-2 mt-6">
          <a
            :href="`/content/${slug}/source.pdf`"
            target="_blank"
            class="text-xs px-3 py-1.5 rounded bg-slate-800 border border-slate-700 hover:bg-slate-700"
          >{{ t('openPdf') }}</a>
          <a
            :href="`/content/${slug}/source.tex`"
            target="_blank"
            class="text-xs px-3 py-1.5 rounded bg-slate-800 border border-slate-700 hover:bg-slate-700"
          >{{ t('openTex') }}</a>
        </div>
      </aside>
    </div>

    <ChatPanel
      v-if="chatOpen"
      :slug="slug"
      :meta="detail.meta"
      @close="chatOpen = false"
    />
  </div>
</template>
