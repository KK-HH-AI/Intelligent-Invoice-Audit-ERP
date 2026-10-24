"""应收服务：销售发票 → 应收单 → 收款凭证（借 1122 应收账款 / 贷 6001 主营业务收入）。

口径与应付对称（三期增补）：凭证过账即视为收款确认 → 应收单标记"已收款"；
含税额全额计收入（与应付模板同口径的演示简化，真实税金拆分留待后续）。
"""
from datetime import datetime

from models import invoice as invoice_model
from models import receivable as receivable_model
from services import voucher_service


def list_receivables() -> list:
    return receivable_model.list_all()


def generate_from_invoice(invoice_id: int) -> dict:
    """销售 + 审查已通过 + 未生成过应收的发票 → 应收单（YS 编号，一票一应收）。"""
    inv = invoice_model.get(invoice_id)
    if inv is None:
        raise ValueError(f"发票不存在: id={invoice_id}")
    if inv["kind"] != "销售":
        raise ValueError("仅销售发票可以生成应收单")
    if inv["status"] != "已通过":
        raise ValueError("仅审查已通过的发票可以生成应收单")
    if receivable_model.find_by_invoice(invoice_id):
        raise ValueError("该发票已生成过应收单")

    year = datetime.now().year
    prefix = f"YS-{year}-"
    seq = 1 + sum(
        1 for r in receivable_model.list_all()
        if (r["code"] or "").startswith(prefix)
    )
    code = f"{prefix}{seq:03d}"
    rid = receivable_model.create(
        code=code, amount=inv["amount"],
        customer=inv["buyer"], invoice_id=invoice_id,
    )
    return {"receivable_id": rid, "code": code,
            "amount": inv["amount"], "customer": inv["buyer"]}


def settle(receivable_id: int) -> dict:
    """应收单 → 收款凭证（借 1122 / 贷 6001）→ 审核 → 过账 → 标记已收款。"""
    rec = receivable_model.get(receivable_id)
    if rec is None:
        raise ValueError(f"应收单不存在: id={receivable_id}")
    if rec["status"] != "待收款":
        raise ValueError("该应收单已生成过凭证")

    amount = rec["amount"]
    entries = [
        {"account": "1122", "accountName": "应收账款",
         "debit": amount, "credit": 0},
        {"account": "6001", "accountName": "主营业务收入",
         "debit": 0, "credit": amount},
    ]
    created = voucher_service.create_voucher(
        summary=f"销售应收：{rec['customer'] or rec['code']}", entries=entries)
    voucher_service.approve_voucher(created["voucher_id"])
    voucher_service.post_voucher(created["voucher_id"])
    receivable_model.mark_received(receivable_id, created["voucher_id"])
    return {"receivable_id": receivable_id, "voucher_id": created["voucher_id"],
            "voucher_code": created["code"], "status": "已收款", "entries": entries}
