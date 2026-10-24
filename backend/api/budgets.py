"""预算路由：预算文件上传解析 / 余额一览（财务专属）。"""
import os
import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from api.deps import require_role
from services import budget_service

router = APIRouter(prefix="/api/budgets", tags=["budgets"])

_ALLOWED_EXTS = (".csv", ".xlsx", ".xls")


@router.post("/upload")
def upload_budget(
    file: UploadFile = File(...),
    period: str = Form(""),
    _: dict = Depends(require_role("finance")),
):
    """上传预算文件（csv/xlsx）解析入库，同类目覆盖限额、已用保留。"""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _ALLOWED_EXTS:
        raise HTTPException(400, f"仅支持 {'/'.join(_ALLOWED_EXTS)} 预算文件")

    from services import UPLOADS_DIR

    tmp_name = f"budget_{int(time.time())}{ext}"
    tmp_path = os.path.join(UPLOADS_DIR, tmp_name)
    try:
        with open(tmp_path, "wb") as out:
            out.write(file.file.read())
        return budget_service.import_rules(tmp_path, period or None)
    except ValueError as e:
        raise HTTPException(400, str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)  # 预算文件解析完即弃，不留盘


@router.get("")
def list_budgets(period: str = "", _: dict = Depends(require_role("finance"))):
    """余额一览：限额/已用/剩余/执行率，period 为空返回全部期间。"""
    return budget_service.list_with_remaining(period or None)
