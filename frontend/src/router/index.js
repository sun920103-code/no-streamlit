import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: () => import('../views/Landing.vue'),
  },
  {
    path: '/yc',
    name: 'YueCai',
    component: () => import('../views/YueCaiShell.vue'),
    children: [
      { path: '', redirect: '/yc/hrp' },
      { path: 'hrp', name: 'HrpConfig', component: () => import('../views/HrpConfig.vue') },
      { path: 'ai', name: 'AiResearch', component: () => import('../views/AiResearch.vue') },
      { path: 'backtest', name: 'Backtest', component: () => import('../views/Backtest.vue') },
      { path: 'whitebox', name: 'Whitebox', component: () => import('../views/WhiteboxView.vue') },
    ],
  },
  {
    path: '/diag',
    name: 'Diagnostics',
    component: () => import('../views/Diagnostics.vue'),
  },
  {
    path: '/smart',
    name: 'SmartSelection',
    component: () => import('../views/SmartSelectionManager.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
