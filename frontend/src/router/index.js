import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
  },
  {
    path: '/portfolio',
    name: 'Portfolio',
    component: () => import('../views/Portfolio.vue'),
  },
  {
    path: '/whitebox',
    name: 'Whitebox',
    component: () => import('../views/Whitebox.vue'),
  },
  {
    path: '/report',
    name: 'Report',
    component: () => import('../views/Report.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
