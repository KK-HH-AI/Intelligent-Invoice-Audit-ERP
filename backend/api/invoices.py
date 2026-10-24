"""发票路由：上传（识别→入库→审查）+ 列表 / 详情。

存盘约定：文件落 services.UPLOADS_DIR，文件名
{时间戳}_{8位随机}{扩展名}；invoices.source_file 与 attachments.file_path
存"存储文件名"，读取时拼接 UPLOADS_DIR。
"""
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

import db
from api.deps import get_current_user
from models import invoice as invoice_model
from services import UPLOADS_DIR
from services import audit_service
from services import ocr_service

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

INVOICE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".pdf")
ATTACH_EXTS = INVOICE_EXTS + (".docx", ".xls", ".xlsx")


def _save_upload(file: UploadFile, allowed_exts: tuple) -> str:
    """校验扩展名并存入 uploads/，返回存储文件名。"""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400,
                            detail=f"不支持的文件类型: {ext or '无扩展名'}")
    stored = f"{datetime.now():%Y%m%d%H%M%S}_{uuid.uuid4().hex[:8]}{ext}"
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    with open(os.path.join(UPLOADS_DIR, stored), "wb") as f:
        f.write(file.file.read())
    return stored


def _remove_files(*stored_names: str) -> None:
    """清理 uploads/ 中的孤儿文件（忽略不存在的情况）。"""
    for name in stored_names:
        if not name:
            continue
        try:
            os.remove(os.path.join(UPLOADS_DIR, name))
        except OSError:
            pass


@router.post("")
def upload_invoice(
    current_user: dict = Depends(get_current_user),
    invoice: UploadFile = File(...),
    attachments: list[UploadFile] = File(default=[]),
    kind: str = Form("报销"),
):
    """上传发票 + 可选随单附件：存盘 → OCR/DeepSeek 识别入库 → AI 审查。

    - kind：发票用途（报销/采购/销售：采购→应付单 二期 T17，销售→应收单 三期）；
    - 发票号重复：清理本次文件，返回 duplicate=true 与已存在记录 id；
    - 识别失败（无法读取/无发票号）：清理文件，400；
    - AI 审查失败不回滚入库：发票保持待审，响应带 audit_error。
    """
    if kind not in ("报销", "采购", "销售"):
        raise HTTPException(status_code=400, detail="kind 仅支持 报销/采购/销售")
    saved = [_save_upload(invoice, INVOICE_EXTS)]
    saved += [_save_upload(a, ATTACH_EXTS) for a in (attachments or [])]

    try:
        # mock 的文件名约定依赖用户原始文件名（存储名是时间戳，不能传）
        result = ocr_service.process_invoice(
            os.path.join(UPLOADS_DIR, saved[0]), invoice.filename or saved[0],
            kind=kind,
        )
    except ValueError as e:
        _remove_files(*saved)
        raise HTTPException(status_code=400, detail=str(e)) from None
    except Exception:
        _remove_files(*saved)
        raise

    if result["duplicate"]:
        _remove_files(*saved)
        return {
            "duplicate": True,
            "invoice_id": result["invoice_id"],
            "message": "该发票已存在，请勿重复上传",
        }

    inv_id = result["invoice_id"]
    if saved[1:]:
        ocr_service.add_attachments(inv_id, saved[1:])

    response = {
        "duplicate": False,
        "invoice": dict(invoice_model.get(inv_id)),
        "fields": result["fields"],
        "audit": None,
    }
    try:
        response["audit"] = audit_service.review_invoice(inv_id)
        if response["audit"]:
            # invoice 对象是审查前取的，同步审查后的最终状态
            response["invoice"]["status"] = response["audit"]["status"]
    except Exception as e:  # DeepSeek 不可用等：留待审状态，稍后重审
        response["audit_error"] = f"AI 审查暂不可用: {e}"
    return response


@router.get("")
def list_invoices(status: str | None = None,
                  current_user: dict = Depends(get_current_user)):
    """发票列表（可按状态过滤），新→旧。"""
    return [dict(row) for row in invoice_model.list_all(status)]


@router.get("/{invoice_id}")
def invoice_detail(invoice_id: int,
                   current_user: dict = Depends(get_current_user)):
    """发票详情：记录 + 随单附件 + 最新一份审查报告。"""
    inv = invoice_model.get(invoice_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="发票不存在")

    conn = db.get_conn()
    try:
        attachments = conn.execute(
            "SELECT id, file_path, kind FROM attachments"
            " WHERE invoice_id = ? ORDER BY id",
            (invoice_id,),
        ).fetchall()
        report = conn.execute(
            "SELECT id, result, content_md, created_at FROM audit_reports"
            " WHERE invoice_id = ? ORDER BY id DESC LIMIT 1",
            (invoice_id,),
        ).fetchone()
    finally:
        conn.close()

    return {
        "invoice": dict(inv),
        "attachments": [dict(row) for row in attachments],
        "report": dict(report) if report else None,
    }
