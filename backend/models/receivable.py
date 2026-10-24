"""应收单实体：销售发票 → 应收单 → 凭证（三期增补）。

纪律：只 import db；编号规则、凭证模板等业务决策在 service 层。
"""
from db import get_conn


def create(*, code: str, amount: float, invoice_id: int, customer=None) -> int:
    """invoice_id 重复时 UNIQUE 约束抛 IntegrityError（一票一应收）。"""
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO receivables (code, customer, amount, invoice_id)"
            " VALUES (?, ?, ?, ?)",
            (code, customer, amount, invoice_id),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get(receivable_id: int):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM receivables WHERE id = ?", (receivable_id,)
        ).fetchone()
    finally:
        conn.close()


def find_by_invoice(invoice_id: int):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM receivables WHERE invoice_id = ?", (invoice_id,)
        ).fetchone()
    finally:
        conn.close()


def list_all() -> list:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM receivables ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def mark_received(receivable_id: int, voucher_id: int) -> None:
    """收款：过账即视为已收款，回填凭证关联。"""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE receivables SET status = '已收款', voucher_id = ? WHERE id = ?",
            (voucher_id, receivable_id),
        )
        conn.commit()
    finally:
        conn.close()
