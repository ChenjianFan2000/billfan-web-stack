<script setup lang="ts">
import { useLangStore } from '@/stores/lang'

const lang = useLangStore()
</script>

<template>
  <div class="inline-flex bg-slate-800 rounded-lg p-0.5 border border-slate-700">
    <button
      class="px-4 py-1.5 text-sm font-semibold rounded-md transition"
      :class="lang.current === 'zh' ? 'bg-brand-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'"
      @click="lang.set('zh')"
    >中文</button>
    <button
      class="px-4 py-1.5 text-sm font-semibold rounded-md transition"
      :class="lang.current === 'en' ? 'bg-brand-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'"
      @click="lang.set('en')"
    >English</button>
  </div>
</template>
