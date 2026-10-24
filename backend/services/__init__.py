"""服务层：业务编排（OCR 识别、AI 审查、凭证生成等一次完整业务动作）。

纪律：
- 可调用 models/ 与 utils/，不 import api/，不写 SQL 以外的 HTTP 概念；
- 编排业务流程、对接外部引擎（PaddleOCR / DeepSeek）；
- attachments / audit_reports 等无独立 model 文件的表，由相关 service
  直接写 SQL，但仍必须通过 db.get_conn() 拿连接。
"""
import os

from dotenv import load_dotenv

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)

# 任意 service 被 import 时统一从项目根 .env 加载配置
# （override=False：不覆盖调用方已设置的环境变量）
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

# 上传文件统一存放目录：api 层存盘、audit_service 读取时都用这个常量
UPLOADS_DIR = os.path.join(_BACKEND_DIR, "uploads")
