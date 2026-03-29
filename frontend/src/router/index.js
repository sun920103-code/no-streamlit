import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: () => import('../views/Landing.vue'),
  },
  {
    path: '/yc',

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
  // ═══ 智选平台 — 独立 Shell + 三页面流水线 ═══
  {
    path: '/smart',

    component: () => import('../views/smart/SmartShell.vue'),
    children: [
      { path: '', redirect: '/smart/macro' },
      { path: 'macro', name: 'SmartMacro', component: () => import('../views/smart/SmartMacro.vue') },
      { path: 'tactical', name: 'SmartTactical', component: () => import('../views/smart/SmartTactical.vue') },
      { path: 'backtest', name: 'SmartBacktest', component: () => import('../views/smart/SmartBacktest.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
