"""组合根：创建 FastAPI 应用，装配数据库 / OCR 引擎 / 总账种子 / 路由。

启动（在 backend/ 目录下）：
    uvicorn app:app --reload --port 8000

分层依赖只向下：api → services → models → db；utils 横向。
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import db
from api import audit, auth, budgets, invoices, payables, receivables, reimburse, reports, vouchers
from services import ocr_engine, voucher_service

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """启动装配：建表 → 总账期初种子 → OCR 引擎（失败不阻塞启动）。"""
    db.init_db()
    voucher_service.seed_ledger_if_empty()
    try:
        ocr_engine.init_ocr()
    except Exception as e:  # 环境缺 paddle 时：上传识别暂不可用，其余功能正常
        logger.warning("OCR 引擎初始化失败，发票识别功能暂不可用: %s", e)
    logger.info("后端启动完成")
    yield


app = FastAPI(title="智能发票审查系统 API", lifespan=lifespan)

# 开发期放开跨域（JWT 走 Authorization 头，不依赖 Cookie）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(invoices.router)
app.include_router(reimburse.router)
app.include_router(vouchers.router)
app.include_router(budgets.router)
app.include_router(payables.router)
app.include_router(audit.router)
app.include_router(reports.router)
app.include_router(receivables.router)
