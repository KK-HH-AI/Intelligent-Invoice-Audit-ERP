"""应付服务：采购发票 → 应付单 → 凭证（借 6401 主营业务成本 / 贷 2202 应付账款）。

口径简化（二期 T17）：凭证过账即视为应付确认入账 → 应付单标记"已付款"；
真实的付款核销流程留待三期。
"""
from datetime import datetime

from models import invoice as invoice_model
from models import payable as payable_model
from services import voucher_service


def list_payables() -> list:
    return payable_model.list_all()


def generate_from_invoice(invoice_id: int) -> dict:
    """采购 + 审查已通过 + 未生成过应付的发票 → 应付单（CG 编号，一票一应付）。"""
    inv = invoice_model.get(invoice_id)
    if inv is None:
        raise ValueError(f"发票不存在: id={invoice_id}")
    if inv["kind"] != "采购":
        raise ValueError("仅采购发票可以生成应付单")
    if inv["status"] != "已通过":
        raise ValueError("仅审查已通过的发票可以生成应付单")
    if payable_model.find_by_invoice(invoice_id):
        raise ValueError("该发票已生成过应付单")

    year = datetime.now().year
    prefix = f"CG-{year}-"
    seq = 1 + sum(
        1 for p in payable_model.list_all()
        if (p["code"] or "").startswith(prefix)
    )
    code = f"{prefix}{seq:03d}"
    pid = payable_model.create(
        code=code, amount=inv["amount"],
        supplier=inv["seller"], invoice_id=invoice_id,
    )
    return {"payable_id": pid, "code": code,
            "amount": inv["amount"], "supplier": inv["seller"]}


def settle(payable_id: int) -> dict:
    """应付单 → 凭证（借 6401 / 贷 2202）→ 审核 → 过账 → 标记已付款。"""
    pay = payable_model.get(payable_id)
    if pay is None:
        raise ValueError(f"应付单不存在: id={payable_id}")
    if pay["status"] != "待付款":
        raise ValueError("该应付单已生成过凭证")

    amount = pay["amount"]
    entries = [
        {"account": "6401", "accountName": "主营业务成本",
         "debit": amount, "credit": 0},
        {"account": "2202", "accountName": "应付账款",
         "debit": 0, "credit": amount},
    ]
    created = voucher_service.create_voucher(
        summary=f"采购应付：{pay['supplier'] or pay['code']}", entries=entries)
    voucher_service.approve_voucher(created["voucher_id"])
    voucher_service.post_voucher(created["voucher_id"])
    payable_model.mark_settled(payable_id, created["voucher_id"])
    return {"payable_id": payable_id, "voucher_id": created["voucher_id"],
            "voucher_code": created["code"], "status": "已付款", "entries": entries}
