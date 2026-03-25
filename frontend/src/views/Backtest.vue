<template>
  <div class="fade-in">
    <div class="section-title">📈 业绩回测与归因</div>

    <!-- KPI Delta Cards -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-label">底仓年化收益</div>
        <div class="kpi-value kpi-navy">5.83%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">AI 增强年化收益</div>
        <div class="kpi-value kpi-green">6.72%</div>
        <div class="kpi-delta" style="color:var(--kpi-green);">▲ +0.89%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">底仓最大回撤</div>
        <div class="kpi-value kpi-amber">-3.21%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">AI 增强最大回撤</div>
        <div class="kpi-value kpi-green">-2.87%</div>
        <div class="kpi-delta" style="color:var(--kpi-green);">▲ 改善 0.34%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">底仓夏普比率</div>
        <div class="kpi-value kpi-navy">1.28</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">AI 增强夏普比率</div>
        <div class="kpi-value kpi-green">1.56</div>
        <div class="kpi-delta" style="color:var(--kpi-green);">▲ +0.28</div>
      </div>
    </div>

    <!-- NAV Curve -->
    <div class="card" style="margin-bottom:24px;">
      <div class="card-title">净值走势对比 (底仓 vs AI 增强 vs 基准)</div>
      <div ref="navChart" style="height:380px;"></div>
    </div>

    <!-- Drawdown -->
    <div class="card" style="margin-bottom:24px;">
      <div class="card-title">回撤分析</div>
      <div ref="ddChart" style="height:260px;"></div>
    </div>

    <!-- Stress Test -->
    <div class="card" style="margin-bottom:24px;">
      <div class="card-title">🔥 压力测试 (时空穿越回测)</div>
      <table class="data-table">
        <thead>
          <tr><th>压力场景</th><th>时间区间</th><th>组合冲击</th><th>基准冲击</th><th>风险等级</th></tr>
        </thead>
        <tbody>
          <tr v-for="s in stressScenarios" :key="s.name">
            <td style="font-weight:600;">{{ s.name }}</td>
            <td style="color:var(--text-secondary);">{{ s.period }}</td>
            <td :style="{ color: 'var(--kpi-red)', fontWeight: 600 }">{{ (s.portfolioImpact * 100).toFixed(1) }}%</td>
            <td style="color:var(--text-secondary);">{{ (s.benchmarkImpact * 100).toFixed(1) }}%</td>
            <td>
              <span class="badge" :class="Math.abs(s.portfolioImpact) > 0.03 ? 'badge-red' : 'badge-amber'">
                {{ Math.abs(s.portfolioImpact) > 0.03 ? '高风险' : '中风险' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- EGARCH -->
    <div class="card">
      <div class="card-title">📉 EGARCH 波动率建模</div>
      <div class="grid-3">
        <div class="kpi-card">
          <div class="kpi-label">预测日波动率</div>
          <div class="kpi-value kpi-amber">0.42%</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">杠杆效应 (非对称性)</div>
          <div class="kpi-value kpi-navy">-0.15</div>
          <div class="kpi-delta" style="color:var(--kpi-amber);">存在轻微负向不对称</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">年化波动率 (预测)</div>
          <div class="kpi-value kpi-green">5.82%</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

const navChart = ref(null)
const ddChart = ref(null)

const stressScenarios = ref([
  { name: '2020 新冠冲击', period: '2020.01-2020.03', portfolioImpact: -0.018, benchmarkImpact: -0.12 },
  { name: '2022 债市调整', period: '2022.11-2022.12', portfolioImpact: -0.012, benchmarkImpact: -0.025 },
  { name: '利率上行 100bp', period: '模拟场景', portfolioImpact: -0.008, benchmarkImpact: -0.015 },
  { name: '股市暴跌 20%', period: '模拟场景', portfolioImpact: -0.011, benchmarkImpact: -0.20 },
  { name: '2015 股灾', period: '2015.06-2015.09', portfolioImpact: -0.035, benchmarkImpact: -0.45 },
])

onMounted(() => {
  initNavChart()
  initDrawdownChart()
})

function initNavChart() {
  const chart = echarts.init(navChart.value)
  const dates = []
  const navBase = []; const navAI = []; const navBench = []
  let base = 1.0, ai = 1.0, bench = 1.0
  for (let i = 0; i < 252; i++) {
    const d = new Date(2025, 2, 1); d.setDate(d.getDate() + i)
    dates.push(`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`)
    base += (Math.random() - 0.47) * 0.002; navBase.push(+base.toFixed(4))
    ai += (Math.random() - 0.46) * 0.0022; navAI.push(+ai.toFixed(4))
    bench += (Math.random() - 0.48) * 0.003; navBench.push(+bench.toFixed(4))
  }
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['HRP 底仓', 'AI 增强', '基准 (偏债混合)'], top: 0 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 10, color: '#94A3B8' }, axisLine: { lineStyle: { color: '#E2E8F0' } } },
    yAxis: { type: 'value', min: 'dataMin', axisLabel: { fontSize: 10, color: '#94A3B8' }, splitLine: { lineStyle: { color: '#F1F5F9' } } },
    grid: { left: 55, right: 20, top: 35, bottom: 30 },
    series: [
      { name: 'HRP 底仓', type: 'line', data: navBase, smooth: true, showSymbol: false, lineStyle: { color: '#1A2A40', width: 2 } },
      { name: 'AI 增强', type: 'line', data: navAI, smooth: true, showSymbol: false, lineStyle: { color: '#3182CE', width: 2 } },
      { name: '基准 (偏债混合)', type: 'line', data: navBench, smooth: true, showSymbol: false, lineStyle: { color: '#CBD5E0', width: 1.5, type: 'dashed' } },
    ],
  })
  window.addEventListener('resize', () => chart.resize())
}

function initDrawdownChart() {
  const chart = echarts.init(ddChart.value)
  const dates = []; const dd = []
  for (let i = 0; i < 252; i++) {
    const d = new Date(2025, 2, 1); d.setDate(d.getDate() + i)
    dates.push(`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`)
    dd.push(-(Math.random() * 0.03 * Math.sin(i / 30) + Math.random() * 0.005).toFixed(4))
  }
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 10, color: '#94A3B8' }, axisLine: { lineStyle: { color: '#E2E8F0' } } },
    yAxis: { type: 'value', axisLabel: { fontSize: 10, color: '#94A3B8', formatter: v => (v*100).toFixed(1) + '%' }, splitLine: { lineStyle: { color: '#F1F5F9' } } },
    grid: { left: 55, right: 20, top: 10, bottom: 30 },
    series: [{
      type: 'line', data: dd, smooth: true, showSymbol: false,
      lineStyle: { color: '#C41E3A', width: 1.5 },
      areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(196,30,58,0.15)'},{offset:1,color:'rgba(196,30,58,0)'}]) },
    }],
  })
  window.addEventListener('resize', () => chart.resize())
}
</script>
