"""应收单路由：生成 / 收款 / 列表（财务专属，对称应付）。"""
from fastapi import APIRouter, Depends, HTTPException

from api.deps import require_role
from services import receivable_service

router = APIRouter(prefix="/api/receivables", tags=["receivables"])


@router.get("")
def list_receivables(_: dict = Depends(require_role("finance"))):
    return receivable_service.list_receivables()


@router.post("/generate")
def generate(body: dict, _: dict = Depends(require_role("finance"))):
    """从已通过的销售发票生成应收单。body: {invoice_id}"""
    invoice_id = body.get("invoice_id")
    if not invoice_id:
        raise HTTPException(400, "缺少 invoice_id")
    try:
        return receivable_service.generate_from_invoice(invoice_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{receivable_id}/settle")
def settle(receivable_id: int, _: dict = Depends(require_role("finance"))):
    """收款：生成凭证（借 1122 / 贷 6001）→ 审核 → 过账 → 已收款。"""
    try:
        return receivable_service.settle(receivable_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
