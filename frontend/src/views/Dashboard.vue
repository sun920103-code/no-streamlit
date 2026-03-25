<template>
  <div class="fade-in">
    <div class="page-header">
      <h2>投资仪表盘</h2>
      <p class="subtitle">广东省属信托自有资金 FOF 系统 · 实时概览</p>
    </div>

    <!-- KPI Cards -->
    <div class="grid-4" style="margin-bottom: 28px;">
      <div class="card">
        <div class="card-title">总资金规模</div>
        <div class="card-value accent">44 亿</div>
      </div>
      <div class="card">
        <div class="card-title">目标年化收益</div>
        <div class="card-value success">5.9%</div>
      </div>
      <div class="card">
        <div class="card-title">当前回撤</div>
        <div class="card-value" :class="drawdownClass">{{ drawdown }}</div>
      </div>
      <div class="card">
        <div class="card-title">宏观体制</div>
        <div class="card-value warning">{{ regime }}</div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="grid-2" style="margin-bottom: 28px;">
      <div class="card">
        <div class="card-title">资产配置分布</div>
        <div ref="pieChart" style="height: 320px;"></div>
      </div>
      <div class="card">
        <div class="card-title">组合净值走势</div>
        <div ref="lineChart" style="height: 320px;"></div>
      </div>
    </div>

    <!-- Asset Table -->
    <div class="card">
      <div class="card-title">资产类别权重</div>
      <div class="table-container" style="margin-top: 12px;">
        <table>
          <thead>
            <tr>
              <th>资产类别</th>
              <th>目标权重</th>
              <th>当前权重</th>
              <th>偏离度</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="asset in assets" :key="asset.name">
              <td>{{ asset.name }}</td>
              <td>{{ asset.target }}%</td>
              <td>{{ asset.current }}%</td>
              <td :style="{ color: Math.abs(asset.deviation) > 2 ? 'var(--warning)' : 'var(--text-secondary)' }">
                {{ asset.deviation > 0 ? '+' : '' }}{{ asset.deviation }}%
              </td>
              <td>
                <span class="badge" :class="asset.status === '正常' ? 'badge-success' : 'badge-warning'">
                  {{ asset.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

const drawdown = ref('-0.8%')
const drawdownClass = ref('success')
const regime = ref('复苏')

const assets = ref([
  { name: '货币现金',  target: 15, current: 14.8, deviation: -0.2, status: '正常' },
  { name: '纯债固收',  target: 25, current: 24.2, deviation: -0.8, status: '正常' },
  { name: '混合债券',  target: 15, current: 15.6, deviation: +0.6, status: '正常' },
  { name: '短债理财',  target: 10, current: 10.1, deviation: +0.1, status: '正常' },
  { name: '固收增强',  target: 15, current: 16.3, deviation: +1.3, status: '正常' },
  { name: '量化对冲',  target: 10, current: 9.2,  deviation: -0.8, status: '正常' },
  { name: '股票多头',  target: 5,  current: 4.5,  deviation: -0.5, status: '正常' },
  { name: '黄金商品',  target: 5,  current: 5.3,  deviation: +0.3, status: '正常' },
])

const pieChart = ref(null)
const lineChart = ref(null)

onMounted(() => {
  initPieChart()
  initLineChart()
})

function initPieChart() {
  const chart = echarts.init(pieChart.value)
  chart.setOption({
    tooltip: { trigger: 'item', backgroundColor: '#1e2235', borderColor: '#333', textStyle: { color: '#e8eaed' } },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['50%', '55%'],
      itemStyle: { borderRadius: 6, borderColor: '#0f1119', borderWidth: 2 },
      label: { color: '#8b8fa3', fontSize: 12 },
      data: assets.value.map((a, i) => ({
        name: a.name,
        value: a.current,
        itemStyle: { color: ['#6384ff','#a855f7','#34d399','#fbbf24','#f87171','#38bdf8','#fb923c','#c084fc'][i] },
      })),
    }],
  })
  window.addEventListener('resize', () => chart.resize())
}

function initLineChart() {
  const chart = echarts.init(lineChart.value)
  // 模拟净值数据
  const dates = []
  const navData = []
  let nav = 1.0
  for (let i = 0; i < 120; i++) {
    const d = new Date(2025, 6, 1)
    d.setDate(d.getDate() + i)
    dates.push(`${d.getMonth()+1}/${d.getDate()}`)
    nav += (Math.random() - 0.48) * 0.003
    navData.push(Number(nav.toFixed(4)))
  }
  chart.setOption({
    tooltip: { trigger: 'axis', backgroundColor: '#1e2235', borderColor: '#333', textStyle: { color: '#e8eaed' } },
    xAxis: { type: 'category', data: dates, axisLine: { lineStyle: { color: '#333' } }, axisLabel: { color: '#5a5e72', fontSize: 11 } },
    yAxis: { type: 'value', min: 'dataMin', axisLine: { show: false }, splitLine: { lineStyle: { color: '#1e2235' } }, axisLabel: { color: '#5a5e72', fontSize: 11 } },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    series: [{
      type: 'line',
      data: navData,
      smooth: true,
      showSymbol: false,
      lineStyle: { color: '#6384ff', width: 2 },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(99,132,255,0.25)' },
        { offset: 1, color: 'rgba(99,132,255,0)' },
      ]) },
    }],
  })
  window.addEventListener('resize', () => chart.resize())
}
</script>
