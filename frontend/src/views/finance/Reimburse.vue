<template>
  <div class="page">
    <h3>费用报销</h3>
    <div class="content">
      <div class="reimburse-tabs">
        <div class="tab-item" :class="{ active: activeTab === 'all' }" @click="activeTab = 'all'">全部报销单</div>
        <div class="tab-item" :class="{ active: activeTab === 'pending' }" @click="activeTab = 'pending'">待财务审批</div>
        <div class="tab-item" :class="{ active: activeTab === 'done' }" @click="activeTab = 'done'">已审批</div>
      </div>

      <!-- 新增报销单：从已通过的发票创建 -->
      <div class="dialog-overlay" v-if="showDialog" @click.self="showDialog = false">
        <div class="dialog">
          <h4>从已通过的发票创建报销单</h4>
          <div class="form-group">
            <label>选择发票（仅 AI 审查通过的发票，金额自动取价税合计）：</label>
            <select v-model="newReimburse.invoice_id">
              <option value="">请选择</option>
              <option v-for="inv in approvedInvoices" :key="inv.id" :value="inv.id">
                {{ inv.invoice_no }} - ¥{{ Number(inv.amount).toFixed(2) }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>报销类型：</label>
            <select v-model="newReimburse.type">
              <option value="差旅费">差旅费</option>
              <option value="交通费">交通费</option>
              <option value="住宿费">住宿费</option>
              <option value="办公费">办公费</option>
              <option value="招待费">招待费</option>
            </select>
          </div>
          <div class="form-group">
            <label>报销说明：</label>
            <textarea v-model="newReimburse.description" placeholder="请输入报销说明"></textarea>
          </div>
          <div class="dialog-btns">
            <button class="btn cancel" @click="showDialog = false">取消</button>
            <button class="btn confirm" @click="submitReimburse" :disabled="submitting">
              {{ submitting ? '提交中...' : '提交' }}
            </button>
          </div>
        </div>
      </div>

      <!-- AI 意见对话框 -->
      <div class="dialog-overlay" v-if="aiOpinion" @click.self="aiOpinion = null">
        <div class="dialog wide">
          <h4>
            财务审批参考 - 发票 AI 审查意见
            <span class="status" :class="statusClass(aiOpinion.result)">{{ aiOpinion.result }}</span>
          </h4>
          <div class="markdown-content" v-html="renderMarkdown(aiOpinion.content_md)"></div>
          <div class="dialog-btns">
            <button class="btn confirm" @click="aiOpinion = null">知道了</button>
          </div>
        </div>
      </div>

      <!-- 报销单列表 -->
      <div class="reimburse-list">
        <table class="table" v-if="filteredList.length > 0">
          <thead>
            <tr>
              <th>报销单号</th>
              <th>报销人</th>
              <th>报销类型</th>
              <th>金额</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredList" :key="item.id">
              <td>{{ item.code }}</td>
              <td>{{ item.employee }}</td>
              <td>{{ item.type }}</td>
              <td>¥{{ Number(item.amount).toFixed(2) }}</td>
              <td><span class="status" :class="statusClass(item.status)">{{ item.status }}</span></td>
              <td>
                <template v-if="isFinance && item.status === '待财务审批'">
                  <button class="btn-sm approve" @click="settle(item.id, 'approve')">审核通过</button>
                  <button class="btn-sm reject" @click="settle(item.id, 'reject')">驳回</button>
                </template>
                <span v-else>-</span>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="empty" v-else>暂无报销单据</div>
        <button class="add-btn" @click="openDialog">+</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { request, getUser } from '../../api'
import { renderMarkdown } from '../../markdown'

const activeTab = ref('all')
const showDialog = ref(false)
const submitting = ref(false)
const list = ref([])              // 报销单列表（后端）
const approvedInvoices = ref([])  // 已通过发票（创建时选择）
const aiOpinion = ref(null)       // 审批响应里的 AI 意见
const newReimburse = ref({ invoice_id: '', type: '差旅费', description: '' })

// 财务角色才显示审批按钮
const isFinance = getUser()?.role === 'finance'

const filteredList = computed(() => {
  if (activeTab.value === 'all') return list.value
  if (activeTab.value === 'pending') {
    return list.value.filter(item => item.status === '待财务审批')
  }
  return list.value.filter(item => item.status !== '待财务审批')
})

const loadList = async () => {
  try {
    list.value = await request('/api/reimburse')
  } catch (e) {
    alert(e.message)
  }
}

const openDialog = async () => {
  newReimburse.value = { invoice_id: '', type: '差旅费', description: '' }
  showDialog.value = true
  try {
    // 拉取可报销发票：仅 AI 审查已通过
    approvedInvoices.value = await request('/api/invoices?status=' + encodeURIComponent('已通过'))
  } catch (e) {
    alert(e.message)
  }
}

const submitReimburse = async () => {
  if (!newReimburse.value.invoice_id) {
    alert('请选择发票')
    return
  }
  submitting.value = true
  try {
    const created = await request('/api/reimburse', {
      method: 'POST',
      body: {
        invoice_id: newReimburse.value.invoice_id,
        type: newReimburse.value.type,
        description: newReimburse.value.description,
      },
    })
    showDialog.value = false
    alert('报销单提交成功！单号：' + created.code)
    await loadList()
  } catch (e) {
    alert(e.message)
  } finally {
    submitting.value = false
  }
}

// 财务审批：通过/驳回，成功后展示发票 AI 意见
const settle = async (id, action) => {
  try {
    const data = await request(`/api/reimburse/${id}/${action}`, { method: 'POST' })
    aiOpinion.value = data.ai_opinion
    await loadList()
  } catch (e) {
    alert(e.message)
  }
}

const statusClass = (status) => ({
  '已通过': 'st-ok',
  '待财务审批': 'st-warn',
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

.reimburse-tabs {
  display: flex;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 20px;
}

.tab-item {
  padding: 12px 20px;
  cursor: pointer;
  position: relative;
}

.tab-item.active {
  color: #409eff;
  font-weight: 600;
}

.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 100%;
  height: 2px;
  background: #409eff;
}

.reimburse-list {
  position: relative;
  min-height: 300px;
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

.add-btn {
  position: fixed;
  bottom: 40px;
  right: 40px;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  border: none;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.3);
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
  width: 420px;
  max-width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.dialog.wide {
  width: 560px;
}

.dialog h4 {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #666;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  box-sizing: border-box;
}

.form-group textarea {
  height: 80px;
  resize: vertical;
}

.dialog-btns {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn:disabled {
  background: #c0c4cc;
  cursor: not-allowed;
}

.btn.cancel {
  background: #f5f7fa;
  color: #333;
}

.btn.confirm {
  background: #409eff;
  color: white;
}

.btn-sm {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  margin-right: 8px;
}

.btn-sm.approve {
  background: #67c23a;
  color: white;
}

.btn-sm.reject {
  background: #f56c6c;
  color: white;
}

.markdown-content {
  font-size: 14px;
  color: #333;
  line-height: 1.7;
}

.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4) {
  margin: 8px 0;
}
</style>
