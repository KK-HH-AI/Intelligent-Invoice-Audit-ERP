<template>
  <div class="page">
    <h3>凭证生成</h3>
    <div class="content">
      <div class="empty" v-if="!isFinance">仅财务角色可访问凭证管理</div>

      <template v-else>
      <div class="toolbar">
        <button class="btn primary" @click="openDialog">+ 从已通过报销单生成凭证</button>
      </div>

      <!-- 生成凭证对话框 -->
      <div class="dialog-overlay" v-if="showDialog" @click.self="showDialog = false">
        <div class="dialog">
          <h4>从已通过的报销单生成凭证</h4>
          <div class="form-group">
            <label>选择报销单（已审批通过且未生成过凭证）：</label>
            <select v-model="generateForm.reimburse_id">
              <option value="">请选择</option>
              <option v-for="item in availableSources" :key="item.id" :value="item.id">
                {{ item.code }} - {{ item.description || item.type }} - ¥{{ Number(item.amount).toFixed(2) }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>分录模板（后端自动生成）：</label>
            <div class="template-hint">
              借：6602 管理费用　　贷：1002 银行存款
            </div>
          </div>
          <div class="dialog-btns">
            <button class="btn cancel" @click="showDialog = false">取消</button>
            <button class="btn confirm" @click="generateVoucher">生成凭证</button>
          </div>
        </div>
      </div>

      <!-- 凭证列表 -->
      <table class="voucher-table" v-if="voucherList.length > 0">
        <thead>
          <tr>
            <th>凭证编号</th>
            <th>日期</th>
            <th>摘要</th>
            <th>会计科目</th>
            <th>借方金额</th>
            <th>贷方金额</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in voucherList" :key="item.id">
            <td>{{ item.code }}</td>
            <td>{{ (item.created_at || '').slice(0, 10) }}</td>
            <td>{{ item.summary }}</td>
            <td>
              <div v-for="entry in item.entries" :key="entry.account">
                {{ entry.account }} {{ entry.accountName }}
              </div>
            </td>
            <td>
              <div v-for="entry in item.entries" :key="entry.account">
                {{ entry.debit > 0 ? '¥' + Number(entry.debit).toFixed(2) : '' }}
              </div>
            </td>
            <td>
              <div v-for="entry in item.entries" :key="entry.account">
                {{ entry.credit > 0 ? '¥' + Number(entry.credit).toFixed(2) : '' }}
              </div>
            </td>
            <td>
              <span class="status" :class="item.status">{{ statusMap[item.status] }}</span>
            </td>
            <td>
              <button v-if="item.status === 'draft'" class="btn-sm approve"
                @click="approveVoucher(item.id)">审核</button>
              <button v-else-if="item.status === 'approved'" class="btn-sm post"
                @click="postVoucher(item.id)">过账</button>
              <span v-else>-</span>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="empty" v-else>暂无凭证数据，请从已通过的报销单生成</div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { request, getUser } from '../../api'

const voucherList = ref([])
const reimburseList = ref([])
const showDialog = ref(false)
const generateForm = ref({ reimburse_id: '' })

const isFinance = getUser()?.role === 'finance'

const statusMap = {
  draft: '草稿',
  approved: '已审核',
  posted: '已过账',
}

// 一期仅支持报销单凭证（应收/应付为二期范围）
const availableSources = computed(() => {
  const usedIds = new Set(voucherList.value.map(v => v.reimburse_id))
  return reimburseList.value.filter(
    item => item.status === '已通过' && !usedIds.has(item.id)
  )
})

const loadAll = async () => {
  try {
    const [vouchers, reimburses] = await Promise.all([
      request('/api/vouchers'),
      request('/api/reimburse'),
    ])
    voucherList.value = vouchers
    reimburseList.value = reimburses
  } catch (e) {
    alert(e.message)
  }
}

const openDialog = () => {
  generateForm.value = { reimburse_id: '' }
  showDialog.value = true
}

const generateVoucher = async () => {
  if (!generateForm.value.reimburse_id) {
    alert('请选择报销单！')
    return
  }
  try {
    const created = await request('/api/vouchers/generate', {
      method: 'POST',
      body: { reimburse_id: generateForm.value.reimburse_id },
    })
    showDialog.value = false
    alert('凭证生成成功！编号：' + created.code)
    await loadAll()
  } catch (e) {
    alert(e.message)
  }
}

const approveVoucher = async (id) => {
  try {
    await request(`/api/vouchers/${id}/approve`, { method: 'POST' })
    alert('凭证已审核！')
    await loadAll()
  } catch (e) {
    alert(e.message)
  }
}

const postVoucher = async (id) => {
  try {
    await request(`/api/vouchers/${id}/post`, { method: 'POST' })
    alert('凭证已过账！可前往总账查看。')
    await loadAll()
  } catch (e) {
    alert(e.message)
  }
}

onMounted(loadAll)
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

.voucher-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #ebeef5;
}

.voucher-table th,
.voucher-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
}

.voucher-table th {
  background: #f5f7fa;
}

.empty {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}

.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status.draft {
  background: #f4f4f5;
  color: #909399;
}

.status.approved {
  background: #ecf5ff;
  color: #409eff;
}

.status.posted {
  background: #f0f9eb;
  color: #67c23a;
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

.template-hint {
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 6px;
  color: #606266;
  font-size: 13px;
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

.btn-sm {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  margin-right: 8px;
}

.btn-sm.approve {
  background: #409eff;
  color: white;
}

.btn-sm.post {
  background: #67c23a;
  color: white;
}
</style>
