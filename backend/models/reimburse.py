"""报销单实体：CRUD + 状态流转。

状态用词此处定稿（建表时未加 CHECK）：待财务审批 → 已通过 / 已驳回。
"""
from db import get_conn

STATUSES = ("待财务审批", "已通过", "已驳回")


def create(*, employee: str, amount: float, type=None, description=None,
           invoice_id=None, code=None) -> int:
    """code（BX 前缀单号）由 service 层生成后传入。"""
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO reimbursements"
            " (code, employee, type, amount, description, invoice_id)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (code, employee, type, amount, description, invoice_id),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get(rid: int):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM reimbursements WHERE id = ?", (rid,)
        ).fetchone()
    finally:
        conn.close()


def list_all() -> list:
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM reimbursements ORDER BY id DESC"
        ).fetchall()
    finally:
        conn.close()


def update_status(rid: int, status: str) -> None:
    """财务审批：通过 / 驳回（附 AI 意见由 audit_reports 关联展示，不入本表）。"""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE reimbursements SET status = ? WHERE id = ?", (status, rid)
        )
        conn.commit()
    finally:
        conn.close()
