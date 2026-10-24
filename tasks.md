# 智能发票审查系统 · 融合任务拆解

## 0. 现状与目标

**现状**
- 财务模块：纯前端 Pinia 内存数据，刷新即失，无后端
- 智能审查：后端 Flask 真实可用，但用磁盘 JSON（invoice.json / file.json）临时传递，无入库、无状态
- 无角色区分（localStorage 单用户）

**目标链路**
```
员工上传发票(+随单附件) ——> OCR入库+查重 ——> AI三方审查(发票+预算规则+随单附件)
——> 一键生成报销单 ——> 财务复核(附AI意见) ——> 转凭证 ——> 过账 ——> 总账/报表
```
数据全部落 SQLite（backend/database.db 已存在），角色分 员工(employee) / 财务(finance)。

## 1. 任务树

```
融合系统
├── M1 数据层（backend）
│   ├── T1 db.py                    连接 + 建表
│   ├── T2 models/invoice.py        发票实体（查重/状态流转）
│   ├── T3 models/reimburse.py      报销单实体
│   ├── T4 models/voucher.py        凭证实体
│   └── T13 models/budget.py        预算规则实体（二期）
├── M2 服务层（backend/services）
│   ├── T5 ocr_service.py           识别 → 字段映射 → 入库 + 查重
│   ├── T6 audit_service.py         AI审查 → 结论 + 报告 → 状态回写
│   ├── T7 voucher_service.py       报销单 → 分录 → 凭证；过账更新总账
│   ├── T14 audit_service 三方升级   +预算对照+余额扣减（二期）
│   └── T15 budget_service.py       预算解析入库/余额（二期）
├── M3 API 层（backend/api）
│   ├── T8 auth.py                  注册/登录 + 角色
│   ├── T9 invoices.py              上传(发票+附件)/列表/触发审查
│   ├── T10 reimburse.py            创建/审批(通过/驳回)
│   ├── T11 vouchers.py             生成/过账
│   └── T16 budgets.py              （二期）
├── M4 前端
│   ├── T12a stores/auth.js         登录态 + 角色
│   ├── T12b InvoiceUpload.vue      改造 InvoiceOcr：识别预览 + 一键转报销单
│   ├── T12c Reimburse.vue          接后端 API，展示 AI 审查意见
│   ├── T12d Voucher.vue            生成/过账接后端
│   ├── T12e Sidebar+router         按角色显隐菜单 + 守卫
│   └── T17 BudgetManage.vue        预算上传/余额一览（二期）
└── 组合根（只装配不逻辑）
    ├── backend/app.py              注册所有蓝图
    └── frontend router             装配页面
```

## 2. 表结构（T1 建表依据）

- **users**(id, username, password, role: employee/finance)
- **invoices**(id, invoice_no, invoice_date, amount, tax, invoice_type, seller, buyer, status: 待审/已通过/已驳回/已入账, source_file, reimburse_id, created_at)
- **attachments**(id, invoice_id, file_path, kind: 随单审批单/发票原件)
- **reimbursements**(id, code, employee, type, amount, desc, status, invoice_id, created_at)
- **vouchers**(id, code, date, summary, entries_json, status: draft/approved/posted, reimburse_id)
- **audit_reports**(id, invoice_id, result: 通过/预警/驳回, content_md, created_at)
- **budget_rules**(id, category, limit_amount, used_amount, period) —— 二期
- **ledger**(account_code, account_name, opening, debit, credit, closing) —— 过账更新

## 3. 一期任务清单（拓扑序）

| # | 任务 | 做什么 | 依赖 | 验证 |
|---|---|---|---|---|
| T1 | db.py | SQLite 连接 + 全部建表 SQL | 无 | 脚本跑通建表 |
| T2 | models/invoice.py | OCR字段→发票入库、按发票号查重、状态流转 | T1 | 脚本插入+查询 |
| T3 | models/reimburse.py | 报销单 CRUD + 状态 | T1 | 脚本 |
| T4 | models/voucher.py | 凭证 CRUD + 过账更新 ledger | T1 | 脚本 |
| T5 | ocr_service.py | 改造 invoice_ocr.py：识别结果不再写 invoice.json，字段映射入 invoices 表，入库前查重 | T2 | 上传样例发票 → 库有记录 |
| T6 | audit_service.py（两方版） | 发票记录 + 随单附件文本（如有）→ DeepSeek 审查 → 结论写回状态 + 存报告 | T2 | 样例发票出报告 |
| T7 | voucher_service.py | 迁移前端 generateVoucher 分录模板到后端；过账更新 ledger | T4 | 报销单转凭证正确 |
| T8 | auth.py | 注册/登录，users 表，返回带角色的会话 | T1 | curl 注册+登录 |
| T9 | invoices.py | POST /api/invoices（multipart 发票+可选附件）→ 调 T5→T6；GET 列表 | T5,T6 | curl 上传 |
| T10 | reimburse.py | POST 创建（员工确认）、approve/reject（财务，附 AI 意见） | T3,T6 | curl |
| T11 | vouchers.py | generate / post | T7 | curl |
| T12 | 前端五件 | auth store、InvoiceUpload（识别→一键转单）、Reimburse 接 API 显 AI 意见、Voucher 接 API、Sidebar/router 角色菜单 | T8~T11 | 浏览器全链路 |

**组合根**：app.py 注册 4 个蓝图；router 装配新页面。

## 4. 二期

| # | 任务 | 做什么 |
|---|---|---|
| T13 | models/budget.py | 预算规则实体（类目/限额/已用/剩余/期间） |
| T14 | audit_service 三方升级 | 审查输入加预算规则：超限拦截/预警；通过后扣减预算，驳回回滚 |
| T15 | budget_service.py | 预算文档解析 → 规则入库 → 余额计算 |
| T16 | budgets.py + BudgetManage.vue | 财务专属：上传预算、余额一览 |
| T17 | 应付融合 | 采购发票复用同链路生成应付单 |

## 5. 三期

- 审查报告归档留痕页（按单据追溯）
- 报表联动统计：预算执行率、审查通过率、驳回原因 TOP

## 6. 一期全链路验收

员工注册登录 → 上传发票(+签批单) → 识别入库查重 → AI 审查出结论 → 一键生成报销单 → 财务审批通过 → 转凭证 → 过账 → 总账科目变化 → 报表反映。发票状态全程可追溯（待审→已通过→已入账）。
