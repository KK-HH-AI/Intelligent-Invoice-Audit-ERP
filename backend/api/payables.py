"""应付路由：生成应付单 / 结算生成凭证 / 列表（财务专属）。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import require_role
from services import payable_service

router = APIRouter(prefix="/api/payables", tags=["payables"])


class GenerateIn(BaseModel):
    invoice_id: int


@router.post("/generate")
def generate_payable(body: GenerateIn, _: dict = Depends(require_role("finance"))):
    """采购发票 → 应付单。"""
    try:
        return payable_service.generate_from_invoice(body.invoice_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from None


@router.post("/{payable_id}/settle")
def settle_payable(payable_id: int, _: dict = Depends(require_role("finance"))):
    """应付单 → 生成凭证并过账 → 标记已付款。"""
    try:
        return payable_service.settle(payable_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from None


@router.get("")
def list_payables(_: dict = Depends(require_role("finance"))):
    return payable_service.list_payables()
