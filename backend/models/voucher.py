"""凭证实体：CRUD + 状态流转 + 总账（ledger）累加原语。"""
from db import get_conn

STATUSES = ("draft", "approved", "posted")


def create(*, code: str, entries_json: str, date=None, summary=None,
           reimburse_id=None) -> int:
    """entries_json 为分录数组 JSON（科目/借贷方向/金额），结构由 voucher_service 定义。"""
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO vouchers"
            " (code, date, summary, entries_json, reimburse_id)"
            " VALUES (?, ?, ?, ?, ?)",
            (code, date, summary, entries_json, reimburse_id),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get(vid: int):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM vouchers WHERE id = ?", (vid,)
        ).fetchone()
    finally:
        conn.close()


def list_all() -> list:
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM vouchers ORDER BY id DESC"
        ).fetchall()
    finally:
        conn.close()


def update_status(vid: int, status: str) -> None:
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE vouchers SET status = ? WHERE id = ?", (status, vid)
        )
        conn.commit()
    finally:
        conn.close()


def ledger_upsert(account_code: str, account_name: str,
                  debit_delta=0.0, credit_delta=0.0, closing_delta=0.0) -> None:
    """总账累加原语：按科目累加借贷发生额与期末余额增量。

    方向规则（借增贷减还是贷增借减）是业务知识，由 voucher_service 计算
    各科目的增量后传入，本函数只做无脑累加，保持与业务解耦。
    """
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO ledger"
            " (account_code, account_name, debit, credit, closing)"
            " VALUES (?, ?, ?, ?, ?)"
            " ON CONFLICT (account_code) DO UPDATE SET"
            "  account_name = excluded.account_name,"
            "  debit   = debit   + excluded.debit,"
            "  credit  = credit  + excluded.credit,"
            "  closing = closing + excluded.closing",
            (account_code, account_name, debit_delta, credit_delta,
             closing_delta),
        )
        conn.commit()
    finally:
        conn.close()


def ledger_list() -> list:
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM ledger ORDER BY account_code"
        ).fetchall()
    finally:
        conn.close()
