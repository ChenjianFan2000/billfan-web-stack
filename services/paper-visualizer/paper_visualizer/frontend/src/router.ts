import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
  {
    path: '/papers/:slug',
    name: 'paper',
    component: () => import('@/views/PaperDetailView.vue'),
    props: true,
  },
  {
    path: '/tags/:kind/:tag?',
    name: 'tags',
    component: () => import('@/views/TagIndexView.vue'),
    props: true,
  },
  { path: '/about', name: 'about', component: () => import('@/views/AboutView.vue') },
]

export default createRouter({ history: createWebHistory(), routes })
