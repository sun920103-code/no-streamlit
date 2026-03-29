<template>
  <div class="zx-tactical-page">
    <!-- 页面标题 -->
    <div class="zx-page-header">
      <div class="zx-header-left">
        <span class="zx-accent-bar"></span>
        <div>
          <h1 class="zx-page-title">战术配置</h1>
          <p class="zx-page-sub">Tactical Adjustment · 基于稳健底仓进行战术偏移</p>
        </div>
      </div>
    </div>

    <!-- ═══ 前置依赖检查 ═══ -->
    <div v-if="!hasSteadyBase" class="zx-notice">
      ⚠️ 请先完成「宏观配置底仓」（页面一），获取稳健基准底仓后再进行战术配置。
      <button class="zx-notice-btn" @click="$router.push('/smart/macro')">前往配置底仓 →</button>
    </div>

    <!-- ═══ 操作面板 ═══ -->
    <div v-if="hasSteadyBase" class="zx-action-panel fade-in">
      <div class="zx-pipeline-cards">
        <!-- 管线 1: 新闻资讯 -->
        <div class="zx-pipeline-card" :class="{ active: selectedPipeline === 'news' }" @click="selectedPipeline = 'news'">
          <span class="zx-pipeline-icon">📰</span>
          <div>
            <div class="zx-pipeline-label">新闻资讯自动调仓</div>
            <div class="zx-pipeline-desc">通过 AI 搜索解析最新宏观/行业资讯，自动偏移</div>
          </div>
          <span class="zx-check" v-if="selectedPipeline === 'news'">✓</span>
        </div>

        <!-- 管线 2: 研报上传 -->
        <div class="zx-pipeline-card" :class="{ active: selectedPipeline === 'report' }" @click="selectedPipeline = 'report'">
          <span class="zx-pipeline-icon">📄</span>
          <div>
            <div class="zx-pipeline-label">专属研报上传调仓</div>
            <div class="zx-pipeline-desc">上传研究报告 PDF，AI 解析并提取因子偏移</div>
          </div>
          <span class="zx-check" v-if="selectedPipeline === 'report'">✓</span>
        </div>
      </div>

      <!-- 研报上传区 -->
      <div v-if="selectedPipeline === 'report'" class="zx-upload-area">
        <input type="file" ref="fileInput" accept=".pdf,.docx,.doc" @change="onFileSelect" />
        <div v-if="uploadedFile" class="zx-file-info">
          📎 {{ uploadedFile.name }} ({{ (uploadedFile.size / 1024).toFixed(1) }}KB)
        </div>
      </div>

      <!-- 执行按钮 -->
      <button class="zx-action-btn" :disabled="loading" @click="runTactical">
        <span v-if="loading" class="zx-spinner"></span>
        <span v-else>⚔️</span>
        {{ loading ? '正在调仓...' : '执行战术调仓' }}
      </button>
    </div>

    <!-- ═══ 3 组 KPI 对比 ═══ -->
    <div v-if="result" class="fade-in">
      <div class="zx-card" style="margin-bottom:24px;">
        <div class="zx-card-title">📊 KPI 对比（原底仓 vs 调仓后）</div>
        <div class="zx-kpi-comparison">
          <div v-for="(item, idx) in result.kpi_comparison" :key="idx" class="zx-kpi-column" :class="{ highlight: idx > 0 }">
            <div class="zx-kpi-col-title">{{ item.label }}</div>
            <div class="zx-kpi-row">
              <span class="zx-kpi-name">年化收益率</span>
              <span class="zx-kpi-val" :style="{ color: item.ann_return_pct > 0 ? '#DC2626' : '#16A34A' }">{{ item.ann_return_pct }}%</span>
            </div>
            <div class="zx-kpi-row">
              <span class="zx-kpi-name">年化波动率</span>
              <span class="zx-kpi-val">{{ item.ann_vol_pct }}%</span>
            </div>
            <div class="zx-kpi-row">
              <span class="zx-kpi-name">最大回撤</span>
              <span class="zx-kpi-val" style="color:#16A34A;">{{ item.max_drawdown_pct }}%</span>
            </div>
            <div class="zx-kpi-row">
              <span class="zx-kpi-name">夏普比率</span>
              <span class="zx-kpi-val">{{ item.sharpe }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ 调仓明细表 ═══ -->
      <div class="zx-card" style="margin-bottom:24px;">
        <div class="zx-card-title">📋 调仓明细 (增减偏移)</div>
        <div class="zx-rebalance-table-wrap">
          <table class="zx-rebalance-table">
            <thead>
              <tr>
                <th>基金代码</th>
                <th style="text-align:right;">原权重</th>
                <th style="text-align:right;">新权重</th>
                <th style="text-align:right;">偏移比例</th>
                <th style="text-align:right;">偏移金额</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in result.rebalance_detail.slice(0, 30)" :key="item.code">
                <td><span class="zx-code-mono">{{ item.code }}</span></td>
                <td style="text-align:right;">{{ item.old_weight_pct }}%</td>
                <td style="text-align:right;font-weight:700;">{{ item.new_weight_pct }}%</td>
                <td style="text-align:right;">
                  <span :class="item.delta_pct > 0 ? 'zx-up' : item.delta_pct < 0 ? 'zx-down' : ''">
                    {{ item.delta_pct > 0 ? '+' : '' }}{{ item.delta_pct }}%
                  </span>
                </td>
                <td style="text-align:right;font-family:'JetBrains Mono',monospace;">
                  <span :class="item.delta_amount > 0 ? 'zx-up' : item.delta_amount < 0 ? 'zx-down' : ''">
                    {{ item.delta_amount > 0 ? '+' : '' }}¥{{ Number(item.delta_amount).toLocaleString() }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ═══ MOE 投委会分析报告 ═══ -->
      <div class="zx-card fade-in">
        <div class="zx-card-title">🏛️ MoE 投委会分析报告</div>
        <div class="zx-moe-report" v-html="formatReport(result.moe_report)"></div>
        <div v-if="result.news_digest" class="zx-news-digest">
          <div class="zx-digest-label">📰 资讯摘要</div>
          <p>{{ result.news_digest }}</p>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!result && hasSteadyBase && !loading" class="zx-empty-state">
      <div class="zx-empty-icon">⚔️</div>
      <h2>等待战术调仓指令</h2>
      <p>选择调仓管线（新闻资讯 或 研报上传），点击执行按钮后系统将自动完成战术偏移计算。</p>
    </div>

    <!-- Error -->
    <div v-if="error" class="zx-error fade-in">❌ {{ error }}</div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useSmartStore } from '../../store/smartSelection'
import { zxTacticalAdjustment } from '../../api/smart'

const store = useSmartStore()
const loading = ref(false)
const error = ref(null)
const selectedPipeline = ref('news')
const uploadedFile = ref(null)
const fileInput = ref(null)

const hasSteadyBase = computed(() => {
  return store.zx_macroResult !== null && store.zx_macroResult.scenarios?.length > 0
})

const result = computed(() => store.zx_tacticalResult)

function onFileSelect(e) {
  uploadedFile.value = e.target.files[0] || null
}

function formatReport(text) {
  if (!text) return ''
  return text
    .replace(/\n/g, '<br />')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}

async function runTactical() {
  loading.value = true
  error.value = null
  try {
    const weights = store.zx_steadyWeights
    const res = await zxTacticalAdjustment({
      base_allocation: weights,
      capital: store.zx_capital,
      max_vol: store.zx_maxVol,
    })
    store.setTacticalResult(res.data)
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || '战术调仓失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.zx-tactical-page { max-width: 1400px; }

/* ─── Header ─── */
.zx-page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(196,198,205,0.15);
}
.zx-header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.zx-accent-bar {
  width: 4px; height: 36px;
  background: #001529;
  border-radius: 9999px;
}
.zx-page-title {
  font-size: 24px;
  font-weight: 800;
  color: #001529;
  margin: 0;
}
.zx-page-sub {
  font-size: 12px;
  color: #74777d;
  margin: 2px 0 0;
}

/* Notice */
.zx-notice {
  background: #FFF7ED;
  border: 1px solid #FDBA74;
  border-radius: 10px;
  padding: 20px 24px;
  color: #92400E;
  font-size: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.zx-notice-btn {
  padding: 8px 20px;
  background: #F97316;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.zx-notice-btn:hover { opacity: 0.85; }

/* ─── Action Panel ─── */
.zx-action-panel { margin-bottom: 28px; }
.zx-pipeline-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.zx-pipeline-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: #ffffff;
  border: 2px solid #e1e3e4;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}
.zx-pipeline-card:hover { border-color: #001529; background: #fafbfc; }
.zx-pipeline-card.active {
  border-color: #001529;
  background: rgba(0,21,41,0.02);
  box-shadow: 0 4px 14px rgba(0,21,41,0.08);
}
.zx-pipeline-icon { font-size: 24px; }
.zx-pipeline-label { font-weight: 700; font-size: 14px; color: #001529; }
.zx-pipeline-desc { font-size: 12px; color: #74777d; margin-top: 2px; }
.zx-check {
  position: absolute;
  top: 12px;
  right: 14px;
  background: #001529;
  color: #fff;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
}

.zx-upload-area {
  padding: 16px;
  background: #f8f9fa;
  border: 2px dashed #c4c6cd;
  border-radius: 8px;
  margin-bottom: 16px;
}
.zx-file-info {
  margin-top: 8px;
  font-size: 13px;
  color: #43474d;
}

.zx-action-btn {
  padding: 12px 28px;
  background: #001529;
  color: #ffffff;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 14px rgba(0,21,41,0.2);
  transition: all 0.15s;
}
.zx-action-btn:hover:not(:disabled) { opacity: 0.9; }
.zx-action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.zx-spinner {
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ─── Cards ─── */
.zx-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid rgba(196,198,205,0.12);
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
.zx-card-title {
  font-size: 14px;
  font-weight: 700;
  color: #001529;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(196,198,205,0.12);
}

/* KPI Comparison */
.zx-kpi-comparison {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}
.zx-kpi-column {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 16px;
  border: 1px solid #e1e3e4;
}
.zx-kpi-column.highlight {
  border: 2px solid #001529;
  background: rgba(0,21,41,0.02);
}
.zx-kpi-col-title {
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 12px;
  color: #001529;
}
.zx-kpi-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid rgba(196,198,205,0.1);
}
.zx-kpi-name { font-size: 12px; color: #74777d; }
.zx-kpi-val { font-size: 14px; font-weight: 700; }

/* Rebalance Table */
.zx-rebalance-table-wrap {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #f3f4f5;
  border-radius: 8px;
}
.zx-rebalance-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.zx-rebalance-table thead th {
  position: sticky;
  top: 0;
  background: #f8f9fa;
  padding: 10px 12px;
  font-weight: 600;
  border-bottom: 1px solid #e1e3e4;
  text-align: left;
}
.zx-rebalance-table tbody td {
  padding: 8px 12px;
  border-bottom: 1px solid #f8f9fa;
}
.zx-code-mono { font-family: 'JetBrains Mono', monospace; color: #43474d; }
.zx-up { color: #DC2626; font-weight: 600; }
.zx-down { color: #16A34A; font-weight: 600; }

/* MOE Report */
.zx-moe-report {
  font-size: 14px;
  line-height: 1.8;
  color: #191c1d;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 16px;
}
.zx-news-digest {
  background: #FFF7ED;
  border-left: 3px solid #F97316;
  padding: 12px 16px;
  border-radius: 0 8px 8px 0;
}
.zx-digest-label {
  font-size: 12px;
  font-weight: 700;
  color: #92400E;
  margin-bottom: 6px;
}
.zx-news-digest p {
  margin: 0;
  font-size: 13px;
  color: #78350F;
  line-height: 1.6;
}

/* ─── Empty State ─── */
.zx-empty-state {
  text-align: center;
  padding: 80px 40px;
  color: #74777d;
}
.zx-empty-icon { font-size: 64px; margin-bottom: 16px; }
.zx-empty-state h2 { font-size: 22px; font-weight: 700; color: #191c1d; margin-bottom: 8px; }
.zx-empty-state p { font-size: 14px; max-width: 480px; margin: 0 auto; line-height: 1.6; }

.zx-error {
  padding: 16px 20px;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 8px;
  color: #991B1B;
  font-size: 14px;
  margin-top: 16px;
}

.fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
</style>
