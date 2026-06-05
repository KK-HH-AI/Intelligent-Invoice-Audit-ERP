<template>
  <div class="page">
    <h3>凭证生成</h3>
    <div class="content">
      <div class="toolbar">
        <button class="btn primary" @click="showDialog = true">+ 从业务单据生成凭证</button>
      </div>

      <!-- 生成凭证对话框 -->
      <div class="dialog-overlay" v-if="showDialog" @click.self="showDialog = false">
        <div class="dialog">
          <h4>从业务单据生成凭证</h4>
          <div class="form-group">
            <label>选择单据类型：</label>
            <select v-model="generateForm.sourceType">
              <option value="reimburse">费用报销单</option>
              <option value="receivable">应收单</option>
              <option value="payable">应付单</option>
            </select>
          </div>
          <div class="form-group">
            <label>选择单据：</label>
            <select v-model="generateForm.sourceId">
              <option value="">请选择</option>
              <option v-for="item in availableSources" :key="item.id" :value="item.id">
                {{ item.id }} - {{ item.desc || item.customer || item.supplier }} - ¥{{ item.amount.toFixed(2) }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>凭证日期：</label>
            <input type="date" v-model="generateForm.date" />
          </div>
          <div class="dialog-btns">
            <button class="btn cancel" @click="showDialog = false">取消</button>
            <button class="btn confirm" @click="generateVoucher">生成凭证</button>
          </div>
        </div>
      </div>

      <!-- 凭证列表 -->
      <table class="voucher-table" v-if="financeStore.voucherList.length > 0">
        <thead>
          <tr>
            <th>凭证编号</th>
            <th>凭证日期</th>
            <th>摘要</th>
            <th>会计科目</th>
            <th>借方金额</th>
            <th>贷方金额</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in financeStore.voucherList" :key="item.id">
            <td>{{ item.id }}</td>
            <td>{{ item.date }}</td>
            <td>{{ item.summary }}</td>
            <td>
              <div v-for="entry in item.entries" :key="entry.account">
                {{ entry.account }} {{ entry.accountName }}
              </div>
            </td>
            <td>
              <div v-for="entry in item.entries" :key="entry.account">
                {{ entry.debit > 0 ? '¥' + entry.debit.toFixed(2) : '' }}
              </div>
            </td>
            <td>
              <div v-for="entry in item.entries" :key="entry.account">
                {{ entry.credit > 0 ? '¥' + entry.credit.toFixed(2) : '' }}
              </div>
            </td>
            <td>
              <span class="status" :class="item.status">
                {{ statusMap[item.status] }}
              </span>
            </td>
            <td>
              <button 
                v-if="item.status === 'draft'" 
                class="btn-sm approve"
                @click="approveVoucher(item.id)"
              >审核</button>
              <button 
                v-if="item.status === 'approved'" 
                class="btn-sm post"
                @click="postVoucher(item.id)"
              >过账</button>
              <span v-else>-</span>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="empty" v-else>暂无凭证数据，请从业务单据生成</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useFinanceStore } from '../../stores/finance'

const financeStore = useFinanceStore()
const showDialog = ref(false)

// 记录要为哪个数据生成凭证
const generateForm = ref({
  sourceType: 'reimburse',
  sourceId: '',
  date: new Date().toISOString().split('T')[0]
})

const statusMap = {
  draft: '草稿',
  approved: '已审核',
  posted: '已过账'
}

// 根据选择的单据类型，获取对应的可生成凭证的单据
const availableSources = computed(() => {
  const type = generateForm.value.sourceType
  if (type === 'reimburse') {
    return financeStore.reimburseList.filter(item => item.status === 'approved')
  } else if (type === 'receivable') {
    // 应收单：所有单据都可以生成凭证（代表收入）
    return financeStore.receivableList
  } else if (type === 'payable') {
    // 应付单：所有单据都可以生成凭证（代表支出）
    return financeStore.payableList
  }
  return []
})

const generateVoucher = () => {
  if (!generateForm.value.sourceId) {
    alert('请选择业务单据！')
    return
  }
  
  const source = availableSources.value.find(s => s.id === generateForm.value.sourceId)
  if (!source) return

  //创建唯一的凭证编号
  const id = 'PZ-2024-' + String(financeStore.voucherList.length + 1).padStart(3, '0')
  
  // 生成凭证分录
  let entries = []
  let summary = ''
  
  if (generateForm.value.sourceType === 'reimburse') {
    entries = [
      { account: '6602', accountName: '管理费用', debit: source.amount, credit: 0 },
      { account: '1002', accountName: '银行存款', debit: 0, credit: source.amount }
    ]
    summary = '报销：' + source.desc
  } else if (generateForm.value.sourceType === 'receivable') {
    entries = [
      { account: '1122', accountName: '应收账款', debit: source.amount, credit: 0 },
      { account: '6001', accountName: '主营业务收入', debit: 0, credit: source.amount }
    ]
    summary = '销售：' + source.customer
  } else if (generateForm.value.sourceType === 'payable') {
    entries = [
      { account: '6401', accountName: '主营业务成本', debit: source.amount, credit: 0 },
      { account: '2202', accountName: '应付账款', debit: 0, credit: source.amount }
    ]
    summary = '采购：' + source.supplier
  }

  financeStore.voucherList.push({
    id,
    date: generateForm.value.date,
    summary,
    entries,
    status: 'draft'
  })
  
  showDialog.value = false
  alert('凭证生成成功！编号：' + id)
}

const approveVoucher = (id) => {
  const item = financeStore.voucherList.find(v => v.id === id)
  if (item) {
    item.status = 'approved'
    alert('凭证 ' + id + ' 已审核！')
  }
}
//将凭证信息更新到全局状态ledgerAccounts中
const postVoucher = (id) => {
  const item = financeStore.voucherList.find(v => v.id === id)
  if (item) {
    item.status = 'posted'
    // 过账：将凭证分录登记到总账科目中
    item.entries.forEach(entry => {
      const account = financeStore.ledgerAccounts.find(a => a.code === entry.account)
      if (account) {
        account.debit += entry.debit
        account.credit += entry.credit
        account.closing = account.opening + account.debit - account.credit
      }
    })
    alert('凭证 ' + id + ' 已过账！可前往总账查看。')
  }
}
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
  width: 400px;
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

.form-group input,
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