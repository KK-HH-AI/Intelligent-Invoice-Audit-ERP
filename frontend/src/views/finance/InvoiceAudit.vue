<template>
  <div class="page">
    <h3>发票审核</h3>
    <div class="content">
      <div class="notice">
        <p>请先在「发票OCR识别」页面上传发票图片，并在「文档分析」页面上传审核单文档，然后再进行发票审核。</p>
      </div>

      <div class="toolbar">
        <button class="btn primary" @click="startAudit" :disabled="loading">
          {{ loading ? '审核中...' : '开始审核' }}
        </button>
      </div>

      <!-- 审核结果 -->
      <div class="result-area" v-if="auditResult">
        <h4>审核报告</h4>
        <div class="audit-card">
          <div class="markdown-content" v-html="renderedMarkdown"></div>
        </div>
      </div>

      <div class="empty" v-if="!auditResult && !loading">
        暂无审核结果，请先完成发票识别和文档分析后点击审核
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const loading = ref(false)
const auditResult = ref('')

// 简易Markdown渲染：将换行转<br>，标题加粗，列表缩进
const renderedMarkdown = computed(() => {
  if (!auditResult.value) return ''
  let md = auditResult.value
  // 转义HTML
  md = md.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  // 标题
  md = md.replace(/^### (.+)$/gm, '<h4>$1</h4>')
  md = md.replace(/^## (.+)$/gm, '<h3>$1</h3>')
  md = md.replace(/^# (.+)$/gm, '<h2>$1</h2>')
  // 加粗
  md = md.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // 列表项
  md = md.replace(/^- (.+)$/gm, '<li>$1</li>')
  // 换行
  md = md.replace(/\n/g, '<br>')
  return md
})

const startAudit = async () => {
  loading.value = true
  auditResult.value = ''

  try {
    const response = await fetch('/api/audit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    const data = await response.json()

    if (data.status === 'success') {
      auditResult.value = data.content
    } else {
      alert('审核失败：' + (data.message || '未知错误'))
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

.notice {
  background: #fdf6ec;
  border: 1px solid #faecd8;
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 20px;
}

.notice p {
  color: #e6a23c;
  font-size: 14px;
  margin: 0;
}

.toolbar {
  margin-bottom: 20px;
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

.audit-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 24px;
  background: #fafafa;
}

.markdown-content {
  line-height: 1.8;
  font-size: 14px;
  color: #333;
}

.markdown-content :deep(h2) {
  font-size: 18px;
  margin: 16px 0 8px;
  color: #303133;
}

.markdown-content :deep(h3) {
  font-size: 16px;
  margin: 12px 0 6px;
  color: #303133;
}

.markdown-content :deep(h4) {
  font-size: 15px;
  margin: 10px 0 4px;
  color: #606266;
}

.markdown-content :deep(li) {
  margin-left: 20px;
  list-style: disc;
}

.empty {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}
</style>
