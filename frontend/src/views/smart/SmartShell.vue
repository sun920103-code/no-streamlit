<template>
  <div class="zx-app-layout">
    <!-- 左侧 Sidebar -->
    <aside class="flex flex-col h-full w-[320px] shrink-0 bg-surface p-6 sm:p-8 gap-10 overflow-y-auto custom-scrollbar border-r border-[#dbe4e7] z-10">
      <!-- Header: Smart Selection Brand Anchor -->
      <header class="flex items-center gap-4">
        <div class="flex flex-col">
          <h1 class="text-2xl font-bold tracking-tight text-on-surface">粤财智选</h1>
        </div>
      </header>

      <!-- Global Configuration Section -->
      <section class="space-y-6">
        <h2 class="text-[12px] font-bold tracking-[0.15em] uppercase text-on-surface-variant/50">全局配置参数</h2>
        <div class="space-y-5">
          <!-- Amount -->
          <div class="group">
            <label class="block text-[11px] font-semibold text-on-surface-variant mb-2 tracking-wide">配置资金 (万元)</label>
            <div class="relative flex items-center">
              <span class="absolute left-4 text-on-surface-variant/50 text-sm">¥</span>
              <input type="number" v-model.number="store.zx_capital" min="1" step="100" class="w-full bg-surface-container border-none rounded-xl pl-10 pr-4 py-3 text-on-surface font-bold focus:ring-2 focus:ring-primary/20 focus:bg-surface-container-lowest transition-all text-base"/>
            </div>
          </div>
          <!-- Exp. Return & Max Volatility -->
          <div class="grid grid-cols-2 gap-4">
            <div class="group">
              <label class="block text-[11px] font-semibold text-on-surface-variant mb-2 tracking-wide">预期收益 (%)</label>
              <input type="number" v-model.number="store.zx_targetReturn" min="0" max="50" step="0.5" class="w-full bg-surface-container border-none rounded-xl px-4 py-3 text-on-surface font-bold focus:ring-2 focus:ring-primary/20 focus:bg-surface-container-lowest transition-all text-base"/>
            </div>
            <div class="group">
              <label class="block text-[11px] font-semibold text-on-surface-variant mb-2 tracking-wide">年化波动率 (%)</label>
              <input type="number" v-model.number="store.zx_maxVol" min="0" max="30" step="0.5" class="w-full bg-surface-container border-none rounded-xl px-4 py-3 text-on-surface font-bold focus:ring-2 focus:ring-primary/20 focus:bg-surface-container-lowest transition-all text-base"/>
            </div>
          </div>
          <small class="block text-[11px] text-[#9f403d] mt-1 font-medium">核心风控红线：超限将触发降级配置</small>
          
          <!-- Holding Period -->
          <div class="group">
            <label class="block text-[11px] font-semibold text-on-surface-variant mb-2 tracking-wide">预计持仓时间</label>
            <div class="relative flex items-center">
              <select v-model="store.zx_period" class="w-full bg-surface-container border-none rounded-xl px-4 py-3 text-on-surface font-bold focus:ring-2 focus:ring-primary/20 focus:bg-surface-container-lowest transition-all text-base appearance-none cursor-pointer" style="background-image: none;">
                <option value="半年">半年</option>
                <option value="1年">1年</option>
                <option value="3年">3年</option>
              </select>
              <span class="material-symbols-outlined absolute right-4 text-on-surface-variant/40 pointer-events-none">expand_more</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Navigation Section -->
      <nav class="flex flex-col gap-2">
        <h2 class="text-[12px] font-bold tracking-[0.15em] uppercase text-on-surface-variant/50 mb-2">功能模块</h2>
        <a v-for="nav in navItems" :key="nav.path"
           href="#"
           @click.prevent="$router.push(nav.path)"
           :class="[
             'flex items-center gap-4 px-6 py-5 rounded-xl transition-all font-bold text-lg group',
             $route.path === nav.path
               ? 'active:scale-[0.98] duration-200 bg-slate-900 text-white shadow-lg'
               : 'text-on-surface-variant/90 hover:text-on-surface hover:bg-surface-container-low'
           ]"
        >
          <span class="material-symbols-outlined !text-[24px]" 
                :style="$route.path === nav.path ? 'font-variation-settings: \'FILL\' 1;' : ''"
                :class="$route.path === nav.path ? 'text-white' : ''">
            {{ nav.iconName }}
          </span>
          <div class="flex flex-col">
             <span>{{ nav.label }}</span>
             <span class="text-[11px] font-normal" :class="$route.path === nav.path ? 'text-white/70' : 'text-on-surface-variant/50'">{{ nav.en }}</span>
          </div>
        </a>
      </nav>

      <!-- Footer Section -->
      <footer class="mt-auto pt-6 space-y-6 border-t border-outline-variant/10 relative">
        <!-- Core Fund Pool CTA -->
        <button class="w-full group flex items-center justify-between px-5 py-4 bg-surface-container hover:bg-surface-container-high rounded-xl transition-all active:scale-[0.98]" @click="drawerOpen = !drawerOpen">
          <div class="flex items-center gap-4">
            <span class="material-symbols-outlined text-primary">account_balance_wallet</span>
            <span class="text-base font-bold text-on-surface">核心精选基金池</span>
          </div>
          <div class="flex items-center gap-1">
            <span class="px-2.5 py-1 bg-primary/10 text-primary text-[11px] font-extrabold rounded-full">{{ store.zx_fundPool.length }}只</span>
            <span class="material-symbols-outlined text-on-surface-variant/50 !text-sm transition-transform" :class="drawerOpen ? 'rotate-180' : ''">arrow_drop_down</span>
          </div>
        </button>

        <!-- Pool Dropdown (Simple overlay) -->
        <div v-show="drawerOpen" class="absolute bottom-[90px] left-0 right-0 bg-white border border-surface-variant shadow-xl rounded-xl p-3 max-h-[300px] overflow-y-auto z-50">
          <div v-if="store.zx_fundPool.length === 0" class="text-center text-on-surface-variant/50 text-xs py-4">加载中...</div>
          <template v-for="(funds, cat) in store.zx_fundPoolGrouped" :key="cat">
            <div class="mb-3">
              <div class="text-[10px] font-bold text-on-primary-fixed bg-primary-fixed/30 px-2 py-1 rounded inline-block mb-1">{{ cat }} ({{ funds.length }})</div>
              <div v-for="fund in funds" :key="fund.code" class="flex justify-between px-2 py-1 text-[11px]">
                <span class="text-on-surface">{{ fund.name }}</span>
                <span class="text-on-surface-variant/60 font-mono">{{ fund.code }}</span>
              </div>
            </div>
          </template>
        </div>

        <!-- Return -->
        <a class="flex items-center justify-center gap-3 px-6 py-4 font-bold rounded-xl active:scale-[0.98] duration-200 transition-all border border-slate-200 text-slate-600 hover:bg-slate-50 text-base group w-full" href="#" @click.prevent="$router.push('/')">
          <span class="material-symbols-outlined !text-[20px] text-primary">keyboard_backspace</span>
          <span class="text-base font-bold text-primary">返回大厅</span>
        </a>
      </footer>
    </aside>

    <!-- 右侧主内容区 -->
    <main class="zx-main">
      <!-- 顶部状态栏 -->
      <div class="zx-topbar">
        <div class="zx-breadcrumb">
          <span>智选平台</span><span class="zx-sep">/</span>
          <span class="zx-current">{{ currentPageLabel }}</span>
        </div>
        <div class="zx-topbar-right">
          <div class="zx-status-dot"></div>
          <span class="zx-status-text">系统正常</span>
          <span class="zx-time">{{ currentTime }}</span>
        </div>
      </div>

      <!-- 子页面路由出口 -->
      <div class="zx-page-content">
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </div>

      <div class="zx-footer">
        © 2026 粤财信托 · 智选资产配置平台 · Powered by Antigravity
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSmartStore } from '../../store/smartSelection'
import { zxGetFundPool } from '../../api/smart'

const route = useRoute()
const store = useSmartStore()

const drawerOpen = ref(false)
const currentTime = ref('')
let timer = null

const navItems = [
  { path: '/smart/macro', label: '宏观配置底仓', en: 'Macro Allocation', iconName: 'analytics' },
  { path: '/smart/tactical', label: '战术配置', en: 'Tactical Adjustment', iconName: 'tune' },
  { path: '/smart/backtest', label: '业绩回测', en: 'Backtest', iconName: 'history' },
]

const currentPageLabel = computed(() => {
  const item = navItems.find(n => route.path === n.path)
  return item ? item.label : '智选平台'
})

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  })
}

async function loadFundPool() {
  if (store.zx_fundPool.length > 0) return
  try {
    const res = await zxGetFundPool()
    if (res.data?.pool) {
      store.setFundPool(res.data.pool, res.data.grouped || {})
    }
  } catch (e) {
    console.error('基金池加载失败:', e)
  }
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
  loadFundPool()
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

.zx-app-layout {
  display: flex;
  height: 100vh;
  background: #f8f9fa;
  font-family: 'Manrope', 'Inter', sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* ═══ Sidebar ═══ */
.zx-sidebar {
  width: 300px;
  background: #ffffff;
  border-right: 1px solid rgba(196,198,205,0.15);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  box-shadow: 4px 0 20px rgba(0,0,0,0.02);
  padding: 24px 20px;
}

.zx-sidebar-header {
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(196,198,205,0.15);
}
.zx-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}
.zx-brand-icon {
  font-size: 28px;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #001529, #003366);
  border-radius: 12px;
}
.zx-brand-title {
  font-size: 16px;
  font-weight: 800;
  color: #001529;
  margin: 0;
  letter-spacing: -0.3px;
}
.zx-brand-sub {
  font-size: 10px;
  color: #74777d;
  margin: 2px 0 0;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-family: 'Inter', sans-serif;
}

/* ─── Parameters ─── */
.zx-params {
  margin-bottom: 24px;
}
.zx-section-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #74777d;
  font-weight: 700;
  margin-bottom: 14px;
  font-family: 'Inter', sans-serif;
}
.zx-param-group {
  margin-bottom: 16px;
}
.zx-param-group label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #43474d;
  margin-bottom: 6px;
}
.zx-input-wrap {
  display: flex;
  align-items: center;
  background: #f8f9fa;
  border: 1px solid #e1e3e4;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s;
}
.zx-input-wrap:focus-within {
  border-color: #001529;
  box-shadow: 0 0 0 3px rgba(0,21,41,0.06);
}
.zx-prefix, .zx-suffix {
  padding: 0 10px;
  color: #74777d;
  font-weight: 600;
  font-size: 13px;
  background: #f3f4f5;
}
.zx-prefix { border-right: 1px solid #e1e3e4; }
.zx-suffix { border-left: 1px solid #e1e3e4; }
.zx-param-group input,
.zx-param-group select {
  flex: 1;
  border: none;
  padding: 9px 12px;
  background: transparent;
  outline: none;
  font-size: 13px;
  font-weight: 600;
  color: #191c1d;
  width: 100%;
  font-family: 'Manrope', sans-serif;
}
.zx-param-group select {
  width: 100%;
  border: 1px solid #e1e3e4;
  border-radius: 8px;
  background: #f8f9fa;
  cursor: pointer;
}
.zx-hint-danger {
  display: block;
  font-size: 10px;
  color: #ba1a1a;
  margin-top: 4px;
  font-weight: 500;
}

/* ─── Navigation ─── */
.zx-nav {
  margin-bottom: 20px;
}
.zx-nav-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  cursor: pointer;
  transition: all 0.15s;
  margin-bottom: 6px;
  text-align: left;
  font-family: 'Manrope', sans-serif;
}
.zx-nav-btn:hover {
  background: #f3f4f5;
}
.zx-nav-btn.active {
  background: #001529;
  color: #ffffff;
  border-color: #001529;
  box-shadow: 0 4px 14px rgba(0,21,41,0.15);
}
.zx-nav-icon {
  font-size: 18px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: rgba(0,21,41,0.05);
  flex-shrink: 0;
}
.zx-nav-btn.active .zx-nav-icon {
  background: rgba(255,255,255,0.15);
}
.zx-nav-text { flex: 1; }
.zx-nav-label {
  font-size: 13px;
  font-weight: 700;
  color: #191c1d;
}
.zx-nav-en {
  font-size: 10px;
  color: #74777d;
  font-family: 'Inter', sans-serif;
}
.zx-nav-btn.active .zx-nav-label,
.zx-nav-btn.active .zx-nav-en {
  color: #ffffff;
}
.zx-nav-arrow {
  color: #c4c6cd;
  font-size: 18px;
  font-weight: 300;
}
.zx-nav-btn.active .zx-nav-arrow {
  color: rgba(255,255,255,0.5);
}

/* ─── Fund Pool Drawer ─── */
.zx-fund-pool {
  margin-top: auto;
  margin-bottom: 16px;
}
.zx-drawer-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #f3f4f5;
  border: 1px solid #e1e3e4;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: #191c1d;
  transition: all 0.15s;
  font-family: 'Manrope', sans-serif;
}
.zx-drawer-toggle:hover { background: #e7e8e9; }
.zx-badge {
  margin-left: auto;
  background: #001529;
  color: #fff;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 700;
}
.zx-arrow {
  font-size: 10px;
  transition: transform 0.2s;
  color: #74777d;
}
.zx-arrow.open { transform: rotate(180deg); }
.zx-drawer-content {
  margin-top: 8px;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e1e3e4;
  border-radius: 8px;
  background: #fafbfc;
  padding: 8px;
}
.zx-pool-cat { margin-bottom: 8px; }
.zx-pool-cat-title {
  font-size: 11px;
  font-weight: 700;
  color: #001529;
  padding: 4px 8px;
  background: rgba(0,21,41,0.04);
  border-radius: 4px;
  margin-bottom: 4px;
}
.zx-pool-item {
  display: flex;
  justify-content: space-between;
  padding: 3px 8px;
  font-size: 11px;
}
.zx-pool-name { color: #43474d; }
.zx-pool-code { color: #94a3b8; font-family: 'JetBrains Mono', monospace; font-size: 10px; }
.zx-empty { text-align: center; color: #94a3b8; font-size: 12px; padding: 16px; }

/* ─── Back Button ─── */
.zx-back-btn {
  width: 100%;
  padding: 10px;
  background: transparent;
  border: 1px dashed #c4c6cd;
  border-radius: 8px;
  color: #74777d;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  font-family: 'Manrope', sans-serif;
}
.zx-back-btn:hover {
  background: #f3f4f5;
  color: #191c1d;
  border-color: #74777d;
}

/* ═══ Main Content ═══ */
.zx-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.zx-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 32px;
  background: #ffffff;
  border-bottom: 1px solid rgba(196,198,205,0.1);
  flex-shrink: 0;
}
.zx-breadcrumb {
  font-size: 13px;
  color: #74777d;
  display: flex;
  align-items: center;
  gap: 6px;
}
.zx-sep { color: #c4c6cd; }
.zx-current { font-weight: 700; color: #001529; }
.zx-topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
}
.zx-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10B981;
  animation: pulse 2s ease-in-out infinite;
}
.zx-status-text { color: #43474d; }
.zx-time { color: #94a3b8; font-family: 'JetBrains Mono', monospace; font-size: 11px; }

.zx-page-content {
  flex: 1;
  overflow-y: auto;
  padding: 28px 32px;
}

.zx-footer {
  text-align: center;
  padding: 12px;
  font-size: 11px;
  color: #94a3b8;
  border-top: 1px solid rgba(196,198,205,0.1);
  background: #ffffff;
  flex-shrink: 0;
}

@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:.4;} }
</style>

