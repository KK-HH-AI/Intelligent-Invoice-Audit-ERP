<template>
  <div class="page">
    <h3>应付管理</h3>
    <div class="content">
      <div class="empty" v-if="!isFinance">仅财务角色可访问应付管理</div>

      <template v-else>
        <div class="toolbar">
          <button class="btn primary" @click="openDialog">+ 从采购发票生成应付单</button>
        </div>

        <!-- 生成应付单对话框 -->
        <div class="dialog-overlay" v-if="showDialog" @click.self="showDialog = false">
          <div class="dialog">
            <h4>从采购发票生成应付单</h4>
            <div class="form-group">
              <label>选择发票（用途=采购 且 AI 审查已通过）：</label>
              <select v-model="generateForm.invoice_id">
                <option value="">请选择</option>
                <option v-for="inv in availableInvoices" :key="inv.id" :value="inv.id">
                  {{ inv.invoice_no }} - {{ inv.seller || '未知销方' }} - ¥{{ Number(inv.amount).toFixed(2) }}
                </option>
              </select>
            </div>
            <div class="dialog-btns">
              <button class="btn cancel" @click="showDialog = false">取消</button>
              <button class="btn confirm" @click="generatePayable">生成应付单</button>
            </div>
          </div>
        </div>

        <!-- 应付单列表 -->
        <table class="table" v-if="payables.length > 0">
          <thead>
            <tr>
              <th>应付单号</th>
              <th>供应商</th>
              <th>金额</th>
              <th>关联发票</th>
              <th>关联凭证</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in payables" :key="item.id">
              <td>{{ item.code }}</td>
              <td>{{ item.supplier || '-' }}</td>
              <td>¥{{ Number(item.amount).toFixed(2) }}</td>
              <td>#{{ item.invoice_id }}</td>
              <td>{{ item.voucher_id ? '#' + item.voucher_id : '-' }}</td>
              <td><span class="status" :class="item.status === '已付款' ? 'st-ok' : 'st-warn'">{{ item.status }}</span></td>
              <td>
                <button v-if="item.status === '待付款'" class="btn-sm settle"
                  @click="settle(item.id)">生成凭证并过账</button>
                <span v-else>-</span>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="empty" v-else>暂无应付单据，请先在「发票上传」上传采购发票</div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { request, getUser } from '../../api'

const payables = ref([])
const approvedInvoices = ref([])
const showDialog = ref(false)
const generateForm = ref({ invoice_id: '' })

const isFinance = getUser()?.role === 'finance'

// 可选发票：采购 + 已通过 + 未生成过应付单
const availableInvoices = computed(() => {
  const usedIds = new Set(payables.value.map(p => p.invoice_id))
  return approvedInvoices.value.filter(
    inv => inv.kind === '采购' && !usedIds.has(inv.id)
  )
})

const loadAll = async () => {
  try {
    const [pays, invoices] = await Promise.all([
      request('/api/payables'),
      request('/api/invoices?status=' + encodeURIComponent('已通过')),
    ])
    payables.value = pays
    approvedInvoices.value = invoices
  } catch (e) {
    alert(e.message)
  }
}

const openDialog = () => {
  generateForm.value = { invoice_id: '' }
  showDialog.value = true
}

const generatePayable = async () => {
  if (!generateForm.value.invoice_id) {
    alert('请选择发票！')
    return
  }
  try {
    const created = await request('/api/payables/generate', {
      method: 'POST',
      body: { invoice_id: generateForm.value.invoice_id },
    })
    showDialog.value = false
    alert('应付单生成成功！编号：' + created.code)
    await loadAll()
  } catch (e) {
    alert(e.message)
  }
}

// 结算：生成凭证（借6401/贷2202）→ 过账 → 标记已付款
const settle = async (id) => {
  try {
    const data = await request(`/api/payables/${id}/settle`, { method: 'POST' })
    alert(`凭证 ${data.voucher_code} 已过账，应付单标记已付款！`)
    await loadAll()
  } catch (e) {
    alert(e.message)
  }
}

onMounted(() => { if (isFinance) loadAll() })
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
  margin-bottom: 20px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
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

.btn-sm.settle {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  background: #67c23a;
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
  width: 460px;
  max-width: 90%;
}

.dialog h4 {
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #666;
}

.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  box-sizing: border-box;
}

.dialog-btns {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.btn.cancel {
  background: #f5f7fa;
  color: #333;
}

.btn.confirm {
  background: #409eff;
  color: white;
}

.empty {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}
</style>
