<template>
  <div class="page">
    <h3>发票上传（OCR 识别 + AI 审查）</h3>
    <div class="content">
      <!-- 发票用途（T17）：采购→应付单，销售→应收单（三期） -->
      <div class="kind-row">
        <span class="kind-label">发票用途：</span>
        <label><input type="radio" value="报销" v-model="kind" /> 报销发票</label>
        <label><input type="radio" value="采购" v-model="kind" /> 采购发票（可生成应付单）</label>
        <label><input type="radio" value="销售" v-model="kind" /> 销售发票（可生成应收单）</label>
      </div>

      <div class="upload-row">
        <!-- 发票原件：单选，替换式 -->
        <div class="upload-box" @click="triggerInvoiceInput" :class="{ dragging: draggingInvoice }"
          @dragover.prevent="draggingInvoice = true" @dragleave="draggingInvoice = false"
          @drop.prevent="handleInvoiceDrop">
          <div class="upload-icon">+</div>
          <p>点击或拖拽上传<b>发票原件</b><br />PNG / JPG / BMP / PDF（单张）</p>
          <input type="file" ref="invoiceInput" accept=".png,.jpg,.jpeg,.bmp,.pdf" style="display: none"
            @change="onInvoiceChange" />
        </div>

        <!-- 随单附件：多选（签批单、合同等） -->
        <div class="upload-box" @click="triggerAttachInput" :class="{ dragging: draggingAttach }"
          @dragover.prevent="draggingAttach = true" @dragleave="draggingAttach = false"
          @drop.prevent="handleAttachDrop">
          <div class="upload-icon">+</div>
          <p>随单附件（可选，最多5个）<br />图片 / PDF / Word / Excel</p>
          <input type="file" ref="attachInput" multiple accept=".png,.jpg,.jpeg,.bmp,.pdf,.docx,.xls,.xlsx"
            style="display: none" @change="onAttachChange" />
        </div>
      </div>

      <div class="file-list" v-if="invoiceFile || attachFiles.length">
        <div class="file-item main" v-if="invoiceFile">
          <span class="file-name">发票原件：{{ invoiceFile.name }}</span>
          <button class="btn-sm remove" @click="invoiceFile = null">移除</button>
        </div>
        <div class="file-item" v-for="(f, index) in attachFiles" :key="index">
          <span class="file-name">附件：{{ f.name }}</span>
          <button class="btn-sm remove" @click="attachFiles.splice(index, 1)">移除</button>
        </div>
      </div>

      <button class="btn primary" @click="submitUpload"
        :disabled="!invoiceFile || uploading">
        {{ uploading ? '识别与审查中，请稍候...' : '上传并审查' }}
      </button>

      <div class="error-line" v-if="errorMsg">{{ errorMsg }}</div>

      <!-- 上传结果 -->
      <div class="result-area" v-if="result">
        <!-- 重复发票 -->
        <div class="warn-card" v-if="result.duplicate">
          该发票已存在（台账记录 #{{ result.invoice_id }}），请勿重复上传。
        </div>

        <template v-else>
          <!-- 识别字段 -->
          <div class="card" v-if="result.fields && Object.keys(result.fields).length">
            <div class="card-header">
              <span class="filename">{{ result.invoice.invoice_no || '识别结果' }}</span>
              <span class="status" :class="statusClass(result.invoice.status)">{{ result.invoice.status }}</span>
            </div>
            <div class="card-body">
              <table class="result-table">
                <tbody>
                  <tr v-for="(value, key) in result.fields" :key="key">
                    <td class="label">{{ key }}</td>
                    <td>{{ value ?? '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- AI 审查报告 -->
          <div class="card" v-if="result.audit">
            <div class="card-header">
              <span>AI 审查报告</span>
              <span class="status" :class="statusClass(result.audit.result)">{{ result.audit.result }}</span>
            </div>
            <div class="card-body markdown-content" v-html="renderMarkdown(result.audit.content_md)"></div>
          </div>

          <div class="warn-card" v-if="result.audit_error">
            {{ result.audit_error }}（发票已入库，稍后可在「发票台账」查看）
          </div>

          <div class="ok-line">已入库，可在「发票台账」查看完整记录</div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { request } from '../../api'
import { renderMarkdown } from '../../markdown'

const invoiceInput = ref(null)
const attachInput = ref(null)
const kind = ref('报销')        // 发票用途：报销/采购/销售
const invoiceFile = ref(null)   // 发票原件（单选，替换式）
const attachFiles = ref([])     // 随单附件（多选）
const draggingInvoice = ref(false)
const draggingAttach = ref(false)
const uploading = ref(false)
const result = ref(null)
const errorMsg = ref('')

const triggerInvoiceInput = () => invoiceInput.value.click()
const triggerAttachInput = () => attachInput.value.click()

const onInvoiceChange = (e) => {
  const f = e.target.files[0]
  if (f) invoiceFile.value = f
  e.target.value = ''
}

const onAttachChange = (e) => {
  addAttach(Array.from(e.target.files))
  e.target.value = ''
}

const handleInvoiceDrop = (e) => {
  draggingInvoice.value = false
  const f = Array.from(e.dataTransfer.files)[0]
  if (f) invoiceFile.value = f
}

const handleAttachDrop = (e) => {
  draggingAttach.value = false
  addAttach(Array.from(e.dataTransfer.files))
}

const addAttach = (files) => {
  const remaining = 5 - attachFiles.value.length
  attachFiles.value.push(...files.slice(0, remaining))
}

const submitUpload = async () => {
  if (!invoiceFile.value || uploading.value) return

  uploading.value = true
  result.value = null
  errorMsg.value = ''

  const formData = new FormData()
  formData.append('invoice', invoiceFile.value)
  formData.append('kind', kind.value)
  attachFiles.value.forEach(f => formData.append('attachments', f))

  try {
    result.value = await request('/api/invoices', { method: 'POST', formData })
    invoiceFile.value = null
    attachFiles.value = []
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    uploading.value = false
  }
}

// 状态徽章样式
const statusClass = (status) => ({
  '已通过': 'st-ok',
  '待审': 'st-warn',
  '预警': 'st-warn',
  '已驳回': 'st-bad',
}[status] || 'st-gray')
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

.kind-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #606266;
}

.kind-row label {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.upload-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.upload-box {
  flex: 1;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 32px 20px;
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
  font-size: 32px;
  color: #409eff;
  margin-bottom: 8px;
  font-weight: bold;
}

.upload-box p {
  color: #909399;
  font-size: 13px;
  line-height: 1.6;
}

.upload-box p b {
  color: #606266;
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

.file-item.main {
  background: #ecf5ff;
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

.error-line {
  margin-top: 12px;
  color: #f56c6c;
}

.result-area {
  margin-top: 24px;
}

.card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  margin-bottom: 16px;
  overflow: hidden;
}

.card-header {
  background: #f5f7fa;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
}

.st-ok { background: #f0f9eb; color: #67c23a; }
.st-warn { background: #fdf6ec; color: #e6a23c; }
.st-bad { background: #fef0f0; color: #f56c6c; }
.st-gray { background: #f4f4f5; color: #909399; }

.warn-card {
  background: #fdf6ec;
  color: #e6a23c;
  border: 1px solid #faecd8;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 16px;
}

.ok-line {
  color: #67c23a;
  font-size: 14px;
}

.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4) {
  margin: 8px 0;
}
</style>
