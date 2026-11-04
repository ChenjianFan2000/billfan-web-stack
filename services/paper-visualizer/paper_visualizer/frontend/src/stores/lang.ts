import { defineStore } from 'pinia'

export type Lang = 'zh' | 'en'

export const useLangStore = defineStore('lang', {
  state: () => ({
    current: ((typeof localStorage !== 'undefined' && localStorage.getItem('lang')) as Lang) || 'zh',
  }),
  actions: {
    set(lang: Lang) {
      this.current = lang
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('lang', lang)
      }
    },
  },
})
