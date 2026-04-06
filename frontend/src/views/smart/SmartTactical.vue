<template>
  <div class="relative min-h-[calc(100vh-64px)] bg-[#f8f9fa] text-[#2b3437] selection:bg-[#d1e4ff] selection:text-[#395472] overflow-hidden w-full font-body">
    <!-- Background Texture Layer -->
    <div class="absolute inset-0 dot-grid opacity-[0.25] pointer-events-none z-0"></div>

    <main class="relative z-10 max-w-[1440px] mx-auto px-8 md:px-16 py-8 md:py-12 flex flex-col h-full">
      <!-- Title Section -->
      <header class="flex flex-col gap-4 max-w-3xl shrink-0 w-full mb-2">
        <div class="flex items-start justify-between w-full">
          <h1 class="font-black tracking-tighter text-[#2b3437] leading-none text-4xl md:text-5xl m-0" style="font-family: 'Inter', sans-serif;">
            战术配置
          </h1>
          <div v-if="hasBaseAllocation && covBuiltAt" class="cov-badge shrink-0">
            <span class="cov-icon">📊</span>
            <span>协方差矩阵 · {{ covBuiltAt }}</span>
          </div>
        </div>
        <div class="flex items-center gap-4 mt-1">
           <span class="h-[1px] w-12 bg-[#46607f]/30"></span>
           <p class="text-xs md:text-sm font-label tracking-[0.2em] uppercase text-[#586064] m-0">
               TACTICAL ADJUSTMENT • 基于稳健底仓进行战术偏移
           </p>
        </div>
      </header>

      <!-- Main Content Card -->
      <section v-if="!hasBaseAllocation" class="relative flex-grow mt-12 w-full glass-card rounded-xl flex items-center justify-center border border-[#abb3b7]/15 overflow-hidden refined-shadow min-h-[400px]">
        <!-- Atmospheric Depth Background -->
        <div class="absolute inset-0 bg-gradient-to-br from-[#f1f4f6]/20 to-transparent pointer-events-none"></div>
        <!-- Locked State (Central Focus) -->
        <div class="relative z-10 flex flex-col items-center text-center max-w-lg px-8 py-16">
          <!-- Icon with Signature Gradient -->
          <div class="mb-10 p-8 bg-[#f1f4f6]/50 backdrop-blur-sm rounded-full border border-white/40 shadow-inner flex items-center justify-center">
            <span class="material-symbols-outlined text-7xl lock-icon-gradient" data-icon="lock" style="font-variation-settings: 'FILL' 1;">
               lock
            </span>
          </div>
          <!-- Main Status Message -->
          <h2 class="text-3xl md:text-4xl font-bold tracking-tight text-[#2b3437] mb-6 m-0">
             请先完成宏观底仓配置
          </h2>
          <!-- Supporting Instruction Text -->
          <p class="text-[#586064] text-lg leading-relaxed font-normal m-0 pb-10">
            战术调仓需要基于稳健配置的底仓权重进行偏移。<br class="hidden md:block"/>
            请先在「宏观配置」页面完成一键配置。
          </p>
        </div>
        <!-- Design Detail: Subtle Decorative Accents -->
        <div class="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#46607f]/10 to-transparent"></div>
      </section>

      <div v-else class="mt-8 relative z-10 pb-16 w-full">
        <!-- ═══════════════════════════════════════════ -->
        <!-- ACTION BAR: Big Button + Report Upload      -->
        <!-- ═══════════════════════════════════════════ -->
        <div class="w-full flex flex-col md:flex-row items-center gap-4 mt-2 mb-8">
          <!-- Primary Blue Tactical Action Button -->
          <button 
            class="group flex-1 w-full md:w-auto h-20 bg-gradient-to-br from-[#46607f] to-[#3a5472] flex items-center justify-between px-10 transition-all active:scale-[0.98] cursor-pointer rounded-xl border-none shadow-md overflow-hidden"
            :class="{ 'opacity-50 cursor-not-allowed': isRunning }"
            :disabled="isRunning"
            @click="executeOneClick"
          >
            <div class="flex items-center gap-6">
              <span v-if="isRunning" class="material-symbols-outlined text-[#f5f7ff] text-3xl animate-spin" style="font-variation-settings: 'FILL' 1;">refresh</span>
              <span v-else class="material-symbols-outlined text-[#f5f7ff] text-3xl" data-icon="swords" style="font-variation-settings: 'FILL' 1;">swords</span>
              <span class="text-2xl font-bold tracking-tight text-[#f5f7ff] m-0">
                {{ isRunning ? pipelineStatus : '一键战术配置' }}
              </span>
            </div>
            <span class="material-symbols-outlined text-[#f5f7ff]/40 group-hover:translate-x-1 transition-transform" data-icon="chevron_right" v-if="!isRunning">
                chevron_right
            </span>
          </button>

          <!-- Secondary Attachment Button -->
          <label 
            class="group w-full md:w-56 h-20 bg-[#ffffff] flex items-center justify-center gap-4 transition-all active:scale-[0.98] cursor-pointer border border-transparent hover:border-[#abb3b7]/40 rounded-xl shadow-sm"
            :class="{ 'opacity-50 cursor-not-allowed': isRunning }"
          >
            <input
              type="file"
              multiple
              accept=".pdf,.txt"
              class="hidden"
              :disabled="isRunning"
              @change="handleFileUpload"
              ref="fileInput"
            />
            <span class="material-symbols-outlined text-[#46607f] text-2xl" data-icon="attach_file" style="font-variation-settings: 'FILL' 1;">
                attach_file
            </span>
            <span class="text-lg font-semibold tracking-wide text-[#2b3437] m-0">
                添加研报
            </span>
          </label>
        </div>

      <!-- Uploaded Files List -->
      <div v-if="uploadedFiles.length" class="file-list">
        <div v-for="(f, idx) in uploadedFiles" :key="idx" class="file-chip">
          <span class="file-name">📄 {{ f.name }}</span>
          <button class="file-remove" @click="removeFile(idx)" :disabled="isRunning">✕</button>
        </div>
      </div>

      <!-- High-end Glassmorphism Loading Container -->
      <div v-if="isRunning" class="relative w-full max-w-xl mx-auto mt-12 flex justify-center">
        <div class="relative w-full">
          <div class="bg-white/40 backdrop-blur-2xl rounded-2xl flex flex-col items-center shadow-[0_40px_80px_-20px_rgba(0,0,0,0.06)] border border-white/60 gap-4 p-16 w-full pulse-animation z-10 relative">
            <!-- KPI Status Section -->
            <div class="flex flex-col items-center space-y-6">
              <!-- Subtle Animated KPI Icon -->
              <div class="text-center">
                <p class="font-headline text-2xl font-medium tracking-tight text-[#2b3437] m-0 flex items-center justify-center gap-3">
                    <span class="material-symbols-outlined text-[#46607f] animate-spin" style="font-variation-settings: 'FILL' 1;">refresh</span>
                    {{ pipelineStatus || 'KPI 计算中...' }}
                </p>
                <p class="font-label text-xs uppercase tracking-[0.2em] text-[#737c7f] mt-3 m-0">
                    PROCESSING INSTITUTIONAL METRICS
                </p>
              </div>
            </div>
            <!-- Minimalist Animated Line -->
            <div class="w-48 h-[1px] bg-[#abb3b7]/30 rounded-full shimmer-line mt-4"></div>
          </div>
          <!-- Subtle background accents for depth -->
          <div class="absolute -top-12 -right-12 w-48 h-48 bg-[#46607f]/5 rounded-full blur-[80px] -z-10 pointer-events-none"></div>
          <div class="absolute -bottom-16 -left-16 w-64 h-64 bg-[#d1e4fb]/20 rounded-full blur-[100px] -z-10 pointer-events-none"></div>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="errorMsg" class="error-banner">
        <span>⚠️ {{ errorMsg }}</span>
        <button @click="errorMsg = ''" class="error-close">✕</button>
      </div>

      <!-- ═══════════════════════════════════════════ -->
      <!-- RESULTS DASHBOARD                           -->
      <!-- ═══════════════════════════════════════════ -->
      <template v-if="result">
        <!-- KPI Comparison Cards -->
        <!-- KPI Comparison Cards -->
        <header class="mb-10 mt-8">
          <h1 class="text-4xl md:text-5xl font-extrabold tracking-tighter text-[#2b3437] mb-2 m-0" style="font-family: 'Inter', sans-serif;">KPI 对比看板</h1>
        </header>

        <div class="grid gap-8 items-stretch mb-16" :class="result.report_result ? 'grid-cols-1 md:grid-cols-3' : 'grid-cols-1 md:grid-cols-2 max-w-4xl mx-auto'">
          <!-- Card 1: 底仓 -->
          <div class="glass-card p-10 rounded-xl flex flex-col justify-between shadow-[0_30px_60px_-15px_rgba(43,52,55,0.06)] border border-white/40">
            <div>
              <div class="flex items-center justify-between mb-8">
                <h2 class="text-2xl font-bold tracking-tight text-[#2b3437] m-0" style="font-family: 'Inter', sans-serif;">底仓</h2>
                <span class="material-symbols-outlined text-[#abb3b7]" data-icon="account_balance_wallet">account_balance_wallet</span>
              </div>
              <p class="text-sm font-label tracking-[0.05em] uppercase text-[#737c7f] mb-12 m-0" style="margin-top: -1rem;">稳健配置基准</p>
              
              <div class="space-y-8">
                <div class="flex flex-col">
                  <span class="text-[0.65rem] font-bold tracking-[0.1em] uppercase text-[#abb3b7] mb-1">年化收益率</span>
                  <span class="text-4xl font-extrabold tracking-tight text-[#2b3437] m-0" style="font-family: 'Inter', sans-serif;">{{ fmtPct(result.base_kpi?.ann_return_pct) }}</span>
                </div>
                
                <div class="grid grid-cols-1 gap-6 pt-4 border-t border-[#eaeff1]">
                  <div class="flex justify-between items-baseline">
                    <span class="text-xs font-label text-[#737c7f] uppercase tracking-wider">年化波动率</span>
                    <span class="text-lg font-medium text-[#2b3437] m-0">{{ fmtPct(result.base_kpi?.ann_vol_pct) }}</span>
                  </div>
                  <div class="flex justify-between items-baseline">
                    <span class="text-xs font-label text-[#737c7f] uppercase tracking-wider">最大回撤</span>
                    <span class="text-lg font-medium text-[#2b3437] m-0">{{ fmtPct(result.base_kpi?.max_drawdown_pct) }}</span>
                  </div>
                  <div class="flex justify-between items-baseline">
                    <span class="text-xs font-label text-[#737c7f] uppercase tracking-wider">夏普比率</span>
                    <span class="text-lg font-bold text-[#2b3437] m-0">{{ fmtNum(result.base_kpi?.sharpe) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Card 2: 新闻 -->
          <div class="relative bg-[#ffffff] p-10 rounded-xl flex flex-col justify-between shadow-[0_40px_80px_-20px_rgba(70,96,127,0.12)] border border-[#46607f]/10">
            <div class="absolute -top-3 left-10 px-4 py-1 bg-[#46607f] text-[#f5f7ff] text-[10px] font-bold tracking-widest uppercase rounded-sm">新闻</div>
            <div>
              <div class="flex items-center justify-between mb-8 mt-2">
                <h2 class="text-2xl font-bold tracking-tight text-[#2b3437] m-0" style="font-family: 'Inter', sans-serif;">新闻资讯调仓</h2>
                <span class="material-symbols-outlined text-[#46607f]" data-icon="newspaper">newspaper</span>
              </div>
              <p class="text-sm font-label tracking-[0.05em] uppercase text-[#46607f] font-medium mb-12 m-0" style="margin-top: -1rem;">超额收益信号</p>
              
              <div class="space-y-8">
                <div class="flex flex-col">
                  <span class="text-[0.65rem] font-bold tracking-[0.1em] uppercase text-[#abb3b7] mb-1">年化收益率</span>
                  <div class="flex items-center gap-3">
                    <span class="text-4xl font-extrabold tracking-tight m-0" style="font-family: 'Inter', sans-serif;" :class="Number(result.news_result?.kpi?.ann_return_pct) > Number(result.base_kpi?.ann_return_pct) + 0.01 ? 'text-[#9f403d]' : 'text-[#2b3437]'">
                      {{ fmtPct(result.news_result?.kpi?.ann_return_pct) }}
                    </span>
                    <span v-if="Number(result.news_result?.kpi?.ann_return_pct) > Number(result.base_kpi?.ann_return_pct) + 0.01" class="material-symbols-outlined text-[#9f403d] text-lg" data-icon="trending_up">trending_up</span>
                  </div>
                </div>
                
                <div class="grid grid-cols-1 gap-6 pt-4 border-t border-[#eaeff1]">
                  <div class="flex justify-between items-baseline">
                    <span class="text-xs font-label text-[#737c7f] uppercase tracking-wider">年化波动率</span>
                    <span class="text-lg font-medium text-[#2b3437] m-0">{{ fmtPct(result.news_result?.kpi?.ann_vol_pct) }}</span>
                  </div>
                  <div class="flex justify-between items-baseline">
                    <span class="text-xs font-label text-[#737c7f] uppercase tracking-wider">最大回撤</span>
                    <span class="text-lg font-medium m-0" :class="Number(result.news_result?.kpi?.max_drawdown_pct) > Number(result.base_kpi?.max_drawdown_pct) + 0.01 ? 'text-[#435d7c]' : 'text-[#2b3437]'">
                      {{ fmtPct(result.news_result?.kpi?.max_drawdown_pct) }}
                    </span>
                  </div>
                  <div class="flex justify-between items-baseline">
                    <span class="text-xs font-label text-[#737c7f] uppercase tracking-wider">夏普比率</span>
                    <span class="text-lg font-bold m-0" :class="Number(result.news_result?.kpi?.sharpe) > Number(result.base_kpi?.sharpe) + 0.01 ? 'text-[#9f403d]' : 'text-[#2b3437]'">
                      {{ fmtNum(result.news_result?.kpi?.sharpe) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Card 3: 研报 -->
          <div v-if="result.report_result" class="glass-card p-10 rounded-xl flex flex-col justify-between shadow-[0_30px_60px_-15px_rgba(43,52,55,0.06)] border border-white/40 relative">
            <div class="absolute -top-3 left-10 px-4 py-1 bg-[#e67e22] text-[#ffffff] text-[10px] font-bold tracking-widest uppercase rounded-sm">研报</div>
            <div>
              <div class="flex items-center justify-between mb-8 mt-2">
                <h2 class="text-2xl font-bold tracking-tight text-[#2b3437] m-0" style="font-family: 'Inter', sans-serif;">研报资讯调仓</h2>
                <span class="material-symbols-outlined text-[#abb3b7]" data-icon="description">description</span>
              </div>
              <p class="text-sm font-label tracking-[0.05em] uppercase text-[#737c7f] mb-12 m-0" style="margin-top: -1rem;">机构洞察基准</p>
              
              <div class="space-y-8">
                <div class="flex flex-col">
                  <span class="text-[0.65rem] font-bold tracking-[0.1em] uppercase text-[#abb3b7] mb-1">年化收益率</span>
                  <div class="flex items-center gap-3">
                    <span class="text-4xl font-extrabold tracking-tight m-0" style="font-family: 'Inter', sans-serif;" :class="Number(result.report_result?.kpi?.ann_return_pct) > Number(result.base_kpi?.ann_return_pct) + 0.01 ? 'text-[#9f403d]' : 'text-[#2b3437]'">
                      {{ fmtPct(result.report_result?.kpi?.ann_return_pct) }}
                    </span>
                    <span v-if="Number(result.report_result?.kpi?.ann_return_pct) > Number(result.base_kpi?.ann_return_pct) + 0.01" class="material-symbols-outlined text-[#9f403d] text-lg" data-icon="trending_up">trending_up</span>
                  </div>
                </div>
                
                <div class="grid grid-cols-1 gap-6 pt-4 border-t border-[#eaeff1]">
                  <div class="flex justify-between items-baseline">
                    <span class="text-xs font-label text-[#737c7f] uppercase tracking-wider">年化波动率</span>
                    <span class="text-lg font-medium text-[#2b3437] m-0">{{ fmtPct(result.report_result?.kpi?.ann_vol_pct) }}</span>
                  </div>
                  <div class="flex justify-between items-baseline">
                    <span class="text-xs font-label text-[#737c7f] uppercase tracking-wider">最大回撤</span>
                    <span class="text-lg font-medium m-0" :class="Number(result.report_result?.kpi?.max_drawdown_pct) > Number(result.base_kpi?.max_drawdown_pct) + 0.01 ? 'text-[#435d7c]' : 'text-[#2b3437]'">
                      {{ fmtPct(result.report_result?.kpi?.max_drawdown_pct) }}
                    </span>
                  </div>
                  <div class="flex justify-between items-baseline">
                    <span class="text-xs font-label text-[#737c7f] uppercase tracking-wider">夏普比率</span>
                    <span class="text-lg font-bold m-0" :class="Number(result.report_result?.kpi?.sharpe) > Number(result.base_kpi?.sharpe) + 0.01 ? 'text-[#9f403d]' : 'text-[#2b3437]'">
                      {{ fmtNum(result.report_result?.kpi?.sharpe) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ═══════════════════════════════════════════ -->
        <!-- REBALANCE DETAIL TABLES                     -->
        <!-- ═══════════════════════════════════════════ -->
        <header class="mb-4 mt-16 flex items-center gap-3">
          <span class="material-symbols-outlined text-2xl text-[#2b3437]">list_alt</span>
          <h1 class="text-2xl font-bold tracking-tight text-[#2b3437] m-0" style="font-family: 'Inter', sans-serif;">调仓明细</h1>
        </header>

        <div class="grid gap-12 mb-16 items-start" :class="result.report_result ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1 max-w-4xl mx-auto'">
          <!-- News-Based Rebalancing (Left) -->
          <section>
            <div class="mb-6 flex items-center justify-between border-b border-[#dbe4e7] pb-4">
              <h2 class="text-xl font-semibold text-[#46607f] flex items-center gap-2 m-0">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">newspaper</span>
                新闻资讯调仓
              </h2>
              <span class="text-[10px] font-bold tracking-widest text-[#586064] uppercase px-2 py-1 bg-[#eaeff1] rounded m-0">System Generated</span>
            </div>
            
            <div v-if="result.news_result?.news_digest" class="bg-[#f8f9fa] border border-[#eaeff1] rounded p-4 mb-6 text-xs text-[#586064] leading-relaxed">
              {{ result.news_result.news_digest.slice(0, 150) }}{{ result.news_result.news_digest.length > 150 ? '...' : '' }}
            </div>

            <div class="overflow-x-auto">
              <table class="w-full text-left border-collapse min-w-[600px]">
                <thead>
                  <tr class="text-[11px] font-bold text-[#586064] uppercase tracking-[0.05em]">
                    <th class="py-4 pr-4 border-b border-[#eaeff1]">基金</th>
                    <th class="py-4 px-4 text-right border-b border-[#eaeff1]">原权重%</th>
                    <th class="py-4 px-4 text-right border-b border-[#eaeff1]">新权重%</th>
                    <th class="py-4 px-4 text-right border-b border-[#eaeff1]">偏移%</th>
                    <th class="py-4 px-4 text-right border-b border-[#eaeff1]">金额调整</th>
                    <th class="py-4 pl-4 border-b border-[#eaeff1]">调仓理由</th>
                  </tr>
                </thead>
                <tbody class="text-sm divide-y divide-[#eaeff1]">
                  <tr v-for="row in (result.news_result?.rebalance_detail || [])" :key="row.code" class="hover:bg-[#f1f4f6] transition-colors group">
                    <td class="py-5 pr-4">
                      <div class="font-medium text-[#2b3437]">{{ row.code }}</div>
                      <div class="text-[11px] text-[#586064] mt-1">{{ row.name || '--' }}</div>
                    </td>
                    <td class="py-5 px-4 text-right text-[#586064]">{{ row.old_weight_pct?.toFixed(2) }}</td>
                    <td class="py-5 px-4 text-right text-[#586064]">{{ row.new_weight_pct?.toFixed(2) }}</td>
                    <td class="py-5 px-4 text-right font-semibold" :class="deltaColor(row.delta_pct)">{{ row.delta_pct > 0 ? '+' : '' }}{{ row.delta_pct?.toFixed(2) }}</td>
                    <td class="py-5 px-4 text-right font-semibold" :class="deltaColor(row.delta_amount)">{{ fmtAmount(row.delta_amount) }}</td>
                    <td class="py-5 pl-4 text-xs italic opacity-90" :class="deltaColor(row.delta_pct)">{{ row.reason || getReason(row.delta_pct) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <!-- Report-Based Rebalancing (Right) -->
          <section v-if="result.report_result">
            <div class="mb-6 flex items-center justify-between border-b border-[#dbe4e7] pb-4">
              <h2 class="text-xl font-semibold text-[#46607f] flex items-center gap-2 m-0">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">analytics</span>
                研报资讯调仓
              </h2>
              <span class="text-[10px] font-bold tracking-widest text-[#586064] uppercase px-2 py-1 bg-[#eaeff1] rounded m-0">Analyst Verified</span>
            </div>
            
            <div class="overflow-x-auto">
              <table class="w-full text-left border-collapse min-w-[600px]">
                <thead>
                  <tr class="text-[11px] font-bold text-[#586064] uppercase tracking-[0.05em]">
                    <th class="py-4 pr-4 border-b border-[#eaeff1]">基金</th>
                    <th class="py-4 px-4 text-right border-b border-[#eaeff1]">原权重%</th>
                    <th class="py-4 px-4 text-right border-b border-[#eaeff1]">新权重%</th>
                    <th class="py-4 px-4 text-right border-b border-[#eaeff1]">偏移%</th>
                    <th class="py-4 px-4 text-right border-b border-[#eaeff1]">金额调整</th>
                    <th class="py-4 pl-4 border-b border-[#eaeff1]">调仓理由</th>
                  </tr>
                </thead>
                <tbody class="text-sm divide-y divide-[#eaeff1]">
                  <tr v-for="row in (result.report_result?.rebalance_detail || [])" :key="row.code" class="hover:bg-[#f1f4f6] transition-colors group">
                    <td class="py-5 pr-4">
                      <div class="font-medium text-[#2b3437]">{{ row.code }}</div>
                      <div class="text-[11px] text-[#586064] mt-1">{{ row.name || '--' }}</div>
                    </td>
                    <td class="py-5 px-4 text-right text-[#586064]">{{ row.old_weight_pct?.toFixed(2) }}</td>
                    <td class="py-5 px-4 text-right text-[#586064]">{{ row.new_weight_pct?.toFixed(2) }}</td>
                    <td class="py-5 px-4 text-right font-semibold" :class="deltaColor(row.delta_pct)">{{ row.delta_pct > 0 ? '+' : '' }}{{ row.delta_pct?.toFixed(2) }}</td>
                    <td class="py-5 px-4 text-right font-semibold" :class="deltaColor(row.delta_amount)">{{ fmtAmount(row.delta_amount) }}</td>
                    <td class="py-5 pl-4 text-xs italic opacity-90" :class="deltaColor(row.delta_pct)">{{ row.reason || getReason(row.delta_pct) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>

        <!-- ═══════════════════════════════════════════ -->
        <!-- RADAR CHARTS: Factor Scores + Asset Views   -->
        <!-- ═══════════════════════════════════════════ -->
        <div class="section-title">🎯 宏观因子雷达图 & 资产观点</div>

        <div class="radar-grid" :class="{ 'has-report': !!result.report_result }">
          <!-- News Radar -->
          <div class="radar-panel">
            <h4 class="radar-title">📡 新闻因子视图</h4>
            <div class="radar-container">
              <svg viewBox="-120 -120 240 240" class="radar-svg">
                <!-- Radar Web -->
                <g>
                  <polygon v-for="r in [100, 75, 50, 25]" :key="'w'+r"
                    :points="hexPoints(r)" fill="none" :stroke="r === 100 ? '#CBD5E1' : '#F1F5F9'" stroke-width="1" />
                  <line v-for="i in 6" :key="'l'+i"
                    x1="0" y1="0"
                    :x2="Math.cos((i-1)*Math.PI/3 - Math.PI/2)*100"
                    :y2="Math.sin((i-1)*Math.PI/3 - Math.PI/2)*100"
                    stroke="#E2E8F0" stroke-width="1" />
                </g>
                <!-- Radar Polygon -->
                <polygon :points="polyPoints(newsFactorScores)" fill="rgba(59,130,246,0.15)" stroke="#3B82F6" stroke-width="2" />
                <!-- Radar Labels -->
                <g>
                  <text v-for="(label, i) in factorLabels" :key="label"
                    :x="Math.cos(i*Math.PI/3 - Math.PI/2)*115"
                    :y="Math.sin(i*Math.PI/3 - Math.PI/2)*115"
                    text-anchor="middle" dominant-baseline="central"
                    fill="#475569" font-size="10" font-weight="600">{{ label }}</text>
                </g>
              </svg>
            </div>
            <div class="asset-views-section">
              <h5>8 大类资产观点</h5>
              <div class="asset-bar-list">
                <div v-for="(val, asset) in (result.news_result?.asset_views || {})" :key="asset" class="asset-bar-row">
                  <span class="asset-name">{{ asset }}</span>
                  <div class="asset-bar-track">
                    <div
                      class="asset-bar-fill"
                      :class="val > 0.05 ? 'bullish' : val < -0.05 ? 'bearish' : 'neutral'"
                      :style="{ width: Math.min(Math.abs(val) * 100, 100) + '%', [val >= 0 ? 'left' : 'right']: '50%' }"
                    ></div>
                  </div>
                  <span class="asset-val" :class="val > 0.05 ? 'bullish' : val < -0.05 ? 'bearish' : ''">
                    {{ val > 0 ? '+' : '' }}{{ (val * 100).toFixed(1) }}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Report Radar (conditional) -->
          <div v-if="result.report_result" class="radar-panel">
            <h4 class="radar-title">📄 研报因子视图</h4>
            <div class="radar-container">
              <svg viewBox="-120 -120 240 240" class="radar-svg">
                <!-- Radar Web -->
                <g>
                  <polygon v-for="r in [100, 75, 50, 25]" :key="'w'+r"
                    :points="hexPoints(r)" fill="none" :stroke="r === 100 ? '#CBD5E1' : '#F1F5F9'" stroke-width="1" />
                  <line v-for="i in 6" :key="'l'+i"
                    x1="0" y1="0"
                    :x2="Math.cos((i-1)*Math.PI/3 - Math.PI/2)*100"
                    :y2="Math.sin((i-1)*Math.PI/3 - Math.PI/2)*100"
                    stroke="#E2E8F0" stroke-width="1" />
                </g>
                <!-- Radar Polygon -->
                <polygon :points="polyPoints(reportFactorScores)" fill="rgba(245,158,11,0.15)" stroke="#F59E0B" stroke-width="2" />
                <!-- Radar Labels -->
                <g>
                  <text v-for="(label, i) in factorLabels" :key="label"
                    :x="Math.cos(i*Math.PI/3 - Math.PI/2)*115"
                    :y="Math.sin(i*Math.PI/3 - Math.PI/2)*115"
                    text-anchor="middle" dominant-baseline="central"
                    fill="#475569" font-size="10" font-weight="600">{{ label }}</text>
                </g>
              </svg>
            </div>
            <div class="asset-views-section">
              <h5>8 大类资产观点</h5>
              <div class="asset-bar-list">
                <div v-for="(val, asset) in (result.report_result?.asset_views || {})" :key="asset" class="asset-bar-row">
                  <span class="asset-name">{{ asset }}</span>
                  <div class="asset-bar-track">
                    <div
                      class="asset-bar-fill"
                      :class="val > 0.05 ? 'bullish' : val < -0.05 ? 'bearish' : 'neutral'"
                      :style="{ width: Math.min(Math.abs(val) * 100, 100) + '%', [val >= 0 ? 'left' : 'right']: '50%' }"
                    ></div>
                  </div>
                  <span class="asset-val" :class="val > 0.05 ? 'bullish' : val < -0.05 ? 'bearish' : ''">
                    {{ val > 0 ? '+' : '' }}{{ (val * 100).toFixed(1) }}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useSmartStore } from '../../store/smartSelection'
import { zxTacticalOneClick } from '../../api/smart'

const store = useSmartStore()

// ── State ──
const isRunning = ref(false)
const currentStep = ref(0)
const pipelineStatus = ref('')
const errorMsg = ref('')
const uploadedFiles = ref([])
const result = ref(null)
const covBuiltAt = ref('')

// ── Computed ──
const hasBaseAllocation = computed(() => {
  return store.zx_macroResult?.scenarios?.length > 0
})

const progressPct = computed(() => {
  if (!isRunning.value) return 0
  const maxSteps = uploadedFiles.value.length ? 3 : 2
  return Math.min(100, (currentStep.value / maxSteps) * 100)
})

const factorLabels = ['经济增长', '通胀商品', '利率环境', '信用扩张', '海外环境', '市场情绪']

const newsFactorScores = computed(() => {
  const factors = result.value?.news_result?.factor_scores || {}
  return factorLabels.map(l => {
    const raw = factors[l] ?? 0
    return Math.max(0, Math.min(1, (raw + 1) / 2))  // normalize [-1,1] → [0,1]
  })
})

const reportFactorScores = computed(() => {
  const factors = result.value?.report_result?.factor_scores || {}
  return factorLabels.map(l => {
    const raw = factors[l] ?? 0
    return Math.max(0, Math.min(1, (raw + 1) / 2))
  })
})

// ── File Management ──
function handleFileUpload(e) {
  const files = Array.from(e.target.files)
  uploadedFiles.value.push(...files)
  e.target.value = ''
}

function removeFile(idx) {
  uploadedFiles.value.splice(idx, 1)
}

// ── Execute Pipeline ──
async function executeOneClick() {
  if (isRunning.value) return
  isRunning.value = true
  errorMsg.value = ''
  result.value = null
  currentStep.value = 1
  pipelineStatus.value = '📡 新闻资讯调仓执行中...'

  try {
    const weights = store.zx_selectedWeights
    if (!weights || Object.keys(weights).length === 0) {
      throw new Error('选中底仓权重为空，请先完成宏观配置')
    }

    const fd = new FormData()
    fd.append('base_allocation', JSON.stringify(weights))
    fd.append('capital', store.zx_capital)
    fd.append('max_vol', store.zx_maxVol)
    fd.append('period', store.zx_period)
    if (store.zx_targetReturn !== undefined) {
      fd.append('target_ret_pct', store.zx_targetReturn)
    }

    for (const file of uploadedFiles.value) {
      fd.append('reports', file)
    }

    if (uploadedFiles.value.length) {
      setTimeout(() => {
        if (isRunning.value) {
          currentStep.value = 2
          pipelineStatus.value = '📄 研报调仓执行中...'
        }
      }, 15000)
    }

    setTimeout(() => {
      if (isRunning.value) {
        currentStep.value = uploadedFiles.value.length ? 3 : 2
        pipelineStatus.value = '📊 KPI 计算中...'
      }
    }, uploadedFiles.value.length ? 30000 : 15000)

    const resp = await zxTacticalOneClick(fd)
    result.value = resp.data
    covBuiltAt.value = resp.data?.cov_built_at || ''
    store.setTacticalOneclickResult(resp.data)
    currentStep.value = 4
  } catch (err) {
    console.error('[TacticalOneClick]', err)
    errorMsg.value = err?.response?.data?.detail || err.message || '一键战术配置失败'
  } finally {
    isRunning.value = false
    pipelineStatus.value = ''
  }
}

// ── Formatters ──
function fmtPct(val) {
  if (val === undefined || val === null || val === 'N/A') return 'N/A'
  return Number(val).toFixed(2) + '%'
}
function fmtNum(val) {
  if (val === undefined || val === null || val === 'N/A') return 'N/A'
  return Number(val).toFixed(2)
}
function fmtAmount(val) {
  if (val === undefined || val === null) return '—'
  const prefix = val > 0 ? '+' : ''
  return prefix + Number(val).toLocaleString('zh-CN', { maximumFractionDigits: 0 })
}
function deltaColor(val) {
  if (val > 0.01) return 'text-[#E74C3C]'
  if (val < -0.01) return 'text-[#27AE60]'
  return ''
}
function deltaClass(newVal, baseVal) {
  if (newVal === 'N/A' || baseVal === 'N/A') return ''
  const diff = Number(newVal) - Number(baseVal)
  if (diff > 0.01) return 'text-[#E74C3C] font-semibold'
  if (diff < -0.01) return 'text-[#27AE60] font-semibold'
  return ''
}
function getReason(delta) {
  if (delta === undefined || delta === null) return '维持当前基准'
  const d = Number(delta)
  if (d >= 1.0) return "强劲动能增配"
  if (d > 0) return "上调乐观配置"
  if (d <= -1.0) return "宏观风险规避"
  if (d < 0) return "下调谨慎配置"
  return "维持当前基准"
}

// ── Radar Helpers ──
function hexPoints(r) {
  return Array.from({length: 6}, (_, i) => {
    const angle = i * Math.PI / 3 - Math.PI / 2
    return `${Math.cos(angle)*r},${Math.sin(angle)*r}`
  }).join(' ')
}

function polyPoints(scores) {
  if (!scores || scores.length < 6) return ''
  return scores.map((s, i) => {
    const r = s * 90
    const angle = i * Math.PI / 3 - Math.PI / 2
    return `${Math.cos(angle)*r},${Math.sin(angle)*r}`
  }).join(' ')
}
</script>

<style scoped>
/* ── Tailwind Custom Utilities ── */
.lock-icon-gradient {
  background: linear-gradient(135deg, #FFB74D 0%, #F57C00 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.dot-grid {
  background-image: radial-gradient(#abb3b7 1px, transparent 1px);
  background-size: 24px 24px;
  background-position: center;
}
.glass-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.5);
}
.refined-shadow {
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.02),
    0 10px 15px -3px rgba(0, 0, 0, 0.03),
    0 20px 40px -10px rgba(0, 0, 0, 0.04);
}
.font-body { font-family: 'Inter', sans-serif; }

.tactical-page {
  padding: 24px 32px;
  max-width: 1400px;
  margin: 0 auto;
  color: #334155;
}

/* ── Header ── */
.tac-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 28px;
}
.tac-title {
  font-size: 26px;
  font-weight: 700;
  color: #0F172A;
  margin: 0 0 4px 0;
  letter-spacing: -0.5px;
}
.tac-subtitle {
  font-size: 13px;
  color: #64748B;
  letter-spacing: 0.3px;
}
.cov-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #64748B;
  background: #F8FAFC;
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid #E2E8F0;
}
.cov-icon { font-size: 14px; }

/* ── Guard Card ── */
.guard-card {
  background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
  border: 1px solid #E2E8F0;
  border-radius: 16px;
  padding: 48px;
  text-align: center;
  box-shadow: 0 4px 15px rgba(0,0,0,0.02);
}
.guard-icon { font-size: 48px; margin-bottom: 16px; }
.guard-card h3 {
  color: #0F172A;
  font-size: 18px;
  margin: 0 0 8px 0;
}
.guard-card p {
  color: #64748B;
  font-size: 14px;
  margin: 0;
}

/* ── Action Bar ── */
.action-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.btn-oneclick {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 18px 32px;
  background: linear-gradient(135deg, #3B82F6 0%, #2563EB 50%, #1D4ED8 100%);
  color: #fff;
  border: none;
  border-radius: 14px;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3);
  letter-spacing: 1px;
}
.btn-oneclick:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(59, 130, 246, 0.45);
}
.btn-oneclick:active:not(:disabled) {
  transform: translateY(0);
}
.btn-oneclick:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.btn-oneclick.is-running {
  background: linear-gradient(135deg, #1E40AF 0%, #1E3A8A 100%);
}
.btn-icon { font-size: 24px; }
.btn-spinner {
  width: 22px;
  height: 22px;
  border: 3px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg) } }

.btn-upload {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 18px 24px;
  background: #FFFFFF;
  border: 1px dashed #CBD5E1;
  border-radius: 14px;
  color: #64748B;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}
.btn-upload:hover:not(.disabled) {
  border-color: #3B82F6;
  color: #3B82F6;
  background: rgba(59, 130, 246, 0.04);
}
.btn-upload.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-upload input { display: none; }
.upload-icon { font-size: 18px; }

/* ── File List ── */
.file-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}
.file-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 20px;
  font-size: 12px;
  color: #475569;
}
.file-remove {
  background: none;
  border: none;
  color: #64748B;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  line-height: 1;
}
.file-remove:hover { color: #EF4444; }

/* ── Pipeline Progress ── */
.pipeline-progress {
  margin-bottom: 24px;
  animation: fadeIn 0.3s ease;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(-8px) } to { opacity: 1; transform: translateY(0) } }

.progress-track {
  width: 100%;
  height: 4px;
  background: #E2E8F0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 12px;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3B82F6, #60A5FA);
  border-radius: 4px;
  transition: width 0.5s ease;
}
.progress-steps {
  display: flex;
  justify-content: space-between;
}
.step {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748B;
  transition: color 0.3s;
}
.step.active { color: #2563EB; }
.step.done { color: #059669; }
.step.skipped { color: #94A3B8; opacity: 0.5; }
.step-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #CBD5E1;
  transition: background 0.3s;
}
.step.active .step-dot { background: #3B82F6; box-shadow: 0 0 8px rgba(59,130,246,0.3); }
.step.done .step-dot { background: #10B981; }

/* ── Error Banner ── */
.error-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 10px;
  color: #DC2626;
  font-size: 14px;
  margin-bottom: 20px;
}
.error-close {
  background: none;
  border: none;
  color: #DC2626;
  cursor: pointer;
  font-size: 16px;
}

/* ── Section Title ── */
.section-title {
  font-size: 17px;
  font-weight: 700;
  color: #0F172A;
  margin: 32px 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #E2E8F0;
  letter-spacing: 0.3px;
}

/* ── KPI Grid ── */
.kpi-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.kpi-grid.has-report {
  grid-template-columns: 1fr 1fr 1fr;
}
.kpi-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.02);
  transition: transform 0.2s, box-shadow 0.2s;
}
.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.06);
}
.kpi-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.kpi-badge {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.kpi-badge.base { background: #F1F5F9; color: #475569; }
.kpi-badge.news { background: rgba(59,130,246,0.1); color: #2563EB; }
.kpi-badge.report { background: rgba(245,158,11,0.1); color: #D97706; }
.kpi-label {
  font-size: 13px;
  color: #64748B;
}
.kpi-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.kpi-item {
  display: flex;
  flex-direction: column;
}
.kpi-value {
  font-size: 22px;
  font-weight: 800;
  color: #0F172A;
  font-family: 'DM Mono', 'JetBrains Mono', monospace;
}
.kpi-desc {
  font-size: 11px;
  color: #64748B;
  margin-top: 2px;
}
.delta-up { color: #DC2626 !important; }
.delta-down { color: #059669 !important; }

/* ── Detail Grid ── */
.detail-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}
.detail-grid.has-report {
  grid-template-columns: 1fr 1fr;
}
.detail-panel {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 14px;
  padding: 20px;
  overflow-x: auto;
  box-shadow: 0 2px 10px rgba(0,0,0,0.02);
}
.detail-header {
  font-size: 15px;
  font-weight: 600;
  color: #0F172A;
  margin: 0 0 12px 0;
}
.detail-digest {
  font-size: 12px;
  color: #475569;
  line-height: 1.6;
  margin-bottom: 12px;
  padding: 10px 14px;
  background: #F8FAFC;
  border-radius: 8px;
  border: 1px solid #F1F5F9;
}
.table-wrap { overflow-x: auto; }
.rebal-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.rebal-table thead th {
  padding: 8px 12px;
  text-align: left;
  background: #F8FAFC;
  color: #64748B;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid #E2E8F0;
}
.rebal-table tbody td {
  padding: 8px 12px;
  border-bottom: 1px solid #F1F5F9;
  color: #334155;
  font-family: 'DM Mono', monospace;
  font-size: 12px;
}
.rebal-table tbody tr:hover {
  background: #F8FAFC;
}
.code-cell {
  font-weight: 600;
  color: #0F172A;
}
.code-text {
  font-size: 12px;
  line-height: 1.2;
}
.name-text {
  font-size: 11px;
  color: #64748B;
  font-weight: 400;
  margin-top: 4px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* ── Radar Grid ── */
.radar-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}
.radar-grid.has-report {
  grid-template-columns: 1fr 1fr;
}
.radar-panel {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.02);
}
.radar-title {
  font-size: 15px;
  font-weight: 600;
  color: #0F172A;
  margin: 0 0 16px 0;
  text-align: center;
}
.radar-container {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}
.radar-svg {
  width: 240px;
  height: 240px;
}
.asset-views-section h5 {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin: 0 0 12px 0;
}
.asset-bar-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.asset-bar-row {
  display: grid;
  grid-template-columns: 80px 1fr 60px;
  align-items: center;
  gap: 10px;
}
.asset-name {
  font-size: 12px;
  color: #475569;
  text-align: right;
  font-weight: 500;
}
.asset-bar-track {
  height: 8px;
  background: #F1F5F9;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}
.asset-bar-fill {
  position: absolute;
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}
.asset-bar-fill.bullish { background: linear-gradient(90deg, #EF4444, #F87171); }
.asset-bar-fill.bearish { background: linear-gradient(90deg, #10B981, #34D399); }
.asset-bar-fill.neutral { background: #94A3B8; }
.asset-val {
  font-size: 12px;
  font-family: 'DM Mono', monospace;
  color: #64748B;
  text-align: right;
}
.asset-val.bullish { color: #DC2626; }
.asset-val.bearish { color: #059669; }
.asset-val.bearish { color: #059669; }

/* ── Custom Animations ── */
.shimmer-line {
  position: relative;
  overflow: hidden;
}
.shimmer-line::after {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(70, 96, 127, 0.4), transparent);
  animation: shimmer 2.5s infinite ease-in-out;
}
@keyframes shimmer {
  100% { left: 100%; }
}
@keyframes pulse-soft {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(0.98); }
}
.pulse-animation {
  animation: pulse-soft 3s infinite ease-in-out;
}

/* ── Responsive ── */
@media (max-width: 900px) {
  .kpi-grid, .kpi-grid.has-report,
  .detail-grid, .detail-grid.has-report,
  .radar-grid, .radar-grid.has-report {
    grid-template-columns: 1fr;
  }
  .action-bar { flex-direction: column; }
  .btn-oneclick { font-size: 16px; padding: 16px 24px; }
}
</style>
