"""数据层唯一入口：连接管理 + 全部建表 SQL。

纪律：
- 本文件是全项目唯一知道"连哪个库、怎么连"的地方，表结构变更只改这里；
- models/ 与 services/ 一律通过 get_conn() 取连接，禁止自行 sqlite3.connect；
- api/ 层不接触本文件。
"""
import os
import sqlite3

# 数据库固定在 backend/ 下，与运行目录无关
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")

# 8 张表，顺序即 tasks.md §2；invoices 与 reimbursements 互为外键（循环引用），
# SQLite 建表阶段不校验外键目标、延迟到写入时解析，故先后顺序无碍。
_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,                            -- bcrypt 哈希，不存明文
    role     TEXT NOT NULL DEFAULT 'employee'
             CHECK (role IN ('employee', 'finance'))
);

-- 发票主表：invoice_no 唯一，作为 OCR 入库前的查重依据
-- kind：发票用途（报销/采购/销售，三期应收增补销售）；category：AI 提取的费用类别，预算对照用（二期 T13）
-- budget_deducted：审查通过后是否已扣减预算，重审回滚的幂等标记（二期 T14）
CREATE TABLE IF NOT EXISTS invoices (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no       TEXT NOT NULL UNIQUE,
    invoice_date     TEXT,
    amount           REAL NOT NULL DEFAULT 0,
    tax              REAL NOT NULL DEFAULT 0,
    invoice_type     TEXT,
    seller           TEXT,
    buyer            TEXT,
    kind             TEXT NOT NULL DEFAULT '报销'
                     CHECK (kind IN ('报销', '采购', '销售')),
    category         TEXT,
    budget_deducted  INTEGER NOT NULL DEFAULT 0,
    status           TEXT NOT NULL DEFAULT '待审'
                     CHECK (status IN ('待审', '已通过', '已驳回', '已入账')),
    source_file      TEXT,                           -- 发票原件在 uploads/ 下的文件名
    reimburse_id     INTEGER REFERENCES reimbursements (id),
    created_at       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices (status);

-- 随单附件（签批单等），发票删除时级联清理
CREATE TABLE IF NOT EXISTS attachments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL REFERENCES invoices (id) ON DELETE CASCADE,
    file_path  TEXT NOT NULL,
    kind       TEXT NOT NULL DEFAULT '发票原件'
               CHECK (kind IN ('随单审批单', '发票原件'))
);
CREATE INDEX IF NOT EXISTS idx_attachments_invoice ON attachments (invoice_id);

-- 报销单（业务单据源头）
-- 注：tasks.md 的字段 desc 与 SQL 关键字 DESC 冲突，列名定为 description；
--     状态枚举 tasks.md 未定义，由 models/reimburse.py 定稿后如需收紧再加 CHECK
CREATE TABLE IF NOT EXISTS reimbursements (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT UNIQUE,                         -- 如 BX20260101001
    employee    TEXT NOT NULL,                       -- 报销人 username
    type        TEXT,                                -- 费用类型，如 差旅费
    amount      REAL NOT NULL DEFAULT 0,
    description TEXT,
    status      TEXT NOT NULL DEFAULT '待财务审批',
    invoice_id  INTEGER REFERENCES invoices (id),
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_reimburse_status ON reimbursements (status);

-- 凭证：分录存 entries_json（含科目/借贷方向/金额），过账时更新 ledger
CREATE TABLE IF NOT EXISTS vouchers (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    code         TEXT UNIQUE,                        -- 如 PZ-2026-001
    date         TEXT,
    summary      TEXT,
    entries_json TEXT NOT NULL DEFAULT '[]',
    status       TEXT NOT NULL DEFAULT 'draft'
                 CHECK (status IN ('draft', 'approved', 'posted')),
    reimburse_id INTEGER REFERENCES reimbursements (id)
);

-- AI 审查报告：一票可多份，删发票级联清理
CREATE TABLE IF NOT EXISTS audit_reports (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL REFERENCES invoices (id) ON DELETE CASCADE,
    result     TEXT NOT NULL
               CHECK (result IN ('通过', '预警', '驳回')),
    reason     TEXT,                                 -- 驳回/预警原因（三期 T20 聚合 TOP 用）
    content_md TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_reports_invoice ON audit_reports (invoice_id);

-- 应付单（二期 T17）：采购发票审查通过后生成；一票一应付（invoice_id 唯一）
-- 口径简化：凭证过账即视为应付确认入账 → status 已付款；付款核销留待三期
CREATE TABLE IF NOT EXISTS payables (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE,                -- CG-2026-001
    supplier    TEXT,
    amount      REAL NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT '待付款'
                CHECK (status IN ('待付款', '已付款')),
    invoice_id  INTEGER NOT NULL UNIQUE REFERENCES invoices (id),
    voucher_id  INTEGER REFERENCES vouchers (id),    -- 结算生成的凭证
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 应收单（三期增补）：销售发票审查通过后生成；一票一应收（invoice_id 唯一）
-- 口径与应付对称：收款生成凭证过账 → status 已收款
CREATE TABLE IF NOT EXISTS receivables (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE,                -- YS-2026-001
    customer    TEXT,                                -- 客户 = 发票购买方
    amount      REAL NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT '待收款'
                CHECK (status IN ('待收款', '已收款')),
    invoice_id  INTEGER NOT NULL UNIQUE REFERENCES invoices (id),
    voucher_id  INTEGER REFERENCES vouchers (id),    -- 收款生成的凭证
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 预算规则：同（类目, 期间）唯一，重复上传即覆盖限额（used_amount 保留）
CREATE TABLE IF NOT EXISTS budget_rules (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    category     TEXT NOT NULL,
    limit_amount REAL NOT NULL DEFAULT 0,
    used_amount  REAL NOT NULL DEFAULT 0,
    period       TEXT NOT NULL,                      -- 如 2026-10
    created_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_budget_cat_period
    ON budget_rules (category, period);

-- 总账：凭证过账时按分录更新借贷发生额与期末余额
CREATE TABLE IF NOT EXISTS ledger (
    account_code TEXT PRIMARY KEY,
    account_name TEXT,
    opening      REAL NOT NULL DEFAULT 0,
    debit        REAL NOT NULL DEFAULT 0,
    credit       REAL NOT NULL DEFAULT 0,
    closing      REAL NOT NULL DEFAULT 0
);
"""


def get_conn() -> sqlite3.Connection:
    """取一条短连接（每请求一取，用完即关）；调用方负责 close。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """建库建表（幂等，可重复执行）；WAL 提升并发读性能。"""
    conn = get_conn()
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()
