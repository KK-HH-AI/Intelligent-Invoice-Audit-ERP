<template>
  <div class="page">
    <h3>审查归档</h3>
    <div class="content">
      <!-- 筛选工具栏 -->
      <div class="toolbar">
        <input class="ipt" v-model="query.invoice_no" placeholder="按发票号模糊查询" @keyup.enter="loadReports" />
        <select class="ipt" v-model="query.result">
          <option value="">全部结论</option>
          <option value="通过">通过</option>
          <option value="预警">预警</option>
          <option value="驳回">驳回</option>
        </select>
        <button class="btn primary" @click="loadReports">查询</button>
        <button class="btn" @click="resetQuery">重置</button>
      </div>

      <!-- 归档流水 -->
      <table class="table" v-if="reports.length > 0">
        <thead>
          <tr>
            <th>发票号</th>
            <th>供应商</th>
            <th>金额</th>
            <th>类别</th>
            <th>结论</th>
            <th>原因</th>
            <th>审查时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in reports" :key="item.id">
            <td class="mono">{{ item.invoice_no }}</td>
            <td>{{ item.seller || '-' }}</td>
            <td>¥{{ Number(item.amount).toFixed(2) }}</td>
            <td>{{ item.category || '-' }}</td>
            <td><span class="status" :class="resultClass(item.result)">{{ item.result }}</span></td>
            <td class="reason-cell" :title="item.reason">{{ item.reason || '-' }}</td>
            <td>{{ item.created_at }}</td>
            <td><button class="btn-sm" @click="openDetail(item)">查看报告</button></td>
          </tr>
        </tbody>
      </table>
      <div class="empty" v-else>暂无审查报告</div>

      <!-- 报告详情（按单据追溯） -->
      <div class="dialog-overlay" v-if="detail" @click.self="detail = null">
        <div class="dialog">
          <h4>审查报告 #{{ detail.id }} — {{ detail.invoice_no }}</h4>
          <div class="meta-row">
            <span>供应商：{{ detail.seller || '-' }}</span>
            <span>金额：¥{{ Number(detail.amount).toFixed(2) }}</span>
            <span>类别：{{ detail.category || '-' }}</span>
            <span>用途：{{ detail.kind }}</span>
            <span>开票日期：{{ detail.invoice_date || '-' }}</span>
            <span>
              结论：<span class="status" :class="resultClass(detail.result)">{{ detail.result }}</span>
            </span>
          </div>
          <div class="reason-bar" v-if="detail.reason">原因：{{ detail.reason }}</div>
          <div class="report-md" v-html="renderedMd"></div>
          <div class="dialog-btns">
            <button class="btn" @click="detail = null">关闭</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { request } from '../../api'
import { renderMarkdown } from '../../markdown'

const reports = ref([])
const query = ref({ invoice_no: '', result: '' })
const detail = ref(null)

const renderedMd = computed(() =>
  detail.value ? renderMarkdown(detail.value.content_md || '') : ''
)

const loadReports = async () => {
  try {
    const params = new URLSearchParams()
    if (query.value.invoice_no) params.append('invoice_no', query.value.invoice_no)
    if (query.value.result) params.append('result', query.value.result)
    const qs = params.toString()
    reports.value = await request('/api/audit/reports' + (qs ? `?${qs}` : ''))
  } catch (e) {
    alert(e.message)
  }
}

const resetQuery = () => {
  query.value = { invoice_no: '', result: '' }
  loadReports()
}

const openDetail = async (item) => {
  try {
    detail.value = await request(`/api/audit/reports/${item.id}`)
  } catch (e) {
    alert(e.message)
  }
}

const resultClass = (result) =>
  ({ 通过: 'st-ok', 预警: 'st-warn', 驳回: 'st-rej' }[result] || '')

onMounted(loadReports)
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
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.ipt {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.ipt:first-child {
  width: 220px;
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

.table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #ebeef5;
}

.table th,
.table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
}

.table th {
  background: #f5f7fa;
}

.mono {
  font-family: Consolas, monospace;
  font-size: 13px;
}

.reason-cell {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #909399;
  font-size: 13px;
}

.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
}

.st-ok {
  background: #f0f9eb;
  color: #67c23a;
}

.st-warn {
  background: #fdf6ec;
  color: #e6a23c;
}

.st-rej {
  background: #fef0f0;
  color: #f56c6c;
}

.btn-sm {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  background: #409eff;
  color: white;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  padding: 24px;
  border-radius: 8px;
  width: 720px;
  max-width: 92%;
  max-height: 85vh;
  overflow-y: auto;
}

.dialog h4 {
  margin-bottom: 16px;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 13px;
  color: #606266;
}

.reason-bar {
  margin-top: 12px;
  padding: 10px 16px;
  background: #fef0f0;
  color: #f56c6c;
  border-radius: 6px;
  font-size: 13px;
}

.report-md {
  margin-top: 16px;
  font-size: 14px;
  line-height: 1.7;
}

.dialog-btns {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.empty {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}
</style>
