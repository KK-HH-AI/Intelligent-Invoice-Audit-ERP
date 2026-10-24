<template>
  <div class="page">
    <h3>总账记账</h3>
    <div class="content">
      <div class="empty" v-if="!isFinance">仅财务角色可访问总账记账</div>

      <template v-else>
      <div class="toolbar">
        <button class="btn primary" @click="loadLedger" :disabled="loading">
          {{ loading ? '加载中...' : '刷新科目余额' }}
        </button>
      </div>

      <!-- 科目余额表（后端 /api/vouchers/ledger） -->
      <table class="ledger-table" v-if="accounts.length > 0">
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
          <tr v-for="account in accounts" :key="account.account_code">
            <td>{{ account.account_code }}</td>
            <td>{{ account.account_name }}</td>
            <td>¥{{ fmt(account.opening) }}</td>
            <td class="debit">¥{{ fmt(account.debit) }}</td>
            <td class="credit">¥{{ fmt(account.credit) }}</td>
            <td class="closing">¥{{ fmt(account.closing) }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td colspan="2">合计</td>
            <td>¥{{ fmt(totalOpening) }}</td>
            <td class="debit">¥{{ fmt(totalDebit) }}</td>
            <td class="credit">¥{{ fmt(totalCredit) }}</td>
            <td class="closing">¥{{ fmt(totalClosing) }}</td>
          </tr>
        </tfoot>
      </table>
      <div class="empty" v-else-if="!loading">暂无科目数据</div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { request, getUser } from '../../api'

const accounts = ref([])
const loading = ref(false)

const isFinance = getUser()?.role === 'finance'

const loadLedger = async () => {
  loading.value = true
  try {
    accounts.value = await request('/api/vouchers/ledger')
  } catch (e) {
    alert(e.message)
  } finally {
    loading.value = false
  }
}

const fmt = (v) => Number(v || 0).toFixed(2)

const totalOpening = computed(() => accounts.value.reduce((sum, a) => sum + Number(a.opening || 0), 0))
const totalDebit = computed(() => accounts.value.reduce((sum, a) => sum + Number(a.debit || 0), 0))
const totalCredit = computed(() => accounts.value.reduce((sum, a) => sum + Number(a.credit || 0), 0))
const totalClosing = computed(() => accounts.value.reduce((sum, a) => sum + Number(a.closing || 0), 0))

onMounted(loadLedger)
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

.btn:disabled {
  background: #c0c4cc;
  cursor: not-allowed;
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

.ledger-table tfoot td {
  font-weight: 600;
  background: #fafafa;
}

.ledger-table .debit {
  color: #409eff;
}

.ledger-table .credit {
  color: #e6a23c;
}

.ledger-table .closing {
  font-weight: 600;
}

.empty {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}
</style>
