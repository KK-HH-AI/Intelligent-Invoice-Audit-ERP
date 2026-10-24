"""预算规则实体：类目 / 限额 / 已用 / 期间。

纪律：只 import db；"扣减还是回滚、剩余怎么算"等规则由 service 决定，
本层只提供无脑读写原语（adjust_used 接受带符号增量）。
"""
from db import get_conn


def upsert_rule(category: str, limit_amount: float, period: str) -> int:
    """写入规则；同（类目, 期间）已存在则覆盖限额，已用额度保留。"""
    conn = get_conn()
    try:
        conn.execute(
            """INSERT INTO budget_rules (category, limit_amount, period)
               VALUES (?, ?, ?)
               ON CONFLICT (category, period)
               DO UPDATE SET limit_amount = excluded.limit_amount""",
            (category, limit_amount, period),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id FROM budget_rules WHERE category = ? AND period = ?",
            (category, period),
        ).fetchone()
        return row["id"]
    finally:
        conn.close()


def find(category: str, period: str):
    """按类目+期间取规则，无则 None。"""
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM budget_rules WHERE category = ? AND period = ?",
            (category, period),
        ).fetchone()
    finally:
        conn.close()


def list_all(period: str | None = None) -> list:
    """规则清单；period 为空返回全部，按类目排序。"""
    conn = get_conn()
    try:
        if period:
            rows = conn.execute(
                "SELECT * FROM budget_rules WHERE period = ? ORDER BY category",
                (period,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM budget_rules ORDER BY period DESC, category"
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def adjust_used(category: str, period: str, delta: float) -> bool:
    """增减已用额度（delta 为负即回滚），返回是否有匹配行。

    MAX(0, ...) 兜底：浮点误差或异常回滚不允许把已用打成负数。
    """
    conn = get_conn()
    try:
        cur = conn.execute(
            """UPDATE budget_rules
               SET used_amount = MAX(0, used_amount + ?)
               WHERE category = ? AND period = ?""",
            (delta, category, period),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
