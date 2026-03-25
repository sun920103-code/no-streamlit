<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-icon">F</div>
        <div>
          <h1>FOF 量化平台</h1>
          <div class="version">v2.0 · FastAPI</div>
        </div>
      </div>

      <nav>
        <div class="nav-section">
          <div class="nav-section-title">概览</div>
          <router-link to="/" class="nav-link" active-class="active">
            <span class="icon">📊</span> 投资仪表盘
          </router-link>
        </div>

        <div class="nav-section">
          <div class="nav-section-title">决策引擎</div>
          <router-link to="/portfolio" class="nav-link" active-class="active">
            <span class="icon">⚖️</span> 资产配置
          </router-link>
          <router-link to="/whitebox" class="nav-link" active-class="active">
            <span class="icon">🔬</span> 量化白盒
          </router-link>
        </div>

        <div class="nav-section">
          <div class="nav-section-title">输出</div>
          <router-link to="/report" class="nav-link" active-class="active">
            <span class="icon">📄</span> 报告中心
          </router-link>
        </div>
      </nav>

      <div style="flex:1"></div>
      <div class="nav-link" style="color: var(--text-muted); font-size: 12px;">
        <span class="icon">⚡</span> 系统运行中
        <span class="badge badge-success" style="margin-left:auto;">● 在线</span>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
// App shell — 侧边栏 + 路由视图
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
