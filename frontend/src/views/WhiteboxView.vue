<template>
  <div class="fade-in">
    <div class="section-title">🔬 量化决策白盒</div>

    <!-- 宏观因子 EDB 数据 -->
    <div class="card" style="margin-bottom:24px;">
      <div class="card-title">📡 宏观经济因子 (EDB Z-Score)</div>
      <table class="data-table">
        <thead>
          <tr><th>因子名称</th><th>最新值</th><th>Z-Score</th><th>方向</th><th>信号</th></tr>
        </thead>
        <tbody>
          <tr v-for="f in macroFactors" :key="f.name">
            <td style="font-weight:600;">{{ f.name }}</td>
            <td>{{ f.value }}</td>
            <td :style="{ color: f.zscore > 0 ? 'var(--kpi-green)' : 'var(--kpi-red)', fontWeight: 600 }">
              {{ f.zscore > 0 ? '+' : '' }}{{ f.zscore.toFixed(2) }}
            </td>
            <td>{{ f.direction }}</td>
            <td>
              <span class="badge" :class="f.signal === '看多' ? 'badge-green' : f.signal === '看空' ? 'badge-red' : 'badge-amber'">
                {{ f.signal }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- BL 观点矩阵 -->
    <div class="card" style="margin-bottom:24px;">
      <div class="card-title">🎯 Black-Litterman 观点矩阵</div>
      <table class="data-table">
        <thead>
          <tr><th>资产类别</th><th>预期超额收益</th><th>置信度</th><th>数据源</th></tr>
        </thead>
        <tbody>
          <tr v-for="v in blViews" :key="v.asset">
            <td style="font-weight:600;">{{ v.asset }}</td>
            <td :style="{ color: v.view > 0 ? 'var(--kpi-green)' : 'var(--kpi-red)', fontWeight:600 }">
              {{ v.view > 0 ? '+' : '' }}{{ (v.view * 100).toFixed(2) }}%
            </td>
            <td>
              <div style="display:flex;align-items:center;gap:8px;">
                <div style="width:80px;height:6px;background:#F1F5F9;border-radius:3px;">
                  <div :style="{ width: v.confidence*100 + '%', height:'100%', background: '#3182CE', borderRadius:'3px' }"></div>
                </div>
                <span style="font-size:12px;color:var(--text-secondary);">{{ (v.confidence*100).toFixed(0) }}%</span>
              </div>
            </td>
            <td style="font-size:12px;color:var(--text-muted);">{{ v.source }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 因子→资产 敏感度矩阵 -->
    <div class="card" style="margin-bottom:24px;">
      <div class="card-title">🧮 6×8 宏观因子敏感度矩阵</div>
      <p style="color:var(--text-secondary);font-size:13px;margin-bottom:12px;">
        通过矩阵乘法综合考虑所有因子对所有资产的交叉影响 (例: 市场情绪看空→降低所有权益; 海外看空→降低QDII但不影响纯债)
      </p>
      <div ref="heatmapChart" style="height:320px;"></div>
    </div>

    <!-- 融合过程 -->
    <div class="card">
      <div class="card-title">🔗 BL 融合过程</div>
      <div style="padding:16px 0;">
        <div v-for="step in fusionSteps" :key="step.id" style="display:flex;align-items:flex-start;gap:12px;margin-bottom:16px;">
          <div style="width:28px;height:28px;border-radius:50%;background:var(--sovereign-accent);color:#FFF;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0;">
            {{ step.id }}
          </div>
          <div>
            <div style="font-weight:600;margin-bottom:2px;">{{ step.title }}</div>
            <div style="color:var(--text-secondary);font-size:13px;">{{ step.desc }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

const macroFactors = ref([
  { name: 'PMI 制造业', value: '50.2', zscore: 0.35, direction: '↑', signal: '看多' },
  { name: 'CPI 同比', value: '0.8%', zscore: -0.82, direction: '↓', signal: '中性' },
  { name: 'M2 增速', value: '7.1%', zscore: 0.15, direction: '→', signal: '中性' },
  { name: '信用脉冲', value: '1.3', zscore: 0.68, direction: '↑', signal: '看多' },
  { name: '10Y 国债收益率', value: '2.28%', zscore: -0.45, direction: '↓', signal: '中性' },
  { name: '美元指数 (DXY)', value: '104.2', zscore: 0.52, direction: '↑', signal: '看空' },
])

const blViews = ref([
  { asset: '股票多头', view: 0.025, confidence: 0.60, source: 'AI NLP + EDB Z-scores' },
  { asset: '纯债固收', view: 0.008, confidence: 0.85, source: 'AI NLP + EDB Z-scores' },
  { asset: '黄金商品', view: 0.015, confidence: 0.50, source: 'AI NLP + 因子映射' },
  { asset: '固收增强', view: 0.012, confidence: 0.70, source: 'AI NLP + EDB Z-scores' },
  { asset: '量化对冲', view: -0.005, confidence: 0.55, source: 'AI NLP + 因子映射' },
  { asset: '混合债券', view: 0.006, confidence: 0.65, source: 'AI NLP + EDB Z-scores' },
])

const fusionSteps = ref([
  { id: 1, title: '市场均衡收益 (隐含先验)', desc: '从 HRP 权重反推均衡收益向量 π = δΣw' },
  { id: 2, title: 'AI 观点矩阵 (P, Q, Ω)', desc: '将新闻因子得分和研报分析结果映射为 BL 观点' },
  { id: 3, title: 'Bayesian 后验融合', desc: 'E[r] = [(τΣ)⁻¹ + P\'Ω⁻¹P]⁻¹ [(τΣ)⁻¹π + P\'Ω⁻¹Q]' },
  { id: 4, title: '约束优化', desc: '在流动性覆盖、单一产品上限、最大回撤等约束下求最优权重' },
  { id: 5, title: '风控叠加', desc: 'NLP 情绪倾斜 ≤ ±10%, 波动率目标约束, EGARCH 风险调节' },
])

const heatmapChart = ref(null)

onMounted(() => {
  initHeatmap()
})

function initHeatmap() {
  const chart = echarts.init(heatmapChart.value)
  const factors = ['市场情绪', '利率', '信用', '通胀', '海外', '流动性']
  const assets = ['货币现金','纯债固收','混合债券','短债理财','固收增强','量化对冲','股票多头','黄金商品']
  const data = []
  for (let i = 0; i < factors.length; i++) {
    for (let j = 0; j < assets.length; j++) {
      const v = (Math.random() - 0.5) * 2
      data.push([j, i, +v.toFixed(2)])
    }
  }
  chart.setOption({
    tooltip: { position: 'top', formatter: p => `${factors[p.value[1]]} → ${assets[p.value[0]]}: ${p.value[2]}` },
    xAxis: { type: 'category', data: assets, axisLabel: { fontSize: 11, color: '#6B7B8D', rotate: 30 }, splitArea: { show: true } },
    yAxis: { type: 'category', data: factors, axisLabel: { fontSize: 11, color: '#6B7B8D' }, splitArea: { show: true } },
    grid: { left: 80, right: 20, top: 10, bottom: 60 },
    visualMap: { min: -1, max: 1, calculable: true, orient: 'horizontal', left: 'center', bottom: 0, inRange: { color: ['#C41E3A','#FDF2F2','#FFFFFF','#F0FDF4','#10B981'] } },
    series: [{ type: 'heatmap', data: data, label: { show: true, fontSize: 10 }, emphasis: { itemStyle: { shadowBlur: 10 } } }],
  })
  window.addEventListener('resize', () => chart.resize())
}
</script>
