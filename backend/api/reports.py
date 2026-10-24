"""财务报表路由：联动统计一次聚合（财务专属，报表含预算与总账数据）。"""
from fastapi import APIRouter, Depends

from api.deps import require_role
from services import report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/summary")
def report_summary(_: dict = Depends(require_role("finance"))):
    """审查通过率 + 驳回原因 TOP + 预算执行率 + 总账概览。"""
    return report_service.get_full_report()
