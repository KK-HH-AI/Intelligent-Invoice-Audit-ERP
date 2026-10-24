"""凭证路由：生成 / 审核 / 过账（财务）+ 列表 / 总账查询（登录用户）。"""
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_current_user, require_role
from models import voucher as voucher_model
from services import voucher_service

router = APIRouter(prefix="/api/vouchers", tags=["vouchers"])


class GenerateIn(BaseModel):
    reimburse_id: int


@router.post("/generate")
def generate_voucher(body: GenerateIn,
                     user: dict = Depends(require_role("finance"))):
    """从已通过的报销单生成凭证（draft），分录由后端模板决定。"""
    try:
        return voucher_service.generate_from_reimburse(body.reimburse_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@router.post("/{voucher_id}/approve")
def approve_voucher(voucher_id: int,
                    user: dict = Depends(require_role("finance"))):
    """审核：draft → approved。"""
    try:
        voucher_service.approve_voucher(voucher_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    return {"id": voucher_id, "status": "approved"}


@router.post("/{voucher_id}/post")
def post_voucher(voucher_id: int,
                 user: dict = Depends(require_role("finance"))):
    """过账：approved → posted，分录登记总账。"""
    try:
        return voucher_service.post_voucher(voucher_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@router.get("")
def list_vouchers(user: dict = Depends(get_current_user)):
    """凭证列表（新→旧），entries 解析为数组供前端直接渲染。"""
    rows = []
    for row in voucher_model.list_all():
        item = dict(row)
        item["entries"] = json.loads(item.pop("entries_json"))
        rows.append(item)
    return rows


@router.get("/ledger")
def ledger(user: dict = Depends(get_current_user)):
    """总账科目余额（期初/借贷发生额/期末），按科目编码排序。"""
    return [dict(row) for row in voucher_model.ledger_list()]
