<template>
  <div class="page">
    <h3>文档分析</h3>
    <div class="content">
      <div class="upload-area">
        <div class="upload-box" @click="triggerFileInput" :class="{ dragging: isDragging }"
          @dragover.prevent="isDragging = true" @dragleave="isDragging = false" @drop.prevent="handleDrop">
          <div class="upload-icon">+</div>
          <p>点击或拖拽上传文档（支持PDF/Word/Excel）</p>
          <input type="file" ref="fileInput" accept=".pdf,.docx,.xls,.xlsx" @change="handleFileChange"
            style="display: none" />
        </div>

        <div class="file-info" v-if="selectedFile">
          <span class="file-name">{{ selectedFile.name }}</span>
          <button class="btn-sm remove" @click="clearFile">删除</button>
        </div>

        <button class="btn primary" @click="submitAnalysis" :disabled="!selectedFile || loading">
          {{ loading ? '分析中...' : '开始分析' }}
        </button>
      </div>

      <!-- 分析结果 -->
      <div class="result-area" v-if="analysisResult">
        <h4>分析结果</h4>
        <div class="result-card">
          <table class="result-table">
            <tbody>
              <tr v-for="(value, key) in analysisResult" :key="key">
                <td class="label">{{ key }}</td>
                <td v-if="typeof value === 'object' && value !== null">
                  <pre class="json-block">{{ JSON.stringify(value, null, 2) }}</pre>
                </td>
                <td v-else>{{ value }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const fileInput = ref(null)
const selectedFile = ref(null)
const isDragging = ref(false)
const loading = ref(false)
const analysisResult = ref(null)

const triggerFileInput = () => {
  fileInput.value.click()
}

const handleFileChange = (e) => {
  const file = e.target.files[0]
  if (file) {
    selectedFile.value = file
  }
}

const handleDrop = (e) => {
  isDragging.value = false
  const file = e.dataTransfer.files[0]
  if (file) {
    selectedFile.value = file
  }
}

const clearFile = () => {
  selectedFile.value = null
  analysisResult.value = null
}

const submitAnalysis = async () => {
  if (!selectedFile.value) return

  loading.value = true
  analysisResult.value = null

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    const response = await fetch('/api/analyze/document', {
      method: 'POST',
      body: formData
    })
    const data = await response.json()

    if (data.error) {
      alert('分析失败：' + data.error)
    } else {
      if (typeof data === 'string') {
        analysisResult.value = JSON.parse(data)
      } else {
        analysisResult.value = data
      }
    }
  } catch (e) {
    alert('请求失败：' + e.message)
  } finally {
    loading.value = false
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

.upload-area {
  margin-bottom: 24px;
}

.upload-box {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s;
  background: #fafafa;
}

.upload-box:hover,
.upload-box.dragging {
  border-color: #409eff;
  background: #ecf5ff;
}

.upload-icon {
  font-size: 36px;
  color: #409eff;
  margin-bottom: 8px;
}

.upload-box p {
  color: #909399;
  font-size: 14px;
}

.file-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  margin: 16px 0;
}

.file-name {
  color: #333;
  font-size: 14px;
}

.btn-sm.remove {
  padding: 2px 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  background: #f56c6c;
  color: white;
}

.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn.primary {
  background: #409eff;
  color: white;
}

.btn:disabled {
  background: #c0c4cc;
  cursor: not-allowed;
}

.result-area {
  margin-top: 24px;
}

.result-area h4 {
  margin-bottom: 16px;
  color: #333;
}

.result-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
}

.result-table {
  width: 100%;
  border-collapse: collapse;
}

.result-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: top;
}

.result-table td.label {
  font-weight: 600;
  color: #606266;
  width: 160px;
  white-space: nowrap;
}

.json-block {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 13px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}
</style>
