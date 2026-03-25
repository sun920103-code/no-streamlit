<template>
  <div class="fade-in">
    <div class="section-title">📊 HRP 基础配置</div>

    <!-- KPI Row -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-label">配置资产规模</div>
        <div class="kpi-value kpi-navy">{{ (capitalYi).toFixed(1) }} 亿</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">目标年化收益</div>
        <div class="kpi-value kpi-green">8.5%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">风险预算 (波动率)</div>
        <div class="kpi-value kpi-amber">6.0%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">最大回撤限制</div>
        <div class="kpi-value kpi-red">5.0%</div>
      </div>
    </div>

    <!-- Weight Distribution -->
    <div class="grid-2" style="margin-bottom: 24px;">
      <div class="card">
        <div class="card-title">HRP 权重分布</div>
        <div ref="pieChart" style="height: 360px;"></div>
      </div>
      <div class="card">
        <div class="card-title">风险贡献分析</div>
        <div ref="riskChart" style="height: 360px;"></div>
      </div>
    </div>

    <!-- Asset Table -->
    <div class="card" style="margin-bottom: 24px;">
      <div class="card-title">基金池权重明细</div>
      <table class="data-table">
        <thead>
          <tr>
            <th>资产类别</th>
            <th>代表基金</th>
            <th>HRP 权重</th>
            <th>风险贡献</th>
            <th>年化波动率</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in assets" :key="a.name">
            <td style="font-weight:600;">{{ a.name }}</td>
            <td style="color:var(--text-secondary);">{{ a.fund }}</td>
            <td>
              <div style="display:flex;align-items:center;gap:8px;">
                <div style="flex:1;height:6px;background:#F1F5F9;border-radius:3px;">
                  <div :style="{ width: a.weight + '%', height:'100%', background: a.weight > 15 ? '#1A2A40' : '#3182CE', borderRadius:'3px' }"></div>
                </div>
                <span style="font-weight:600;min-width:45px;text-align:right;">{{ a.weight.toFixed(1) }}%</span>
              </div>
            </td>
            <td>{{ a.riskContrib.toFixed(1) }}%</td>
            <td>{{ a.vol.toFixed(1) }}%</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 负债管理模式 -->
    <div class="expander">
      <div class="expander-header" @click="showDebt = !showDebt">
        🎯 负债管理模式 (目标导向配置)
        <span>{{ showDebt ? '▲' : '▼' }}</span>
      </div>
      <div class="expander-body" v-show="showDebt">
        <p style="color:var(--text-secondary);font-size:13px;margin-bottom:16px;">
          基于刚性开支与目标盈利，生成负债驱动型(LDI)专项配置方案。
        </p>
        <div class="grid-4" style="margin-bottom:16px;">
          <div class="param-group" style="color:var(--text-primary);">
            <label style="color:var(--text-secondary);">年度刚性开支 (万)</label>
            <input type="number" value="150" style="background:#F8FAFC;color:var(--text-primary);border:1px solid #E2E8F0;" />
          </div>
          <div class="param-group" style="color:var(--text-primary);">
            <label style="color:var(--text-secondary);">年度目标盈利 (万)</label>
            <input type="number" value="250" style="background:#F8FAFC;color:var(--text-primary);border:1px solid #E2E8F0;" />
          </div>
          <div class="param-group" style="color:var(--text-primary);">
            <label style="color:var(--text-secondary);">投资金额 (万)</label>
            <input type="number" value="10000" style="background:#F8FAFC;color:var(--text-primary);border:1px solid #E2E8F0;" />
          </div>
          <div class="param-group" style="color:var(--text-primary);">
            <label style="color:var(--text-secondary);">最大容忍波动 (%)</label>
            <input type="number" value="10" style="background:#F8FAFC;color:var(--text-primary);border:1px solid #E2E8F0;" />
          </div>
        </div>
        <button class="btn btn-primary btn-block">运行目标诊断</button>
      </div>
    </div>

    <!-- 研报上传 + 引擎启动 -->
    <div class="divider"></div>
    <div class="card">
      <div class="card-title">📄 步骤二：上传最新宏观研报 (可选但强烈建议)</div>
      <p style="color:var(--text-secondary);font-size:13px;margin-bottom:16px;">
        多模型集成虚拟投委会将基于此研判当前经济周期、核心因子风向并生成定制调仓基准。
      </p>
      <div style="border:2px dashed #E2E8F0;border-radius:8px;padding:24px;text-align:center;margin-bottom:16px;">
        <p style="color:var(--text-muted);">📎 拖拽上传研报 (PDF/TXT) 或点击选择文件</p>
        <input type="file" accept=".pdf,.txt" multiple style="margin-top:8px;" />
      </div>
      <button class="btn btn-primary btn-block">
        🧠 启动多模型集成研报解析与 AI 智能配置引擎
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

const showDebt = ref(false)
const capitalYi = ref(0.5)

const assets = ref([
  { name: '货币现金', fund: '天弘余额宝', weight: 15.2, riskContrib: 2.1, vol: 0.8 },
  { name: '纯债固收', fund: '富国信用债', weight: 24.8, riskContrib: 8.3, vol: 2.1 },
  { name: '混合债券', fund: '易方达稳健', weight: 14.6, riskContrib: 9.7, vol: 3.5 },
  { name: '短债理财', fund: '招商短债', weight: 10.3, riskContrib: 3.2, vol: 1.2 },
  { name: '固收增强', fund: '广发聚利', weight: 15.1, riskContrib: 18.5, vol: 4.8 },
  { name: '量化对冲', fund: '景顺量化', weight: 9.5, riskContrib: 22.4, vol: 8.2 },
  { name: '股票多头', fund: '兴全合润', weight: 5.8, riskContrib: 28.6, vol: 18.5 },
  { name: '黄金商品', fund: '华安黄金', weight: 4.7, riskContrib: 7.2, vol: 12.3 },
])

const pieChart = ref(null)
const riskChart = ref(null)

const colors = ['#1A2A40','#2C5282','#3182CE','#63B3ED','#C8A97E','#F59E0B','#C41E3A','#10B981']

onMounted(() => {
  initPieChart()
  initRiskChart()
})

function initPieChart() {
  const chart = echarts.init(pieChart.value)
  chart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie', radius: ['40%', '68%'], center: ['50%', '50%'],
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      label: { fontSize: 12, color: '#6B7B8D' },
      data: assets.value.map((a, i) => ({ name: a.name, value: a.weight, itemStyle: { color: colors[i] } })),
    }],
  })
  window.addEventListener('resize', () => chart.resize())
}

function initRiskChart() {
  const chart = echarts.init(riskChart.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: assets.value.map(a => a.name), axisLabel: { fontSize: 11, color: '#6B7B8D', rotate: 30 }, axisLine: { lineStyle: { color: '#E2E8F0' } } },
    yAxis: { type: 'value', name: '风险贡献 (%)', axisLabel: { fontSize: 11, color: '#6B7B8D' }, splitLine: { lineStyle: { color: '#F1F5F9' } } },
    grid: { left: 60, right: 20, top: 40, bottom: 60 },
    series: [{
      type: 'bar', data: assets.value.map((a, i) => ({ value: a.riskContrib, itemStyle: { color: colors[i] } })),
      barWidth: 28, itemStyle: { borderRadius: [4,4,0,0] },
    }],
  })
  window.addEventListener('resize', () => chart.resize())
}
</script>
