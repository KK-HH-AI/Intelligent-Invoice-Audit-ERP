<template>
  <div class="page">
    <h3>发票台账</h3>
    <div class="content">
      <div class="toolbar">
        <button class="btn" @click="loadList" :disabled="loadingList">
          {{ loadingList ? '加载中...' : '刷新' }}
        </button>
      </div>

      <!-- 发票列表 -->
      <table class="table" v-if="list.length > 0">
        <thead>
          <tr>
            <th>发票号码</th>
            <th>开票日期</th>
            <th>销售方</th>
            <th>价税合计</th>
            <th>税额</th>
            <th>状态</th>
            <th>关联报销单</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in list" :key="item.id" class="clickable"
            :class="{ selected: selectedId === item.id }" @click="selectItem(item)">
            <td>{{ item.invoice_no }}</td>
            <td>{{ item.invoice_date || '-' }}</td>
            <td>{{ item.seller || '-' }}</td>
            <td>{{ fmtMoney(item.amount) }}</td>
            <td>{{ item.tax ?? '-' }}</td>
            <td><span class="status" :class="statusClass(item.status)">{{ item.status }}</span></td>
            <td>{{ item.reimburse_id ? '#' + item.reimburse_id : '-' }}</td>
          </tr>
        </tbody>
      </table>
      <div class="empty" v-else-if="!loadingList">暂无发票，请先在「发票上传」页上传</div>

      <!-- 详情：基础信息 + 附件 + 最新审查报告 -->
      <div class="detail-area" v-if="detail">
        <h4>发票详情 #{{ detail.invoice.id }}</h4>
        <div class="detail-grid">
          <div class="grid-item"><label>发票号码</label><span>{{ detail.invoice.invoice_no }}</span></div>
          <div class="grid-item"><label>开票日期</label><span>{{ detail.invoice.invoice_date || '-' }}</span></div>
          <div class="grid-item"><label>销售方</label><span>{{ detail.invoice.seller || '-' }}</span></div>
          <div class="grid-item"><label>价税合计</label><span>{{ fmtMoney(detail.invoice.amount) }}</span></div>
          <div class="grid-item"><label>税额</label><span>{{ detail.invoice.tax ?? '-' }}</span></div>
          <div class="grid-item"><label>状态</label>
            <span class="status" :class="statusClass(detail.invoice.status)">{{ detail.invoice.status }}</span>
          </div>
        </div>

        <h4>随单附件</h4>
        <ul class="attach-list" v-if="detail.attachments.length">
          <li v-for="a in detail.attachments" :key="a.id">{{ a.file_path }}</li>
        </ul>
        <div class="empty small" v-else>无附件</div>

        <template v-if="detail.report">
          <h4>最新审查报告</h4>
          <div class="card">
            <div class="card-header">
              <span>{{ detail.report.created_at }}</span>
              <span class="status" :class="statusClass(detail.report.result)">{{ detail.report.result }}</span>
            </div>
            <div class="card-body markdown-content" v-html="renderMarkdown(detail.report.content_md)"></div>
          </div>
        </template>
        <div class="empty small" v-else>暂无审查报告</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { request } from '../../api'
import { renderMarkdown } from '../../markdown'

const list = ref([])
const loadingList = ref(false)
const selectedId = ref(null)
const detail = ref(null)

const loadList = async () => {
  loadingList.value = true
  try {
    list.value = await request('/api/invoices')
  } catch (e) {
    alert(e.message)
  } finally {
    loadingList.value = false
  }
}

const selectItem = async (item) => {
  selectedId.value = item.id
  try {
    detail.value = await request(`/api/invoices/${item.id}`)
  } catch (e) {
    alert(e.message)
  }
}

const fmtMoney = (v) => (v === null || v === undefined) ? '-' : '¥' + Number(v).toFixed(2)

const statusClass = (status) => ({
  '已通过': 'st-ok',
  '待审': 'st-warn',
  '预警': 'st-warn',
  '已驳回': 'st-bad',
}[status] || 'st-gray')

onMounted(loadList)
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
  background: #409eff;
  color: white;
}

.btn:disabled {
  background: #c0c4cc;
  cursor: not-allowed;
}

.table {
  width: 100%;
  border-collapse: collapse;
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

.table tbody tr.clickable {
  cursor: pointer;
}

.table tbody tr.clickable:hover {
  background: #f5f9ff;
}

.table tbody tr.selected {
  background: #ecf5ff;
}

.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
}

.st-ok { background: #f0f9eb; color: #67c23a; }
.st-warn { background: #fdf6ec; color: #e6a23c; }
.st-bad { background: #fef0f0; color: #f56c6c; }
.st-gray { background: #f4f4f5; color: #909399; }

.empty {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}

.empty.small {
  padding: 12px 0;
  text-align: left;
  font-size: 13px;
}

.detail-area {
  margin-top: 24px;
  border-top: 1px solid #ebeef5;
  padding-top: 16px;
}

.detail-area h4 {
  margin: 12px 0;
  color: #333;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.grid-item label {
  display: block;
  color: #909399;
  font-size: 12px;
  margin-bottom: 4px;
}

.grid-item span {
  color: #333;
}

.attach-list {
  margin: 0 0 8px 0;
  padding-left: 20px;
  color: #606266;
  font-size: 13px;
}

.card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
}

.card-header {
  background: #f5f7fa;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #909399;
  font-size: 13px;
}

.card-body {
  padding: 16px;
}

.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4) {
  margin: 8px 0;
}
</style>
