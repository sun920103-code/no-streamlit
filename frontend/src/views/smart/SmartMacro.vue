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
    </div>
    
    <!-- Main Dashboard Row Layout -->
    <div v-if="result" class="flex flex-col xl:flex-row gap-6 items-stretch fade-in mb-6">
      
      <!-- Section 1: 宏观特征引擎 (EDB) -->
      <section class="flex-[2] bg-[#f1f4f6] p-6 rounded-xl border border-[#eaeff1] flex flex-col justify-between">
        <div class="flex items-center gap-3 mb-6">
          <span class="material-symbols-outlined text-[#737c7f]" data-icon="query_stats">query_stats</span>
          <h2 class="text-sm font-bold tracking-widest text-[#2b3437] uppercase whitespace-nowrap">宏观特征引擎 (EDB)</h2>
        </div>
        <div class="flex items-center gap-8 mb-8">
          <div class="flex-none">
            <div class="flex items-baseline gap-3">
              <span class="text-6xl font-black tracking-tighter" :class="result.edb_data.composite_score < 0 ? 'text-[#9f403d]' : 'text-[#46607f]'">{{ (result.edb_data.composite_score || 0).toFixed(3) }}</span>
              <span class="px-3 py-1 bg-[#dbe4e7] text-[#586064] text-[10px] font-black tracking-[0.2em] uppercase rounded-full">{{ result.edb_data.market_state }}</span>
            </div>
            <p class="text-[9px] text-[#737c7f] tracking-widest uppercase font-bold mt-1">INDICATOR STRENGTH 评分强度</p>
          </div>

          <div class="flex-grow grid grid-cols-1 gap-4 border-l border-[#dbe4e7]/30 pl-8">
            <div class="space-y-2">
              <div class="flex justify-between items-end">
                <p class="text-[9px] uppercase tracking-[0.15em] text-[#737c7f] font-bold">Macro 宏观因子</p>
                <p class="text-sm font-black text-[#2b3437]">{{ (result.edb_data.macro_total || 0).toFixed(3) }}</p>
              </div>
              <div class="w-full h-1 bg-[#dbe4e7] overflow-hidden rounded-full flex" :class="(result.edb_data.macro_total || 0) < 0 ? 'justify-end' : ''">
                <div class="h-full" :class="(result.edb_data.macro_total || 0) < 0 ? 'bg-[#9f403d]' : 'bg-[#46607f]'" :style="{ width: Math.min(Math.abs(result.edb_data.macro_total || 0) * 50, 100) + '%' }"></div>
              </div>
            </div>
            
            <div class="space-y-2">
              <div class="flex justify-between items-end">
                <p class="text-[9px] uppercase tracking-[0.15em] text-[#737c7f] font-bold">Valuation 估值水平</p>
                <p class="text-sm font-black text-[#2b3437]">{{ (result.edb_data.valuation_total || 0).toFixed(3) }}</p>
              </div>
              <div class="w-full h-1 bg-[#dbe4e7] overflow-hidden rounded-full flex" :class="(result.edb_data.valuation_total || 0) < 0 ? 'justify-end' : ''">
                <div class="h-full" :class="(result.edb_data.valuation_total || 0) < 0 ? 'bg-[#9f403d]' : 'bg-[#46607f]/60'" :style="{ width: Math.min(Math.abs(result.edb_data.valuation_total || 0) * 50, 100) + '%' }"></div>
              </div>
            </div>
            
            <div class="space-y-2">
              <div class="flex justify-between items-end">
                <p class="text-[9px] uppercase tracking-[0.15em] text-[#737c7f] font-bold">Risk 风险偏好</p>
                <p class="text-sm font-black" :class="(result.edb_data.risk_total || 0) < 0 ? 'text-[#9f403d]' : 'text-[#2b3437]'">{{ (result.edb_data.risk_total || 0).toFixed(3) }}</p>
              </div>
              <div class="w-full h-1 bg-[#dbe4e7] overflow-hidden rounded-full flex" :class="(result.edb_data.risk_total || 0) < 0 ? 'justify-end' : ''">
                <div class="h-full" :class="(result.edb_data.risk_total || 0) < 0 ? 'bg-[#9f403d]' : 'bg-[#46607f]/40'" :style="{ width: Math.min(Math.abs(result.edb_data.risk_total || 0) * 50, 100) + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
        <p class="text-[9px] text-[#737c7f] leading-relaxed italic opacity-60">
            * 引擎实时捕捉全球宏观经济变动、货币政策及市场风险溢价。
        </p>
      </section>

      <!-- Section 2: 宏观象限定位 -->
      <section class="flex-[2] bg-[#ffffff] p-6 rounded-xl border border-[#f1f4f6] shadow-sm flex flex-col justify-between">
        <div class="flex items-center gap-3 mb-6">
          <span class="material-symbols-outlined text-[#46607f] text-xl" data-icon="explore">explore</span>
          <h2 class="text-sm font-bold tracking-widest text-[#2b3437] uppercase whitespace-nowrap">宏观象限定位</h2>
        </div>
        
        <div class="bg-[#46607f]/5 px-6 py-4 rounded-xl border border-[#46607f]/10 mb-6">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <span class="material-symbols-outlined text-[#46607f] text-3xl" data-icon="potted_plant">{{ qColors[result.quadrant.current]?.icon || 'potted_plant' }}</span>
              <div>
                <h3 class="text-xl font-black text-[#46607f] tracking-tight">{{ result.quadrant.label }}</h3>
                <p class="text-[9px] text-[#46607f]/60 font-bold tracking-[0.3em] uppercase mt-0.5">{{ result.quadrant.description }}</p>
              </div>
            </div>
            <div class="text-[9px] font-bold text-[#46607f]/80 bg-[#46607f]/5 px-3 py-1.5 rounded border border-[#46607f]/5 uppercase tracking-widest hidden sm:block">
              {{ result.quadrant.markov_regime || 'Current Regime' }}
            </div>
          </div>
        </div>
        
        <div class="space-y-4">
          <!-- Positive Assets -->
          <div class="flex items-center gap-4" v-if="result.quadrant.best_assets && result.quadrant.best_assets.length > 0">
            <div class="flex items-center gap-2 w-28 flex-none">
              <span class="w-2 h-2 rounded-full bg-[#46607f]"></span>
              <span class="text-[9px] font-black tracking-widest text-[#2b3437] uppercase">利好 POSITIVE</span>
            </div>
            <div class="flex flex-wrap items-center gap-3 bg-[#f1f4f6]/40 px-3 py-2.5 rounded-lg border border-[#eaeff1] flex-grow">
              <template v-for="(asset, index) in result.quadrant.best_assets" :key="asset">
                <div class="flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[#46607f] text-base" data-icon="trending_up">trending_up</span>
                  <span class="text-xs font-bold text-[#2b3437]">{{ asset }}</span>
                </div>
                <div class="w-px h-3 bg-[#dbe4e7]/50" v-if="index < result.quadrant.best_assets.length - 1"></div>
              </template>
            </div>
          </div>
          
          <!-- Pressure Assets -->
          <div class="flex items-center gap-4" v-if="result.quadrant.worst_assets && result.quadrant.worst_assets.length > 0">
            <div class="flex items-center gap-2 w-28 flex-none">
              <span class="w-2 h-2 rounded-full bg-[#9f403d]"></span>
              <span class="text-[9px] font-black tracking-widest text-[#2b3437] uppercase">承压 PRESSURE</span>
            </div>
            <div class="flex flex-wrap items-center gap-3 bg-[#f1f4f6]/40 px-3 py-2.5 rounded-lg border border-[#eaeff1] flex-grow">
              <template v-for="(asset, index) in result.quadrant.worst_assets" :key="asset">
                <div class="flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[#9f403d] text-base" data-icon="trending_down">trending_down</span>
                  <span class="text-xs font-bold text-[#2b3437]">{{ asset }}</span>
                </div>
                <div class="w-px h-3 bg-[#dbe4e7]/50" v-if="index < result.quadrant.worst_assets.length - 1"></div>
              </template>
            </div>
          </div>
        </div>
      </section>

      <!-- Section 3: 配置模式 -->
      <section class="flex-1 bg-[#e3e9ec] p-6 rounded-xl border border-[#eaeff1] flex flex-col">
        <div class="flex items-center gap-3 mb-4">
          <span class="material-symbols-outlined text-[#737c7f]" data-icon="tune">tune</span>
          <h2 class="text-sm font-bold tracking-widest text-[#2b3437] uppercase whitespace-nowrap">配置模式</h2>
        </div>
        <div class="bg-[#46607f]/10 px-4 py-3 rounded-lg flex gap-3 mb-6">
          <span class="material-symbols-outlined text-[#46607f] text-sm flex-none" data-icon="info">info</span>
          <p class="text-[10px] font-bold text-[#46607f] leading-tight">
            根据风险约束与收益目标匹配配置策略。
          </p>
        </div>
        
        <div class="flex flex-col gap-4 flex-grow">
          <!-- Scenario A - Highlighted -->
          <div v-if="result.scenario_type === 'A'" class="bg-[#ffffff] p-4 rounded-lg border-2 border-[#46607f] ring-2 ring-[#46607f]/5">
            <div class="flex justify-between items-center mb-2">
              <span class="text-[9px] font-black text-[#46607f] tracking-[0.2em] uppercase">情景 A — 活动建议</span>
              <span class="material-symbols-outlined text-[#46607f] text-lg" data-icon="check_circle" style="font-variation-settings: 'FILL' 1;">check_circle</span>
            </div>
            <p class="text-[11px] text-[#2b3437] font-semibold leading-relaxed">
              波动率约束可满足目标收益，已生成 3 套平滑配置方案（进取/稳健/防守）。
            </p>
          </div>
          
          <!-- Scenario B - Highlighted -->
          <div v-else class="bg-[#ffffff] p-4 rounded-lg border-2 border-[#9f403d] ring-2 ring-[#9f403d]/5">
            <div class="flex justify-between items-center mb-2">
              <span class="text-[9px] font-black text-[#9f403d] tracking-[0.2em] uppercase">情景 B — 自动防御</span>
              <span class="material-symbols-outlined text-[#9f403d] text-lg" data-icon="warning_amber" style="font-variation-settings: 'FILL' 1;">warning_amber</span>
            </div>
            <p class="text-[11px] text-[#2b3437] font-semibold leading-relaxed">
              波动率无法覆盖高收益目标。已降级为 1 套稳健配置，以波动率为锚点。
            </p>
          </div>

          <!-- Inactive Scenarios (Visual only) -->
          <div class="flex-grow flex flex-col gap-2">
            <div v-if="result.scenario_type !== 'A'" class="bg-[#ffffff]/50 p-3 px-4 rounded-lg border border-transparent flex items-center justify-between opacity-70">
              <span class="text-[10px] font-bold text-[#737c7f] uppercase">情景 A</span>
              <span class="material-symbols-outlined text-[#737c7f]/30 text-sm" data-icon="radio_button_unchecked">radio_button_unchecked</span>
            </div>
            <div v-if="result.scenario_type !== 'B'" class="bg-[#ffffff]/50 p-3 px-4 rounded-lg border border-transparent flex items-center justify-between opacity-70">
              <span class="text-[10px] font-bold text-[#737c7f] uppercase">情景 B</span>
              <span class="material-symbols-outlined text-[#737c7f]/30 text-sm" data-icon="radio_button_unchecked">radio_button_unchecked</span>
            </div>
            <div class="bg-[#ffffff]/50 p-3 px-4 rounded-lg border border-transparent flex items-center justify-between opacity-70">
              <span class="text-[10px] font-bold text-[#737c7f] uppercase">情景 C</span>
              <span class="material-symbols-outlined text-[#737c7f]/30 text-sm" data-icon="radio_button_unchecked">radio_button_unchecked</span>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- ═══ 因子传导链条 ═══ -->
    <details v-if="result && result.transmission_chain && result.transmission_chain.length" class="zx-card fade-in group" style="margin-bottom:24px;">
      <summary class="zx-card-title cursor-pointer flex items-center gap-2 outline-none select-none list-none [&::-webkit-details-marker]:hidden hover:text-primary transition-colors" style="margin-bottom:0;">
        <span class="material-symbols-outlined text-primary text-xl">account_tree</span>
        因子传导链条 (点击展开底仓生成依据)
        <span class="material-symbols-outlined ml-auto text-on-surface-variant transition-transform group-open:rotate-180">expand_more</span>
      </summary>
      <div class="mt-6 pt-6 border-t border-surface-variant flex flex-col gap-6 relative px-2 pb-4">
        <!-- Connecting Line behind steps -->
        <div class="absolute left-[38px] top-8 bottom-8 w-0.5 bg-[#e3e9ec] z-0"></div>

        <!-- Step 1: EDB 底座 -->
        <div class="relative z-10 flex gap-5 items-start">
          <div class="w-14 h-14 rounded-full bg-primary-container text-primary flex items-center justify-center font-bold text-xl shrink-0 border-4 border-[#ffffff] shadow-sm">1</div>
          <div class="flex-grow bg-[#f8f9fa] rounded-xl p-5 border border-outline-variant/20 shadow-sm">
            <h4 class="font-bold text-[#1a1c1e] text-base mb-3 flex items-center gap-2">
              <span class="material-symbols-outlined text-[18px]">database</span>
              EDB 宏观多因子底座合成
            </h4>
            <div class="flex flex-wrap gap-4 text-sm mt-4">
              <div class="flex flex-col bg-white px-4 py-3 rounded-lg border border-outline-variant/10 min-w-[120px] shadow-sm">
                <span class="text-[#737c7f] text-xs mb-1">宏观经济得分</span>
                <span class="font-bold text-[#1a1c1e] text-lg">{{ result.edb_data.macro_total }}</span>
              </div>
              <div class="flex flex-col bg-white px-4 py-3 rounded-lg border border-outline-variant/10 min-w-[120px] shadow-sm">
                <span class="text-[#737c7f] text-xs mb-1">估值水位得分</span>
                <span class="font-bold text-[#1a1c1e] text-lg">{{ result.edb_data.valuation_total }}</span>
              </div>
              <div class="flex flex-col bg-white px-4 py-3 rounded-lg border border-outline-variant/10 min-w-[120px] shadow-sm">
                <span class="text-[#737c7f] text-xs mb-1">风险动能得分</span>
                <span class="font-bold text-[#1a1c1e] text-lg">{{ result.edb_data.risk_total }}</span>
              </div>
              <div class="flex items-center ml-2 text-primary font-bold bg-primary-container/30 px-4 rounded-lg">
                <span class="material-symbols-outlined mr-2">arrow_forward</span>
                综合判定: <span class="ml-2 text-[#001529]">{{ result.edb_data.composite_score }} ({{ result.edb_data.market_state }})</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 2: 宏观动能解码 -->
        <div class="relative z-10 flex gap-5 items-start">
          <div class="w-14 h-14 rounded-full bg-primary-container text-primary flex items-center justify-center font-bold text-xl shrink-0 border-4 border-[#ffffff] shadow-sm">2</div>
          <div class="flex-grow bg-[#f8f9fa] rounded-xl p-5 border border-outline-variant/20 shadow-sm">
            <h4 class="font-bold text-[#1a1c1e] text-base mb-3 flex items-center gap-2">
              <span class="material-symbols-outlined text-[18px]">hub</span>
              六大基本面因子解码
            </h4>
            <div class="flex flex-wrap gap-3 mt-4">
              <div v-for="item in result.transmission_chain" :key="item.factor"
                class="flex flex-col items-center justify-center p-3 rounded-lg min-w-[110px] shadow-sm transition-transform hover:-translate-y-1"
                :style="{ background: item.score > 0 ? '#FEF2F2' : '#F0FDF4', border: '1px solid ' + (item.score > 0 ? '#FECACA' : '#BBF7D0') }">
                <span class="text-xs font-semibold" style="color:#191c1d">{{ item.factor }}</span>
                <span class="text-xl font-bold mt-1" :style="{ color: item.score > 0 ? '#DC2626' : '#16A34A' }">
                  {{ item.score > 0 ? '+' : '' }}{{ item.score }}
                </span>
                <span class="text-[10px] text-[#94a3b8] mt-1 bg-white/60 px-2 py-0.5 rounded-full" v-if="item.regime_modifier !== 1">HMM 修正: ×{{ item.regime_modifier }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 3: 象限映射及交叉验证 -->
        <div class="relative z-10 flex gap-5 items-start">
          <div class="w-14 h-14 rounded-full bg-primary-container text-primary flex items-center justify-center font-bold text-xl shrink-0 border-4 border-[#ffffff] shadow-sm">3</div>
          <div class="flex-grow bg-[#f8f9fa] rounded-xl p-5 border border-outline-variant/20 shadow-sm">
            <h4 class="font-bold text-[#1a1c1e] text-base mb-3 flex items-center gap-2">
              <span class="material-symbols-outlined text-[18px]">explore</span>
              美林象限映射与隐马尔可夫验证
            </h4>
            <div class="flex flex-col gap-3 text-sm mt-4">
              <div class="flex items-center gap-3">
                <span class="px-3 py-1 bg-surface-container rounded text-[#43474d] text-xs font-medium">算法测算定位</span>
                <strong class="text-[#001529] text-base">{{ result.quadrant.label }}</strong>
                <span class="text-[#74777d] text-xs ml-2">{{ result.quadrant.description }}</span>
              </div>
              <div class="flex items-center gap-3">
                <span class="px-3 py-1 bg-surface-container rounded text-[#43474d] text-xs font-medium">HMM 量价验证</span>
                <strong class="text-primary text-base">{{ result.quadrant.markov_regime }}</strong>
                <span class="text-primary text-xs ml-2 px-2 py-0.5 bg-primary-container/50 rounded-full font-bold">可信度: {{ ((result.quadrant.markov_confidence || 0) * 100).toFixed(1) }}%</span>
              </div>
              <div class="mt-3 flex gap-6 p-4 bg-white rounded-lg border border-outline-variant/20 shadow-sm">
                <div class="flex-1">
                  <div class="text-xs text-[#74777d] mb-2 font-medium">利好大类资产 (做多推荐)</div>
                  <div class="font-bold text-[#10B981] text-[15px] leading-relaxed">{{ (result.quadrant.best_assets || []).join('、') }}</div>
                </div>
                <!-- Line separator -->
                <div class="w-px bg-outline-variant/20 self-stretch"></div>
                <div class="flex-1">
                  <div class="text-xs text-[#74777d] mb-2 font-medium">承压大类资产 (规避或低配)</div>
                  <div class="font-bold text-[#EF4444] text-[15px] leading-relaxed">{{ (result.quadrant.worst_assets || []).join('、') }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 4: 极值求解约束 -->
        <div class="relative z-10 flex gap-5 items-start">
          <div class="w-14 h-14 rounded-full bg-[#1a1c1e] text-white flex items-center justify-center font-bold text-xl shrink-0 border-4 border-[#ffffff] shadow-md">4</div>
          <div class="flex-grow bg-[#f8f9fa] rounded-xl p-5 border border-outline-variant/20 shadow-sm">
            <h4 class="font-bold text-[#1a1c1e] text-base mb-3 flex items-center gap-2">
              <span class="material-symbols-outlined text-[18px]">tune</span>
              最小波动率约束优化 (Min-Vol Engine)
            </h4>
            <div class="text-sm text-[#43474d] mb-4 leading-relaxed">
              根据资金侧预期与市场真实环境，基于《核心146池》协方差矩阵执行二次规划优化。
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="p-4 bg-white rounded-lg border-l-4 border-l-primary shadow-sm hover:shadow transition-shadow">
                <div class="text-xs text-[#737c7f] mb-2 font-medium uppercase tracking-wider">目标函数</div>
                <div class="font-bold text-[#1a1c1e] leading-snug">锁定预期目标收益率界限<br/><span class="text-primary font-black">求解组合全局方差最小化权重</span></div>
              </div>
              <div class="p-4 bg-white rounded-lg border-l-4 shadow-sm" :class="result.scenario_type === 'A' ? 'border-l-[#10B981]' : 'border-l-[#F59E0B]'">
                <div class="text-xs text-[#737c7f] mb-2 font-medium uppercase tracking-wider">引擎判定结论</div>
                <div class="font-bold text-[#1a1c1e] leading-snug" v-if="result.scenario_type === 'A'">
                  <span class="text-[#10B981] mr-1">■ 情景 A:</span>
                  当前波动约束下可实现收益要求，平台已生成进取、稳健、防守三套平滑方案。
                </div>
                <div class="font-bold text-[#1a1c1e] leading-snug" v-else>
                  <span class="text-[#F59E0B] mr-1">■ 情景 B:</span>
                  当前波动率难以完全覆盖预设的高收益目标，引擎已自动降级防守，仅产出单一稳健解。
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </details>

    <!-- ═══ 资产配置方案对比组 (每个方案一列) ═══ -->
    <section v-if="result && result.scenarios" class="grid grid-cols-1 md:grid-cols-3 gap-8 fade-in mb-8">
      <!-- Dynamic scenario rendering -->
      <div v-for="(sc, idx) in result.scenarios" :key="sc.name"
           class="flex flex-col bg-[#f1f4f6] rounded-xl overflow-hidden relative transition-all duration-300"
           :class="{ 'ring-2 ring-[#46607f] shadow-lg scale-[1.02]': idx === activeScenarioIndex }"
           style="cursor:pointer;"
           @click="activeScenarioIndex = idx">
        
        <!-- Highlight Indicator -->
        <div class="absolute top-0 left-0 w-full h-1 bg-[#46607f]" v-if="idx === activeScenarioIndex"></div>

        <div class="p-8 pb-4 flex flex-col gap-6">
          <div class="flex justify-between items-start">
            <div class="flex flex-col gap-1">
              <span class="text-[10px] tracking-widest uppercase text-[#586064] flex items-center gap-1">
                Model Portfolio
                <span v-if="sc.kpi._source !== 'wind'" class="text-[#9f403d] font-bold tracking-widest bg-[#fe8983]/20 px-1.5 py-0.5 rounded-full inline-block ml-2 text-[8px]" title="Wind不可用，波动率/回撤/夏普显示为N/A">⚠️ Wind数据缺失</span>
              </span>
              <h2 class="text-2xl font-bold tracking-tight text-[#2b3437]">
                <span class="text-sm mr-1" v-if="idx === activeScenarioIndex">🌟</span>{{ sc.name }}
              </h2>
            </div>
            
            <span v-if="sc.name.includes('进取')" class="bg-[#46607f] text-[#f5f7ff] text-[10px] px-2 py-1 rounded-full font-bold tracking-widest uppercase">AGGRESSIVE</span>
            <span v-else-if="sc.name.includes('稳健')" class="bg-[#d1e4fb] text-[#415366] text-[10px] px-2 py-1 rounded-full font-bold tracking-widest uppercase border border-[#abb3b7]/20">BALANCE</span>
            <span v-else class="bg-[#dbe4e7] text-[#586064] text-[10px] px-2 py-1 rounded-full font-bold tracking-widest uppercase">CONSERVATIVE</span>
          </div>
          
          <div class="grid grid-cols-2 gap-y-8 mt-4">
            <div class="flex flex-col">
              <span class="text-[10px] tracking-widest uppercase text-[#737c7f] mb-1">预期年化收益率</span>
              <span class="text-3xl font-bold tracking-tighter text-[#DC2626]">{{ sc.kpi.ann_return_pct }}%</span>
            </div>
            <div class="flex flex-col">
              <span class="text-[10px] tracking-widest uppercase text-[#737c7f] mb-1">年化波动率</span>
              <span class="text-3xl font-bold tracking-tighter text-[#2b3437]">{{ sc.kpi.ann_vol_pct === 'N/A' ? 'N/A' : sc.kpi.ann_vol_pct + '%' }}</span>
            </div>
            <div class="flex flex-col">
              <span class="text-[10px] tracking-widest uppercase text-[#737c7f] mb-1">最大回撤</span>
              <span class="text-3xl font-bold tracking-tighter text-[#16A34A]">{{ sc.kpi.max_drawdown_pct === 'N/A' ? 'N/A' : sc.kpi.max_drawdown_pct + '%' }}</span>
            </div>
            <div class="flex flex-col">
              <span class="text-[10px] tracking-widest uppercase text-[#737c7f] mb-1">夏普比率</span>
              <span class="text-3xl font-bold tracking-tighter text-[#2b3437]">{{ sc.kpi.sharpe === 'N/A' ? 'N/A' : sc.kpi.sharpe }}</span>
            </div>
          </div>
        </div>
        
        <div class="bg-[#ffffff] m-4 rounded-lg p-6 flex flex-col gap-4 overflow-hidden">
          <div class="flex justify-between items-center border-b border-[#e3e9ec] pb-2">
            <span class="text-[10px] font-bold tracking-widest uppercase text-[#586064]">
              底层基金明细 
              <span class="text-[#46607f]">({{ sc.allocations.filter(a => a.weight_pct > 0.1).length }}只)</span>
            </span>
            <span class="text-[10px] font-bold tracking-widest uppercase text-[#586064]">权重 / 金额</span>
          </div>
          <ul class="flex flex-col gap-4 max-h-[180px] overflow-y-auto pr-2 custom-scrollbar">
            <li class="flex justify-between items-center" v-for="alloc in sc.allocations.filter(a => a.weight_pct > 0.1)" :key="alloc.code">
              <div class="flex flex-col w-3/5">
                <span class="text-sm font-semibold text-[#2b3437] truncate" :title="alloc.name">{{ alloc.name }}</span>
                <div class="flex items-center gap-2 mt-0.5">
                  <span class="text-[10px] text-[#737c7f] tracking-wider uppercase truncate">{{ alloc.category }}</span>
                  <span class="text-[9px] text-[#737c7f]/60 font-mono">{{ alloc.code }}</span>
                </div>
              </div>
              <div class="text-right w-2/5 flex flex-col items-end">
                <div class="text-sm font-bold text-[#2b3437]">{{ alloc.weight_pct }}%</div>
                <div class="text-[10px] text-[#737c7f] font-mono">¥{{ Number(alloc.amount).toLocaleString() }}</div>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <!-- ═══ 深度基资料展示 (核心精选 10 支) ═══ -->
    <div v-if="recommendedProfiles.length > 0" class="zx-profiles-section fade-in">
      <div class="zx-card">
        <div class="zx-card-title zxp-flex-title">
          <span>📊 核心精选深度资料</span>
          <span class="zx-profiles-sub">基于【{{ recommendedScenario.name }}】的底层穿透</span>
        </div>
        
        <div class="zx-profiles-grid">
          <div v-for="profile in recommendedProfiles" :key="profile.code" class="zx-profile-card hover:-translate-y-1 hover:shadow-xl transition-all duration-300 cursor-pointer" @click="openFundPage(profile.code)" title="点击前往天天基金网查看此基金详情">
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

    <!-- 空状态与主引擎入口 -->
    <div v-if="!result" class="flex-grow flex flex-col items-center justify-center min-h-[600px] relative overflow-hidden fade-in">
      <!-- Background Tonal Shifts -->
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full blur-[120px] pointer-events-none" style="background: rgba(209, 228, 255, 0.15);"></div>
      <!-- Centered Content Wrapper -->
      <div class="relative z-10 flex flex-col items-center max-w-2xl text-center">
        <!-- Abstract Factor Visual -->
        <div class="mb-14 relative w-64 h-48 flex items-center justify-center visual-float">
          <div class="grid grid-cols-3 gap-x-8 gap-y-6">
            <span class="text-3xl font-extrabold tracking-tighter" style="color: #B8860B; opacity: 0.9;">GDP</span>
            <span class="text-xl font-light self-end" style="color: #78866B; opacity: 0.7;">CPI</span>
            <span class="text-2xl font-semibold" style="color: #5F9EA0; opacity: 0.8;">IR</span>
            <span class="text-lg font-medium" style="color: #BC8F8F; opacity: 0.6;">FX</span>
            <span class="text-4xl font-bold tracking-tighter" style="color: #1a1c1e; opacity: 0.9;">PMI</span>
            <span class="text-xl font-light self-center" style="color: #778899; opacity: 0.7;">M2</span>
            <span class="text-sm font-bold uppercase" style="color: #A0522D; opacity: 0.5;">PPI</span>
            <span class="text-2xl font-light" style="color: #556B2F; opacity: 0.8;">NFP</span>
            <span class="text-lg font-semibold" style="color: #483D8B; opacity: 0.6;">VIX</span>
          </div>
          <!-- Decorative surrounding elements -->
          <div class="absolute inset-0 -m-6 border rounded-3xl" style="border-color: rgba(115, 124, 127, 0.05);"></div>
          <div class="absolute inset-4 border rounded-2xl" style="border-color: rgba(115, 124, 127, 0.1);"></div>
        </div>
        <!-- Typography Stack -->
        <div class="space-y-8 flex flex-col items-center">
          <!-- Action Button replaces the Heading Text -->
          <button @click="runMacroAllocation" :disabled="loading" class="px-12 text-[#f5f7ff] rounded-2xl shadow-2xl transition-all active:scale-[0.98] group relative overflow-hidden flex flex-col items-center justify-center min-w-[520px] py-10 border border-white/5 bg-gradient-to-br from-[#1e3a8a] to-[#172554] disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none" style="box-shadow: 0 25px 50px -12px rgba(30, 58, 138, 0.35);">
            <div class="relative z-10 flex flex-col items-center gap-4">
              <!-- All-Weather Season Icons -->
              <div class="flex items-center gap-6 opacity-90">
                <span class="material-symbols-outlined text-lg text-emerald-400/70" data-icon="potted_plant">potted_plant</span>
                <span class="material-symbols-outlined text-lg text-amber-400/70" data-icon="wb_sunny">wb_sunny</span>
                <span class="material-symbols-outlined text-lg text-orange-400/70" data-icon="eco">eco</span>
                <span class="material-symbols-outlined text-lg text-blue-300/70" data-icon="ac_unit">ac_unit</span>
              </div>
              <span class="text-3xl md:text-3xl tracking-tight leading-tight uppercase font-bold flex items-center gap-4">
                <span v-if="loading" class="zx-spinner" style="border-width: 3px; width: 26px; height: 26px; border-top-color: white; border-right-color: rgba(255,255,255,0.2); border-bottom-color: rgba(255,255,255,0.2); border-left-color: rgba(255,255,255,0.2);"></span>
                {{ loading ? '引擎运转中...' : '全天候宏观象限配置引擎' }}
              </span>
            </div>
            <div class="absolute inset-0 bg-gradient-to-tr from-black/20 to-white/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </button>
          <p class="text-lg text-[#586064] font-light leading-relaxed max-w-xl mx-auto opacity-80" v-if="!loading">
            点击上方引擎，系统将自动从 <span class="text-[#2b3437] font-medium">EDB</span> 获取宏观因子数据，定位当前经济周期象限，并生成配置方案。
          </p>
        </div>
        <!-- Terminal-style Loading Indicators -->
        <div v-if="loading" class="mt-12 flex items-center gap-10 fade-in">
          <div class="flex items-center gap-3">
            <div class="w-1.5 h-1.5 rounded-full bg-[#1a1c1e] animate-pulse"></div>
            <span class="text-[10px] uppercase tracking-[0.2em] font-bold text-[#586064]/80">Data Connectivity</span>
          </div>
          <div class="flex items-center gap-3">
            <div class="w-1.5 h-1.5 rounded-full bg-[#1a1c1e] animate-pulse" style="animation-delay: 0.2s"></div>
            <span class="text-[10px] uppercase tracking-[0.2em] font-bold text-[#586064]/80">Quadrant Analysis</span>
          </div>
          <div class="flex items-center gap-3">
            <div class="w-1.5 h-1.5 rounded-full bg-[#1a1c1e] animate-pulse" style="animation-delay: 0.4s"></div>
            <span class="text-[10px] uppercase tracking-[0.2em] font-bold text-[#586064]/80">Strategy Synthesis</span>
          </div>
        </div>
      </div>
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

function openFundPage(code) {
  if (!code) return;
  const match = code.match(/\d{6}/);
  if (match) {
    window.open(`https://fund.eastmoney.com/${match[0]}.html`, '_blank');
  }
}
</script>

<style scoped>
.material-symbols-outlined {
    font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
}
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
  background: #1e3a8a;
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
  box-shadow: 0 4px 14px rgba(30,58,138,0.3);
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

/* ─── Empty State replaced by main engine ─── */
.visual-float {
  animation: float 6s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
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
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
}
@media (max-width: 1400px) {
  .zx-profiles-grid { grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }
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

/* ── 数据来源标注 ── */
.zx-kpi-source {
  margin-top: 8px;
  text-align: center;
}
.zx-source-badge {
  display: inline-block;
  font-size: 10px;
  padding: 3px 10px;
  border-radius: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
}
.zx-source-wind {
  background: #EFF6FF;
  color: #1D4ED8;
  border: 1px solid #BFDBFE;
}
.zx-source-na {
  background: #FEF3C7;
  color: #92400E;
  border: 1px solid #FDE68A;
}

/* ── 自定义滚动条 ── */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #dbe4e7;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #abb3b7;
}
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: #dbe4e7 transparent;
}

.fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
</style>
