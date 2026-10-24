"""应付单实体：采购发票 → 应付单 → 凭证（二期 T17）。

纪律：只 import db；编号规则、凭证模板等业务决策在 service 层。
"""
from db import get_conn


def create(*, code: str, amount: float, invoice_id: int, supplier=None) -> int:
    """invoice_id 重复时 UNIQUE 约束抛 IntegrityError（一票一应付）。"""
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO payables (code, supplier, amount, invoice_id)"
            " VALUES (?, ?, ?, ?)",
            (code, supplier, amount, invoice_id),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get(payable_id: int):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM payables WHERE id = ?", (payable_id,)
        ).fetchone()
    finally:
        conn.close()


def find_by_invoice(invoice_id: int):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM payables WHERE invoice_id = ?", (invoice_id,)
        ).fetchone()
    finally:
        conn.close()


def list_all() -> list:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM payables ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def mark_settled(payable_id: int, voucher_id: int) -> None:
    """结算：过账即视为已付款（二期简化口径），回填凭证关联。"""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE payables SET status = '已付款', voucher_id = ? WHERE id = ?",
            (voucher_id, payable_id),
        )
        conn.commit()
    finally:
        conn.close()
