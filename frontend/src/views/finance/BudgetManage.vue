<template>
  <div class="page">
    <h3>预算管理</h3>
    <div class="content">
      <!-- 非财务角色拦截（菜单已隐藏，防直接输 URL） -->
      <div class="empty" v-if="!isFinance">仅财务角色可访问预算管理</div>

      <template v-else>
        <!-- 预算文件上传 -->
        <div class="upload-row">
          <input type="file" ref="fileInput" accept=".csv,.xlsx,.xls" style="display: none"
            @change="onFileChange" />
          <button class="btn primary" @click="fileInput.click()">选择预算文件（csv/xlsx）</button>
          <label class="period-label">期间：
            <input type="month" v-model="period" />
          </label>
          <button class="btn" :disabled="!file || uploading" @click="uploadBudget">
            {{ uploading ? '解析中...' : '上传解析' }}
          </button>
          <span class="hint" v-if="file">{{ file.name }}</span>
          <span class="hint dim" v-else>表头需含：类目、限额；期间不填默认当前月</span>
        </div>

        <div class="msg ok" v-if="uploadMsg">{{ uploadMsg }}</div>
        <div class="msg err" v-if="errorMsg">{{ errorMsg }}</div>

        <!-- 余额一览 -->
        <div class="toolbar">
          <button class="btn" @click="loadRules" :disabled="loading">
            {{ loading ? '加载中...' : '刷新余额' }}
          </button>
        </div>

        <table class="table" v-if="rules.length > 0">
          <thead>
            <tr>
              <th>期间</th>
              <th>类目</th>
              <th>限额</th>
              <th>已用</th>
              <th>剩余</th>
              <th>执行率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rule in rules" :key="rule.id">
              <td>{{ rule.period }}</td>
              <td>{{ rule.category }}</td>
              <td>¥{{ fmt(rule.limit_amount) }}</td>
              <td>¥{{ fmt(rule.used_amount) }}</td>
              <td>¥{{ fmt(rule.remaining) }}</td>
              <td>
                <div class="rate-cell">
                  <div class="rate-bar">
                    <div class="rate-fill" :class="rateClass(rule)" :style="{ width: barWidth(rule) }"></div>
                  </div>
                  <span>{{ rule.usage_rate === null ? '-' : rule.usage_rate + '%' }}</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="empty" v-else-if="!loading">暂无预算规则，请上传预算文件</div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { request, getUser } from '../../api'

const fileInput = ref(null)
const file = ref(null)
const period = ref('')
const uploading = ref(false)
const uploadMsg = ref('')
const errorMsg = ref('')
const rules = ref([])
const loading = ref(false)

const isFinance = getUser()?.role === 'finance'

const onFileChange = (e) => {
  file.value = e.target.files[0] || null
  e.target.value = ''
}

const uploadBudget = async () => {
  if (!file.value || uploading.value) return
  uploading.value = true
  uploadMsg.value = ''
  errorMsg.value = ''
  const formData = new FormData()
  formData.append('file', file.value)
  formData.append('period', period.value)
  try {
    const stat = await request('/api/budgets/upload', { method: 'POST', formData })
    uploadMsg.value = `导入成功：${stat.count} 条规则（期间 ${stat.period}）`
    file.value = null
    await loadRules()
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    uploading.value = false
  }
}

const loadRules = async () => {
  loading.value = true
  try {
    rules.value = await request('/api/budgets')
  } catch (e) {
    alert(e.message)
  } finally {
    loading.value = false
  }
}

const fmt = (v) => Number(v || 0).toFixed(2)
const barWidth = (rule) => (rule.usage_rate === null ? '0%' : Math.min(rule.usage_rate, 100) + '%')
const rateClass = (rule) => {
  const rate = rule.usage_rate
  if (rate === null) return ''
  if (rate > 100) return 'over'
  if (rate >= 80) return 'warn'
  return 'safe'
}

onMounted(() => { if (isFinance) loadRules() })
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

.upload-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.period-label {
  color: #606266;
  font-size: 14px;
}

.period-label input {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.hint {
  color: #67c23a;
  font-size: 13px;
}

.hint.dim {
  color: #909399;
}

.msg {
  margin-bottom: 16px;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 13px;
}

.msg.ok {
  background: #f0f9eb;
  color: #67c23a;
}

.msg.err {
  background: #fef0f0;
  color: #f56c6c;
}

.toolbar {
  margin-bottom: 16px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  background: #f5f7fa;
  color: #333;
}

.btn.primary {
  background: #409eff;
  color: white;
}

.btn:disabled {
  background: #c0c4cc;
  cursor: not-allowed;
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

.rate-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rate-bar {
  width: 100px;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.rate-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}

.rate-fill.safe {
  background: #409eff;
}

.rate-fill.warn {
  background: #e6a23c;
}

.rate-fill.over {
  background: #f56c6c;
}

.empty {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}
</style>
