<template>
  <div class="page">
    <h3>发票OCR识别</h3>
    <div class="content">
      <div class="upload-area">
        <div class="upload-box" @click="triggerFileInput" :class="{ dragging: isDragging }"
          @dragover.prevent="isDragging = true" @dragleave="isDragging = false" @drop.prevent="handleDrop">
          <div class="upload-icon">+</div>
          <p>点击或拖拽上传发票图片（支持PNG/JPG/PDF，最多3张）</p>
          <input type="file" ref="fileInput" multiple accept=".png,.jpg,.jpeg,.bmp,.pdf" @change="handleFileChange"
            style="display: none" />
        </div>

        <div class="file-list" v-if="fileList.length > 0">
          <div class="file-item" v-for="(file, index) in fileList" :key="index">
            <span class="file-name">{{ file.name }}</span>
            <button class="btn-sm remove" @click="removeFile(index)">删除</button>
          </div>
        </div>

        <button class="btn primary" @click="submitOcr" :disabled="fileList.length === 0 || loading">
          {{ loading ? '识别中...' : '开始识别' }}
        </button>
      </div>

      <!-- 识别结果 -->
      <div class="result-area" v-if="ocrResults">
        <h4>识别结果</h4>
        <div class="invoice-card" v-for="(invoice, filename) in ocrResults" :key="filename">
          <div class="card-header">
            <span class="filename">{{ filename }}</span>
          </div>
          <div class="card-body" v-if="invoice.error">
            <p class="error-text">{{ invoice.error }}</p>
          </div>
          <div class="card-body" v-else>
            <table class="result-table">
              <tbody>
                <tr v-for="(value, key) in invoice" :key="key">
                  <td class="label">{{ key }}</td>
                  <td v-if="Array.isArray(value)">
                    <div v-for="(item, idx) in value" :key="idx" class="sub-item">
                      <span v-for="(v, k) in item" :key="k" class="sub-field">
                        <strong>{{ k }}:</strong> {{ v }}
                      </span>
                    </div>
                  </td>
                  <td v-else>{{ value }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const fileInput = ref(null)
const fileList = ref([])
const isDragging = ref(false)
const loading = ref(false)
const ocrResults = ref(null)

const triggerFileInput = () => {
  fileInput.value.click()
}

const handleFileChange = (e) => {
  const files = Array.from(e.target.files)
  addFiles(files)
}

const handleDrop = (e) => {
  isDragging.value = false
  const files = Array.from(e.dataTransfer.files)
  addFiles(files)
}

const addFiles = (files) => {
  const validExts = ['.png', '.jpg', '.jpeg', '.bmp', '.pdf']
  const newFiles = files.filter(f => {
    const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase()
    return validExts.includes(ext)
  })
  // 最多3张
  const remaining = 3 - fileList.value.length
  fileList.value.push(...newFiles.slice(0, remaining))
}

const removeFile = (index) => {
  fileList.value.splice(index, 1)
}

const submitOcr = async () => {
  if (fileList.value.length === 0) return

  loading.value = true
  ocrResults.value = null

  const formData = new FormData()
  fileList.value.forEach(file => {
    formData.append('files', file)
  })

  try {
    const response = await fetch('/api/ocr/invoice', {
      method: 'POST',
      body: formData
    })
    const data = await response.json()

    if (data.error) {
      alert('识别失败：' + data.error)
    } else {
      // 后端返回的是JSON字符串，需要解析
      if (typeof data === 'string') {
        ocrResults.value = JSON.parse(data)
      } else {
        ocrResults.value = data
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

.file-list {
  margin: 16px 0;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 8px;
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

.invoice-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  margin-bottom: 16px;
  overflow: hidden;
}

.card-header {
  background: #f5f7fa;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
}

.filename {
  font-weight: 600;
  color: #409eff;
}

.card-body {
  padding: 16px;
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

.sub-item {
  padding: 4px 0;
  border-bottom: 1px dashed #eee;
}

.sub-item:last-child {
  border-bottom: none;
}

.sub-field {
  margin-right: 16px;
  font-size: 13px;
}

.error-text {
  color: #f56c6c;
}
</style>
