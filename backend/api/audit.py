"""审查归档路由：报告流水查询 / 详情（登录用户可查，按单据追溯）。"""
from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user
from services import audit_service

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/reports")
def list_reports(invoice_no: str = "", result: str = "", limit: int = 100,
                 _: dict = Depends(get_current_user)):
    """归档流水：发票号模糊 / 结论筛选，新→旧。"""
    if result and result not in ("通过", "预警", "驳回"):
        raise HTTPException(400, "result 仅支持 通过/预警/驳回")
    return audit_service.list_reports(invoice_no or None, result or None, limit)


@router.get("/reports/{report_id}")
def get_report(report_id: int, _: dict = Depends(get_current_user)):
    """报告详情（含关联发票信息）。"""
    report = audit_service.get_report(report_id)
    if report is None:
        raise HTTPException(404, "报告不存在")
    return report
