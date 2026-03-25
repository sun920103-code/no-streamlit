<template>
  <div class="fade-in">
    <div class="page-header">
      <h2>量化决策白盒</h2>
      <p class="subtitle">Black-Litterman 观点矩阵 · 宏观体制判断 · 压力测试</p>
    </div>

    <!-- BL Views -->
    <div class="card" style="margin-bottom: 28px;">
      <div class="card-title">Black-Litterman 观点矩阵</div>
      <div class="table-container" style="margin-top: 12px;">
        <table>
          <thead>
            <tr><th>资产类别</th><th>预期收益</th><th>置信度</th><th>来源</th></tr>
          </thead>
          <tbody>
            <tr v-for="v in blViews" :key="v.asset">
              <td>{{ v.asset }}</td>
              <td :style="{ color: v.expected_return > 0.05 ? 'var(--success)' : 'var(--text-primary)' }">
                {{ (v.expected_return * 100).toFixed(1) }}%
              </td>
              <td>
                <div style="display:flex;align-items:center;gap:8px;">
                  <div style="flex:1;height:6px;background:var(--bg-primary);border-radius:3px;">
                    <div :style="{ width: v.confidence * 100 + '%', height: '100%', background: 'var(--accent)', borderRadius: '3px' }"></div>
                  </div>
                  <span style="font-size:12px;color:var(--text-secondary);">{{ (v.confidence * 100).toFixed(0) }}%</span>
                </div>
              </td>
              <td style="font-size:12px;color:var(--text-muted);">AI + EDB Z-scores</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="grid-2">
      <!-- Macro Regime -->
      <div class="card">
        <div class="card-title">宏观经济体制</div>
        <div style="text-align:center;padding:20px 0;">
          <div style="font-size:48px;margin-bottom:8px;">🔄</div>
          <div class="card-value warning">复苏阶段</div>
          <p style="color:var(--text-secondary);font-size:13px;margin-top:8px;">
            PMI 重返荣枯线上方，信用脉冲回升
          </p>
        </div>
        <div class="table-container" style="margin-top: 12px;">
          <table>
            <thead><tr><th>指标</th><th>当前值</th></tr></thead>
            <tbody>
              <tr><td>PMI</td><td>50.2</td></tr>
              <tr><td>CPI 同比</td><td>0.8%</td></tr>
              <tr><td>M2 增速</td><td>7.1%</td></tr>
              <tr><td>信用脉冲</td><td>1.3</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Stress Test -->
      <div class="card">
        <div class="card-title">压力测试场景</div>
        <div class="table-container" style="margin-top: 12px;">
          <table>
            <thead><tr><th>场景</th><th>组合冲击</th><th>风险等级</th></tr></thead>
            <tbody>
              <tr v-for="s in stressTests" :key="s.name">
                <td>{{ s.name }}</td>
                <td :style="{ color: 'var(--danger)' }">{{ (s.impact * 100).toFixed(1) }}%</td>
                <td>
                  <span class="badge" :class="Math.abs(s.impact) > 0.015 ? 'badge-danger' : 'badge-warning'">
                    {{ Math.abs(s.impact) > 0.015 ? '高风险' : '中风险' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const blViews = ref([
  { asset: '股票多头', expected_return: 0.08, confidence: 0.6 },
  { asset: '纯债固收', expected_return: 0.035, confidence: 0.85 },
  { asset: '黄金商品', expected_return: 0.05, confidence: 0.5 },
  { asset: '固收增强', expected_return: 0.045, confidence: 0.7 },
  { asset: '量化对冲', expected_return: 0.04, confidence: 0.65 },
])

const stressTests = ref([
  { name: '2020 新冠冲击', impact: -0.018 },
  { name: '2022 债市调整', impact: -0.012 },
  { name: '利率上行 100bp', impact: -0.008 },
  { name: '股市暴跌 20%', impact: -0.011 },
])
</script>
