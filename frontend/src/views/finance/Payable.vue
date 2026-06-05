<template>
  <div class="page">
    <h3>应付管理</h3>
    <div class="content">
      <div class="toolbar">
        <button class="btn primary" @click="showDialog = true">+ 新增应付单</button>
        <button class="btn default" @click="showPayDialog = true">付款核销</button>
      </div>

      <!-- 新增应付单对话框 -->
      <div class="dialog-overlay" v-if="showDialog" @click.self="showDialog = false">
        <div class="dialog">
          <h4>新增应付单</h4>
          <div class="form-group">
            <label>供应商名称：</label>
            <input v-model="newPayable.supplier" placeholder="请输入供应商名称" />
          </div>
          <div class="form-group">
            <label>应付金额：</label>
            <input v-model.number="newPayable.amount" type="number" placeholder="请输入金额" />
          </div>
          <div class="form-group">
            <label>业务类型：</label>
            <select v-model="newPayable.type">
              <option value="采购原材料">采购原材料</option>
              <option value="采购服务">采购服务</option>
              <option value="其他">其他</option>
            </select>
          </div>
          <div class="form-group">
            <label>说明：</label>
            <textarea v-model="newPayable.desc" placeholder="请输入说明"></textarea>
          </div>
          <div class="dialog-btns">
            <button class="btn cancel" @click="showDialog = false">取消</button>
            <button class="btn confirm" @click="submitPayable">提交</button>
          </div>
        </div>
      </div>

      <!-- 付款核销对话框 -->
      <div class="dialog-overlay" v-if="showPayDialog" @click.self="showPayDialog = false">
        <div class="dialog">
          <h4>付款核销</h4>
          <div class="form-group">
            <label>选择应付单：</label>
            <select v-model="payForm.id">
              <option value="">请选择</option>
              <option v-for="item in unpaidList" :key="item.id" :value="item.id">
                {{ item.id }} - {{ item.supplier }} - ¥{{ item.amount.toFixed(2) }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>付款金额：</label>
            <input v-model.number="payForm.amount" type="number" placeholder="请输入付款金额" />
          </div>
          <div class="form-group">
            <label>付款方式：</label>
            <select v-model="payForm.method">
              <option value="银行转账">银行转账</option>
              <option value="现金">现金</option>
              <option value="支票">支票</option>
            </select>
          </div>
          <div class="dialog-btns">
            <button class="btn cancel" @click="showPayDialog = false">取消</button>
            <button class="btn confirm" @click="submitPay">确认付款</button>
          </div>
        </div>
      </div>

      <!-- 应付单列表 -->
      <table class="table" v-if="financeStore.payableList.length > 0">
        <thead>
          <tr>
            <th>应付单号</th>
            <th>供应商名称</th>
            <th>业务类型</th>
            <th>应付金额</th>
            <th>已付金额</th>
            <th>未付金额</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in financeStore.payableList" :key="item.id">
            <td>{{ item.id }}</td>
            <td>{{ item.supplier }}</td>
            <td>{{ item.type }}</td>
            <td>¥{{ item.amount.toFixed(2) }}</td>
            <td>¥{{ item.paid.toFixed(2) }}</td>
            <td>¥{{ (item.amount - item.paid).toFixed(2) }}</td>
            <td>
              <span class="status" :class="item.status">
                {{ statusMap[item.status] }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="empty" v-else>暂无应付数据</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useFinanceStore } from '../../stores/finance'

const financeStore = useFinanceStore()

const showDialog = ref(false)
const showPayDialog = ref(false)

const newPayable = ref({
  supplier: '供应商X公司',
  amount: 5000,
  type: '采购原材料',
  desc: '采购原材料一批'
})

const payForm = ref({
  id: '',
  amount: 0,
  method: '银行转账'
})

const statusMap = {
  unpaid: '未付款',
  partial: '部分付款',
  paid: '已结清'
}

const unpaidList = computed(() => {
  return financeStore.payableList.filter(item => item.status !== 'paid')
})

const submitPayable = () => {
  const id = 'YF202405' + String(financeStore.payableList.length + 1).padStart(2, '0')
  financeStore.payableList.push({
    id,
    supplier: newPayable.value.supplier,
    type: newPayable.value.type,
    amount: newPayable.value.amount,
    paid: 0,
    desc: newPayable.value.desc,
    status: 'unpaid',
    date: new Date().toISOString().split('T')[0]
  })
  showDialog.value = false
  alert('应付单创建成功！单号：' + id)
}

const submitPay = () => {
  if (!payForm.value.id) {
    alert('请选择应付单！')
    return
  }
  const item = financeStore.payableList.find(i => i.id === payForm.value.id)
  if (item) {
    const unpaid = item.amount - item.paid
    if (payForm.value.amount > unpaid) {
      alert('付款金额不能超过未付金额！')
      return
    }
    item.paid += payForm.value.amount
    item.status = item.paid >= item.amount ? 'paid' : 'partial'
    showPayDialog.value = false
    alert('付款核销成功！')
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
  display: flex;
  gap: 12px;
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

.btn.default {
  background: #f5f7fa;
  color: #333;
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
}

.status.unpaid {
  background: #fdf6ec;
  color: #e6a23c;
}

.status.partial {
  background: #ecf5ff;
  color: #409eff;
}

.status.paid {
  background: #f0f9eb;
  color: #67c23a;
}

.empty {
  text-align: center;
  padding: 40px 0;
  color: #909399;
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

.btn.cancel {
  background: #f5f7fa;
  color: #333;
}

.btn.confirm {
  background: #409eff;
  color: white;
}
</style>