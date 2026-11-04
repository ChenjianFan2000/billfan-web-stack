<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import katex from 'katex'

const props = defineProps<{ tex: string; display?: boolean }>()
const host = ref<HTMLElement | null>(null)

function render() {
  if (!host.value) return
  try {
    katex.render(props.tex, host.value, {
      displayMode: !!props.display,
      throwOnError: false,
      output: 'html',
    })
  } catch {
    host.value.textContent = props.tex
  }
}

onMounted(render)
watch(() => props.tex, render)
</script>

<template>
  <span v-if="!display" ref="host" class="inline-block align-middle" />
  <div v-else ref="host" class="my-4 overflow-x-auto" />
</template>
