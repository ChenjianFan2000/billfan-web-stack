<script setup lang="ts">
import Header from '@/components/Header.vue'
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <Header />
    <main class="flex-1"><RouterView /></main>
  </div>
</template>
