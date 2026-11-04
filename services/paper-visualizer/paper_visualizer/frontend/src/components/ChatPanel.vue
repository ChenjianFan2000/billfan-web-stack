<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { PaperMeta } from '@/api'
import { useChatStore } from '@/stores/chat'
import { useChat } from '@/composables/useChat'
import { useLangStore } from '@/stores/lang'
import { useT } from '@/i18n'

const props = defineProps<{ slug: string; meta: PaperMeta }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const lang = useLangStore()
const t = useT()
const store = useChatStore()
const { pending, error, send } = useChat(props.slug)

const input = ref('')
const scroller = ref<HTMLElement | null>(null)

const messages = computed(() => store.get(props.slug))

const presets = computed(() => {
  const thm = props.meta.main_theorems[0]
  const id = thm?.id ?? ''
  const labelZh = thm?.label?.zh || id || '主定理'
  const labelEn = thm?.label?.en || id || 'the main theorem'
  if (lang.current === 'zh') {
    return [
      `💡 用大白话解释 ${labelZh}`,
      '🔑 证明中最难的一步是哪一步？',
      '🔗 这篇和本项目其他哪篇论文关联最强？',
    ]
  }
  return [
    `💡 Explain ${labelEn} in plain English`,
    '🔑 What is the hardest step in the proof?',
    '🔗 Which other paper in the project is most closely related?',
  ]
})

async function submit(text: string) {
  if (!text.trim() || pending.value) return
  input.value = ''
  await send(text, lang.current)
  await nextTick()
  scroller.value?.scrollTo({ top: scroller.value.scrollHeight })
}

watch(
  messages,
  async () => {
    await nextTick()
    scroller.value?.scrollTo({ top: scroller.value.scrollHeight })
  },
  { deep: true },
)
</script>

<template>
  <div class="fixed inset-0 z-40 flex">
    <div class="flex-1 bg-slate-950/60" @click="emit('close')"></div>
    <aside class="w-full sm:w-[420px] max-w-full border-l-2 border-brand-500 bg-slate-900 flex flex-col">
      <div class="flex items-center justify-between px-5 py-3 border-b border-slate-800">
        <strong class="flex items-center gap-2">💬 {{ t('chatHeader') }}</strong>
        <div class="flex gap-2 items-center">
          <button
            class="text-xs text-slate-400 hover:text-slate-200"
            @click="store.clear(slug)"
          >{{ t('clearChat') }}</button>
          <button
            class="text-2xl leading-none text-slate-400 hover:text-slate-200 px-2"
            @click="emit('close')"
          >×</button>
        </div>
      </div>

      <div class="px-5 py-3 border-b border-slate-800">
        <div class="text-[11px] uppercase tracking-wider text-slate-500 mb-2">
          {{ t('quickQuestions') }}
        </div>
        <div class="flex flex-col gap-1.5">
          <button
            v-for="(p, i) in presets"
            :key="i"
            class="text-left text-xs px-3 py-1.5 rounded bg-brand-500/10 hover:bg-brand-500/20 border border-brand-500/20 text-slate-200"
            :disabled="pending"
            @click="submit(p)"
          >{{ p }}</button>
        </div>
      </div>

      <div
        ref="scroller"
        class="flex-1 overflow-y-auto px-5 py-3 space-y-3"
      >
        <div v-if="messages.length === 0" class="text-sm text-slate-500 italic pt-10 text-center">
          {{ lang.current === 'zh' ? '向 Claude 提问这篇论文的任何内容。' : 'Ask Claude anything about this paper.' }}
        </div>
        <div
          v-for="(m, i) in messages"
          :key="i"
          class="rounded-lg px-4 py-2 text-sm leading-relaxed whitespace-pre-wrap"
          :class="m.role === 'user' ? 'bg-slate-800 text-slate-200' : 'bg-brand-500/10 border border-brand-500/20 text-slate-200'"
        >
          <span class="block text-[11px] uppercase tracking-wider text-slate-500 mb-1">
            {{ m.role === 'user' ? t('you') : 'Claude' }}
          </span>
          <span v-if="m.content">{{ m.content }}</span>
          <span v-else class="italic text-slate-500">…</span>
        </div>
        <div v-if="error" class="text-sm text-rose-400 px-4 py-2">{{ error }}</div>
      </div>

      <form
        class="flex gap-2 px-5 py-3 border-t border-slate-800"
        @submit.prevent="submit(input)"
      >
        <input
          v-model="input"
          :placeholder="t('inputPlaceholder')"
          class="flex-1 px-3 py-2 text-sm rounded bg-slate-800 border border-slate-700 focus:outline-none focus:border-brand-500 placeholder-slate-500"
          :disabled="pending"
        />
        <button
          type="submit"
          class="px-4 py-2 text-sm rounded bg-brand-500 hover:bg-brand-600 text-white disabled:opacity-50"
          :disabled="pending || !input.trim()"
        >{{ t('send') }}</button>
      </form>
    </aside>
  </div>
</template>
