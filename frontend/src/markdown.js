// 简易 Markdown 渲染：转义 HTML → 标题/加粗/列表/换行
// 仅用于展示 AI 报告，不追求完整 Markdown 规范
export function renderMarkdown(md) {
  if (!md) return ''
  let text = String(md)
  // 转义 HTML，防止注入
  text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  // 标题
  text = text.replace(/^### (.+)$/gm, '<h4>$1</h4>')
  text = text.replace(/^## (.+)$/gm, '<h3>$1</h3>')
  text = text.replace(/^# (.+)$/gm, '<h2>$1</h2>')
  // 加粗
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // 列表项
  text = text.replace(/^- (.+)$/gm, '<li>$1</li>')
  // 换行
  text = text.replace(/\n/g, '<br>')
  return text
}
