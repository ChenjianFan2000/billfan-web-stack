<script setup lang="ts">
import { RouterLink } from 'vue-router'
import LanguageToggle from './LanguageToggle.vue'
import { useT } from '@/i18n'
import { usePapersStore } from '@/stores/papers'

const t = useT()
const papers = usePapersStore()
</script>

<template>
  <header class="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-30">
    <div class="max-w-7xl mx-auto px-5 py-3 flex items-center justify-between gap-4">
      <RouterLink to="/" class="flex items-center gap-2 font-semibold">
        <span class="text-xl">📘</span>
        <span>{{ t('brand') }}</span>
        <span class="text-slate-500 text-xs ml-2 hidden md:inline">MATHPROVER</span>
      </RouterLink>
      <div class="flex items-center gap-3">
        <input
          v-model="papers.search"
          :placeholder="t('searchPlaceholder')"
          class="px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-sm w-48 md:w-64 focus:outline-none focus:border-brand-500 placeholder-slate-500"
        />
        <LanguageToggle />
        <RouterLink
          to="/about"
          class="text-sm text-slate-400 hover:text-slate-200 hidden sm:inline"
        >{{ t('about') }}</RouterLink>
      </div>
    </div>
  </header>
</template>
