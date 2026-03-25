<template>
  <div class="card" style="margin-bottom:24px;">
    <div class="card-title">📡 Wind 数据拉取</div>
    <AsyncButton
      :action="triggerWindFetch"
      type="primary"
      text="📥 连线 Wind：下载客户持仓特征与历史净值"
      @success="handleWindSuccess"
    />
    <p style="color:var(--text-muted);font-size:12px;margin-top:8px;">
      通过 Wind 终端获取持仓基金的最新净值和收益率数据。
    </p>

    <!-- Wind Fetch Results -->
    <div v-if="windResult" class="fade-in" style="margin-top:20px;padding:16px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;">
      <div style="color:var(--navy);font-weight:600;font-size:14px;margin-bottom:16px;display:flex;align-items:center;gap:6px;">
        <span style="color:#10B981;">✅</span> 行情与穿透分析完成
      </div>
      <div style="display:flex;gap:40px;">
        <div>
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">匹配基金</div>
          <div style="font-size:20px;font-weight:600;color:var(--text-primary);">
            {{ windResult.funds_matched }} / {{ windResult.funds_total }} <span style="font-size:12px;font-weight:400;color:var(--text-secondary);">只</span>
          </div>
        </div>
        <div>
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">行情拉取</div>
          <div style="font-size:20px;font-weight:600;color:var(--text-primary);">
            {{ windResult.prices_days }} <span style="font-size:12px;font-weight:400;color:var(--text-secondary);">天</span>
          </div>
        </div>
        <div>
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">提取重仓股</div>
          <div style="font-size:20px;font-weight:600;color:var(--text-primary);">
            {{ windResult.total_stocks_count }} <span style="font-size:12px;font-weight:400;color:var(--text-secondary);">只</span>
          </div>
        </div>
        <div>
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">去重后资产</div>
          <div style="font-size:20px;font-weight:600;color:var(--text-primary);">
            {{ windResult.unique_stocks_count }} <span style="font-size:12px;font-weight:400;color:var(--text-secondary);">只</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import AsyncButton from './common/AsyncButton.vue'
import { generatedApi } from '../api'

const props = defineProps({
  holdings: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['success'])

const windResult = ref(null)

// Clear result if holdings change completely
watch(() => props.holdings, () => {
  windResult.value = null
}, { deep: true })

async function triggerWindFetch() {
  if (props.holdings.length === 0) {
    throw new Error("请先按照'步骤一'上传包含基金代码的 CSV。")
  }
  
  const codes = props.holdings.map(h => h.code)
  
  // 1. 发送触发任务请求
  const res = await generatedApi.syncClientPortfolioApiV1DataSyncClientPortfolioPost({ fund_codes: codes })
  const taskId = res.data.task_id
  
  // 2. 轮询后台任务状态 (隔离长耗时请求防超时)
  return new Promise((resolve, reject) => {
    const checkStatus = async () => {
      try {
        const statusRes = await generatedApi.getSyncStatusApiV1DataSyncStatusTaskIdGet(taskId)
        const statusData = statusRes.data
        
        if (statusData.status === "success") {
          resolve(statusData)
        } else if (statusData.status === "error") {
          reject(new Error(statusData.message))
        } else {
          // processing
          setTimeout(checkStatus, 2000)
        }
      } catch (err) {
        reject(err)
      }
    }
    setTimeout(checkStatus, 1000)
  })
}

function handleWindSuccess(res) {
  const payload = res.result?.data || res.result
  if (payload) {
    windResult.value = payload
    emit('success', payload)
  } else {
    alert('Wind 行情数据拉取已完成！但未获取到统计详情。')
  }
}
</script>
