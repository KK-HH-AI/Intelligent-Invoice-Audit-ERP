<template>
  <div class="page">
    <h3>应收管理</h3>
    <div class="content">
      <!-- 顶部导航按钮 -->
      <div class="toolbar">
        <button class="btn primary" @click="showDialog = true">+ 新增应收单</button>
        <button class="btn default" @click="showReceiveDialog = true">收款核销</button>
      </div>

      <!-- 应收单对话框 -->
      <div class="dialog-overlay" v-if="showDialog" @click.self="showDialog = false">
        <div class="dialog">
          <h4>新增应收单</h4>
          <div class="form-group">
            <label>客户名称：</label>
            <input v-model="newReceivable.customer" placeholder="请输入客户名称" />
          </div>
          <div class="form-group">
            <label>应收金额：</label>
            <input v-model.number="newReceivable.amount" type="number" placeholder="请输入金额" />
          </div>
          <div class="form-group">
            <label>业务类型：</label>
            <select v-model="newReceivable.type">
              <option value="销售商品">销售商品</option>
              <option value="提供服务">提供服务</option>
              <option value="其他">其他</option>
            </select>
          </div>
          <div class="form-group">
            <label>说明：</label>
            <textarea v-model="newReceivable.desc" placeholder="请输入说明"></textarea>
          </div>
          <div class="dialog-btns">
            <button class="btn cancel" @click="showDialog = false">取消</button>
            <button class="btn confirm" @click="submitReceivable">提交</button>
          </div>
        </div>
      </div>

      <!-- 收款核销对话框 -->
      <div class="dialog-overlay" v-if="showReceiveDialog" @click.self="showReceiveDialog = false">
        <div class="dialog">
          <h4>收款核销</h4>
          <div class="form-group">
            <label>选择应收单：</label>
            <select v-model="receiveForm.id">
              <option value="">请选择</option>
              <option v-for="item in unpaidList" :key="item.id" :value="item.id">
                {{ item.id }} - {{ item.customer }} - ¥{{ item.amount.toFixed(2) }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>收款金额：</label>
            <input v-model.number="receiveForm.amount" type="number" placeholder="请输入收款金额" />
          </div>
          <div class="form-group">
            <label>收款方式：</label>
            <select v-model="receiveForm.method">
              <option value="银行转账">银行转账</option>
              <option value="现金">现金</option>
              <option value="支票">支票</option>
            </select>
          </div>
          <div class="dialog-btns">
            <button class="btn cancel" @click="showReceiveDialog = false">取消</button>
            <button class="btn confirm" @click="submitReceive">确认核销</button>
          </div>
        </div>
      </div>

      <!-- 应收单列表 -->
      <table class="table" v-if="financeStore.receivableList.length > 0">
        <thead>
          <tr>
            <th>应收单号</th>
            <th>客户名称</th>
            <th>业务类型</th>
            <th>应收金额</th>
            <th>已收金额</th>
            <th>未收金额</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in financeStore.receivableList" :key="item.id">
            <td>{{ item.id }}</td>
            <td>{{ item.customer }}</td>
            <td>{{ item.type }}</td>
            <td>¥{{ item.amount.toFixed(2) }}</td>
            <td>¥{{ item.received.toFixed(2) }}</td>
            <td>¥{{ (item.amount - item.received).toFixed(2) }}</td><!-- tofixed:强制保留小数点后 2 位 -->
            <td>
              <span class="status" :class="item.status">
                {{ statusMap[item.status] }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="empty" v-else>暂无应收数据</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useFinanceStore } from '../../stores/finance'

const showDialog = ref(false)
const showReceiveDialog = ref(false)
const newReceivable = ref({
  customer: '客户A公司',
  amount: 10000,
  type: '销售商品',
  desc: '销售产品一批'
})
const receiveForm = ref({
  id: '',
  amount: 0,
  method: '银行转账'
})

const financeStore = useFinanceStore()//全局共享状态

const statusMap = {
  unpaid: '未收款',
  partial: '部分收款',
  paid: '已结清'
}

//计算属性：未收款应收单列表
const unpaidList = computed(() => {
  return financeStore.receivableList.filter(item => item.status !== 'paid')
})

// 1. 创建并提交【应收单】
const submitReceivable = () => {
  // 生成唯一应收单号：YS20240501、YS20240502...
  const id = 'YS202405' + String(financeStore.receivableList.length + 1).padStart(2, '0')
  
  // 把新应收单添加到列表中
  financeStore.receivableList.push({
    id,                  // 应收单号
    customer: newReceivable.value.customer, // 客户名称
    type: newReceivable.value.type,         // 款项类型
    amount: newReceivable.value.amount,     // 总应收金额
    received: 0,         // 已收金额（默认0）
    desc: newReceivable.value.desc,         // 备注说明
    status: 'unpaid',     // 状态：未收款
    date: new Date().toISOString().split('T')[0] // 创建日期
  })
  
  // 关闭弹窗
  showDialog.value = false
  // 提示成功
  alert('应收单创建成功！单号：' + id)
}

// 2. 提交【收款核销】（给某个应收单收钱）
const submitReceive = () => {
  // 如果没选择要收款的应收单 → 提示并退出
  if (!receiveForm.value.id) {
    alert('请选择应收单！')
    return
  }

  // 根据选中的应收单号，找到对应的应收单数据
  const item = financeStore.receivableList.find(i => i.id === receiveForm.value.id)
  
  // 如果找到了这条应收单
  if (item) {
    // 计算：未收金额 = 总金额 - 已收金额
    const unpaid = item.amount - item.received
    
    // 如果填写的收款金额 > 未收金额 → 提示错误，不允许提交
    if (receiveForm.value.amount > unpaid) {
      alert('收款金额不能超过未收金额！')
      return
    }

    // 把本次收款金额，累加到“已收金额”里
    item.received += receiveForm.value.amount
    
    // 更新状态：
    // 如果已收 >= 总金额 → 状态为“已结清(paid)”
    // 否则 → 状态为“部分收款(partial)”
    item.status = item.received >= item.amount ? 'paid' : 'partial'
    
    // 关闭收款弹窗
    showReceiveDialog.value = false
    // 提示成功
    alert('收款核销成功！')
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