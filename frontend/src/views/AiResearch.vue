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

      <div class="card" style="margin-bottom:24px;">
        <div class="card-title">📉 EDB 数据检索提取</div>
        <p style="color:var(--text-secondary);font-size:13px;margin-bottom:12px;">
          从宏观数据库抽取当月数十项高密集的经济基本面历史数据。
        </p>
        <AsyncButton
          :action="mockEdbFetch"
          type="primary"
          text="🚀 启动 EDB 数据检索提取"
          @success="() => { edbResult = true; if(currentStep < 1) currentStep = 1; }"
        />
        
        <div v-if="edbResult" class="fade-in" style="margin-top:20px;padding:16px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;">
          <div style="display:flex;gap:24px;">
            <div style="flex:1;border:2px dashed #CBD5E1;border-radius:8px;padding:32px;text-align:center;background:#fff;">
              <div style="font-size:32px;margin-bottom:8px;">⏱️</div>
              <div style="font-weight:700;color:var(--navy);margin-bottom:4px;font-size:15px;">“经济时钟”(美林时钟) 图谱</div>
              <div style="font-size:12px;color:var(--text-muted);">(当前位于：复苏期 / 宽信用)</div>
            </div>
            <div style="flex:1;border:2px dashed #CBD5E1;border-radius:8px;padding:32px;text-align:center;background:#fff;">
              <div style="font-size:32px;margin-bottom:8px;">📊</div>
              <div style="font-weight:700;color:var(--navy);margin-bottom:4px;font-size:15px;">EDB Z-Score 散点图</div>
              <div style="font-size:12px;color:var(--text-muted);">(12 项核心指标景气度均 > 0.5)</div>
            </div>
          </div>
        </div>
      </div>

      <div class="card" style="margin-bottom:24px;transition:opacity 0.3s;" :style="{ opacity: currentStep >= 1 ? 1 : 0.5, pointerEvents: currentStep >= 1 ? 'auto' : 'none' }">
        <div class="card-title">🤖 多智能体投研分析会</div>
        <p style="color:var(--text-secondary);font-size:13px;margin-bottom:12px;">
          基于 EDB 经济数据，并行唤醒 3 个 AI 专家 (多头分析师、空头分析师、长线宏观专家) 进行 Debate。
        </p>
        <AsyncButton
          :action="mockDebateFetch"
          type="primary"
          text="🧠 运行 Kimi 虚拟投研分析会"
          @success="() => { debateResult = true; if(currentStep < 2) currentStep = 2; }"
        />
        
        <div v-if="debateResult" class="fade-in" style="margin-top:20px;display:flex;gap:24px;">
          <div style="flex:2;background:#F4F6F6;border-radius:8px;padding:16px;border:1px solid #D0ECE7;">
            <div v-for="(log, i) in debateLogs" :key="i" style="margin-bottom:16px;display:flex;gap:12px;" class="fade-in" :style="{animationDelay: i * 0.4 + 's'}">
              <div style="width:40px;height:40px;border-radius:50%;background:#1A5276;color:#FFF;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;flex-shrink:0;"
                   :style="{background: log.avatar === '空' ? '#C0392B' : (log.avatar === '多' ? '#10B981' : '#2E86C1')}">
                {{ log.avatar }}
              </div>
              <div>
                <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">{{ log.role }}</div>
                <div style="background:#FFF;padding:10px 14px;border-radius:0 8px 8px 8px;font-size:13px;color:var(--text-primary);box-shadow:0 1px 3px rgba(0,0,0,0.05);line-height:1.6;">
                  {{ log.content }}
                </div>
              </div>
            </div>
          </div>
          <div style="flex:1;border:2px dashed #D0ECE7;border-radius:8px;padding:32px;text-align:center;display:flex;flex-direction:column;justify-content:center;background:#E8F8F5;">
            <div style="font-size:32px;margin-bottom:8px;">🕸️</div>
            <div style="font-weight:700;color:#0E6251;margin-bottom:4px;font-size:15px;">情绪雷达图</div>
            <div style="font-size:12px;color:#117864;">(多空强弱对比：多头显著占优)</div>
          </div>
        </div>
      </div>

      <div class="card" style="margin-bottom:24px;transition:opacity 0.3s;" :style="{ opacity: currentStep >= 2 ? 1 : 0.5, pointerEvents: currentStep >= 2 ? 'auto' : 'none' }">
        <div class="card-title">🎯 宏观分析与配置运算</div>
        <p style="color:var(--text-secondary);font-size:13px;margin-bottom:12px;">
          汇集前序观点的最终结论，计算出各宏观大类资产的配置建议比例（百分比）。
        </p>
        <AsyncButton
          :action="mockAllocation"
          type="primary"
          text="🎯 执行宏观分析与资产配置运算"
          @success="() => { allocationResult = true; if(currentStep < 3) currentStep = 3; }"
        />
        
        <div v-if="allocationResult" class="fade-in" style="margin-top:20px;padding:24px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;">
          <div style="display:flex;gap:32px;align-items:center;">
            <div style="width:200px;height:200px;border:16px solid #3498DB;border-radius:50%;border-top-color:#1ABC9C;border-right-color:#F1C40F;border-left-color:#E74C3C;position:relative;display:flex;align-items:center;justify-content:center;box-shadow:inset 0 2px 5px rgba(0,0,0,0.05);">
              <div style="text-align:center;background:#fff;width:140px;height:140px;border-radius:50%;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                <div style="font-weight:700;font-size:24px;color:var(--navy);">100%</div>
                <div style="font-size:11px;color:var(--text-muted);">目标配置比例</div>
              </div>
            </div>
            <div style="flex:1;">
              <table class="data-table" style="width:100%;">
                <thead>
                  <tr>
                    <th>大类资产</th>
                    <th style="text-align:right;">建议目标权重</th>
                    <th>配置逻辑说明</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style="font-weight:600;color:var(--navy);">大盘价值 (H/A)</td>
                    <td style="text-align:right;font-family:'JetBrains Mono',monospace;color:#EF4444;font-weight:600;">35.0%</td>
                    <td style="font-size:12px;color:var(--text-secondary);">宽信用周期确立，低估值顺周期资产胜率最高。</td>
                  </tr>
                  <tr>
                    <td style="font-weight:600;color:var(--navy);">纯债固收</td>
                    <td style="text-align:right;font-family:'JetBrains Mono',monospace;font-weight:600;">30.0%</td>
                    <td style="font-size:12px;color:var(--text-secondary);">作为组合压舱石，防御系统性下行风险。</td>
                  </tr>
                  <tr>
                    <td style="font-weight:600;color:var(--navy);">高成长主题</td>
                    <td style="text-align:right;font-family:'JetBrains Mono',monospace;color:#EF4444;font-weight:600;">20.0%</td>
                    <td style="font-size:12px;color:var(--text-secondary);">维持一定的高景气度行业暴露以获取超额收益。</td>
                  </tr>
                  <tr>
                    <td style="font-weight:600;color:var(--navy);">黄金商品</td>
                    <td style="text-align:right;font-family:'JetBrains Mono',monospace;color:#F59E0B;font-weight:600;">15.0%</td>
                    <td style="font-size:12px;color:var(--text-secondary);">对冲海外潜在的输入性通胀和地缘尾部风险。</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div class="section-title" style="margin-top:48px;">模块二：底层资产到基金映射区</div>
      
      <div class="card" style="margin-bottom:48px;transition:opacity 0.3s;" :style="{ opacity: currentStep >= 3 ? 1 : 0.5, pointerEvents: currentStep >= 3 ? 'auto' : 'none' }">
        <div class="card-title">🔀 实体基金一键匹配</div>
        <p style="color:var(--text-secondary);font-size:13px;margin-bottom:12px;">
          在给定的资产配置目标下，穿透底层数据库，自动从候选池寻找最契合的基金组建实盘组合。
        </p>
        <AsyncButton
          :action="mockFundMapping"
          type="primary"
          text="🔍 一键配置 (根据权重自动匹配实体基金)"
          @success="() => { fundMappingResult = true; }"
        />
        
        <div v-if="fundMappingResult" class="fade-in" style="margin-top:24px;">
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
                <tr>
                  <td style="font-family:'JetBrains Mono',monospace;font-weight:600;color:var(--navy);">000979.OF</td>
                  <td>核心资产精选混合</td>
                  <td><span style="background:#EBF5FB;color:#2E86C1;padding:2px 6px;border-radius:4px;font-size:11px;">大盘价值 (H/A)</span></td>
                  <td style="text-align:right;font-family:'JetBrains Mono',monospace;color:#10B981;font-weight:600;">92.4%</td>
                  <td style="text-align:right;font-family:'JetBrains Mono',monospace;font-weight:600;">35.00%</td>
                </tr>
                <tr>
                  <td style="font-family:'JetBrains Mono',monospace;font-weight:600;color:var(--navy);">001203.OF</td>
                  <td>稳健纯债债券A</td>
                  <td><span style="background:#F4F6F6;color:#34495E;padding:2px 6px;border-radius:4px;font-size:11px;">纯债固收</span></td>
                  <td style="text-align:right;font-family:'JetBrains Mono',monospace;color:#10B981;font-weight:600;">98.1%</td>
                  <td style="text-align:right;font-family:'JetBrains Mono',monospace;font-weight:600;">30.00%</td>
                </tr>
                <tr>
                  <td style="font-family:'JetBrains Mono',monospace;font-weight:600;color:var(--navy);">002657.OF</td>
                  <td>高成长行业精选</td>
                  <td><span style="background:#FDEDEC;color:#C0392B;padding:2px 6px;border-radius:4px;font-size:11px;">高成长主题</span></td>
                  <td style="text-align:right;font-family:'JetBrains Mono',monospace;color:#F59E0B;font-weight:600;">85.3%</td>
                  <td style="text-align:right;font-family:'JetBrains Mono',monospace;font-weight:600;">20.00%</td>
                </tr>
                <tr>
                  <td style="font-family:'JetBrains Mono',monospace;font-weight:600;color:var(--navy);">518880.SH</td>
                  <td>华安黄金ETF</td>
                  <td><span style="background:#FEF9E7;color:#B7950B;padding:2px 6px;border-radius:4px;font-size:11px;">黄金商品</span></td>
                  <td style="text-align:right;font-family:'JetBrains Mono',monospace;color:#10B981;font-weight:600;">99.5%</td>
                  <td style="text-align:right;font-family:'JetBrains Mono',monospace;font-weight:600;">15.00%</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div style="display:flex;gap:24px;">
            <div style="flex:2;border:1px solid #E2E8F0;background:#F8FAFC;border-radius:8px;padding:32px 24px;text-align:center;display:flex;flex-direction:column;justify-content:center;align-items:center;">
              <div style="font-size:32px;margin-bottom:8px;">📈</div>
              <div style="font-weight:700;color:var(--navy);margin-bottom:4px;font-size:15px;">组合历史回测走势图 (Echarts)</div>
              <div style="font-size:12px;color:var(--text-muted);">(基于近 3 年数据绘制从 1.0 起跑的净值走势和最大回撤折线图)</div>
            </div>
            <div style="flex:1;border:1px solid #E2E8F0;background:#F8FAFC;border-radius:8px;padding:32px 24px;text-align:center;display:flex;flex-direction:column;justify-content:center;align-items:center;">
              <div style="font-size:32px;margin-bottom:8px;">🔥</div>
              <div style="font-weight:700;color:var(--navy);margin-bottom:4px;font-size:15px;">成分相关性 Heatmap</div>
              <div style="font-size:12px;color:var(--text-muted);">(确保各底层标的呈低相关甚至负相关)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AsyncButton from '../components/common/AsyncButton.vue'

const currentStep = ref(0) // 控制解耦模块和步骤（0=EDB, 1=Debate, 2=配置, 3=基金映射）

const edbResult = ref(false)
const debateResult = ref(false)
const allocationResult = ref(false)
const fundMappingResult = ref(false)

const debateLogs = ref([
  { role: '多头分析师 (Kimi)', avatar: '多', content: '基于最新提取的 EDB 数据，12 项核心指标中有 9 项位于景气度荣枯线以上。信用脉冲连续两个月呈复苏态势，建议大幅超配权益，特别是顺周期的大盘价值板块拿满 35%！' },
  { role: '空头分析师 (DeepSeek)', avatar: '空', content: '反对！虽然表观数据复苏，但地产和化债的长期约束仍在。海外通胀有二次抬升迹象，这说明系统性尾部风险未解除。我建议权益敞口不超过 20%，同时增加 15% 黄金商品作为对冲。' },
  { role: '风控投委会 (主席)', avatar: '裁', content: '两位说的都有充足的底层数据支撑。综合来看，当前处于“宽信用+弱复苏”阶段，系统性崩盘概率低，但单边大牛市尚需政策强验证。我们取折中方案：权益总量控制在 55%（35%低估值价值压舱，20%成长博弈），30%固收吃票息，15%黄金全天候对冲海外地缘。' }
])

// Mock 异步任务（模拟延迟并拉起防连击 Loading）
const mockEdbFetch = () => new Promise(resolve => setTimeout(resolve, 800))
const mockDebateFetch = () => new Promise(resolve => setTimeout(resolve, 1500))
const mockAllocation = () => new Promise(resolve => setTimeout(resolve, 600))
const mockFundMapping = () => new Promise(resolve => setTimeout(resolve, 1200))

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
</style>
