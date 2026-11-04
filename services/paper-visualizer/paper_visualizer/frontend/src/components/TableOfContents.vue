<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

interface TocItem {
  id: string
  title: string
}

const props = defineProps<{ items: TocItem[] }>()
const active = ref<string>('')

let observer: IntersectionObserver | null = null

function attach() {
  observer?.disconnect()
  if (!props.items.length) return
  observer = new IntersectionObserver(
    (entries) => {
      const vis = entries.filter((e) => e.isIntersecting)
      if (vis.length) active.value = (vis[0].target as HTMLElement).id
    },
    { rootMargin: '-120px 0px -60% 0px' },
  )
  for (const item of props.items) {
    const el = document.getElementById(item.id)
    if (el) observer.observe(el)
  }
}

onMounted(attach)
watch(() => props.items, () => setTimeout(attach, 0))
onBeforeUnmount(() => observer?.disconnect())
</script>

<template>
  <nav class="text-sm">
    <a
      v-for="item in items"
      :key="item.id"
      :href="`#${item.id}`"
      class="block py-1 transition"
      :class="active === item.id ? 'text-brand-500 font-semibold' : 'text-slate-400 hover:text-slate-200'"
    >{{ item.title }}</a>
  </nav>
</template>
