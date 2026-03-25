<template>
  <div class="fade-in">
    <div class="page-header">
      <h2>资产配置</h2>
      <p class="subtitle">组合再平衡 · HRP / Risk Parity / Black-Litterman</p>
    </div>

    <div class="grid-2" style="margin-bottom: 28px;">
      <div class="card">
        <div class="card-title">风险偏好</div>
        <div style="display: flex; gap: 12px; margin-top: 8px;">
          <button
            v-for="level in ['conservative', 'moderate', 'aggressive']"
            :key="level"
            class="btn"
            :class="riskLevel === level ? 'btn-primary' : 'btn-outline'"
            @click="riskLevel = level"
          >
            {{ labelMap[level] }}
          </button>
        </div>
      </div>
      <div class="card">
        <div class="card-title">操作</div>
        <div style="display: flex; gap: 12px; margin-top: 8px;">
          <button class="btn btn-primary pulse-glow" @click="handleRebalance">
            ⚡ 触发再平衡
          </button>
          <button class="btn btn-outline">
            📥 导出配置
          </button>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">约束参数</div>
      <div class="table-container" style="margin-top: 12px;">
        <table>
          <thead>
            <tr><th>参数</th><th>当前值</th><th>说明</th></tr>
          </thead>
          <tbody>
            <tr><td>流动性覆盖率底线</td><td>15%</td><td>T+0/T+1 资产最低占比</td></tr>
            <tr><td>单一产品投资上限</td><td>20%</td><td>单一资管产品占比上限</td></tr>
            <tr><td>最大回撤预警线</td><td>2%</td><td>系统强制停损阈值</td></tr>
            <tr><td>ERC 单资产权重区间</td><td>2% ~ 40%</td><td>Risk Parity 约束</td></tr>
            <tr><td>NLP 动量最大偏离</td><td>±10%</td><td>AI 情绪因子倾斜上限</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const riskLevel = ref('moderate')
const labelMap = {
  conservative: '🛡️ 保守型',
  moderate: '⚖️ 稳健型',
  aggressive: '🚀 进取型',
}

function handleRebalance() {
  alert('再平衡任务已提交 (Phase 2 对接 Celery)')
}
</script>
