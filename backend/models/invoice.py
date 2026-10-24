"""发票实体：入库、按发票号查重、状态流转。"""
from db import get_conn

# 与建表 CHECK 一致的状态集，供上层做准入判断
STATUSES = ("待审", "已通过", "已驳回", "已入账")


def create(*, invoice_no: str, amount: float, invoice_date=None, tax=0.0,
           invoice_type=None, seller=None, buyer=None, source_file=None,
           kind='报销', category=None) -> int:
    """OCR 字段映射后入库；invoice_no 重复时 UNIQUE 约束抛 IntegrityError。

    kind: 发票用途（报销/采购，二期）；category: 费用类别（预算对照，二期）。
    """
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO invoices"
            " (invoice_no, invoice_date, amount, tax, invoice_type,"
            "  seller, buyer, kind, category, source_file)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (invoice_no, invoice_date, amount, tax, invoice_type,
             seller, buyer, kind, category, source_file),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def find_by_no(invoice_no: str):
    """入库前查重用。"""
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM invoices WHERE invoice_no = ?", (invoice_no,)
        ).fetchone()
    finally:
        conn.close()


def get(inv_id: int):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM invoices WHERE id = ?", (inv_id,)
        ).fetchone()
    finally:
        conn.close()


def list_all(status=None) -> list:
    """列表页；status 传则按状态过滤，新→旧排序。"""
    conn = get_conn()
    try:
        if status:
            return conn.execute(
                "SELECT * FROM invoices WHERE status = ? ORDER BY id DESC",
                (status,),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM invoices ORDER BY id DESC"
        ).fetchall()
    finally:
        conn.close()


def update_status(inv_id: int, status: str) -> None:
    """状态流转：待审 → 已通过/已驳回 → 已入账；非法值由 CHECK 拦截。"""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE invoices SET status = ? WHERE id = ?", (status, inv_id)
        )
        conn.commit()
    finally:
        conn.close()


def set_budget_deducted(inv_id: int, deducted: bool) -> None:
    """预算扣减幂等标记（T14）：重审回滚的依据。"""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE invoices SET budget_deducted = ? WHERE id = ?",
            (1 if deducted else 0, inv_id),
        )
        conn.commit()
    finally:
        conn.close()


def set_reimburse(inv_id: int, reimburse_id: int) -> None:
    """生成报销单后回填关联。"""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE invoices SET reimburse_id = ? WHERE id = ?",
            (reimburse_id, inv_id),
        )
        conn.commit()
    finally:
        conn.close()
