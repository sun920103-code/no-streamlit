<template>
  <div class="zx-macro-page">
    <!-- 页面标题 -->
    <div class="zx-page-header">
      <div class="zx-header-left">
        <span class="zx-accent-bar"></span>
        <div>
          <h1 class="zx-page-title">宏观配置底仓</h1>
          <p class="zx-page-sub">Macro-Quadrant Base Allocation · EDB → 象限定位 → 配置方案生成</p>
        </div>
      </div>
      <button class="zx-action-btn" :disabled="loading" @click="runMacroAllocation">
        <span v-if="loading" class="zx-spinner"></span>
        <span v-else>🚀</span>
        {{ loading ? '正在计算...' : '一键获取 EDB + 宏观象限底仓' }}
      </button>
    </div>

    <!-- ═══ EDB + 象限信息 ═══ -->
    <div v-if="result" class="zx-info-row fade-in">
      <!-- EDB 宏观引擎 -->
      <div class="zx-card zx-card-edb">
        <div class="zx-card-title">📡 宏观特征引擎 (EDB)</div>
        <div class="zx-metric">
          <span class="zx-label">市场状态</span>
          <span class="zx-value zx-highlight">{{ result.edb_data.market_state }}</span>
        </div>
        <div class="zx-metric">
          <span class="zx-label">综合得分</span>
          <span class="zx-value">{{ result.edb_data.composite_score }}</span>
        </div>
        <div class="zx-sub-metrics">
          <div>宏观: {{ result.edb_data.macro_total }}</div>
          <div>估值: {{ result.edb_data.valuation_total }}</div>
          <div>风险: {{ result.edb_data.risk_total }}</div>
        </div>
      </div>

      <!-- 宏观象限定位 -->
      <div class="zx-card zx-card-quadrant">
        <div class="zx-card-title">🧭 宏观象限定位</div>
        <div class="zx-quadrant-header">
          <div class="zx-quadrant-icon" :style="{ background: qColors[result.quadrant.current]?.bg || '#f3f4f5' }">
            {{ qColors[result.quadrant.current]?.icon || '🧭' }}
          </div>
          <div>
            <div class="zx-quadrant-label">{{ result.quadrant.label }}</div>
            <div class="zx-quadrant-desc">{{ result.quadrant.description }}</div>
          </div>
        </div>
        <div class="zx-asset-signals">
          <div class="zx-signal-good">
            <div class="zx-signal-title">利好</div>
            <div class="zx-signal-value">{{ (result.quadrant.best_assets || []).join(', ') }}</div>
          </div>
          <div class="zx-signal-bad">
            <div class="zx-signal-title">承压</div>
            <div class="zx-signal-value">{{ (result.quadrant.worst_assets || []).join(', ') }}</div>
          </div>
        </div>
        <div class="zx-markov">
          Markov: <b>{{ result.quadrant.markov_regime }}</b>
          ({{ ((result.quadrant.markov_confidence || 0) * 100).toFixed(0) }}%)
        </div>
      </div>

      <!-- 情景类型提示 -->
      <div class="zx-card zx-card-scenario-type">
        <div class="zx-card-title">📋 配置模式</div>
        <div class="zx-scenario-badge" :class="result.scenario_type === 'A' ? 'badge-a' : 'badge-b'">
          情景 {{ result.scenario_type }}
        </div>
        <p class="zx-scenario-explain" v-if="result.scenario_type === 'A'">
          波动率约束可满足目标收益，已生成 <b>3 套配置方案</b>（进取/稳健/防守）。
        </p>
        <p class="zx-scenario-explain" v-else>
          波动率无法覆盖目标收益，已降级为 <b>1 套稳健配置</b>，以波动率为绝对锚点。
        </p>
      </div>
    </div>

    <!-- ═══ 因子传导链条 ═══ -->
    <div v-if="result && result.transmission_chain && result.transmission_chain.length" class="zx-card fade-in" style="margin-bottom:24px;">
      <div class="zx-card-title">🎯 因子传导链条 (底仓生成依据)</div>
      <div class="zx-chain-row">
        <div v-for="item in result.transmission_chain" :key="item.factor"
          class="zx-chain-item"
          :style="{ background: item.score > 0 ? '#FEF2F2' : '#F0FDF4', border: '1px solid ' + (item.score > 0 ? '#FECACA' : '#BBF7D0') }">
          <div class="zx-chain-factor">{{ item.factor }}</div>
          <div class="zx-chain-score" :style="{ color: item.score > 0 ? '#DC2626' : '#16A34A' }">
            {{ item.score > 0 ? '+' : '' }}{{ item.score }}
          </div>
          <div class="zx-chain-modifier">×{{ item.regime_modifier }}</div>
        </div>
      </div>
    </div>

    <!-- ═══ KPI 卡片组 (每个方案一列) ═══ -->
    <div v-if="result && result.scenarios" class="zx-scenarios-grid fade-in">
      <div v-for="(sc, idx) in result.scenarios" :key="sc.name"
        class="zx-scenario-card"
        :class="{ 'zx-scenario-highlight': idx === activeScenarioIndex }"
        style="cursor:pointer;"
        @click="activeScenarioIndex = idx">
        <!-- 标记 -->
        <div class="zx-scenario-tag" v-if="idx === activeScenarioIndex">🌟 当前选中</div>

        <h3 class="zx-scenario-name">{{ sc.name }}</h3>

        <!-- KPI 卡片 -->
        <div class="zx-kpi-grid">
          <div class="zx-kpi-item">
            <div class="zx-kpi-label">年化收益率</div>
            <div class="zx-kpi-value" style="color:#DC2626;">{{ sc.kpi.ann_return_pct }}%</div>
          </div>
          <div class="zx-kpi-item">
            <div class="zx-kpi-label">年化波动率</div>
            <div class="zx-kpi-value">{{ sc.kpi.ann_vol_pct }}%</div>
          </div>
          <div class="zx-kpi-item">
            <div class="zx-kpi-label">最大回撤</div>
            <div class="zx-kpi-value" style="color:#16A34A;">{{ sc.kpi.max_drawdown_pct }}%</div>
          </div>
          <div class="zx-kpi-item">
            <div class="zx-kpi-label">夏普比率</div>
            <div class="zx-kpi-value">{{ sc.kpi.sharpe }}</div>
          </div>
        </div>

        <!-- 资产明细表格 -->
        <div class="zx-alloc-table-wrap">
          <table class="zx-alloc-table">
            <thead>
              <tr>
                <th>基金名称</th>
                <th>类别</th>
                <th style="text-align:right;">权重</th>
                <th style="text-align:right;">金额 (元)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="alloc in sc.allocations.filter(a => a.weight_pct > 0.1)" :key="alloc.code">
                <td>
                  <div class="zx-fund-name">{{ alloc.name }}</div>
                  <div class="zx-fund-code">{{ alloc.code }}</div>
                </td>
                <td><span class="zx-cat-tag">{{ alloc.category }}</span></td>
                <td style="text-align:right;font-weight:700;color:#001529;">{{ alloc.weight_pct }}%</td>
                <td style="text-align:right;font-family:'JetBrains Mono',monospace;color:#43474d;">
                  ¥{{ Number(alloc.amount).toLocaleString() }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ═══ 深度基资料展示 (核心精选 10 支) ═══ -->
    <div v-if="recommendedProfiles.length > 0" class="zx-profiles-section fade-in">
      <div class="zx-card">
        <div class="zx-card-title zxp-flex-title">
          <span>📊 核心精选深度资料</span>
          <span class="zx-profiles-sub">基于【{{ recommendedScenario.name }}】的底层穿透</span>
        </div>
        
        <div class="zx-profiles-grid">
          <div v-for="profile in recommendedProfiles" :key="profile.code" class="zx-profile-card">
            <div class="zxp-header">
              <div class="zxp-title">
                <div class="zxp-fund-name" :title="profile.name">{{ profile.name }}</div>
                <div class="zxp-fund-code">{{ profile.code }}</div>
              </div>
              <div class="zxp-alloc">
                <div class="zxp-cat-tag">{{ profile._alloc_cat || '未知' }}</div>
                <div class="zxp-weight-tag">{{ profile._alloc_weight }}%</div>
              </div>
            </div>
            
            <div class="zxp-body">
              <table class="zxp-table">
                <tbody>
                  <tr>
                    <td>基金经理</td>
                    <td><b>{{ profile.mgrname }}</b></td>
                  </tr>
                  <tr>
                    <td>成立日期</td>
                    <td>{{ profile.setupdate }}</td>
                  </tr>
                  <tr>
                    <td>管理规模</td>
                    <td>{{ profile.scale }}</td>
                  </tr>
                  <tr>
                    <td>今年回报</td>
                    <td :class="{'zxp-good': profile.navytd && profile.navytd.includes && !profile.navytd.includes('-') && profile.navytd !== '暂无'}">{{ profile.navytd }}</td>
                  </tr>
                  <tr>
                    <td>近1年回报</td>
                    <td :class="{'zxp-good': profile.nav1y && profile.nav1y.includes && !profile.nav1y.includes('-') && profile.nav1y !== '暂无'}">{{ profile.nav1y }}</td>
                  </tr>
                  <tr>
                    <td>近3年回报</td>
                    <td :class="{'zxp-good': profile.nav3y && profile.nav3y.includes && !profile.nav3y.includes('-') && profile.nav3y !== '暂无'}">{{ profile.nav3y }}</td>
                  </tr>
                  <tr>
                    <td>年化波动</td>
                    <td>{{ profile.volatility }}</td>
                  </tr>
                  <tr>
                    <td>最大回撤</td>
                    <td style="color:#16A34A;">{{ profile.maxdrawdown }}</td>
                  </tr>
                  <tr>
                    <td>夏普比率</td>
                    <td :class="{'zxp-good': parseFloat(profile.sharpe) > 0}">{{ profile.sharpe }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!result && !loading" class="zx-empty-state">
      <div class="zx-empty-icon">🧭</div>
      <h2>等待宏观象限检索</h2>
      <p>点击上方按钮，系统将自动从 EDB 获取宏观因子数据，定位当前经济周期象限，并生成配置方案。</p>
    </div>

    <!-- Error -->
    <div v-if="error" class="zx-error fade-in">
      ❌ {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useSmartStore } from '../../store/smartSelection'
import { zxMacroAllocation } from '../../api/smart'

const store = useSmartStore()
const loading = ref(false)
const error = ref(null)

const activeScenarioIndex = ref(1)

const result = computed(() => store.zx_macroResult)

watch(() => result.value, (newVal) => {
  if (newVal && newVal.scenarios) {
    activeScenarioIndex.value = newVal.scenarios.length >= 2 ? 1 : 0
  }
})

const recommendedScenario = computed(() => {
  if (!result.value || !result.value.scenarios) return null;
  return result.value.scenarios[activeScenarioIndex.value] || result.value.scenarios[0];
});

const recommendedProfiles = computed(() => {
  return recommendedScenario.value?.profiles || [];
});

const qColors = {
  recovery: { bg: '#ECFDF5', icon: '🌱' },
  overheat: { bg: '#FEF3C7', icon: '🔥' },
  stagflation: { bg: '#FEE2E2', icon: '⚠️' },
  deflation: { bg: '#DBEAFE', icon: '❄️' },
}

async function runMacroAllocation() {
  loading.value = true
  error.value = null
  try {
    const res = await zxMacroAllocation({
      capital: store.zx_capital,
      target_ret: store.zx_targetReturn,
      max_vol: store.zx_maxVol,
      period: store.zx_period,
    })
    store.setMacroResult(res.data)
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || '宏观底仓计算失败'
    console.error('宏观底仓异常:', e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.zx-macro-page { max-width: 100%; }

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
  width: 4px;
  height: 36px;
  background: #001529;
  border-radius: 9999px;
  flex-shrink: 0;
}
.zx-page-title {
  font-size: 24px;
  font-weight: 800;
  color: #001529;
  margin: 0;
  letter-spacing: -0.5px;
}
.zx-page-sub {
  font-size: 12px;
  color: #74777d;
  margin: 2px 0 0;
  font-family: 'Inter', sans-serif;
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
  transition: all 0.15s;
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'Manrope', sans-serif;
  box-shadow: 0 4px 14px rgba(0,21,41,0.2);
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

/* ─── Info Row ─── */
.zx-info-row {
  display: grid;
  grid-template-columns: 320px 1fr 280px;
  gap: 20px;
  margin-bottom: 24px;
}

/* ─── Cards ─── */
.zx-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
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

/* EDB */
.zx-metric {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 13px;
}
.zx-label { color: #74777d; }
.zx-value { font-weight: 700; color: #191c1d; }
.zx-highlight { color: #DC2626; font-size: 15px; }
.zx-sub-metrics {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #74777d;
  background: #f8f9fa;
  padding: 8px 12px;
  border-radius: 6px;
  margin-top: 8px;
}

/* Quadrant */
.zx-quadrant-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}
.zx-quadrant-icon {
  width: 44px; height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}
.zx-quadrant-label { font-weight: 700; font-size: 16px; color: #001529; }
.zx-quadrant-desc { font-size: 12px; color: #74777d; }
.zx-asset-signals {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 10px;
}
.zx-signal-good {
  padding: 8px 10px;
  background: #F0FDF4;
  border-radius: 6px;
  border-left: 2px solid #10B981;
}
.zx-signal-bad {
  padding: 8px 10px;
  background: #FEF2F2;
  border-radius: 6px;
  border-left: 2px solid #EF4444;
}
.zx-signal-title { font-size: 10px; color: #74777d; margin-bottom: 2px; }
.zx-signal-value { font-size: 12px; font-weight: 600; }
.zx-signal-good .zx-signal-value { color: #10B981; }
.zx-signal-bad .zx-signal-value { color: #EF4444; }
.zx-markov { font-size: 11px; color: #94a3b8; }

/* Scenario Type */
.zx-scenario-badge {
  display: inline-block;
  padding: 6px 16px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 800;
  margin-bottom: 12px;
}
.badge-a { background: #ECFDF5; color: #065F46; }
.badge-b { background: #FEF3C7; color: #92400E; }
.zx-scenario-explain {
  font-size: 13px;
  color: #43474d;
  line-height: 1.6;
  margin: 0;
}

/* ─── Transmission Chain ─── */
.zx-chain-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.zx-chain-item {
  padding: 10px 14px;
  border-radius: 8px;
  text-align: center;
  min-width: 90px;
}
.zx-chain-factor { font-weight: 600; font-size: 12px; color: #191c1d; }
.zx-chain-score { font-size: 18px; font-weight: 700; }
.zx-chain-modifier { font-size: 10px; color: #94a3b8; }

/* ─── Scenarios Grid ─── */
.zx-scenarios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}
.zx-scenario-card {
  background: #ffffff;
  border-radius: 14px;
  padding: 24px;
  border: 1px solid rgba(196,198,205,0.12);
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
  position: relative;
  transition: transform 0.2s;
}
.zx-scenario-card:hover { transform: translateY(-2px); }
.zx-scenario-highlight {
  border: 2px solid #001529;
  box-shadow: 0 8px 24px rgba(0,21,41,0.1);
}
.zx-scenario-tag {
  position: absolute;
  top: -10px;
  right: 16px;
  background: #001529;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 9999px;
}
.zx-scenario-name {
  font-size: 18px;
  font-weight: 800;
  color: #001529;
  margin: 0 0 18px;
}

/* KPI */
.zx-kpi-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
}
.zx-kpi-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px;
  text-align: center;
}
.zx-kpi-label {
  font-size: 10px;
  color: #74777d;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}
.zx-kpi-value {
  font-size: 20px;
  font-weight: 800;
  color: #191c1d;
  font-family: 'Manrope', sans-serif;
}

/* Allocation Table */
.zx-alloc-table-wrap {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #f3f4f5;
  border-radius: 8px;
}
.zx-alloc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.zx-alloc-table thead th {
  position: sticky;
  top: 0;
  background: #f8f9fa;
  padding: 8px 10px;
  font-weight: 600;
  color: #43474d;
  border-bottom: 1px solid #e1e3e4;
  text-align: left;
}
.zx-alloc-table tbody td {
  padding: 8px 10px;
  border-bottom: 1px solid #f8f9fa;
}
.zx-fund-name { font-weight: 600; color: #191c1d; }
.zx-fund-code { font-size: 10px; color: #94a3b8; font-family: 'JetBrains Mono', monospace; }
.zx-cat-tag {
  background: #E0E7FF;
  color: #4338CA;
  border-radius: 12px;
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 600;
}

/* ─── Empty State ─── */
.zx-empty-state {
  text-align: center;
  padding: 80px 40px;
  color: #74777d;
}
.zx-empty-icon { font-size: 64px; margin-bottom: 16px; }
.zx-empty-state h2 {
  font-size: 22px;
  font-weight: 700;
  color: #191c1d;
  margin-bottom: 8px;
}
.zx-empty-state p {
  font-size: 14px;
  max-width: 480px;
  margin: 0 auto;
  line-height: 1.6;
}

.zx-error {
  padding: 16px 20px;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 8px;
  color: #991B1B;
  font-size: 14px;
  margin-top: 16px;
}

/* ─── Fund Profiles ─── */
.zx-profiles-section {
  margin-bottom: 32px;
}
.zxp-flex-title {
  display: flex;
  align-items: center;
  gap: 12px;
}
.zx-profiles-sub {
  font-size: 11px;
  color: #74777d;
  font-weight: 400;
  background: #f3f4f5;
  padding: 4px 10px;
  border-radius: 12px;
}
.zx-profiles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}
.zx-profile-card {
  background: #f8f9fa;
  border: 1px solid rgba(196,198,205,0.2);
  border-radius: 10px;
  padding: 14px;
  transition: all 0.2s;
}
.zx-profile-card:hover {
  background: #ffffff;
  border-color: #001529;
  box-shadow: 0 4px 16px rgba(0,21,41,0.06);
}
.zxp-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px dashed rgba(196,198,205,0.4);
}
.zxp-fund-name {
  font-weight: 700;
  font-size: 13px;
  color: #001529;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
}
.zxp-fund-code {
  font-size: 10px;
  color: #94a3b8;
  font-family: 'JetBrains Mono', monospace;
  margin-top: 2px;
}
.zxp-alloc {
  text-align: right;
}
.zxp-weight-tag {
  font-size: 14px;
  font-weight: 800;
  color: #001529;
  font-family: 'Manrope', sans-serif;
}
.zxp-table {
  width: 100%;
  font-size: 11px;
  color: #43474d;
  border-collapse: collapse;
}
.zxp-table td {
  padding: 4px 0;
}
.zxp-table td:last-child {
  text-align: right;
  color: #191c1d;
  font-family: 'Inter', sans-serif;
}
.zxp-good { color: #DC2626 !important; font-weight: 600; }

.fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
</style>
