<template>
  <div class="page">
    <h3>财务报表</h3>
    <div class="content">
      <!-- 非财务角色拦截（菜单已隐藏，防直接输 URL） -->
      <div class="empty" v-if="!isFinance">仅财务角色可访问财务报表</div>

      <template v-else>
        <div class="toolbar">
          <button class="btn primary" @click="loadSummary" :disabled="loading">
            {{ loading ? '统计中...' : '刷新报表' }}
          </button>
        </div>
        <div class="msg err" v-if="errorMsg">{{ errorMsg }}</div>

        <!-- 审查质量卡片 -->
        <div class="card-row">
          <div class="card">
            <div class="card-label">审查报告总数</div>
            <div class="card-value">{{ summary.audit?.total_reports ?? '-' }}</div>
          </div>
          <div class="card highlight">
            <div class="card-label">审查通过率</div>
            <div class="card-value">{{ summary.audit?.pass_rate ?? '-' }}<span class="unit" v-if="summary.audit?.pass_rate !== null && summary.audit?.pass_rate !== undefined">%</span></div>
          </div>
          <div class="card">
            <div class="card-label">预警（待人工复核）</div>
            <div class="card-value warn-text">{{ summary.audit?.warned ?? '-' }}</div>
          </div>
          <div class="card">
            <div class="card-label">驳回</div>
            <div class="card-value rej-text">{{ summary.audit?.rejected ?? '-' }}</div>
          </div>
        </div>

        <div class="section-row">
          <!-- 驳回/预警原因 TOP -->
          <div class="panel">
            <h4>驳回 / 预警原因 TOP5</h4>
            <div v-if="summary.audit?.top_reasons?.length" class="top-list">
              <div class="top-item" v-for="(item, idx) in summary.audit.top_reasons" :key="idx">
                <span class="top-rank">{{ idx + 1 }}</span>
                <span class="top-reason" :title="item.reason">{{ item.reason }}</span>
                <div class="top-bar">
                  <div class="top-fill" :style="{ width: barWidth(item.count) }"></div>
                </div>
                <span class="top-count">{{ item.count }} 次</span>
              </div>
            </div>
            <div class="empty" v-else>暂无驳回 / 预警记录</div>
          </div>

          <!-- 发票概况 -->
          <div class="panel">
            <h4>发票概况</h4>
            <div class="inv-stats" v-if="summary.invoices">
              <div class="inv-line"><span>发票总数</span><b>{{ summary.invoices.total }}</b></div>
              <div class="inv-line"><span>待审</span><b class="warn-text">{{ summary.invoices.by_status['待审'] }}</b></div>
              <div class="inv-line"><span>已通过</span><b class="ok-text">{{ summary.invoices.by_status['已通过'] }}</b></div>
              <div class="inv-line"><span>已驳回</span><b class="rej-text">{{ summary.invoices.by_status['已驳回'] }}</b></div>
              <div class="inv-line"><span>已入账</span><b>{{ summary.invoices.by_status['已入账'] }}</b></div>
              <div class="inv-line total"><span>已通过金额合计</span><b>¥{{ fmt(summary.invoices.approved_amount) }}</b></div>
            </div>
          </div>
        </div>

        <!-- 预算执行率 -->
        <div class="panel">
          <h4>预算执行率</h4>
          <table class="table" v-if="summary.budgets?.length">
            <thead>
              <tr><th>期间</th><th>类目</th><th>限额</th><th>已用</th><th>剩余</th><th>执行率</th></tr>
            </thead>
            <tbody>
              <tr v-for="rule in summary.budgets" :key="rule.id">
                <td>{{ rule.period }}</td>
                <td>{{ rule.category }}</td>
                <td>¥{{ fmt(rule.limit_amount) }}</td>
                <td>¥{{ fmt(rule.used_amount) }}</td>
                <td>¥{{ fmt(rule.remaining) }}</td>
                <td>
                  <div class="rate-cell">
                    <div class="rate-bar">
                      <div class="rate-fill" :class="rateClass(rule.usage_rate)"
                        :style="{ width: Math.min(rule.usage_rate ?? 0, 100) + '%' }"></div>
                    </div>
                    <span>{{ rule.usage_rate === null ? '-' : rule.usage_rate + '%' }}</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <div class="empty" v-else>暂无预算规则</div>
        </div>

        <!-- 总账摘要 -->
        <div class="panel">
          <h4>总账概览</h4>
          <table class="table" v-if="summary.ledger?.length">
            <thead>
              <tr><th>科目编码</th><th>科目名称</th><th>期初</th><th>本期借方</th><th>本期贷方</th><th>期末</th></tr>
            </thead>
            <tbody>
              <tr v-for="row in summary.ledger" :key="row.account_code">
                <td class="mono">{{ row.account_code }}</td>
                <td>{{ row.account_name }}</td>
                <td>¥{{ fmt(row.opening) }}</td>
                <td>¥{{ fmt(row.debit) }}</td>
                <td>¥{{ fmt(row.credit) }}</td>
                <td>¥{{ fmt(row.closing) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { request, getUser } from '../../api'

const summary = ref({})
const loading = ref(false)
const errorMsg = ref('')

const isFinance = getUser()?.role === 'finance'

const loadSummary = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    summary.value = await request('/api/reports/summary')
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    loading.value = false
  }
}

const fmt = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

// TOP 原因条形：以最大计数为基准
const barWidth = (count) => {
  const list = summary.value.audit?.top_reasons || []
  if (!list.length) return '0%'
  const max = Math.max(...list.map(i => i.count))
  return `${Math.round((count / max) * 100)}%`
}

const rateClass = (rate) => {
  if (rate === null || rate === undefined) return ''
  if (rate > 100) return 'over'
  if (rate >= 80) return 'warn'
  return 'safe'
}

onMounted(() => { if (isFinance) loadSummary() })
</script>

<style scoped>
.page {
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  min-height: calc(100vh - 140px);
}

.content {
  margin-top: 20px;
}

.toolbar {
  margin-bottom: 16px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  background: #f5f7fa;
  color: #333;
}

.btn.primary {
  background: #409eff;
  color: white;
}

.btn:disabled {
  background: #c0c4cc;
  cursor: not-allowed;
}

.msg.err {
  margin-bottom: 16px;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 13px;
  background: #fef0f0;
  color: #f56c6c;
}

/* 统计卡片 */
.card-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.card {
  flex: 1;
  min-width: 160px;
  padding: 18px 20px;
  background: #f8f9fb;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.card.highlight {
  background: #ecf5ff;
  border-color: #d9ecff;
}

.card-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.card-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.card-value .unit {
  font-size: 14px;
  font-weight: 400;
  margin-left: 2px;
}

.warn-text { color: #e6a23c; }
.rej-text { color: #f56c6c; }
.ok-text { color: #67c23a; }

/* 分区面板 */
.section-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.panel {
  flex: 1;
  min-width: 320px;
  padding: 16px 20px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  margin-bottom: 20px;
}

.section-row .panel {
  margin-bottom: 0;
}

.panel h4 {
  margin-bottom: 14px;
  color: #303133;
}

/* 原因 TOP 榜 */
.top-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.top-rank {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.top-reason {
  width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  color: #606266;
  flex-shrink: 0;
}

.top-bar {
  flex: 1;
  height: 10px;
  background: #f0f0f0;
  border-radius: 5px;
  overflow: hidden;
}

.top-fill {
  height: 100%;
  background: #f56c6c;
  border-radius: 5px;
  transition: width 0.3s;
}

.top-count {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}

/* 发票概况 */
.inv-line {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px dashed #ebeef5;
  font-size: 14px;
  color: #606266;
}

.inv-line.total {
  border-bottom: none;
  font-weight: 600;
  color: #303133;
}

/* 表格 */
.table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #ebeef5;
}

.table th,
.table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
  font-size: 13px;
}

.table th {
  background: #f5f7fa;
}

.mono {
  font-family: Consolas, monospace;
}

.rate-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rate-bar {
  width: 90px;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.rate-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}

.rate-fill.safe { background: #409eff; }
.rate-fill.warn { background: #e6a23c; }
.rate-fill.over { background: #f56c6c; }

.empty {
  text-align: center;
  padding: 30px 0;
  color: #909399;
}
</style>
