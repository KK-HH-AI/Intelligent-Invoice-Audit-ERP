"""报销单路由：创建（登录用户）/ 审批（仅财务）。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.deps import get_current_user, require_role
from models import reimburse as reimburse_model
from services import reimburse_service

router = APIRouter(prefix="/api/reimburse", tags=["reimburse"])


class ReimburseIn(BaseModel):
    invoice_id: int
    type: str = Field(min_length=1, max_length=32)
    description: str = Field(default=None, max_length=200)


@router.post("")
def create_reimburse(body: ReimburseIn,
                     user: dict = Depends(get_current_user)):
    """基于一张 AI 审查通过的发票创建报销单（金额取发票价税合计）。"""
    try:
        rb = reimburse_service.create(
            user["username"], body.invoice_id, body.type, body.description
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    return dict(rb)


@router.get("")
def list_reimburse(user: dict = Depends(get_current_user)):
    """报销单列表（新→旧）。"""
    return [dict(row) for row in reimburse_model.list_all()]


@router.post("/{reimburse_id}/approve")
def approve_reimburse(reimburse_id: int,
                      user: dict = Depends(require_role("finance"))):
    """财务审批通过；返回单据 + 发票最新 AI 审查意见。"""
    rb = _settle(reimburse_service.approve, reimburse_id)
    return {
        "reimbursement": dict(rb),
        "ai_opinion": reimburse_service.latest_audit_report(rb["invoice_id"]),
    }


@router.post("/{reimburse_id}/reject")
def reject_reimburse(reimburse_id: int,
                     user: dict = Depends(require_role("finance"))):
    """财务驳回；返回单据 + 发票最新 AI 审查意见。"""
    rb = _settle(reimburse_service.reject, reimburse_id)
    return {
        "reimbursement": dict(rb),
        "ai_opinion": reimburse_service.latest_audit_report(rb["invoice_id"]),
    }


def _settle(action, reimburse_id: int):
    try:
        return action(reimburse_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
