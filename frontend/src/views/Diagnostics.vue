<template>
  <div style="min-height:100vh;background:var(--bg-page);">
    <!-- Main Flex Container -->
    <div style="display:flex;">
      <!-- Left Sidebar — Faithful to Reference Design -->
      <aside class="smart-sidebar">
        <!-- Sidebar Header -->
        <header style="display:flex; justify-content:space-between; align-items:center; margin-bottom:40px; padding:0 4px;">
          <h1 style="font-family:'Manrope',sans-serif; font-weight:800; font-size:18px; letter-spacing:-0.5px; color:#001529; margin:0;">粤财信托资产配置智能分析</h1>
          <span class="material-symbols-outlined" style="color:#001529; cursor:pointer;">notifications</span>
        </header>

        <!-- Portfolio Hero -->
        <section style="margin-bottom:32px; padding:0 4px;">
          <p style="font-family:'Inter',sans-serif; font-size:11px; color:#43474d; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:8px;">资产总额</p>
          <div style="display:flex; align-items:baseline; gap:8px;">
            <span style="font-family:'Manrope',sans-serif; font-weight:800; font-size:32px; color:#191C1D;">¥{{ holdingsTotal > 0 ? formatNumber(holdingsTotal) : '0' }}</span>
            <span v-if="avgMonthlyPl !== 0" 
              :style="{ color: avgMonthlyPl >= 0 ? '#0c5216' : '#93000a', background: avgMonthlyPl >= 0 ? '#acf4a4' : '#ffdad6', padding:'2px 8px', borderRadius:'9999px', fontSize:'12px', fontWeight:700 }">
              {{ avgMonthlyPl > 0 ? '+' : '' }}{{ avgMonthlyPl.toFixed(1) }}%
            </span>
            <span v-else style="color:#74777d; background:#e1e3e4; padding:2px 8px; border-radius:9999px; font-size:12px; font-weight:700;">0.0%</span>
          </div>
        </section>

        <!-- Nav Cards -->
        <div style="display:flex;flex-direction:column;gap:12px;margin-bottom:32px;">
          <div
            v-for="(page, i) in subPageCards" :key="i"
            @click="activePage = i"
            class="ref-card"
            :class="{ 'active': activePage === i }"
          >
            <div class="ref-icon-box">
              <span class="material-symbols-outlined ref-icon">{{ page.icon }}</span>
            </div>
            <div style="flex:1;">
              <div style="display:flex;align-items:center;gap:8px;">
                <div class="ref-card-title">{{ page.label }}</div>
                <span v-if="page.pro" style="font-size:10px; font-weight:700; border:1px solid currentColor; padding:2px 6px; border-radius:9999px; opacity:0.8;">PRO</span>
              </div>
              <div class="ref-card-sub">{{ page.en }}</div>
            </div>
            <span class="material-symbols-outlined" style="color:currentColor; opacity:0.4;">chevron_right</span>
          </div>
        </div>

        <!-- Market Trends Panel -->
        <section style="background:#f3f4f5; border-radius:12px; padding:24px; margin-top:auto;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
            <h4 style="font-family:'Manrope',sans-serif; font-weight:800; font-size:14px; color:#191c1d; margin:0;">市场行情</h4>
          </div>
          <div v-if="marketQuotes.length === 0" style="text-align:center;color:#43474d;font-size:12px;padding:20px 0;">
            ⏳ 加载中...
          </div>
          <div style="display:flex; flex-direction:column; gap:12px;">
            <div v-for="q in marketQuotes" :key="q.code" style="background:#ffffff; padding:12px; border-radius:8px; display:flex; justify-content:space-between; align-items:center;">
              <div style="width:72px;">
                <p style="font-size:14px; font-weight:800; color:#191c1d; margin:0; white-space:nowrap;">{{ q.name }}</p>
                <p style="font-size:10px; color:#43474d; margin:0; margin-top:2px;">{{ q.en }}</p>
              </div>
              <div style="flex:1;"></div>
              <div style="text-align:right;">
                <p :style="{ margin:0, fontWeight:800, fontSize:'14px', color: (q.pct_chg ?? 0) >= 0 ? '#ba1a1a' : '#0c5216' }">
                  {{ q.close != null ? q.close.toLocaleString() : '—' }}
                </p>
                <p :style="{ margin:0, fontWeight:600, fontSize:'10px', color: (q.pct_chg ?? 0) >= 0 ? '#ba1a1a' : '#0c5216' }">
                  {{ q.pct_chg != null ? ((q.pct_chg > 0 ? '+' : '') + q.pct_chg.toFixed(2) + '%') : '—' }}
                </p>
              </div>
            </div>
          </div>
        </section>
      </aside>

      <!-- Main Area -->
      <main style="flex:1;padding:24px 32px;height:100vh;overflow-y:auto;">
        
        <!-- Global Actions Context Line -->
        <div style="display:flex;justify-content:flex-end;margin-bottom:24px;">
           <button @click="$router.push('/')"
             style="display:flex;align-items:center;gap:8px;padding:8px 20px;background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;box-shadow:0 4px 12px rgba(0,0,0,0.04);cursor:pointer;transition:all 0.3s;font-size:13px;font-weight:700;color:#001529;font-family:'Manrope',sans-serif;"
           >
             <span class="material-symbols-outlined" style="font-size:18px;">arrow_back</span>
             返回大厅
           </button>
        </div>

        <!-- Page 1: 持仓分析 -->
        <div v-if="activePage === 0" class="fade-in">
          <!-- Bento-style Upload Container -->
          <div class="bento-upload-container">
            <!-- Main Upload Area -->
            <div class="relative cursor-pointer"
                 @dragover.prevent="dragActive=true"
                 @dragleave="dragActive=false"
                 @drop.prevent="onDrop"
                 @click="$refs.fileInput.click()"
            >
              <div class="upload-dropzone" :class="{'dropzone-active': dragActive}">
                <div class="upload-icon-circle">
                  <span class="material-symbols-outlined" style="font-size:40px; font-variation-settings:'wght' 300;">cloud_upload</span>
                </div>
                <div style="text-align:center;">
                  <h2 style="font-family:'Manrope',sans-serif; font-weight:800; font-size:24px; color:#071d31; margin-bottom:8px;">上传投资组合文档</h2>
                  <p style="font-family:'Inter',sans-serif; font-size:14px; color:#43474d; margin:0;">支持 Excel, PDF 或 CSV 格式文件</p>
                </div>
                <div style="display:flex; justify-content:center; gap:12px; align-items:center;">
                  <button class="upload-btn">选择文件</button>
                  <span v-if="selectedFileName" style="font-size:14px; color:#071d31; font-weight:600;">{{ selectedFileName }}</span>
                </div>
                <p style="font-size:12px; color:#74777d; letter-spacing:0.05em; text-transform:uppercase;">最大支持文件限制 50MB</p>
                
                <input ref="fileInput" type="file" accept=".csv" @change="onFileChange" style="display:none;" />
                
                <!-- Uploading / Error States -->
                <div v-if="uploading" style="margin-top:16px; color:#43474d; font-size:14px;">
                  ⏳ 正在解析持仓数据并将自动触发诊断引擎...
                </div>
                <div v-if="uploadError" style="margin-top:16px; padding:12px 16px; background:#ffdad6; color:#93000a; border-radius:8px; font-size:14px;">
                  ❌ {{ uploadError }}
                </div>
              </div>
            </div>

            <!-- Template Download Section -->
            <div class="download-template-card">
              <div style="display:flex; align-items:center; gap:16px;">
                <div class="template-icon">
                  <span class="material-symbols-outlined">description</span>
                </div>
                <div>
                  <h3 style="font-family:'Manrope',sans-serif; font-weight:700; font-size:16px; color:#071d31; margin:0;">标准化模板</h3>
                  <p style="font-family:'Inter',sans-serif; font-size:12px; color:#43474d; margin:4px 0 0 0;">使用标准模板可获得更精准的解析结果</p>
                </div>
              </div>
              <button class="download-btn" @click="downloadTemplate">
                <span class="material-symbols-outlined" style="font-size:18px;">download</span>
                下载标准模板
              </button>
            </div>

            <!-- Visualization / Trust Markers -->
            <div class="trust-markers">
              <div class="trust-item">
                <span class="material-symbols-outlined" style="color:rgba(0,34,3,0.4);">security</span>
                <p>数据加密处理，严格遵守粤财信托合规安全标准。</p>
              </div>
              <div class="trust-item">
                <span class="material-symbols-outlined" style="color:rgba(0,34,3,0.4);">bolt</span>
                <p>AI 智能引擎解析，秒级生成 20+ 维度的穿透报告。</p>
              </div>
              <div class="trust-item">
                <span class="material-symbols-outlined" style="color:rgba(0,34,3,0.4);">analytics</span>
                <p>支持多币种、多品类资产穿透，覆盖全球主要市场。</p>
              </div>
            </div>
          </div>

          <!-- Holdings Table — NordicFinance Style -->
          <div v-if="holdings.length > 0" class="fade-in" style="margin-bottom:24px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
              <span style="font-weight:600;color:var(--navy);font-size:14px;">
                ✅ 解析完成：{{ holdings.length }} 只基金 · 总资产 ¥{{ formatNumber(holdingsTotal) }}
              </span>
              <button class="btn btn-outline" style="padding:4px 12px;font-size:12px;" @click="clearHoldings">🗑️ 清除</button>
            </div>
            <!-- Wind Sync Loading Banner -->
            <div v-if="windSyncing" style="padding:12px 16px;background:#EBF5FB;border:1px solid #2E86C1;border-radius:8px;margin-bottom:12px;font-size:13px;color:#1A5276;display:flex;align-items:center;gap:8px;">
              <span style="animation:spin 1s linear infinite;display:inline-block;">⏳</span>
              {{ windSyncMessage }}
            </div>
            <div class="portfolio-table-container">
              <table class="nf-table">
                <thead>
                  <tr>
                    <th style="width:40px;text-align:center;">#</th>
                    <th>基金名称 / 代码</th>
                    <th style="text-align:right;">持仓金额 (元)</th>
                    <th style="text-align:center;width:140px;">占比 (%)</th>
                    <th style="text-align:right;">近一月 (%)</th>
                    <th style="text-align:right;">今年至今 (%)</th>
                    <th style="text-align:right;">过去一年 (%)</th>
                    <th style="text-align:right;">年化波动率 (%)</th>
                    <th style="text-align:center;width:90px;">状态</th>
                    <th style="text-align:center;width:70px;">风格漂移</th>
                    <th style="text-align:center;width:80px;">经理变更</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(h, i) in holdings" :key="h.code">
                    <td style="text-align:center;font-weight:700;color:#94A3B8;">{{ String(i + 1).padStart(2, '0') }}</td>
                    <td>
                      <div style="display:flex;flex-direction:column;">
                        <span style="font-weight:700;color:#1E293B;line-height:1.3;">{{ fundEnhanced[h.code]?.name || h.name || '—' }}</span>
                        <span style="font-size:10px;color:#94A3B8;font-family:'JetBrains Mono',monospace;margin-top:2px;">{{ h.code }}</span>
                      </div>
                    </td>
                    <td style="text-align:right;font-weight:700;color:#334155;font-family:'JetBrains Mono',monospace;">{{ formatNumber(h.amount) }}</td>
                    <td>
                      <div style="display:flex;align-items:center;justify-content:center;gap:8px;">
                        <div style="width:50px;height:4px;background:#E2E8F0;border-radius:9999px;overflow:hidden;">
                          <div :style="{ width: (h.proportion * 100) + '%', height: '100%', background: '#1E293B', borderRadius: '9999px' }"></div>
                        </div>
                        <span style="font-size:11px;font-weight:600;width:46px;text-align:right;">{{ (h.proportion * 100).toFixed(2) }}%</span>
                      </div>
                    </td>
                    <td :style="{ textAlign: 'right', fontWeight: 700, fontFamily: '\'JetBrains Mono\',monospace', color: (fundEnhanced[h.code]?.monthly_pl || 0) >= 0 ? '#16A34A' : '#DC2626' }">
                      {{ (fundEnhanced[h.code]?.monthly_pl || 0) > 0 ? '+' : '' }}{{ (fundEnhanced[h.code]?.monthly_pl || 0).toFixed(2) }}%
                    </td>
                    <td :style="{ textAlign: 'right', fontWeight: 600, fontFamily: '\'JetBrains Mono\',monospace', color: (fundEnhanced[h.code]?.ret_ytd ?? 0) >= 0 ? '#16A34A' : '#DC2626' }">
                      {{ fundEnhanced[h.code]?.ret_ytd != null ? ((fundEnhanced[h.code].ret_ytd > 0 ? '+' : '') + fundEnhanced[h.code].ret_ytd.toFixed(2) + '%') : '—' }}
                    </td>
                    <td :style="{ textAlign: 'right', fontWeight: 600, fontFamily: '\'JetBrains Mono\',monospace', color: (fundEnhanced[h.code]?.ret_1y ?? 0) >= 0 ? '#16A34A' : '#DC2626' }">
                      {{ fundEnhanced[h.code]?.ret_1y != null ? ((fundEnhanced[h.code].ret_1y > 0 ? '+' : '') + fundEnhanced[h.code].ret_1y.toFixed(2) + '%') : '—' }}
                    </td>
                    <td style="text-align:right;color:#64748B;font-weight:500;">{{ (fundEnhanced[h.code]?.volatility || 0).toFixed(1) }}%</td>
                    <td style="text-align:center;">
                      <span class="status-pill" :class="'status-' + (fundEnhanced[h.code]?.status || 'HOLDING').toLowerCase()">
                        {{ fundEnhanced[h.code]?.status || 'HOLDING' }}
                      </span>
                    </td>
                    <td style="text-align:center;">
                      <span v-if="fundEnhanced[h.code]?.style_drifted" style="color:#DC2626;font-weight:700;font-size:12px;">⚠️ 漂移</span>
                      <span v-else style="color:#16A34A;font-size:12px;">✅</span>
                    </td>
                    <td style="text-align:center;">
                      <span v-if="fundEnhanced[h.code]?.mgr_changed" style="color:#F59E0B;font-weight:700;font-size:12px;">🔄 已变更</span>
                      <span v-else style="color:#94A3B8;font-size:12px;">—</span>
                    </td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <td colspan="2">
                      <div style="font-size:11px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.05em;">Portfolio Totals</div>
                    </td>
                    <td style="text-align:right;font-size:16px;font-weight:800;color:#1E293B;font-family:'JetBrains Mono',monospace;">
                      ¥{{ formatNumber(holdingsTotal) }}
                    </td>
                    <td style="text-align:center;font-weight:700;">100.00%</td>
                    <td style="text-align:right;">
                      <div :style="{ color: avgMonthlyPl >= 0 ? '#16A34A' : '#DC2626', fontSize: '14px', fontWeight: 700 }">
                        {{ avgMonthlyPl > 0 ? '+' : '' }}{{ avgMonthlyPl.toFixed(2) }}%
                      </div>
                    </td>
                    <td></td>
                    <td></td>
                    <td style="text-align:right;">
                      <div style="font-size:14px;font-weight:700;color:#334155;">{{ avgVolatility.toFixed(1) }}%</div>
                    </td>
                    <td></td>
                    <td></td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <!-- Skipped warnings -->
            <div v-if="skippedItems.length > 0" style="margin-top:12px;padding:10px 14px;background:#FEF9E7;border-radius:6px;font-size:12px;color:#7D6608;">
              ⚠️ 以下 {{ skippedItems.length }} 行被跳过：<span v-for="(s, i) in skippedItems" :key="i">{{ s }}<span v-if="i < skippedItems.length-1">、</span></span>
            </div>

            <!-- ═══ Alert Cards ═══ -->
            <div v-if="alertsData && alertsData.total_alerts > 0" style="margin-top:20px;">
              <!-- Manager Change Alerts -->
              <div v-if="alertsData.manager_alerts && alertsData.manager_alerts.length > 0"
                   style="padding:14px 18px;border-radius:8px;border-left:4px solid #F59E0B;background:#FFFBEB;margin-bottom:12px;">
                <div style="font-weight:700;font-size:14px;margin-bottom:8px;color:#92400E;">
                  🔄 更换基金经理预警 ({{ alertsData.manager_alerts.length }} 条)
                </div>
                <div v-for="(a, i) in alertsData.manager_alerts" :key="'mgr'+i"
                     style="font-size:13px;margin-bottom:6px;padding:6px 10px;background:white;border-radius:6px;border:1px solid #FDE68A;">
                  <span style="font-weight:600;">{{ a.severity_label }}</span> |
                  <b>{{ a.fund_name }}</b> ({{ a.fund }})
                  在 <b>{{ a.days_since_change }}</b> 天前发生基金经理变更
                  （现任：<b>{{ a.manager }}</b>，任职起始日：{{ a.start_date }}）
                </div>
              </div>

              <!-- Style Drift Alerts -->
              <div v-if="alertsData.drift_alerts && alertsData.drift_alerts.length > 0"
                   style="padding:14px 18px;border-radius:8px;border-left:4px solid #8B5CF6;background:#F5F3FF;margin-bottom:12px;">
                <div style="font-weight:700;font-size:14px;margin-bottom:8px;color:#5B21B6;">
                  📊 风格漂移预警 ({{ alertsData.drift_alerts.length }} 条)
                </div>
                <div v-for="(a, i) in alertsData.drift_alerts" :key="'drift'+i"
                     style="font-size:13px;margin-bottom:6px;padding:6px 10px;background:white;border-radius:6px;border:1px solid #DDD6FE;">
                  <b>{{ a.fund }}</b> — {{ a.message }}
                  <span v-if="a.from_style && a.to_style" style="color:#7C3AED;">
                    ({{ a.from_style }} → {{ a.to_style }})
                  </span>
                </div>
              </div>

              <!-- Stock Crash Alerts -->
              <div v-if="alertsData.crash_alerts && alertsData.crash_alerts.length > 0"
                   style="padding:14px 18px;border-radius:8px;border-left:4px solid #DC2626;background:#FEF2F2;margin-bottom:12px;">
                <div style="font-weight:700;font-size:14px;margin-bottom:8px;color:#991B1B;">
                  📉 重仓股连续下跌预警 ({{ alertsData.crash_alerts.length }} 条)
                </div>
                <div v-for="(a, i) in alertsData.crash_alerts" :key="'crash'+i"
                     style="font-size:13px;margin-bottom:6px;padding:6px 10px;background:white;border-radius:6px;border:1px solid #FECACA;">
                  ⚠️ <b>{{ a.fund }}</b> 重仓股 <b>{{ a.stock }}</b> ({{ a.stock_code }})
                  连续 <b style="color:#DC2626;">{{ a.consecutive_days }}</b> 个交易日跌幅超过 10%
                </div>
              </div>
            </div>

            <!-- All Clear -->
            <div v-else-if="alertsData && alertsData.total_alerts === 0 && !windSyncing"
                 style="margin-top:16px;padding:12px 16px;background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;font-size:13px;color:#166534;">
              ✅ 底层资产健康，未发现近期经理变更、风格漂移或重仓股暴跌。您的持仓目前风控绿灯。
            </div>
          </div>

          <!-- ═══ 投资组合表现月度回顾 ═══ -->
          <div v-if="holdings.length > 0 && !windSyncing" class="card fade-in" style="margin-bottom:24px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
              <div class="card-title" style="margin-bottom:0;">📋 投资组合表现月度回顾</div>
              <span v-if="monthlyReviewLoading" style="font-size:12px;color:#64748B;">⏳ Kimi 正在联网搜索持仓基金新闻，正在生成回顾报告...</span>
            </div>
            <div v-if="monthlyReview" style="white-space:pre-wrap;font-size:14px;line-height:1.8;color:#334155;">
              {{ monthlyReview }}
            </div>
            <div v-if="!monthlyReview && !monthlyReviewLoading" style="text-align:center;color:#94A3B8;font-size:13px;padding:20px 0;">
              等待 Wind 数据同步完成后自动生成...
            </div>
          </div>


        </div>

        <!-- Page 2: AI 研判调仓 -->
        <div v-if="activePage === 1" class="fade-in">
          <div class="section-title">🧠 一键策略调仓</div>

          <!-- ── 操作栏: 上传研报 + 一键调仓 ── -->
          <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #E2E8F0;padding-bottom:20px;margin-bottom:24px;gap:16px;flex-wrap:wrap;">
             <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
               <label style="padding:10px 20px;background:white;border:2px dashed #CBD5E1;border-radius:8px;color:#475569;cursor:pointer;font-size:14px;font-weight:500;transition:all 0.2s;">
                 📄 上传研报 (可选)
                 <input type="file" accept=".pdf,.txt,.docx" multiple @change="onRebalReportSelect" style="display:none;" />
               </label>
               <span v-for="(f, i) in rebalReports" :key="i" style="background:#EFF6FF;border:1px solid #BFDBFE;color:#1D4ED8;padding:4px 10px;border-radius:16px;font-size:12px;display:flex;align-items:center;gap:6px;">
                 📎 {{ f.name }}
                 <span style="cursor:pointer;font-weight:bold;color:#EF4444;" @click="rebalReports.splice(i,1)">×</span>
               </span>
             </div>
             <button @click="runRebalPipeline" :disabled="rebalRunning || holdings.length === 0"
               style="padding:12px 32px;background:linear-gradient(135deg,#3B82F6,#2563EB);color:white;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer;box-shadow:0 4px 14px rgba(59,130,246,0.3);transition:all 0.2s;"
               :style="rebalRunning || holdings.length === 0 ? {opacity:0.6,cursor:'not-allowed'} : {}"
             >
               {{ rebalRunning ? '⏳ 管线运行中...' : '🚀 一键配置调仓' }}
             </button>
          </div>
          <div v-if="holdings.length === 0" style="padding:20px;background:#FEF3C7;border:1px solid #F59E0B;border-radius:8px;color:#92400E;font-size:13px;margin-bottom:16px;">
            ⚠️ 请先在「持仓分析」页面上传持仓 CSV 文件
          </div>

          <!-- ── SSE 进度日志 ── -->
          <div v-if="rebalLogs.length > 0 || rebalRunning" style="background:white;border-radius:12px;border:1px solid #E2E8F0;padding:16px 20px;margin-bottom:24px;">
            <div class="card-title">📡 运行日志</div>
            <div ref="rebalLogRef" style="max-height:200px;overflow-y:auto;font-family:'JetBrains Mono',monospace;font-size:12px;color:#334155;background:#F8FAFC;border-radius:8px;padding:12px;">
              <div v-for="(log, idx) in rebalLogs" :key="idx" style="margin-bottom:4px;line-height:1.6;">{{ log }}</div>
              <div v-if="rebalRunning" style="color:#94A3B8;">处理中<span style="animation:blink 1.4s infinite both;">.</span><span style="animation:blink 1.4s infinite both 0.2s;">.</span><span style="animation:blink 1.4s infinite both 0.4s;">.</span></div>
            </div>
          </div>

          <!-- ── KPI 看板 ── -->
          <div v-if="rebalResult" style="margin-bottom:28px;">
            <div class="card-title">📊 KPI 业绩对比看板</div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;">
              <div v-for="kpi in rebalResult.kpi_dashboard" :key="kpi.label" style="background:white;border-radius:12px;border:1px solid #E2E8F0;padding:16px;transition:transform 0.2s,box-shadow 0.2s;">
                <div style="font-size:14px;font-weight:600;color:#1E293B;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid #3B82F6;">{{ kpi.label }}</div>
                <div style="display:flex;flex-direction:column;gap:6px;">
                  <div style="display:flex;justify-content:space-between;font-size:13px;"><span style="color:#94A3B8;">年化收益</span><span style="font-weight:600;font-family:monospace;" :style="{color:(kpi.ann_return||0)>0?'#EF4444':'#10B981'}">{{ ((kpi.ann_return||0)*100).toFixed(2) }}%</span></div>
                  <div style="display:flex;justify-content:space-between;font-size:13px;"><span style="color:#94A3B8;">年化波动</span><span style="font-weight:600;font-family:monospace;">{{ ((kpi.ann_vol||0)*100).toFixed(2) }}%</span></div>
                  <div style="display:flex;justify-content:space-between;font-size:13px;"><span style="color:#94A3B8;">最大回撤</span><span style="font-weight:600;font-family:monospace;color:#10B981;">{{ ((kpi.max_dd||0)*100).toFixed(2) }}%</span></div>
                  <div style="display:flex;justify-content:space-between;font-size:13px;"><span style="color:#94A3B8;">夏普比率</span><span style="font-weight:600;font-family:monospace;">{{ (kpi.sharpe||0).toFixed(2) }}</span></div>
                  <div style="display:flex;justify-content:space-between;font-size:13px;"><span style="color:#94A3B8;">卡玛比率</span><span style="font-weight:600;font-family:monospace;">{{ (kpi.calmar||0).toFixed(2) }}</span></div>
                </div>
              </div>
            </div>
          </div>

          <!-- ── 宏观象限 ── -->
          <div v-if="rebalResult && rebalResult.quadrant && rebalResult.quadrant.label" class="card" style="margin-bottom:24px;max-width:600px;">
            <div class="card-title">🧭 宏观象限定位</div>
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
              <div style="width:44px;height:44px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:22px;background:#ECFDF5;">🧭</div>
              <div>
                <div style="font-weight:700;font-size:15px;">{{ rebalResult.quadrant.label }}</div>
                <div style="color:#64748B;font-size:12px;">{{ rebalResult.quadrant.description }}</div>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
              <div style="padding:8px 12px;border-radius:8px;background:#F0FDF4;border-left:3px solid #10B981;">
                <div style="color:#94A3B8;font-size:10px;margin-bottom:2px;">利好</div>
                <div style="font-weight:600;color:#10B981;font-size:12px;">{{ (rebalResult.quadrant.best_assets||[]).join(', ') }}</div>
              </div>
              <div style="padding:8px 12px;border-radius:8px;background:#FEF2F2;border-left:3px solid #EF4444;">
                <div style="color:#94A3B8;font-size:10px;margin-bottom:2px;">承压</div>
                <div style="font-weight:600;color:#EF4444;font-size:12px;">{{ (rebalResult.quadrant.worst_assets||[]).join(', ') }}</div>
              </div>
            </div>
          </div>

          <!-- ── 调仓明细表格 ── -->
          <div v-if="rebalResult && rebalResult.tables" style="margin-bottom:28px;">
            <div class="card-title">📋 调仓明细</div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:16px;">
              <template v-for="(label, key) in rebalTableKeys" :key="key">
                <div class="card" v-if="rebalResult.tables[key] && rebalResult.tables[key].length > 0" style="padding:16px;">
                  <div style="font-weight:600;font-size:14px;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid #E2E8F0;">{{ label }}</div>
                  <table style="width:100%;border-collapse:collapse;">
                    <thead>
                      <tr>
                        <th style="text-align:left;font-size:12px;font-weight:600;padding:8px;background:#F8FAFC;border-bottom:1px solid #E2E8F0;">基金</th>
                        <th style="text-align:right;font-size:12px;font-weight:600;padding:8px;background:#F8FAFC;border-bottom:1px solid #E2E8F0;">原权重</th>
                        <th style="text-align:right;font-size:12px;font-weight:600;padding:8px;background:#F8FAFC;border-bottom:1px solid #E2E8F0;">新权重</th>
                        <th style="text-align:right;font-size:12px;font-weight:600;padding:8px;background:#F8FAFC;border-bottom:1px solid #E2E8F0;">调仓金额</th>
                        <th style="text-align:left;font-size:12px;font-weight:600;padding:8px;background:#F8FAFC;border-bottom:1px solid #E2E8F0;">原因</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="row in rebalResult.tables[key]" :key="row.code">
                        <td style="font-size:12px;padding:8px;border-bottom:1px solid #F1F5F9;">
                          <strong>{{ row.name || row.code }}</strong>
                          <span style="color:#94A3B8;font-family:monospace;font-size:10px;margin-left:4px;">{{ row.code }}</span>
                        </td>
                        <td style="text-align:right;font-size:12px;padding:8px;border-bottom:1px solid #F1F5F9;font-family:monospace;">{{ row.old_weight.toFixed(1) }}%</td>
                        <td style="text-align:right;font-size:12px;padding:8px;border-bottom:1px solid #F1F5F9;font-family:monospace;font-weight:bold;" :style="{color: row.delta_weight > 0 ? '#EF4444' : (row.delta_weight < 0 ? '#10B981' : '')}">{{ row.new_weight.toFixed(1) }}%</td>
                        <td style="text-align:right;font-size:12px;padding:8px;border-bottom:1px solid #F1F5F9;font-family:monospace;" :style="{color: row.delta_amount > 0 ? '#EF4444' : (row.delta_amount < 0 ? '#10B981' : '')}">{{ row.delta_amount > 0 ? '+' : '' }}{{ Math.round(row.delta_amount).toLocaleString() }}</td>
                        <td style="font-size:12px;padding:8px;border-bottom:1px solid #F1F5F9;">
                          <span style="padding:2px 8px;border-radius:10px;font-size:10px;font-weight:500;"
                            :style="{background: row.reason === '看多增配' ? '#F0FDF4' : (row.reason === '看空减配' ? '#FEF2F2' : '#F8FAFC'), color: row.reason === '看多增配' ? '#10B981' : (row.reason === '看空减配' ? '#EF4444' : '#94A3B8')}">{{ row.reason }}</span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </template>
            </div>
          </div>

          <!-- ── AI 投委会折叠面板 (仅研报 Step3) ── -->
          <div v-if="rebalResult && rebalResult.has_report && rebalResult.debate_logs && rebalResult.debate_logs.length > 0" class="card" style="margin-bottom:24px;">
            <div style="display:flex;justify-content:space-between;align-items:center;cursor:pointer;font-size:15px;font-weight:600;color:#1E293B;padding:4px 0;" @click="rebalAiOpen = !rebalAiOpen">
              <span>🤖 AI 虚拟投委会决策过程 (研报调仓)</span>
              <span style="font-size:12px;color:#94A3B8;">{{ rebalAiOpen ? '▲' : '▼' }}</span>
            </div>
            <div v-show="rebalAiOpen" style="margin-top:16px;">
              <div v-for="(log, idx) in rebalResult.debate_logs" :key="idx" style="display:flex;gap:12px;margin-bottom:16px;padding:12px;background:#F8FAFC;border-radius:8px;border-left:3px solid #8B5CF6;">
                <div style="font-size:24px;flex-shrink:0;">{{ log.avatar || '🤖' }}</div>
                <div style="flex:1;min-width:0;">
                  <div style="font-weight:600;font-size:13px;color:#6366F1;margin-bottom:4px;">{{ log.name || log.role || 'Agent' }}</div>
                  <div style="font-size:12px;color:#475569;line-height:1.6;word-break:break-word;" v-html="formatRebalMd(log.content)"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Page 4: 🧭 宏观象限调仓 -->
        <div v-if="activePage === 3" class="fade-in">
          <div class="section-title">🧭 宏观象限调仓</div>

          <!-- 四象限定位 -->
          <div class="card" style="margin-bottom:24px;">
            <div class="card-title">🧭 桥水全天候四象限定位</div>
            <p style="color:var(--text-secondary);font-size:13px;margin-bottom:12px;">
              以经济增长和通胀两个核心因子坐标定位当前所处宏观象限，自动匹配最优攻防资产。
            </p>
            <div style="display:flex;gap:24px;flex-wrap:wrap;">
              <div style="flex:1;min-width:300px;">
                <div ref="quadrantChartRef" style="height:340px;"></div>
              </div>
              <div style="flex:1;min-width:280px;">
                <div v-if="quadrantData" style="padding:8px 0;">
                  <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
                    <div :style="{width:'48px',height:'48px',borderRadius:'12px',display:'flex',alignItems:'center',justifyContent:'center',fontSize:'24px',background: qColors[quadrantData.current_quadrant]?.bg || '#EDF2F7'}">
                      {{ qColors[quadrantData.current_quadrant]?.icon || '🧭' }}
                    </div>
                    <div>
                      <div style="font-weight:700;font-size:18px;">{{ quadrantData.quadrant_label }}</div>
                      <div style="color:var(--text-secondary);font-size:13px;">{{ quadrantData.quadrant_description }}</div>
                    </div>
                  </div>
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;">
                    <div style="padding:10px 12px;border-radius:8px;background:#F0FDF4;border-left:3px solid #10B981;">
                      <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px;">利好资产</div>
                      <div style="color:#10B981;font-weight:600;font-size:13px;">{{ (quadrantData.best_assets || []).join(', ') }}</div>
                    </div>
                    <div style="padding:10px 12px;border-radius:8px;background:#FEF2F2;border-left:3px solid #EF4444;">
                      <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px;">承压资产</div>
                      <div style="color:#EF4444;font-weight:600;font-size:13px;">{{ (quadrantData.worst_assets || []).join(', ') }}</div>
                    </div>
                  </div>
                  <div style="font-size:12px;color:var(--text-muted);">
                    🔗 Markov: <b>{{ quadrantData.markov_regime }}</b> ({{ ((quadrantData.markov_confidence||0)*100).toFixed(0) }}%)
                  </div>
                </div>
                <div v-else style="text-align:center;padding:20px;">
                  <AsyncButton :action="loadQuadrant" type="primary" text="🧭 加载宏观象限" />
                </div>
              </div>
            </div>
          </div>

          <!-- MBL 因子传导 -->
          <div class="card" style="margin-bottom:24px;">
            <div class="card-title">🎯 MBL 因子传导引擎</div>
            <p style="color:var(--text-secondary);font-size:13px;margin-bottom:12px;">
              AI 因子得分 → 因子载荷矩阵传导 → 大类资产目标权重，结果可用于客户持仓调仓。
            </p>
            <AsyncButton v-if="!mblResult" :action="runMbl" type="primary" text="🎯 运行 MBL 因子传导" />
            <div v-if="mblResult">
              <div style="display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap;">
                <div v-for="item in mblResult.transmission_chain" :key="item.factor"
                     style="padding:12px 16px;border-radius:10px;text-align:center;min-width:100px;transition:transform 0.2s;"
                     :style="{background: item.score>0?'#F0FDF4':'#FEF2F2',border:'1px solid '+(item.score>0?'#10B981':'#EF4444')}">
                  <div style="font-weight:600;font-size:13px;">{{ item.factor }}</div>
                  <div style="font-size:18px;font-weight:700;" :style="{color:item.score>0?'#10B981':'#EF4444'}">{{ item.score>0?'+':'' }}{{ item.score }}</div>
                  <div style="font-size:11px;color:var(--text-muted);">×{{ item.regime_modifier }}={{ item.effective_score>0?'+':'' }}{{ item.effective_score }}</div>
                </div>
              </div>
              <div style="margin-bottom:16px;">
                <div style="font-weight:600;font-size:14px;margin-bottom:8px;">📊 资产预期收益信号 → 目标权重</div>
                <div v-for="(w, asset) in mblResult.target_weights" :key="asset"
                     style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                  <div style="width:80px;font-size:13px;">{{ asset }}</div>
                  <div style="flex:1;height:14px;background:#F1F5F9;border-radius:4px;overflow:hidden;">
                    <div :style="{width:w*100+'%',height:'100%',background:'var(--sovereign-accent)',borderRadius:'4px'}"></div>
                  </div>
                  <div style="width:50px;text-align:right;font-size:12px;font-weight:600;">{{ (w*100).toFixed(1) }}%</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 因子风险平价 -->
          <div class="card" style="margin-bottom:24px;">
            <div class="card-title">🛡️ 宏观象限对应配置 (因子风险平价)</div>
            <p style="color:var(--text-secondary);font-size:13px;margin-bottom:12px;">
              根据当前象限自适应调整资产权重，确保各宏观因子的风险贡献均衡，结果可直接作为调仓依据。
            </p>
            <AsyncButton v-if="!factorRpResult" :action="runFactorRp" type="primary" text="🛡️ 生成象限对应配置" />
            <div v-if="factorRpResult">
              <div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:16px;">
                <div style="flex:1;min-width:240px;">
                  <div style="font-weight:600;font-size:14px;margin-bottom:8px;">⚖️ 目标权重</div>
                  <div v-for="(w, asset) in factorRpResult.target_weights" :key="asset"
                       style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    <div style="width:80px;font-size:13px;">{{ asset }}</div>
                    <div style="flex:1;height:14px;background:#F1F5F9;border-radius:4px;overflow:hidden;">
                      <div :style="{width:w*100+'%',height:'100%',background:'var(--sovereign-accent)',borderRadius:'4px'}"></div>
                    </div>
                    <div style="width:45px;text-align:right;font-size:12px;font-weight:600;">{{ (w*100).toFixed(1) }}%</div>
                  </div>
                </div>
                <div style="flex:1;min-width:240px;">
                  <div style="font-weight:600;font-size:14px;margin-bottom:8px;">🏗️ 因子风险贡献</div>
                  <div v-for="(r, factor) in factorRpResult.factor_risk_contributions" :key="factor"
                       style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    <div style="width:65px;font-size:13px;">{{ factor }}</div>
                    <div style="flex:1;height:14px;background:#F1F5F9;border-radius:4px;overflow:hidden;">
                      <div :style="{width:r*100+'%',height:'100%',background:'#6366F1',borderRadius:'4px'}"></div>
                    </div>
                    <div style="width:45px;text-align:right;font-size:12px;font-weight:600;">{{ (r*100).toFixed(1) }}%</div>
                  </div>
                </div>
              </div>
              <div v-if="factorRpResult.defense_log && factorRpResult.defense_log.length"
                   style="padding:12px 16px;border-radius:8px;background:#FFFBEB;border:1px solid #FDE68A;margin-top:12px;">
                <div style="font-weight:600;font-size:14px;margin-bottom:4px;">🛡️ 象限防御执行记录</div>
                <div v-for="(log, idx) in factorRpResult.defense_log" :key="idx"
                     style="font-size:13px;margin-bottom:4px;color:var(--text-secondary);">{{ log }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Page 3: 业绩回测 (Now fully dynamic) -->
        <div v-if="activePage === 2 && holdings.length > 0" class="fade-in">
           <!-- Campaign 13: The 3-Way Grid Component -->
           <ThreeWayMatrix />
           <BacktestDashboard 
             :strategiesPayload="getStrategiesPayload" 
             :pdfStatePayload="getPdfStatePayload" 
           />
        </div>
        <div v-if="activePage === 2 && holdings.length === 0" class="fade-in">
          <div class="card" style="text-align:center;color:var(--text-muted);padding:40px;">
            请先在左侧「📂 持仓分析」界面上传您的当前持仓
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import api, { uploadHoldings, optimizeHrp, getRebalanceInstructions, extractNewsViews, extractReportViews, optimizeBl, getMacroQuadrant, optimizeMbl, optimizeFactorRp, generatedApi } from '../api'
import AsyncButton from '../components/common/AsyncButton.vue'
import WindDashboard from '../components/WindDashboard.vue'
import RebalanceTable from '../components/RebalanceTable.vue'
import BacktestDashboard from '../components/BacktestDashboard.vue'
import ThreeWayMatrix from '../components/ThreeWayMatrix.vue'

const activePage = ref(0)
const currentStep = ref(0) // 0: upload, 1: mapping, 2: hrp
const hrpResultTable = ref(null)

// ── 一键调仓管线状态 ──
const rebalReports = ref([])
const rebalRunning = ref(false)
const rebalLogs = ref([])
const rebalResult = ref(null)
const rebalAiOpen = ref(false)
const rebalLogRef = ref(null)
const rebalTableKeys = computed(() => {
  const base = { 'macro': '🧭 宏观象限调仓', 'news': '📰 新闻资讯调仓' }
  if (rebalResult.value?.has_report) base['report'] = '📄 研报调仓'
  return base
})

function onRebalReportSelect(e) {
  const files = Array.from(e.target.files || [])
  rebalReports.value.push(...files)
  e.target.value = ''
}

async function runRebalPipeline() {
  if (holdings.value.length === 0) return
  rebalRunning.value = true
  rebalLogs.value = []
  rebalResult.value = null

  const formData = new FormData()
  for (const f of rebalReports.value) {
    formData.append('files', f)
  }
  const codes = holdings.value.map(h => h.code)
  formData.append('portfolio_codes_json', JSON.stringify(codes))
  formData.append('total_amount', String(holdingsTotal.value || 10000000))

  try {
    const response = await fetch('http://localhost:8000/api/v1/rebalance/run_full_pipeline', {
      method: 'POST',
      body: formData,
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
              rebalLogs.value.push(parsed.content)
              nextTick(() => { const el = rebalLogRef.value; if (el) el.scrollTop = el.scrollHeight })
            } else if (parsed.type === 'finish') {
              rebalResult.value = parsed.result
            } else if (parsed.type === 'error') {
              rebalLogs.value.push(`❌ 错误: ${parsed.content}`)
            }
          } catch (e) { console.error('SSE parse error', e) }
        }
      }
    }
  } catch (e) {
    rebalLogs.value.push(`❌ 连接异常: ${e.message}`)
  } finally {
    rebalRunning.value = false
  }
}

function formatRebalMd(text) {
  if (!text) return ''
  return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>')
}

async function runHrpOptimization() {
  if (holdings.value.length === 0) {
    throw new Error("无持仓数据，无法进行宏观象限配置");
  }
  
  // 1. Prepare inputs
  const assetNames = holdings.value.map(h => h.code);
  const n = assetNames.length;
  // Mock standard diagonal matrix as frontend doesn't strictly hold the C++ Wind result array yet
  const mockCov = Array(n).fill(0).map((_, i) => Array(n).fill(0).map((_, j) => i === j ? 0.04 : 0.01));
  
  // 2. Call optimize_hrp
  const hrpRes = await optimizeHrp({
    asset_names: assetNames,
    cov_matrix_2d: mockCov,
    max_weight: 0.35,
    min_weight: 0.02
  });
  
  if (hrpRes.data.status === "error") {
    throw new Error(hrpRes.data.message || "象限配置模型失败");
  }
  
  const targetWeights = hrpRes.data.target_weights;
  
  // 3. Prepare for rebalance_instructions
  const currentWeights = {};
  const assetClassMap = {};
  const fundNameMap = {};
  
  holdings.value.forEach(h => {
    currentWeights[h.code] = h.proportion;
    assetClassMap[h.code] = h.asset_class || "主动股票"; 
    fundNameMap[h.code] = h.name;
    // ensure missing assets in target are 0
    if (!(h.code in targetWeights)) {
      targetWeights[h.code] = 0.0;
    }
  });
  
  // 4. Call rebalance_instructions
  const rebalRes = await getRebalanceInstructions({
    current_weights: currentWeights,
    target_weights: targetWeights,
    total_aum: holdingsTotal.value,
    asset_class_map: assetClassMap,
    fund_name_map: fundNameMap
  });
  
  // 5. Render
  hrpResultTable.value = rebalRes.data;
  
  if (currentStep.value < 3) {
    currentStep.value = 3;
  }
}

function handleKpiSuccess(res) {
  kpiResult.value = res.data || res
}

// === AI BL Rebalance Methods ===

const aiNewsResultTable = ref(null)
const aiReportResultTable = ref(null)
const reportFileInput = ref(null)

async function executeBlOptimization(nlpScores) {
  const assetNames = holdings.value.map(h => h.code);
  const n = assetNames.length;
  const mockCov = Array(n).fill(0).map((_, i) => Array(n).fill(0).map((_, j) => i === j ? 0.04 : 0.01));
  
  const currentWeights = {};
  const assetClassMap = {};
  holdings.value.forEach(h => {
    currentWeights[h.code] = h.proportion;
    assetClassMap[h.code] = h.asset_class || "主动股票"; 
  });
  
  const res = await optimizeBl({
    nlp_scores: nlpScores,
    current_weights: currentWeights,
    total_aum: holdingsTotal.value,
    asset_class_map: assetClassMap,
    cov_matrix_2d: mockCov,
    asset_names: assetNames
  });
  return res.data;
}

async function runAiNewsRebalance() {
  if (holdings.value.length === 0) throw new Error("请先根据步骤一上传持仓");
  
  // 1. Extract Views
  const viewsRes = await extractNewsViews({ query: "最新宏观经济焦点" });
  if (viewsRes.data.status !== "success") throw new Error("新闻推演计算异常");
  
  // 2. BL Optimization
  const blRes = await executeBlOptimization(viewsRes.data.nlp_scores);
  aiNewsResultTable.value = blRes;
}

async function runAiReportRebalance() {
  if (holdings.value.length === 0) throw new Error("请先上传持仓组合");
  
  const file = reportFileInput.value?.files?.[0];
  if (!file) throw new Error("请您先选择至少一份本地宏观研报");
  
  // 1. Upload & Extract Views
  const formData = new FormData();
  formData.append('file', file);
  
  const viewsRes = await extractReportViews(formData);
  if (viewsRes.data.status !== "success") throw new Error("研报解析失利");
  
  // 2. BL Optimization
  const blRes = await executeBlOptimization(viewsRes.data.nlp_scores);
  aiReportResultTable.value = blRes;
}

// === Payload Generators for KPI Backtest & PDF Export ===

function getStrategiesPayload() {
  const assetNames = holdings.value.map(h => h.code);
  const n = assetNames.length;
  // Simple mock cov matrix for stateless calculation visualization
  const mockCov = Array(n).fill(0).map((_, i) => Array(n).fill(0).map((_, j) => i === j ? 0.04 : 0.01));

  const clientWeights = {};
  holdings.value.forEach(h => clientWeights[h.code] = h.proportion);
  
  const strats = [{ label: '📋 客户持仓', weights: clientWeights }];
  
  if (hrpResultTable.value) {
    const w = { ...clientWeights };
    hrpResultTable.value.instructions.forEach(ins => w[ins.code] += ins.delta_w);
    strats.push({ label: '🧭 宏观象限对应配置 [沪深300基准]', weights: w });
  }
  if (aiNewsResultTable.value) {
    const w = { ...clientWeights };
    aiNewsResultTable.value.instructions.forEach(ins => w[ins.code] += ins.delta_w);
    strats.push({ label: '📡 资讯调仓', weights: w });
  }
  if (aiReportResultTable.value) {
    const w = { ...clientWeights };
    aiReportResultTable.value.instructions.forEach(ins => w[ins.code] += ins.delta_w);
    strats.push({ label: '📄 研报调仓', weights: w });
  }
  
  return {
    strategies: strats,
    benchmark_code: "000300.SH",
    cov_matrix_2d: mockCov,
    asset_names: assetNames
  }
}

function getPdfStatePayload() {
  return {
    diagnose_state: {
      client_holdings: holdings.value,
      client_total_aum: holdingsTotal.value,
      hrp_instructions: hrpResultTable.value?.instructions || [],
      ai_news_instructions: aiNewsResultTable.value?.instructions || [],
      ai_report_instructions: aiReportResultTable.value?.instructions || []
    }
  }
}

const showAlert = (msg) => alert(msg)

const subPageCards = [
  { icon: 'pie_chart', label: '持仓分析', en: 'Portfolio Insight', pro: false },
  { icon: 'psychology_alt', label: '策略调仓', en: 'Smart Rebalance', pro: true },
  { icon: 'query_stats', label: '业绩回测', en: 'Backtesting', pro: false },
]

function generateSparkline(pct) {
  if (pct >= 0) {
    return "M0,20 L10,18 L20,22 L30,15 L40,12 L50,16 L60,8 L70,12 L80,5 L90,10 L100,2";
  } else {
    return "M0,5 L10,12 L20,8 L30,18 L40,15 L50,22 L60,18 L70,20 L80,12 L90,15 L100,18";
  }
}

// ═══ Market Quotes (市场行情 5分钟自动刷新) ═══
const marketQuotes = ref([])
const marketUpdatedAt = ref('')
let _marketTimer = null

async function fetchMarketQuotes() {
  try {
    const res = await api.get('/api/v1/data/market_quotes', { timeout: 10000 })
    if (res.data?.quotes?.length) {
      marketQuotes.value = res.data.quotes
      marketUpdatedAt.value = res.data.updated_at || ''
    } else {
      // API 返回但无数据 — 使用占位
      _applyFallbackQuotes()
    }
  } catch (err) {
    console.warn('市场行情获取失败:', err.message)
    // Wind 不可用 — 显示结构占位
    if (marketQuotes.value.length === 0) _applyFallbackQuotes()
  }
}

function _applyFallbackQuotes() {
  marketQuotes.value = [
    { code: '000001.SH', name: '上证指数', en: 'SSE Composite', close: null, pct_chg: null },
    { code: '000300.SH', name: '沪深300', en: 'CSI 300', close: null, pct_chg: null },
    { code: '399001.SZ', name: '深证成指', en: 'SZSE Comp', close: null, pct_chg: null },
    { code: '399006.SZ', name: '创业板指', en: 'ChiNext', close: null, pct_chg: null },
    { code: '000905.SH', name: '中证500', en: 'CSI 500', close: null, pct_chg: null },
    { code: '000852.SH', name: '中证1000', en: 'CSI 1000', close: null, pct_chg: null },
    { code: 'HSI.HI',    name: '恒生指数', en: 'Hang Seng', close: null, pct_chg: null },
  ]
  marketUpdatedAt.value = '等待连接'
}

onMounted(() => {
  fetchMarketQuotes()
  _marketTimer = setInterval(fetchMarketQuotes, 5 * 60 * 1000) // 5分钟轮询
})

onUnmounted(() => {
  if (_marketTimer) clearInterval(_marketTimer)
})

const pipelineSteps = [
  { icon: '📂', label: '上传 CSV' },
  { icon: '📡', label: 'Wind 拉取' },
  { icon: '🔬', label: '因子映射' },
  { icon: '⚖️', label: 'RP 体检' },
  { icon: '🧠', label: 'AI 增强' },
]

// Holdings state
const holdings = ref([])
const holdingsTotal = ref(0)
const skippedItems = ref([])
const selectedFileName = ref('')
const uploading = ref(false)
const uploadError = ref('')
const dragActive = ref(false)


// ═══ Wind Auto-Sync + Enhanced Data ═══
const fundEnhanced = ref({})
const alertsData = ref(null)
const windSyncing = ref(false)
const windSyncMessage = ref('')

// ═══ Monthly Review (Kimi News) ═══
const monthlyReview = ref('')
const monthlyReviewLoading = ref(false)

const avgMonthlyPl = computed(() => {
  if (holdings.value.length === 0) return 0
  const vals = holdings.value.map(h => fundEnhanced.value[h.code]?.monthly_pl || 0)
  return vals.reduce((a, b) => a + b, 0) / vals.length
})

const avgVolatility = computed(() => {
  if (holdings.value.length === 0) return 0
  let totalW = 0, weightedVol = 0
  holdings.value.forEach(h => {
    const vol = fundEnhanced.value[h.code]?.volatility || 0
    const w = h.proportion || 0
    weightedVol += vol * w
    totalW += w
  })
  return totalW > 0 ? weightedVol / totalW : 0
})

function formatNumber(n) {
  return Number(n).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function processFile(file) {
  if (!file) return
  selectedFileName.value = file.name
  uploading.value = true
  uploadError.value = ''
  fundEnhanced.value = {}
  alertsData.value = null

  try {
    const res = await uploadHoldings(file)
    const data = res.data
    if (data.status === 'ok') {
      holdings.value = data.holdings
      holdingsTotal.value = data.total
      skippedItems.value = data.skipped || []
      currentStep.value = 1

      // ── 自动触发 Wind 数据拉取 ──
      autoTriggerWindSync()
    } else {
      uploadError.value = data.message || '解析失败'
    }
  } catch (e) {
    uploadError.value = e.response?.data?.detail || e.message || '上传失败'
  } finally {
    uploading.value = false
  }
}

// ── Auto Wind Sync: CSV 上传成功后自动触发 ──
async function autoTriggerWindSync() {
  if (holdings.value.length === 0) return
  windSyncing.value = true
  windSyncMessage.value = '正在连接 Wind 终端下载实时行情与持仓穿透数据...'

  try {
    const codes = holdings.value.map(h => h.code)
    const res = await generatedApi.syncClientPortfolioApiV1DataSyncClientPortfolioPost({ fund_codes: codes })
    const taskId = res.data.task_id
    currentStep.value = 2

    // 轮询等待完成
    const pollInterval = 2000
    const checkStatus = async () => {
      try {
        const statusRes = await generatedApi.getSyncStatusApiV1DataSyncStatusTaskIdGet(taskId)
        const statusData = statusRes.data

        if (statusData.status === 'success') {
          windSyncing.value = false
          windSyncMessage.value = ''
          currentStep.value = 3

          // 提取增强数据
          const result = statusData.result?.data || statusData.result || {}
          if (result.fund_summary) {
            fundEnhanced.value = result.fund_summary
          }
          if (result.alerts) {
            alertsData.value = result.alerts
          }

          // 自动触发 Kimi 基金新闻搜索 + 生成月度回顾
          fetchMonthlyReview()
        } else if (statusData.status === 'error') {
          windSyncing.value = false
          windSyncMessage.value = ''
          console.warn('Wind sync failed:', statusData.message)
        } else {
          // processing — keep polling
          windSyncMessage.value = statusData.message || '正在拉取中...'
          setTimeout(checkStatus, pollInterval)
        }
      } catch (err) {
        windSyncing.value = false
        windSyncMessage.value = ''
        console.error('Wind poll error:', err)
      }
    }
    setTimeout(checkStatus, 1000)
  } catch (err) {
    windSyncing.value = false
    windSyncMessage.value = ''
    console.error('Wind auto-sync trigger error:', err)
  }
}

function onFileChange(e) {
  const file = e.target.files[0]
  processFile(file)
}

function onDrop(e) {
  dragActive.value = false
  const file = e.dataTransfer.files[0]
  if (file && file.name.endsWith('.csv')) {
    processFile(file)
  }
}

function clearHoldings() {
  holdings.value = []
  holdingsTotal.value = 0
  skippedItems.value = []
  selectedFileName.value = ''
  currentStep.value = 0
  fundEnhanced.value = {}
  alertsData.value = null
  windSyncing.value = false
  monthlyReview.value = ''
  monthlyReviewLoading.value = false
}

async function fetchMonthlyReview() {
  if (holdings.value.length === 0) return
  monthlyReviewLoading.value = true
  monthlyReview.value = ''
  try {
    // 收集基金名称
    const fundNames = holdings.value.map(h => {
      const enhanced = fundEnhanced.value[h.code]
      return enhanced?.name || h.name || h.code
    }).filter(n => n && n !== '—')

    const res = await api.post('/api/v1/data/fund_news_review', {
      fund_names: fundNames
    }, { timeout: 120000 })
    if (res.data?.review) {
      monthlyReview.value = res.data.review
    } else {
      monthlyReview.value = '近一个月无上述持仓基金的市场资讯'
    }
  } catch (err) {
    console.error('Kimi 基金新闻搜索失败:', err)
    monthlyReview.value = '生成回顾报告失败，请稍后重试'
  } finally {
    monthlyReviewLoading.value = false
  }
}

function downloadTemplate() {
  const csv = '\ufeff基金代码,基金名称,持有金额(元)\n000979,,1997602.88\n001203,,2997003.00\n002657,,999400.36\n005014,,2949300.07\n006965,,2900389.02\n'
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '客户持仓模板.csv'
  a.click()
  URL.revokeObjectURL(url)
}

// ═══ 宏观象限调仓 (Page 4) ═══
const quadrantData = ref(null)
const mblResult = ref(null)
const factorRpResult = ref(null)
const quadrantChartRef = ref(null)

const qColors = {
  recovery: { bg: '#ECFDF5', icon: '🌱' },
  overheat: { bg: '#FEF3C7', icon: '🔥' },
  stagflation: { bg: '#FEE2E2', icon: '⚠️' },
  deflation: { bg: '#DBEAFE', icon: '❄️' },
}

// 默认因子得分（实际由 AI 委员会产出）
const defaultFactorScores = {
  "经济增长": 0.3, "通胀商品": -0.2, "利率环境": 0.4,
  "信用扩张": 0.1, "海外环境": 0.0, "市场情绪": 0.2,
}

async function loadQuadrant() {
  const res = await getMacroQuadrant({ factor_scores: defaultFactorScores })
  quadrantData.value = res.data
  await nextTick()
  initQuadrantChart()
}

async function runMbl() {
  const res = await optimizeMbl({ factor_scores: defaultFactorScores, apply_regime: true })
  mblResult.value = res.data
}

async function runFactorRp() {
  const res = await optimizeFactorRp({ factor_scores: defaultFactorScores, apply_regime: true })
  factorRpResult.value = res.data
}

function initQuadrantChart() {
  if (!quadrantChartRef.value || !quadrantData.value) return
  const chart = echarts.init(quadrantChartRef.value)
  const gx = quadrantData.value.growth_axis || 0
  const ix = quadrantData.value.inflation_axis || 0
  chart.setOption({
    tooltip: {},
    xAxis: { name: '通胀 →', min: -1, max: 1, nameLocation: 'end', axisLine: { lineStyle: { color: '#94A3B8' } }, splitLine: { show: false } },
    yAxis: { name: '增长 ↑', min: -1, max: 1, nameLocation: 'end', axisLine: { lineStyle: { color: '#94A3B8' } }, splitLine: { show: false } },
    grid: { left: 50, right: 30, top: 30, bottom: 40 },
    graphic: [
      { type: 'rect', left: '50%', top: 30, shape: { width: 200, height: 140 }, style: { fill: 'rgba(254,243,199,0.3)' } },
      { type: 'rect', right: '50%', top: 30, shape: { width: 200, height: 140 }, style: { fill: 'rgba(236,253,245,0.3)' } },
      { type: 'rect', left: '50%', bottom: 40, shape: { width: 200, height: 140 }, style: { fill: 'rgba(254,226,226,0.3)' } },
      { type: 'rect', right: '50%', bottom: 40, shape: { width: 200, height: 140 }, style: { fill: 'rgba(219,234,254,0.3)' } },
      { type: 'text', left: '27%', top: 45, style: { text: '🌱 复苏', fill: '#059669', fontSize: 13, fontWeight: 'bold' } },
      { type: 'text', left: '62%', top: 45, style: { text: '🔥 过热', fill: '#D97706', fontSize: 13, fontWeight: 'bold' } },
      { type: 'text', left: '62%', bottom: 55, style: { text: '⚠️ 滞胀', fill: '#DC2626', fontSize: 13, fontWeight: 'bold' } },
      { type: 'text', left: '27%', bottom: 55, style: { text: '❄️ 衰退', fill: '#2563EB', fontSize: 13, fontWeight: 'bold' } },
    ],
    series: [{
      type: 'scatter', symbolSize: 24, data: [[ix, gx]],
      itemStyle: { color: '#F97316', borderColor: '#FFF', borderWidth: 3, shadowBlur: 12, shadowColor: 'rgba(249,115,22,0.5)' },
      label: { show: true, formatter: '当前', position: 'top', fontSize: 12, fontWeight: 'bold', color: '#F97316' },
    }],
  })
  window.addEventListener('resize', () => chart.resize())
}
</script>

<style scoped>
/* ═══ NordicFinance Portfolio Table ═══ */
.portfolio-table-container {
  overflow: hidden;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  border: 1px solid #E2E8F0;
  background: #FFFFFF;
}
.nf-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.nf-table thead {
  background: #0d1b2a;
}
.nf-table thead th {
  color: #FFFFFF;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 16px 20px;
  white-space: nowrap;
}
.nf-table tbody td {
  padding: 14px 20px;
  border-bottom: 1px solid #F1F5F9;
  color: #334155;
  transition: background 0.15s;
}
.nf-table tbody tr:hover td {
  background: #F8FAFC;
}
.nf-table tfoot td {
  padding: 16px 20px;
  background: #F8FAFC;
  border-top: 2px solid #E2E8F0;
  border-bottom: none;
}

/* ═══ Status Pills ═══ */
.status-pill {
  display: inline-block;
  font-size: 10px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.status-active {
  background: #DCFCE7;
  color: #16A34A;
}
.status-stable {
  background: #D1FAE5;
  color: #059669;
}
.status-holding {
  background: #E5E7EB;
  color: #6B7280;
}
.status-outperform {
  background: #BBF7D0;
  color: #15803D;
}
.status-volatility {
  background: #FEE2E2;
  color: #DC2626;
}

/* ═══ Legacy support ═══ */
.holdings-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.holdings-table th {
  background: #F8FAFC;
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
  padding: 10px 12px;
  border-bottom: 1px solid #F1F5F9;
  color: var(--text-primary);
}
.holdings-table tbody tr:hover {
  background: #F8FAFC;
}
.holdings-table tfoot td {
  border-top: 2px solid #E2E8F0;
  border-bottom: none;
  padding: 12px;
  background: #F8FAFC;
}

/* ═══ Spin Animation ═══ */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
/* ═══ Smart Sidebar (Exact Reference Design) ═══ */
.smart-sidebar {
  width: 380px;
  background-color: #f8f9fa;
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow-y: auto;
  border-right: 1px solid #e1e3e4;
  flex-shrink: 0;
}
.smart-sidebar::-webkit-scrollbar { width: 0px; }

.ref-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #191c1d;
}
.ref-card:hover { background: #edeeef; }
.ref-card.active {
  background: #071d31;
  padding: 24px 20px;
  transform: scale(1.02);
  box-shadow: 0 12px 32px rgba(7,29,49,0.2);
  z-index: 10;
  color: #ffffff;
}

.ref-icon-box {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: #f3f4f5;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.3s ease;
}
.ref-card.active .ref-icon-box {
  background: rgba(255,255,255,0.15);
}

.material-symbols-outlined {
  font-family: 'Material Symbols Outlined' !important;
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

.ref-icon { font-size: 28px !important; color: #071d31; }
.ref-card.active .ref-icon { color: #ffffff; }

.ref-card-title {
  font-family: 'Manrope', sans-serif;
  font-size: 18px;
  font-weight: 800;
  line-height: 1.2;
}
.ref-card-sub {
  font-size: 12px;
  color: #74777d;
  margin-top: 4px;
}
.ref-card.active .ref-card-sub { color: rgba(255,255,255,0.6); }

/* ═══ Bento Upload UI ═══ */
.bento-upload-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 800px;
  margin: 0 auto 32px auto;
}
.upload-dropzone {
  border: 2px dashed rgba(116,119,125,0.3);
  border-radius: 16px;
  padding: 64px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  background: #ffffff;
  transition: all 0.3s ease;
}
.upload-dropzone:hover, .dropzone-active {
  box-shadow: 0 24px 48px rgba(7,29,49,0.05);
  border-color: rgba(7,29,49,0.2);
}
.upload-icon-circle {
  width: 80px;
  height: 80px;
  background: #f3f4f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #071d31;
  transition: transform 0.5s ease;
}
.upload-dropzone:hover .upload-icon-circle, .dropzone-active .upload-icon-circle {
  transform: scale(1.1);
}
.upload-btn {
  background: #071d31;
  color: #ffffff;
  padding: 12px 32px;
  border-radius: 8px;
  font-weight: 600;
  font-family: 'Inter', sans-serif;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  pointer-events: none;
}
.download-template-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  background: #f3f4f5;
  border-radius: 16px;
  border: 1px solid rgba(196,198,205,0.1);
  flex-wrap: wrap;
  gap: 16px;
}
.template-icon {
  width: 40px;
  height: 40px;
  background: #e1e3e4;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #43474d;
}
.download-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #071d31;
  background: transparent;
  border: none;
  font-weight: 600;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s ease;
}
.download-btn:hover {
  background: #e1e3e4;
  text-decoration: underline;
}
.trust-markers {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  padding-top: 16px;
}
.trust-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.trust-item p {
  font-size: 12px;
  color: #43474d;
  line-height: 1.6;
  margin: 0;
}
@media (max-width: 768px) {
  .trust-markers {
    grid-template-columns: 1fr;
  }
}

/* Sparkline CSS */
.sparkline-up {
  stroke: #91d78a;
  fill: none;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.sparkline-down {
  stroke: #ba1a1a;
  fill: none;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
</style>

