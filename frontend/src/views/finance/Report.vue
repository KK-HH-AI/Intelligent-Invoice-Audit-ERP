<template>
  <div class="page">
    <h3>财务报表</h3>
    <div class="content">
      <div class="toolbar">
        <span class="period-label">当前期间：2024年5月</span>
        <button class="btn primary" @click="refreshReport">刷新报表</button>
      </div>

      <!-- 报表类型选择 -->
      <div class="report-type">
        <div
          class="report-item"
          :class="{ active: selectedReport === 'balance' }"
          @click="selectReport('balance')"
        >
          资产负债表
        </div>
        <div
          class="report-item"
          :class="{ active: selectedReport === 'profit' }"
          @click="selectReport('profit')"
        >
          利润表
        </div>
      </div>

      <!-- 报表数据展示 -->
      <div class="report-content">
        <table class="report-table" v-if="selectedReport && reportData.length > 0">
          <thead>
            <tr>
              <th>项目</th>
              <th>金额（元）</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in reportData" :key="index">
              <td>{{ item.name }}</td>
              <td :class="item.class">¥{{ item.amount.toFixed(2) }}</td>
            </tr>
          </tbody>
          <tfoot v-if="selectedReport === 'balance'">
            <tr>
              <td>合计</td>
              <td class="total">¥{{ totalAmount.toFixed(2) }}</td>
            </tr>
          </tfoot>
        </table>
        <div class="empty" v-else-if="!selectedReport">请选择报表类型</div>
        <div class="empty" v-else>暂无报表数据</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useFinanceStore } from '../../stores/finance'

const financeStore = useFinanceStore()

const selectedReport = ref('')

const selectReport = (type) => {
  selectedReport.value = type
}

// 根据选择的报表类型生成报表数据
const reportData = computed(() => {
  if (!selectedReport.value) return []

  const accounts = financeStore.ledgerAccounts

  switch (selectedReport.value) {
    case 'balance':
      return [
        { name: '银行存款', amount: accounts.find(a => a.code === '1002')?.closing || 0, class: 'asset' },
        { name: '应收账款', amount: accounts.find(a => a.code === '1122')?.closing || 0, class: 'asset' },
        { name: '应付账款', amount: accounts.find(a => a.code === '2202')?.closing || 0, class: 'liability' },
        { name: '所有者权益', amount: 0, class: 'equity' },
      ]
    case 'profit':
      // 收入类科目贷方表示增加，closing 为负数，需要取绝对值
      const revenue = Math.abs(accounts.find(a => a.code === '6001')?.closing || 0)
      // 成本费用类科目借方表示增加，closing 为正数
      const cost = accounts.find(a => a.code === '6401')?.closing || 0
      const expense = accounts.find(a => a.code === '6602')?.closing || 0
      const profit = revenue - cost - expense
      
      return [
        { name: '主营业务收入', amount: revenue, class: 'income' },
        { name: '主营业务成本', amount: cost, class: 'cost' },
        { name: '管理费用', amount: expense, class: 'expense' },
        { name: '净利润', amount: profit, class: 'profit' },
      ]
    default:
      return []
  }
})

const totalAmount = computed(() => {
  return reportData.value.reduce((sum, item) => sum + item.amount, 0)
})

const refreshReport = () => {
  alert('报表已刷新！')
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
  align-items: center;
}

.period-label {
  font-size: 16px;
  color: #333;
  font-weight: 500;
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

.report-type {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.report-item {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.report-item:hover {
  background: #e8f0fe;
  color: #409eff;
}

.report-item.active {
  background: #409eff;
  color: white;
}

.report-content {
  background: #f9fafc;
  padding: 20px;
  border-radius: 8px;
}

.report-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #ebeef5;
}

.report-table th,
.report-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
}

.report-table th {
  background: #f5f7fa;
}

.report-table tfoot {
  background: #f5f7fa;
  font-weight: bold;
}

.asset {
  color: #409eff;
}

.liability {
  color: #f56c6c;
}

.equity {
  color: #67c23a;
}

.income {
  color: #67c23a;
}

.cost {
  color: #f56c6c;
}

.expense {
  color: #e6a23c;
}

.profit {
  font-weight: bold;
  color: #67c23a;
}

.total {
  font-weight: bold;
}

.empty {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}
</style>