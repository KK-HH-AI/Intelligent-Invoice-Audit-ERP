<template>
  <div class="page">
    <h3>费用报销</h3>
    <div class="content">
      <div class="reimburse-tabs">
        <div 
          class="tab-item" 
          :class="{ active: activeTab === 'all' }"
          @click="activeTab = 'all'"
        >全部报销单</div>
        <div 
          class="tab-item" 
          :class="{ active: activeTab === 'pending' }"
          @click="activeTab = 'pending'"
        >待审批</div>
        <div 
          class="tab-item" 
          :class="{ active: activeTab === 'done' }"
          @click="activeTab = 'done'"
        >已审批</div>
      </div>

      <!-- 新增报销单对话框 -->
      <div class="dialog-overlay" v-if="showDialog" @click.self="showDialog = false"><!--遮罩（表单（按钮））-->>
        <div class="dialog">
          <h4>新增报销单</h4>
          <div class="form-group">
            <label>报销人：</label>
            <input v-model="newReimburse.employee" placeholder="请输入报销人" />
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
            <label>报销金额：</label>
            <input v-model.number="newReimburse.amount" type="number" placeholder="请输入金额" />
          </div>
          <div class="form-group">
            <label>报销说明：</label>
            <textarea v-model="newReimburse.desc" placeholder="请输入报销说明"></textarea>
          </div>
          <div class="dialog-btns">
            <button class="btn cancel" @click="showDialog = false">取消</button>
            <button class="btn confirm" @click="submitReimburse">提交</button>
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
            <tr v-for="item in filteredList" :key="item.id"><!--每一行都有一个id-->
              <td>{{ item.id }}</td>
              <td>{{ item.employee }}</td>
              <td>{{ item.type }}</td>
              <td>¥{{ item.amount.toFixed(2) }}</td>
              <td>
                <span class="status" :class="item.status">
                  {{ statusMap[item.status] }}
                </span>
              </td>
              <td>
                <button 
                  v-if="item.status === 'pending' && activeTab === 'pending'" 
                  class="btn-sm approve"
                  @click="approveReimburse(item.id)"
                >审核通过</button>
                <button 
                  v-if="item.status === 'pending' && activeTab === 'pending'" 
                  class="btn-sm reject"
                  @click="rejectReimburse(item.id)"
                >驳回</button>
                <span v-else>-</span>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="empty" v-else>暂无报销单据</div>
        <button class="add-btn" @click="showDialog = true">+</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useFinanceStore } from '../../stores/finance'

const activeTab = ref('all')
const showDialog = ref(false)
const newReimburse = ref({
  employee: '张三',
  type: '差旅费',
  amount: 1300,
  desc: '2024年5月出差北京，交通费500元，住宿费800元'
})

const financeStore = useFinanceStore()//全局共享状态
const statusMap = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已驳回'
}

//计算属性
const filteredList = computed(() => {
  if (activeTab.value === 'all') {
    return financeStore.reimburseList
  } else if (activeTab.value === 'pending') {
    return financeStore.reimburseList.filter(item => item.status === 'pending')
  } else {
    return financeStore.reimburseList.filter(item => item.status === 'approved' || item.status === 'rejected')
  }
})

const submitReimburse = () => {
  // 1. 生成唯一报销单号：BX20240501、BX20240502…
  const id = 'BX202405' + String(financeStore.reimburseList.length + 1).padStart(2, '0')

  // 2. 把表单数据 push 到报销列表里
  financeStore.reimburseList.push({
    id,               // 单号
    employee: newReimburse.value.employee, // 报销人
    type: newReimburse.value.type,        // 类型
    amount: newReimburse.value.amount,    // 金额
    desc: newReimburse.value.desc,        // 描述
    status: 'pending', // 状态：待审核
    date: new Date().toISOString().split('T')[0] // 今天日期
  })

  // 3. 关闭弹窗
  showDialog.value = false

  // 4. 提示成功
  alert('报销单提交成功！单号：' + id)
}

const approveReimburse = (id) => {
  const item = financeStore.reimburseList.find(i => i.id === id)
  if (item) {
    item.status = 'approved'
    alert('报销单 ' + id + ' 已审核通过！可生成凭证。')
  }
}

const rejectReimburse = (id) => {
  const item = financeStore.reimburseList.find(i => i.id === id)
  if (item) {
    item.status = 'rejected'
    alert('报销单 ' + id + ' 已驳回！')
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
}

.status.pending {
  background: #fdf6ec;
  color: #e6a23c;
}

.status.approved {
  background: #f0f9eb;
  color: #67c23a;
}

.status.rejected {
  background: #fef0f0;
  color: #f56c6c;
}

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

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
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
</style>