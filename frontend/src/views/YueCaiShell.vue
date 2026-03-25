<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="section-label">核心控制</div>
      </div>

      <!-- 4 Navigation Buttons -->
      <button
        v-for="nav in navItems" :key="nav.path"
        class="nav-btn"
        :class="$route.path === nav.path ? 'active' : 'inactive'"
        @click="$router.push(nav.path)"
      >{{ nav.label }}</button>

      <!-- Parameters Section -->
      <div class="sidebar-section">
        <div class="section-label">参数</div>

        <div class="param-group">
          <label>配置资产规模 (万元)</label>
          <input type="number" v-model.number="params.capitalWan" min="1" step="100" />
        </div>

        <div class="param-group">
          <label>目标收益率 (%)</label>
          <input type="number" v-model.number="params.targetReturn" min="0" max="50" step="0.5" />
        </div>

        <div class="param-group">
          <label>年化波动率 (%)</label>
          <input type="number" v-model.number="params.targetVol" min="0" max="30" step="0.5" />
        </div>

        <div class="param-group">
          <label>最大回撤 (%)</label>
          <input type="number" v-model.number="params.maxDrawdown" min="0" max="30" step="0.5" />
        </div>

        <div class="param-group">
          <label>优化窗口</label>
          <select v-model="params.window">
            <option value="3y">近3年</option>
            <option value="5y">近5年</option>
            <option value="full">2015至今</option>
          </select>
        </div>
      </div>

      <!-- Back to Landing -->
      <button class="sidebar-back-btn" @click="$router.push('/')">
        🔙 返回大厅
      </button>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <!-- HUD Top Bar -->
      <div class="hud-bar">
        <div class="breadcrumb">
          <span>资产管理</span><span>/</span>
          <span>组合分析</span><span>/</span>
          <span class="current">HRP配置工作站</span>
        </div>
        <div style="display:flex;align-items:center;gap:16px;">
          <div class="status-badge">
            <span class="status-dot"></span>
            系统运行状态：稳定
          </div>
          <div class="session-time">
            <div class="label">会话时间</div>
            <div class="time">{{ currentTime }}</div>
          </div>
        </div>
      </div>

      <!-- Title Block -->
      <div class="page-content">
        <div class="page-title-block" style="margin-bottom:4px;">
          <img :src="logoSrc" alt="粤财信托" style="width: 120px; margin-bottom: 8px;" v-if="logoSrc" />
          <h1>粤财信托 · 资产配置智能助手</h1>
          <p class="subtitle">
            底层支撑：宏观因子精选池 + 多模型集成研报增强 + Black-Litterman 主客观融合 + HRP 均衡风控
          </p>
        </div>

        <!-- Router view for the 4 sub-views -->
        <router-view />

        <div class="footer">
          © 2026 粤财信托 · Powered by Antigravity
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const navItems = [
  { path: '/yc/hrp', label: 'HRP基础配置' },
  { path: '/yc/ai', label: 'AI 研判与战术调仓' },
  { path: '/yc/backtest', label: '业绩回测与归因' },
  { path: '/yc/whitebox', label: '量化决策白盒' },
]

const params = ref({
  capitalWan: 5000,
  targetReturn: 8.5,
  targetVol: 6.0,
  maxDrawdown: 5.0,
  window: '3y',
})

const currentTime = ref('')
const logoSrc = ref('')
let timer = null

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false,
  })
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>
