"""OCR 引擎封装：PaddleOCR 单例（懒加载）。

由旧 api/global_config.py 瘦身而来：
- 删除从未被调用的依赖版本检查、与 OCRManager 重复的 initialize_ocr；
- 模型目录默认指向 backend/ocr_models/（原 models/ 已改名），相对路径一律
  相对 backend/ 解析，摆脱对启动目录的依赖；
- 懒加载：import 本模块不触发引擎初始化，由 app 启动时显式调 init_ocr()。
"""
import logging
import os

# 环境变量由 services 包初始化时统一从项目根 .env 加载
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

# 模型目录：相对路径相对 backend/ 解析
_dir = os.getenv("PADDLE_OCR_MODEL_DIR") or "ocr_models"
MODEL_DIR = _dir if os.path.isabs(_dir) else os.path.join(_BACKEND_DIR, _dir)

DET_MODEL = os.getenv("PADDLE_OCR_DET_MODEL", "ch_PP-OCRv4_det_infer")
REC_MODEL = os.getenv("PADDLE_OCR_REC_MODEL", "ch_PP-OCRv4_rec_infer")
CLS_MODEL = os.getenv("PADDLE_OCR_CLS_MODEL", "ch_ppocr_mobile_v2.0_cls_infer")

_ocr_instance = None


def init_ocr(lang: str = "ch", use_angle_cls: bool = True) -> None:
    """初始化引擎（幂等，可重复调用）；由 app 启动流程触发一次。"""
    global _ocr_instance
    if _ocr_instance is not None:
        return

    # 函数内导入：无 paddle 环境时仅识别功能不可用，不阻塞其余功能启动
    from paddleocr import PaddleOCR

    ocr_params = {
        "use_angle_cls": use_angle_cls,
        "lang": lang,
        "use_gpu": False,
        "det_model_dir": os.path.join(MODEL_DIR, DET_MODEL),
        "rec_model_dir": os.path.join(MODEL_DIR, REC_MODEL),
        "cls_model_dir": os.path.join(MODEL_DIR, CLS_MODEL),
    }
    try:
        _ocr_instance = PaddleOCR(**ocr_params)
        logger.info("PaddleOCR 初始化成功，模型目录: %s", MODEL_DIR)
    except Exception as e:
        logger.error("PaddleOCR 初始化失败: %s", e)
        raise RuntimeError(f"PaddleOCR 初始化失败: {e}") from e


def get_ocr():
    """取引擎实例；未初始化时自动补一次初始化。"""
    if _ocr_instance is None:
        init_ocr()
    return _ocr_instance
