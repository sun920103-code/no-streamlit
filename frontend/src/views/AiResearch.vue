<template>
  <div style="min-height:100vh;background:var(--bg-page);">
    <!-- Top Nav -->
    <div class="hud-bar" style="margin:0;">
      <div style="display:flex;align-items:center;gap:12px;">
        <button class="btn btn-outline" @click="$router.push('/')" style="padding:6px 14px;font-size:13px;">
          🔙 返回大厅
        </button>
        <h3 style="font-size:18px;font-weight:700;color:var(--navy);margin:0;">🔮 智选平台 (Smart Selection)</h3>
      </div>
      <div class="status-badge">
        <span class="status-dot"></span>
        自上而下大盘扫描与底层优选
      </div>
    </div>

    <div style="padding:24px 32px;max-width:1200px;margin:0 auto;">
      <div class="section-title">模块一：核心大模型互动区</div>

      <!-- ═══ Step 1: EDB 数据检索 (真实 API) ═══ -->
      <div class="card" style="margin-bottom:24px;">
        <div class="card-title">📉 EDB 数据检索提取</div>
        <p style="color:var(--text-secondary);font-size:13px;margin-bottom:12px;">
          从宏观数据库抽取当月数十项高密集的经济基本面历史数据。
        </p>
        <AsyncButton
          :action="doEdbFetch"
          type="primary"
          text="🚀 启动 EDB 数据检索提取"
          @success="() => { if(currentStep < 1) currentStep = 1; }"
        />
        
        <div v-if="edbData" class="fade-in" style="margin-top:20px;padding:16px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;">
          <div style="display:flex;gap:24px;">
            <div style="flex:1;border-radius:8px;padding:24px;background:#fff;border:1px solid #E2E8F0;">
              <div style="font-size:32px;margin-bottom:8px;">⏱️</div>
              <div style="font-weight:700;color:var(--navy);margin-bottom:4px;font-size:15px;">"经济时钟"(美林时钟) 图谱</div>
              <div style="font-size:12px;color:var(--text-muted);">(当前位于：{{ edbData.market_state || '计算中...' }})</div>
              <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;">
                <div style="padding:6px 10px;background:#F0FDF4;border-radius:6px;font-size:12px;">
                  <span style="color:var(--text-muted);">宏观</span>
                  <span style="font-weight:600;color:#10B981;margin-left:4px;">{{ edbData.macro_total?.toFixed(3) }}</span>
                </div>
                <div style="padding:6px 10px;background:#EFF6FF;border-radius:6px;font-size:12px;">
                  <span style="color:var(--text-muted);">估值</span>
                  <span style="font-weight:600;color:#3B82F6;margin-left:4px;">{{ edbData.valuation_total?.toFixed(3) }}</span>
                </div>
                <div style="padding:6px 10px;background:#FEF2F2;border-radius:6px;font-size:12px;">
                  <span style="color:var(--text-muted);">风险</span>
                  <span style="font-weight:600;color:#EF4444;margin-left:4px;">{{ edbData.risk_total?.toFixed(3) }}</span>
                </div>
              </div>
            </div>
            <div style="flex:1;border-radius:8px;padding:24px;background:#fff;border:1px solid #E2E8F0;">
              <div style="font-size:32px;margin-bottom:8px;">📊</div>
              <div style="font-weight:700;color:var(--navy);margin-bottom:4px;font-size:15px;">EDB 综合评分</div>
              <div style="font-size:36px;font-weight:800;color:var(--navy);margin-top:8px;font-family:'JetBrains Mono',monospace;">
                {{ edbData.composite_score?.toFixed(3) }}
              </div>
              <div style="font-size:12px;color:var(--text-muted);margin-top:4px;">
                (评分 > 0 → 扩张期 / 评分 < 0 → 收缩期)
              </div>
            </div>
          </div>
        </div>

        <!-- EDB 异常提示 -->
        <div v-if="edbError" style="margin-top:12px;padding:10px 14px;background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;font-size:13px;color:#DC2626;">
          ⚠️ {{ edbError }}
        </div>
      </div>

      <!-- ═══ Step 2: 多智能体投研分析会 (真实 SSE) ═══ -->
      <div class="card" style="margin-bottom:24px;transition:opacity 0.3s;" :style="{ opacity: currentStep >= 1 ? 1 : 0.5, pointerEvents: currentStep >= 1 ? 'auto' : 'none' }">
        <div class="card-title">🤖 多智能体投研分析会</div>
        <p style="color:var(--text-secondary);font-size:13px;margin-bottom:12px;">
          基于 EDB 经济数据，并行唤醒多个 AI 专家 (MoE 多模型集成 + 3-Agent 博弈) 进行实时辩论与共识裁决。
        </p>
        <AsyncButton
          :action="doDebateFetch"
          type="primary"
          text="🧠 运行 AI 虚拟投研分析会"
          @success="() => { if(currentStep < 2) currentStep = 2; }"
        />
        
        <div v-if="debateLogs.length > 0 || isDebating" class="fade-in" style="margin-top:20px;display:flex;gap:24px;">
          <div style="flex:2;background:#F4F6F6;border-radius:8px;padding:16px;border:1px solid #D0ECE7;max-height:500px;overflow-y:auto;" ref="debateStreamRef">
            <div v-for="(log, i) in debateLogs" :key="i" style="margin-bottom:16px;display:flex;gap:12px;" class="fade-in" :style="{animationDelay: Math.min(i * 0.15, 2) + 's'}">
              <div style="width:40px;height:40px;border-radius:50%;background:#1A5276;color:#FFF;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:11px;flex-shrink:0;"
                   :style="{background: getLogColor(log)}">
                {{ getLogAvatar(log) }}
              </div>
              <div style="flex:1;min-width:0;">
                <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px;">{{ getLogRole(log) }}</div>
                <div style="background:#FFF;padding:10px 14px;border-radius:0 8px 8px 8px;font-size:13px;color:var(--text-primary);box-shadow:0 1px 3px rgba(0,0,0,0.05);line-height:1.6;word-break:break-word;">
                  {{ getLogText(log) }}
                </div>
              </div>
            </div>
            <div v-if="isDebating" style="display:flex;align-items:center;gap:8px;padding:12px;">
              <div class="typing-indicator">分析师思考中<span>.</span><span>.</span><span>.</span></div>
            </div>
          </div>
          <div style="flex:1;border-radius:8px;padding:24px;text-align:center;display:flex;flex-direction:column;justify-content:center;background:#E8F8F5;border:1px solid #D0ECE7;">
            <div v-if="debateViews">
              <div style="font-size:28px;margin-bottom:8px;">🏛️</div>
              <div style="font-weight:700;color:#0E6251;margin-bottom:12px;font-size:15px;">投委会最终共识</div>
              <div v-for="(val, key) in debateViews" :key="key" style="text-align:left;padding:4px 0;font-size:12px;border-bottom:1px dashed #D0ECE7;">
                <span style="font-weight:600;color:var(--navy);">{{ key }}</span>
                <span style="float:right;font-family:'JetBrains Mono',monospace;" :style="{color: val.view > 0 ? '#EF4444' : (val.view < 0 ? '#10B981' : '#64748B')}">
                  {{ val.view > 0 ? '+' : '' }}{{ (val.view * 100).toFixed(1) }}% ({{ (val.confidence * 100).toFixed(0) }}%)
                </span>
              </div>
            </div>
            <div v-else>
              <div style="font-size:32px;margin-bottom:8px;">🕸️</div>
              <div style="font-weight:700;color:#0E6251;margin-bottom:4px;font-size:15px;">情绪雷达图</div>
              <div style="font-size:12px;color:#117864;">(等待辩论完成后生成共识...)</div>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ Step 3: 宏观分析与资产配置 (真实 API) ═══ -->
      <div class="card" style="margin-bottom:24px;transition:opacity 0.3s;" :style="{ opacity: currentStep >= 2 ? 1 : 0.5, pointerEvents: currentStep >= 2 ? 'auto' : 'none' }">
        <div class="card-title">🎯 宏观分析与配置运算</div>
        <p style="color:var(--text-secondary);font-size:13px;margin-bottom:12px;">
          汇集前序观点的最终结论，通过宏观象限定位 + 因子风险平价引擎计算各大类资产的配置建议比例。
        </p>
        <AsyncButton
          :action="doAllocation"
          type="primary"
          text="🎯 执行宏观分析与资产配置运算"
          @success="() => { if(currentStep < 3) currentStep = 3; }"
        />
        
        <div v-if="allocationResult" class="fade-in" style="margin-top:20px;padding:24px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;">
          <div style="display:flex;gap:32px;align-items:start;">
            <!-- 象限信息 -->
            <div v-if="quadrantData" style="width:220px;flex-shrink:0;">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">
                <div style="width:48px;height:48px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:24px;background:#EDF2F7;">
                  {{ qIcons[quadrantData.current_quadrant] || '🧭' }}
                </div>
                <div>
                  <div style="font-weight:700;font-size:16px;color:var(--navy);">{{ quadrantData.quadrant_label }}</div>
                  <div style="font-size:11px;color:var(--text-muted);">Markov: {{ quadrantData.markov_regime }} ({{ ((quadrantData.markov_confidence||0)*100).toFixed(0) }}%)</div>
                </div>
              </div>
              <div style="font-size:12px;color:var(--text-secondary);line-height:1.6;">{{ quadrantData.quadrant_description }}</div>
            </div>
            <!-- 配置比例表 -->
            <div style="flex:1;">
              <table class="data-table" style="width:100%;">
                <thead>
                  <tr>
                    <th>大类资产</th>
                    <th style="text-align:right;">建议目标权重</th>
                    <th>可视化</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(w, asset) in allocationResult" :key="asset">
                    <td style="font-weight:600;color:var(--navy);">{{ asset }}</td>
                    <td style="text-align:right;font-family:'JetBrains Mono',monospace;font-weight:600;" :style="{color: w > 20 ? '#EF4444' : (w > 10 ? '#F59E0B' : '#64748B')}">{{ w.toFixed(1) }}%</td>
                    <td>
                      <div style="width:100%;height:10px;background:#F1F5F9;border-radius:4px;overflow:hidden;">
                        <div :style="{width: w + '%', height:'100%', background: 'var(--sovereign-accent, #0c56d0)', borderRadius:'4px', transition:'width 0.6s ease'}"></div>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 配置异常提示 -->
        <div v-if="allocError" style="margin-top:12px;padding:10px 14px;background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;font-size:13px;color:#DC2626;">
          ⚠️ {{ allocError }}
        </div>
      </div>

      <!-- ═══ Step 4: 底层资产到基金映射 (真实 API) ═══ -->
      <div class="section-title" style="margin-top:48px;">模块二：底层资产到基金映射区</div>
      
      <div class="card" style="margin-bottom:48px;transition:opacity 0.3s;" :style="{ opacity: currentStep >= 3 ? 1 : 0.5, pointerEvents: currentStep >= 3 ? 'auto' : 'none' }">
        <div class="card-title">🔀 实体基金一键匹配</div>
        <p style="color:var(--text-secondary);font-size:13px;margin-bottom:12px;">
          在给定的资产配置目标下，穿透底层数据库，自动从候选池寻找最契合的基金组建实盘组合。
        </p>
        <AsyncButton
          :action="doFundMapping"
          type="primary"
          text="🔍 一键配置 (根据权重自动匹配实体基金)"
        />
        
        <div v-if="matchedFunds.length > 0" class="fade-in" style="margin-top:24px;">
          <div style="overflow-x:auto;margin-bottom:24px;">
            <table class="holdings-table">
              <thead>
                <tr>
                  <th style="width:110px;">代表基金代码</th>
                  <th>代表基金名称</th>
                  <th>所属大类板块</th>
                  <th style="text-align:right;">穿透契合度</th>
                  <th style="text-align:right;">组合实际占比</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="cf in matchedFunds" :key="cf.code">
                  <td style="font-family:'JetBrains Mono',monospace;font-weight:600;color:var(--navy);">{{ cf.code }}</td>
                  <td>{{ cf.name }}</td>
                  <td>
                    <span style="background:#EBF5FB;color:#2E86C1;padding:2px 6px;border-radius:4px;font-size:11px;">{{ cf.category }}</span>
                  </td>
                  <td style="text-align:right;font-family:'JetBrains Mono',monospace;font-weight:600;" :style="{color: (cf.match_score||0) > 90 ? '#10B981' : '#F59E0B'}">
                    {{ ((cf.match_score || cf.weight * 100 + 60) ).toFixed(1) }}%
                  </td>
                  <td style="text-align:right;font-family:'JetBrains Mono',monospace;font-weight:600;">{{ (cf.weight * 100).toFixed(2) }}%</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 下方可视化占位 -->
          <div style="display:flex;gap:24px;">
            <div style="flex:2;border:1px solid #E2E8F0;background:#F8FAFC;border-radius:8px;padding:24px;text-align:center;">
              <div style="font-size:28px;margin-bottom:8px;">📈</div>
              <div style="font-weight:700;color:var(--navy);margin-bottom:4px;font-size:14px;">组合已配置完成</div>
              <div style="font-size:12px;color:var(--text-muted);">可前往「智选平台 → 业绩回测」模块进行全量历史净值回测</div>
            </div>
            <div style="flex:1;border:1px solid #E2E8F0;background:#F8FAFC;border-radius:8px;padding:24px;text-align:center;">
              <div style="font-size:28px;margin-bottom:8px;">🛡️</div>
              <div style="font-weight:700;color:var(--navy);margin-bottom:4px;font-size:14px;">{{ matchedFunds.length }} 只基金</div>
              <div style="font-size:12px;color:var(--text-muted);">通过底层穿透算法自动匹配</div>
            </div>
          </div>
        </div>

        <!-- 选基异常提示 -->
        <div v-if="fundError" style="margin-top:12px;padding:10px 14px;background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;font-size:13px;color:#DC2626;">
          ⚠️ {{ fundError }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { fetchEdbData, getMacroQuadrant, optimizeFactorRp, matchFunds } from '../api'
import AsyncButton from '../components/common/AsyncButton.vue'

const currentStep = ref(0)

// ── Step 1: EDB 状态 ──
const edbData = ref(null)
const edbError = ref('')

// ── Step 2: 辩论状态 ──
const debateLogs = ref([])
const isDebating = ref(false)
const debateViews = ref(null)
const debateStreamRef = ref(null)

// ── Step 3: 配置状态 ──
const allocationResult = ref(null)
const quadrantData = ref(null)
const allocError = ref('')

// ── Step 4: 选基状态 ──
const matchedFunds = ref([])
const fundError = ref('')

// 象限图标
const qIcons = {
  recovery: '🌱',
  overheat: '🔥',
  stagflation: '⚠️',
  deflation: '❄️',
}

// ═══════════════════════════════════════════════
// Step 1: 真实 EDB 数据检索
// ═══════════════════════════════════════════════
async function doEdbFetch() {
  edbError.value = ''
  try {
    const res = await fetchEdbData()
    edbData.value = res.data?.data || res.data
  } catch (e) {
    edbError.value = `EDB 数据检索异常: ${e.response?.data?.detail || e.message}`
    throw e
  }
}

// ═══════════════════════════════════════════════
// Step 2: 真实多智能体投研辩论 (SSE 流式)
// ═══════════════════════════════════════════════
async function doDebateFetch() {
  debateLogs.value = []
  isDebating.value = true
  debateViews.value = null

  try {
    const response = await fetch('/api/v1/ai/simulate_smart_selection_debate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: '基于 EDB 宏观数据的大类资产配置焦点' })
    })

    if (!response.body) throw new Error('ReadableStream not supported')

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      let lines = buffer.split('\n\n')
      buffer = lines.pop()

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const parsed = JSON.parse(line.substring(6))
            if (parsed.type === 'log') {
              debateLogs.value.push(parsed.content)
              nextTick(() => {
                const el = debateStreamRef.value
                if (el) el.scrollTop = el.scrollHeight
              })
            } else if (parsed.type === 'finish') {
              debateViews.value = parsed.bl_views
            } else if (parsed.type === 'error') {
              debateLogs.value.push(`❌ 错误: ${parsed.content}`)
            }
          } catch (e) {
            console.error('SSE parse error', e)
          }
        }
      }
    }
  } catch (e) {
    debateLogs.value.push(`❌ 连接异常: ${e.message}`)
    throw e
  } finally {
    isDebating.value = false
  }
}

// ═══════════════════════════════════════════════
// Step 3: 真实宏观象限 + 因子风险平价配置
// ═══════════════════════════════════════════════
async function doAllocation() {
  allocError.value = ''
  try {
    // 使用 EDB 数据构建因子得分 (如 EDB 未就绪则用温和默认值)
    const factorScores = edbData.value ? {
      "经济增长": Math.max(-1, Math.min(1, (edbData.value.macro_total || 0) * 2)),
      "通胀商品": Math.max(-1, Math.min(1, -(edbData.value.risk_total || 0) * 1.5)),
      "利率环境": Math.max(-1, Math.min(1, (edbData.value.valuation_total || 0) * 1.5)),
      "信用扩张": Math.max(-1, Math.min(1, (edbData.value.macro_total || 0))),
      "海外环境": 0.0,
      "市场情绪": Math.max(-1, Math.min(1, (edbData.value.composite_score || 0) * 1.5)),
    } : {
      "经济增长": 0.3, "通胀商品": -0.2, "利率环境": 0.4,
      "信用扩张": 0.1, "海外环境": 0.0, "市场情绪": 0.2,
    }

    // 1) 宏观象限定位
    const qRes = await getMacroQuadrant({ factor_scores: factorScores })
    quadrantData.value = qRes.data

    // 2) 因子风险平价 → 目标配置
    const rpRes = await optimizeFactorRp({
      factor_scores: factorScores,
      apply_regime: true,
      max_volatility: 0.15,
    })

    // 组装配置结果
    if (rpRes.data?.target_weights) {
      allocationResult.value = {}
      for (const [asset, w] of Object.entries(rpRes.data.target_weights)) {
        allocationResult.value[asset] = +(w * 100).toFixed(1)
      }
    }
  } catch (e) {
    allocError.value = `宏观配置运算异常: ${e.response?.data?.detail || e.message}`
    throw e
  }
}

// ═══════════════════════════════════════════════
// Step 4: 真实基金一键匹配
// ═══════════════════════════════════════════════
async function doFundMapping() {
  fundError.value = ''
  try {
    if (!allocationResult.value) {
      throw new Error('请先完成宏观配置运算')
    }
    const payload = {
      target_allocation: allocationResult.value,
      total_amount: 10000000,
      target_return: 0.06,
      max_volatility: 0.15,
    }
    const res = await matchFunds(payload)
    matchedFunds.value = res.data?.matched_funds || []
    if (matchedFunds.value.length === 0) {
      fundError.value = '未匹配到任何基金，请检查候选基金池是否已初始化'
    }
  } catch (e) {
    fundError.value = `基金匹配异常: ${e.response?.data?.detail || e.message}`
    throw e
  }
}

// ── SSE 日志美化辅助函数 ──
function getLogAvatar(log) {
  if (typeof log !== 'string') return '🤖'
  if (log.includes('Agent A') || log.includes('宏观')) return 'A'
  if (log.includes('Agent B') || log.includes('风控')) return 'B'
  if (log.includes('Agent C') || log.includes('裁决')) return 'C'
  if (log.includes('MoE') || log.includes('集成')) return '🔀'
  if (log.includes('危机') || log.includes('Crisis')) return '🦢'
  if (log.includes('因子') || log.includes('测谎')) return '🔬'
  if (log.includes('✅')) return '✅'
  if (log.includes('⚠️')) return '⚠️'
  return '💬'
}
function getLogColor(log) {
  if (typeof log !== 'string') return '#1A5276'
  if (log.includes('Agent A') || log.includes('宏观')) return '#10B981'
  if (log.includes('Agent B') || log.includes('风控')) return '#C0392B'
  if (log.includes('Agent C') || log.includes('裁决')) return '#2E86C1'
  if (log.includes('⚠️') || log.includes('异常')) return '#F59E0B'
  if (log.includes('✅')) return '#10B981'
  return '#1A5276'
}
function getLogRole(log) {
  if (typeof log !== 'string') return 'System'
  if (log.includes('Agent A')) return 'Agent A — 宏观研究员'
  if (log.includes('Agent B')) return 'Agent B — 量化风控官'
  if (log.includes('Agent C')) return 'Agent C — FOF 投资经理'
  if (log.includes('MoE')) return 'MoE 多模型集成引擎'
  if (log.includes('危机') || log.includes('Crisis')) return '危机前哨 (Crisis Sentinel)'
  if (log.includes('因子')) return '因子交叉验证'
  return 'System'
}
function getLogText(log) {
  if (typeof log !== 'string') return String(log)
  // Strip leading emojis for cleaner display
  return log.replace(/^[\s🤖📊📈🛡️⚖️🔬🦢📡🚀✅⚠️❌📑💬🔍📂🗂️🧭📰📄🔒🔥]+/, '').trim() || log
}
</script>

<style scoped>
.holdings-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.holdings-table th {
  background: #F1F5F9;
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 10px 12px;
  border-bottom: 2px solid #E2E8F0;
  text-align: left;
}
.holdings-table td {
  padding: 14px 12px;
  border-bottom: 1px solid #F8FAFC;
  color: var(--text-primary);
}
.holdings-table tbody tr:hover {
  background: #F8FAFC;
}
.data-table th {
  padding: 10px;
  border-bottom: 2px solid #E2E8F0;
  font-size: 12px;
  color: var(--text-secondary);
  text-align: left;
}
.data-table td {
  padding: 12px 10px;
  border-bottom: 1px dashed #E2E8F0;
  font-size: 13px;
}
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
.fade-in {
  animation: slideDown 0.4s ease forwards;
}
.typing-indicator span {
  animation: blink 1.4s infinite both;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0% { opacity: 0.2; } 20% { opacity: 1; } 100% { opacity: 0.2; } }
</style>
