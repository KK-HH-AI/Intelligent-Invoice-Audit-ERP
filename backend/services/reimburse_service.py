"""报销单服务：创建（含一票一报防重）与财务审批流转。

规则：
- 仅 AI 审查"已通过"的发票可发起报销；
- 一张发票只能关联一张报销单（invoices.reimburse_id 回填锁定）；
- 仅"待财务审批"状态可审批，审批后不可重复操作。
"""
import db
from models import invoice as invoice_model
from models import reimburse as reimburse_model
from datetime import datetime


def create(employee: str, invoice_id: int, type=None, description=None) -> dict:
    """员工基于一张已通过的发票创建报销单，回填发票关联。"""
    inv = invoice_model.get(invoice_id)
    if inv is None:
        raise ValueError(f"发票不存在: id={invoice_id}")
    if inv["status"] != "已通过":
        raise ValueError("仅 AI 审查通过的发票可以报销")
    if inv["reimburse_id"]:
        raise ValueError("该发票已关联报销单，不能重复报销")

    rid = reimburse_model.create(
        code=_next_code(),
        employee=employee,
        type=type,
        amount=inv["amount"],  # 报销金额取发票价税合计，不信任前端传入
        description=description,
        invoice_id=invoice_id,
    )
    invoice_model.set_reimburse(invoice_id, rid)
    return reimburse_model.get(rid)


def approve(reimburse_id: int) -> dict:
    """财务审批通过。"""
    return _settle(reimburse_id, "已通过")


def reject(reimburse_id: int) -> dict:
    """财务驳回。"""
    return _settle(reimburse_id, "已驳回")


def latest_audit_report(invoice_id: int):
    """财务审批页的 AI 意见：发票最新一份审查报告，无则 None。"""
    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT result, content_md, created_at FROM audit_reports"
            " WHERE invoice_id = ? ORDER BY id DESC LIMIT 1",
            (invoice_id,),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def _settle(rid: int, status: str) -> dict:
    rb = reimburse_model.get(rid)
    if rb is None:
        raise ValueError(f"报销单不存在: id={rid}")
    if rb["status"] != "待财务审批":
        raise ValueError("该报销单已审批，不能重复操作")
    reimburse_model.update_status(rid, status)
    return reimburse_model.get(rid)


def _next_code() -> str:
    """报销单编号 BX-{年份}-{序号:03d}，年度内自增。"""
    prefix = f"BX-{datetime.now().year}-"
    seq = 1 + sum(
        1 for r in reimburse_model.list_all()
        if (r["code"] or "").startswith(prefix)
    )
    return f"{prefix}{seq:03d}"
