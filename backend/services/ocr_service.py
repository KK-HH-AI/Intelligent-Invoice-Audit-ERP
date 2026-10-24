"""发票识别服务：文件 → 图像 → OCR → DeepSeek 字段提取 → 映射入库 + 查重。

由旧 api/invoice_ocr.py 改造：
- 修复 PDF 多页 bug：旧实现在循环内覆盖同一个 image 变量，多页 PDF 只有
  最后一页被识别；现在逐页识别并合并结果；
- 识别结果不再落 invoice.json（旧 app.py 的磁盘临时传递方式），直接返回
  结构化数据并入库；
- need.txt / ignore.txt 提示词资产随服务迁入 services/（旧 api/ 下副本冻结）；
- 附件文件由 api 层存入 uploads/，本服务只负责写表。
"""
import json
import logging
import os
import re

import cv2
import fitz
import numpy as np
from openai import APIConnectionError, APIError, OpenAI

import db
from models import invoice as invoice_model
from services import ai_mock
from services.ocr_engine import get_ocr

logger = logging.getLogger(__name__)

_SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))
_NEED_PATH = os.path.join(_SERVICES_DIR, "need.txt")
_IGNORE_PATH = os.path.join(_SERVICES_DIR, "ignore.txt")


def process_invoice(source_path: str, original_name: str, kind: str = "报销") -> dict:
    """识别一张发票文件（图片或 PDF）→ 查重 → 入库。

    Args:
        source_path: 已存盘的发票文件路径（api 层负责存入 uploads/）
        original_name: 存储文件名（写入 invoices.source_file）

    Returns:
        dict: {invoice_id, duplicate, fields}
        duplicate=True 时 invoice_id 为已存在记录的 id，不重复入库；
        fields 为 DeepSeek 原始提取结果（前端识别预览用）。

    Raises:
        ValueError: 文件无法读取 / 未识别到文字 / 未提取到发票号码
    """
    ocr_items = []
    if ai_mock.is_mock_enabled():
        # 模拟模式：不做真 OCR/DeepSeek，按文件名约定生成假提取结果
        raw = ai_mock.fake_fields(original_name)
    else:
        for page_no, image in enumerate(_load_images(source_path), start=1):
            page_items = _ocr_image(_preprocess_image(image))
            for item in page_items:
                item["page"] = page_no  # 多页 PDF 标注来源页
            ocr_items.extend(page_items)

        if not ocr_items:
            raise ValueError("未识别到任何文字内容")
        raw = _extract_fields(ocr_items)

    fields = map_fields(raw)
    if not fields["invoice_no"]:
        raise ValueError("未能提取到发票号码，无法入库")

    existing = invoice_model.find_by_no(fields["invoice_no"])
    if existing:
        logger.info("发票重复入库拦截: %s", fields["invoice_no"])
        return {"invoice_id": existing["id"], "duplicate": True, "fields": fields}

    inv_id = invoice_model.create(source_file=original_name, kind=kind, **fields)
    return {"invoice_id": inv_id, "duplicate": False, "fields": fields}


def add_attachments(invoice_id: int, stored_names) -> list:
    """登记随单附件（kind=随单审批单）；文件已由 api 层存盘，此处只写表。"""
    if not stored_names:
        return []
    conn = db.get_conn()
    try:
        ids = []
        for name in stored_names:
            cur = conn.execute(
                "INSERT INTO attachments (invoice_id, file_path, kind)"
                " VALUES (?, ?, '随单审批单')",
                (invoice_id, name),
            )
            ids.append(cur.lastrowid)
        conn.commit()
        return ids
    finally:
        conn.close()


def map_fields(raw: dict) -> dict:
    """DeepSeek 提取结果 → invoices 表列；纯函数，便于单独验证。

    amount 取价税合计（入账与报销均按含税总额），tax 取合计税额；
    "无" / 空值统一清洗为 None，金额无法解析时回落 0.0。
    """
    return {
        "invoice_no": _clean(raw.get("发票号码")),
        "invoice_date": _parse_date(raw.get("开票日期")),
        "amount": _parse_amount(raw.get("价税合计(小写)")),
        "tax": _parse_amount(raw.get("合计税额")),
        "invoice_type": _clean(raw.get("发票名称")),
        "seller": _clean(raw.get("销售方名称")),
        "buyer": _clean(raw.get("购买方名称")),
        "category": _clean(raw.get("费用类别")),   # 预算对照类目（二期）
    }


def _clean(value):
    if value is None:
        return None
    text = str(value).strip()
    return None if text in ("", "无") else text


def _parse_amount(value) -> float:
    text = _clean(value)
    if not text:
        return 0.0
    matched = re.search(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    return float(matched.group()) if matched else 0.0


def _parse_date(value):
    text = _clean(value)
    if not text:
        return None
    matched = re.search(r"(\d{4})[年\-/.](\d{1,2})[月\-/.](\d{1,2})", text)
    if matched:
        return f"{int(matched[1]):04d}-{int(matched[2]):02d}-{int(matched[3]):02d}"
    return text


def _load_images(path: str) -> list:
    """文件 → 图像列表；PDF 逐页渲染（修复旧版只识别最后一页的 bug）。"""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        images = []
        doc = fitz.Document(path)
        try:
            for page in doc:
                zoom = 2.0
                side = max(page.rect.width, page.rect.height)
                if side > 2000:
                    zoom = 1.5
                elif side < 1000:
                    zoom = 2.5
                pix = page.get_pixmap(
                    matrix=fitz.Matrix(zoom, zoom),
                    alpha=False,
                    colorspace=fitz.csRGB,
                )
                image = np.frombuffer(pix.samples, dtype=np.uint8)
                image = image.reshape(pix.h, pix.w, pix.n)
                if pix.n == 4:
                    image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
                elif pix.n == 1:
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
                images.append(image)
        finally:
            doc.close()
        return images

    image = cv2.imread(path)
    if image is None:
        raise ValueError(f"无法读取图像文件: {os.path.basename(path)}")
    return [image]


def _ocr_image(image) -> list:
    """单张图像 OCR → [{text, x, y}, ...]（文本框中心点坐标）。"""
    result = get_ocr().ocr(image)
    if not result or result[0] is None:
        return []
    items = []
    for line in result[0]:
        text = line[1][0]
        position = line[0]
        xs = [p[0] for p in position]
        ys = [p[1] for p in position]
        items.append({
            "text": text,
            "x": int((min(xs) + max(xs)) / 2),
            "y": int((min(ys) + max(ys)) / 2),
        })
    return items


def _extract_fields(ocr_items: list) -> dict:
    """OCR 结果 + need/ignore 字段表 → DeepSeek 提取 → dict。"""
    with open(_NEED_PATH, encoding="utf-8") as f:
        need_fields = f.read().strip()
    with open(_IGNORE_PATH, encoding="utf-8") as f:
        ignore_fields = f.read().strip()

    api_key = os.getenv("DEEPSEEK_API_KEY")
    api_url = os.getenv("DEEPSEEK_API_URL")
    model = os.getenv("DEEPSEEK_MODEL_NAME")
    if not api_key or not api_url or not model:
        raise ValueError("DeepSeek API 配置缺失，请检查 .env 文件")

    system_prompt = (
        "你是一个专业的电子发票字段提取与结构化处理AI助手。\n"
        "你的核心任务是根据用户提供的包含文本和坐标信息的OCR识别结果，"
        "精确地提取指定的关键字段，并忽略其他无关信息。\n"
        "请严格遵循以下规则进行处理：\n"
        "1.  角色定位: 你是发票信息提取专家，务必保证提取结果的准确性和完整性，"
        "追求语言的真实性，不虚构不存在的内容。\n"
        "2.  输入理解: \n"
        "    1.输入是包含文本 (text) 及其位置 (x, y 坐标) 的OCR结果列表。"
        "你需要利用文本和坐标信息来定位字段及其对应的值，"
        "通常字段名和其值在空间上是邻近的。\n"
        "3.  字段处理:\n"
        "    1. 用户将在后续消息中提供需要提取的字段列表 (`need.txt`) "
        "和需要忽略的字段列表 (`ignore.txt`)。\n"
        "    2. 你必须提取 `need.txt` 中要求的所有字段。\n"
        "    3. 你必须忽略 `ignore.txt` 中列出的所有字段。\n"
        "4.  处理缺失值:\n"
        "    1. 如果在OCR结果中无法找到 `need.txt` 中某个字段的对应值"
        "（或该字段本身在发票中不存在），请在该字段的值处填入字符串 \"无\"。\n"
        "    2. 对于列表类型的字段（例如'购买货物及服务'），"
        "如果发票中没有相关的项目信息，请返回一个空列表 `[]`。\n"
        "5.  输出格式:\n"
        "    1. JSON对象应包含所有在 `need.txt` 中要求的字段作为键。\n"
        "    2. 最终结果**必须**以严格的JSON对象格式返回。\n"
        "    3. **绝对不要**在JSON结果之外添加任何解释性文字、"
        "代码标记（如 ```json ... ```）、注释或其他非JSON内容。"
        "输出必须是纯粹的、可以直接解析的JSON。\n"
    )
    user_prompt = (
        "请根据系统定义的规则，处理以下OCR结果：\n"
        f"OCR数据: {json.dumps(ocr_items, ensure_ascii=False)}\n"
        f"need.txt: {need_fields}\n"
        f"ignore.txt: {ignore_fields}\n"
    )

    client = OpenAI(api_key=api_key, base_url=api_url)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            timeout=150,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
    except APIConnectionError as e:
        raise Exception(f"DeepSeek 连接失败: {e}") from e
    except APIError as e:
        raise Exception(f"DeepSeek API错误: {e.status_code} - {e.message}") from e

    # 部分兼容网关会包 ```json 围栏，剥掉再解析
    content = re.sub(r"^\s*```json\s*", "", content or "", flags=re.IGNORECASE)
    content = re.sub(r"\s*```\s*$", "", content, flags=re.IGNORECASE)
    return json.loads(content)


def _preprocess_image(image, max_size=3000):
    """增强图像质量以提高 OCR 识别率（旧实现原样迁移）。"""
    if image is None or image.size == 0:
        raise ValueError("输入图像无效")

    try:
        # 1. 限制图像尺寸，避免内存溢出
        height, width = image.shape[:2]
        if max(height, width) > max_size:
            scale = max_size / max(height, width)
            image = cv2.resize(
                image, (int(width * scale), int(height * scale)),
                interpolation=cv2.INTER_AREA,
            )
            logger.info("图像已缩小以避免内存溢出")

        # 2-6. 灰度 → 自适应二值化 → 开运算降噪 → 边缘增强 → 叠加回原图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2,
        )
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        edges = cv2.Canny(opening, 50, 150)
        dilated_edges = cv2.dilate(edges, kernel, iterations=1)
        enhanced_binary = cv2.addWeighted(binary, 0.8, dilated_edges, 0.2, 0)

        # 7-9. 转回彩色 → CLAHE 对比度增强 → USM 锐化
        enhanced_color = cv2.cvtColor(enhanced_binary, cv2.COLOR_GRAY2BGR)
        lab = cv2.cvtColor(enhanced_color, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        merged = cv2.merge([clahe.apply(l_channel), a_channel, b_channel])
        final_image = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
        gaussian = cv2.GaussianBlur(final_image, (0, 0), 3)
        final_image = cv2.addWeighted(final_image, 1.5, gaussian, -0.5, 0)

        # 10. 图像太小时适当放大，提高识别率
        height, width = final_image.shape[:2]
        if min(height, width) < 1000:
            scale = 1000 / min(height, width)
            final_image = cv2.resize(
                final_image, (int(width * scale), int(height * scale)),
                interpolation=cv2.INTER_CUBIC,
            )
        return final_image

    except cv2.error as cv_err:
        logger.error("OpenCV处理图像时出错: %s", cv_err)
        # 降级：缩放 + 简单锐化
        try:
            height, width = image.shape[:2]
            if max(height, width) > max_size:
                scale = max_size / max(height, width)
                image = cv2.resize(
                    image, (int(width * scale), int(height * scale)),
                    interpolation=cv2.INTER_AREA,
                )
            sharpen_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            return cv2.filter2D(image, -1, sharpen_kernel)
        except Exception as e:
            logger.error("基本图像处理也失败: %s", e)
            return image
    except Exception as e:
        logger.error("图像预处理失败: %s", e)
        return image
