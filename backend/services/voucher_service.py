"""凭证服务：报销单 → 分录模板 → 凭证；审核；过账更新总账。

分录模板迁移自前端 Voucher.vue 的 generateVoucher（一期仅报销单）：
    借 管理费用(6602) / 贷 银行存款(1002)
期末余额沿用前端口径：closing = opening + debit - credit
（报销链路的 6602 借方增、1002 贷方减均适用；应收/应付类型二期 T17
接入时再按科目方向扩展）。

凭证状态流：draft --审核--> approved --过账--> posted（与前端一致）。
"""
import json
from datetime import datetime

import db
from models import reimburse as reimburse_model
from models import voucher as voucher_model

# 前端 finance.js 的演示种子科目：银行存款期初 10 万；后端化后由 app 启动时补种
_SEED_ACCOUNTS = [
    {"code": "1002", "name": "银行存款", "opening": 100000.0},
    {"code": "1122", "name": "应收账款", "opening": 0.0},
    {"code": "2202", "name": "应付账款", "opening": 0.0},
    {"code": "6001", "name": "主营业务收入", "opening": 0.0},
    {"code": "6401", "name": "主营业务成本", "opening": 0.0},
    {"code": "6602", "name": "管理费用", "opening": 0.0},
]


def seed_ledger_if_empty() -> None:
    """ledger 为空时按前端演示数据补种期初余额（幂等）。"""
    conn = db.get_conn()
    try:
        count = conn.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
        if count:
            return
        for account in _SEED_ACCOUNTS:
            conn.execute(
                "INSERT INTO ledger (account_code, account_name, opening, closing)"
                " VALUES (?, ?, ?, ?)",
                (account["code"], account["name"],
                 account["opening"], account["opening"]),
            )
        conn.commit()
    finally:
        conn.close()


def create_voucher(summary: str, entries: list, date: str = None) -> dict:
    """通用建凭证入口（PZ 编号统一收口）：报销/应付等业务共用。"""
    code = _next_code()
    vid = voucher_model.create(
        code=code,
        entries_json=json.dumps(entries, ensure_ascii=False),
        date=date or datetime.now().strftime("%Y-%m-%d"),
        summary=summary,
        reimburse_id=None,
    )
    return {"voucher_id": vid, "code": code, "summary": summary, "entries": entries}


def generate_from_reimburse(reimburse_id: int, date: str = None) -> dict:
    """已通过的报销单 → 凭证（draft）。

    仅报销单 status=已通过 可生成（对应前端只列 approved 单据的限制）。
    """
    rb = reimburse_model.get(reimburse_id)
    if rb is None:
        raise ValueError(f"报销单不存在: id={reimburse_id}")
    if rb["status"] != "已通过":
        raise ValueError("仅已通过的报销单可以生成凭证")

    amount = rb["amount"]
    entries = [
        {"account": "6602", "accountName": "管理费用",
         "debit": amount, "credit": 0},
        {"account": "1002", "accountName": "银行存款",
         "debit": 0, "credit": amount},
    ]
    summary = "报销：" + (rb["description"] or rb["type"] or "")
    return create_voucher(summary, entries, date=date)


def approve_voucher(voucher_id: int) -> None:
    """审核：draft → approved。"""
    voucher = voucher_model.get(voucher_id)
    if voucher is None:
        raise ValueError(f"凭证不存在: id={voucher_id}")
    if voucher["status"] != "draft":
        raise ValueError("仅草稿状态的凭证可以审核")
    voucher_model.update_status(voucher_id, "approved")


def post_voucher(voucher_id: int) -> dict:
    """过账：approved → posted，并按分录累加总账。

    状态门槛同时是幂等保护：posted 凭证无法再次过账重复记账。
    """
    voucher = voucher_model.get(voucher_id)
    if voucher is None:
        raise ValueError(f"凭证不存在: id={voucher_id}")
    if voucher["status"] != "approved":
        raise ValueError("仅已审核(approved)的凭证可以过账")

    entries = json.loads(voucher["entries_json"])
    for entry in entries:
        debit = float(entry.get("debit") or 0)
        credit = float(entry.get("credit") or 0)
        # 前端口径：closing = opening + debit - credit，故增量 = 借 - 贷
        voucher_model.ledger_upsert(
            entry["account"], entry["accountName"],
            debit_delta=debit, credit_delta=credit,
            closing_delta=debit - credit,
        )
    voucher_model.update_status(voucher_id, "posted")
    return {"voucher_id": voucher_id, "entries": entries}


def _next_code() -> str:
    """凭证编号 PZ-{年份}-{序号:03d}，年度内自增。"""
    year = datetime.now().year
    prefix = f"PZ-{year}-"
    seq = 1 + sum(
        1 for v in voucher_model.list_all()
        if (v["code"] or "").startswith(prefix)
    )
    return f"{prefix}{seq:03d}"
