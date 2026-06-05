<template>
  <div class="page">
    <h3>总账记账</h3>
    <div class="content">
      <div class="toolbar">
        <span class="period-label">当前期间：2024年5月</span>
        <button class="btn primary" @click="refreshLedger">刷新科目余额</button>
      </div>

      <!-- 科目余额表 -->
      <table class="ledger-table" v-if="financeStore.ledgerAccounts.length > 0">
        <thead>
          <tr>
            <th>科目编码</th>
            <th>科目名称</th>
            <th>期初余额</th>
            <th>本期借方</th>
            <th>本期贷方</th>
            <th>期末余额</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="account in financeStore.ledgerAccounts" :key="account.code">
            <td>{{ account.code }}</td>
            <td>{{ account.name }}</td>
            <td>¥{{ account.opening.toFixed(2) }}</td>
            <td class="debit">¥{{ account.debit.toFixed(2) }}</td>
            <td class="credit">¥{{ account.credit.toFixed(2) }}</td>
            <td class="closing">¥{{ account.closing.toFixed(2) }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td colspan="2">合计</td>
            <td>¥{{ totalOpening.toFixed(2) }}</td>
            <td class="debit">¥{{ totalDebit.toFixed(2) }}</td>
            <td class="credit">¥{{ totalCredit.toFixed(2) }}</td>
            <td class="closing">¥{{ totalClosing.toFixed(2) }}</td>
          </tr>
        </tfoot>
      </table>
      <div class="empty" v-else>暂无科目数据</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useFinanceStore } from '../../stores/finance'

const financeStore = useFinanceStore()

const totalOpening = computed(() => {
  //reduce = 把数组里所有数，一步步加起来（或计算），最后返回一个总数
  return financeStore.ledgerAccounts.reduce((sum, a) => sum + a.opening, 0)
})

const totalDebit = computed(() => {
  return financeStore.ledgerAccounts.reduce((sum, a) => sum + a.debit, 0)
})

const totalCredit = computed(() => {
  return financeStore.ledgerAccounts.reduce((sum, a) => sum + a.credit, 0)
})

const totalClosing = computed(() => {
  return financeStore.ledgerAccounts.reduce((sum, a) => sum + a.closing, 0)
})

const refreshLedger = () => {
  alert('科目余额已刷新！')
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

.ledger-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #ebeef5;
}

.ledger-table th,
.ledger-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
}

.ledger-table th {
  background: #f5f7fa;
}

.ledger-table tfoot {
  background: #f5f7fa;
  font-weight: bold;
}

.debit {
  color: #f56c6c;
}

.credit {
  color: #67c23a;
}

.closing {
  font-weight: bold;
}

.empty {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}
</style>