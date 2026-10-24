"""发票 AI 审查服务：发票记录 + 随单附件文本 + 预算对照 → AI → 报告入库 + 状态回写。

由旧 api/invoice_audit.py 改造：
- 旧版从磁盘临时文件 invoice.json / file.json 读输入、报告落 summary.md；
  新版输入直接取库（invoices + attachments），报告入 audit_reports 表；
- 结论与状态映射：通过→已通过，驳回→已驳回，预警→保持待审（人工复核）；
- 报告末行要求模型输出机器可读的「审查结论：通过|预警|驳回」，解析失败
  时按预警处理（宁可多一次人工复核，不可误放行）。

二期 T14 预算融合：
- 审查前先做真实预算对照（类目+期间匹配规则，金额>剩余 → 强制预警），
  预算是硬业务规则，模型结论不允许覆盖；
- 结论"通过"且规则存在 → 扣减 used_amount 并打 budget_deducted 标记；
  重审先回滚旧扣减再按新结论处理（幂等）；预警/驳回不扣减。
- AI_MOCK=1 时报告文案由 ai_mock 生成，预算对照/扣减逻辑仍真实执行。
"""
import logging
import os
import re
from datetime import datetime

import cv2
from openai import APIConnectionError, APIError, OpenAI

import db
from models import budget as budget_model
from models import invoice as invoice_model
from services import UPLOADS_DIR
from services import ai_mock
from services import doc_extract

logger = logging.getLogger(__name__)

# 结论 → 发票状态；None 表示保持现状（预警需人工复核）
_RESULT_TO_STATUS = {"通过": "已通过", "驳回": "已驳回", "预警": None}

# 模拟模式大额驳回线（三期演示规则）：文件名金额超此值 → 驳回，可造驳回测试数据
MOCK_REJECT_AMOUNT = 100000.0

_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp")


def review_invoice(invoice_id: int) -> dict:
    """审查一张发票，写报告并回写状态。

    Returns:
        dict: {report_id, result, status, content_md}
        status 为回写后的发票状态（预警时与原状态一致）。
    """
    inv = invoice_model.get(invoice_id)
    if inv is None:
        raise ValueError(f"发票不存在: id={invoice_id}")

    period = _period_of(inv)
    budget_lines, budget_result, rule = _budget_check(inv, period)

    # 幂等：重审先回滚上一次的预算扣减，再按本次结论处理
    if inv["budget_deducted"]:
        _rollback_budget(inv, period)

    content = _build_audit_content(inv, _attachment_texts(invoice_id), budget_lines)

    if ai_mock.is_mock_enabled():
        # 模拟结论优先级：预算硬规则 > 大额驳回（模拟规则，文件名可控金额造数） > 通过
        if budget_result:
            mock_result, mock_reason = budget_result, None
        elif inv["amount"] > MOCK_REJECT_AMOUNT:
            mock_result = "驳回"
            # 原因文本不带金额：同类驳回才能在报表 TOP 中聚成一类
            mock_reason = f"金额异常偏大（模拟规则：超 {MOCK_REJECT_AMOUNT:.0f} 元自动驳回）"
        else:
            mock_result, mock_reason = "通过", None
        report_md = ai_mock.fake_report(inv, budget_lines, mock_result, mock_reason)
    else:
        report_md = _call_deepseek(content)

    result, reason = _parse_result(report_md)
    if budget_result:
        # 硬规则：超限预算不允许被模型结论放行
        result, reason = budget_result, None

    report_id = _save_report(invoice_id, result, report_md, reason)
    new_status = _RESULT_TO_STATUS.get(result)
    if new_status:
        invoice_model.update_status(invoice_id, new_status)
    else:
        new_status = inv["status"]

    # 结论"通过"且有预算规则 → 扣减额度并打标记；预警/驳回不扣
    if result == "通过" and rule is not None:
        _deduct_budget(inv, period)

    return {
        "report_id": report_id,
        "result": result,
        "status": new_status,
        "content_md": report_md,
    }


def _period_of(inv) -> str:
    """预算期间约定：发票开票日期所在月（YYYY-MM），缺日期取当前月。"""
    if inv["invoice_date"]:
        return inv["invoice_date"][:7]
    return datetime.now().strftime("%Y-%m")


def _budget_check(inv, period: str) -> tuple:
    """发票金额 vs 预算规则（真实硬规则，两种模式都执行）。

    Returns:
        (报告行列表, 结论倾向 or None, 命中的规则 or None)
        结论倾向："预警"=金额超出剩余预算；None=交给 AI/默认结论。
    """
    if not inv["category"]:
        return ["- 发票未识别费用类别，跳过预算对照"], None, None
    rule = budget_model.find(inv["category"], period)
    if rule is None:
        return [f"- {inv['category']}（{period}）无预算规则，跳过预算对照"], None, None

    remaining = (rule["limit_amount"] or 0) - (rule["used_amount"] or 0)
    line = (f"- {inv['category']}（{period}）：预算 {rule['limit_amount']:.2f} 元，"
            f"已用 {rule['used_amount']:.2f} 元，剩余 {remaining:.2f} 元；"
            f"本发票 {inv['amount']:.2f} 元")
    if inv["amount"] > remaining:
        return [line + " → **超出剩余预算**"], "预警", rule
    return [line + " → 预算内"], None, rule


def _deduct_budget(inv, period: str) -> None:
    """扣减已用额度并打标记；标记失败则回滚扣减，防重审双扣。"""
    if not budget_model.adjust_used(inv["category"], period, inv["amount"]):
        return  # 规则在审查间隙被删除，扣减落空但审查结论不受影响
    try:
        invoice_model.set_budget_deducted(inv["id"], True)
    except Exception:
        budget_model.adjust_used(inv["category"], period, -inv["amount"])
        raise


def _rollback_budget(inv, period: str) -> None:
    """回滚上一次扣减并清标记；清标记失败则恢复扣减，防重复回滚。"""
    if not budget_model.adjust_used(inv["category"], period, -inv["amount"]):
        invoice_model.set_budget_deducted(inv["id"], False)  # 规则已删，只需清标记
        return
    try:
        invoice_model.set_budget_deducted(inv["id"], False)
    except Exception:
        budget_model.adjust_used(inv["category"], period, inv["amount"])
        raise


def _build_audit_content(inv, attachment_texts: list, budget_lines: list) -> str:
    """发票记录 + 附件文本 + 预算对照 → 审查输入（沿用旧版的分节标识）。"""
    invoice_json = (
        "{"
        + ", ".join(
            f'"{k}": "{inv[k]}"' for k in inv.keys() if k != "password"
        )
        + "}"
    )
    parts = ["【发票信息】", invoice_json, "【预算对照】", *(budget_lines or ["（无）"])]
    if attachment_texts:
        parts.append("【随单附件】")
        parts.extend(attachment_texts)
    else:
        parts.append("【随单附件】（本次上传未附随单附件，按发票本身审核）")
    return "\n".join(parts)


def _attachment_texts(invoice_id: int) -> list:
    """随单附件 → 文本列表：文档走提取器，图片走 OCR，缺失/失败给出标注。"""
    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT file_path, kind FROM attachments WHERE invoice_id = ?"
            " ORDER BY id",
            (invoice_id,),
        ).fetchall()
    finally:
        conn.close()

    if ai_mock.is_mock_enabled():
        # 模拟模式：不做真实 OCR/文档提取，避免 paddle 缺环境影响审查链路
        return [f"[模拟模式] 附件 {r['file_path']}（{r['kind']}）文本省略" for r in rows]

    texts = []
    for row in rows:
        path = os.path.join(UPLOADS_DIR, row["file_path"])
        if not os.path.exists(path):
            texts.append(f"[附件缺失: {row['file_path']}]")
            continue
        ext = os.path.splitext(row["file_path"])[1].lower()
        if ext in _IMAGE_EXTS:
            image = cv2.imread(path)
            items = doc_extract.process_image_ocr(image) if image is not None else None
            if isinstance(items, list) and items:
                texts.append(f"--- 附件 {row['file_path']}（{row['kind']}，OCR） ---\n"
                             + "\n".join(i["text"] for i in items))
            else:
                texts.append(f"[附件 {row['file_path']} OCR失败: {items}]")
            continue
        try:
            texts.append(
                f"--- 附件 {row['file_path']}（{row['kind']}） ---\n"
                + doc_extract.extract_file_content(path, row["file_path"])
            )
        except ValueError as e:
            texts.append(f"[附件 {row['file_path']} 无法提取文本: {e}]")
    return texts


def _call_deepseek(content: str) -> str:
    """发票 + 附件文本 → DeepSeek 审查 → markdown 报告。"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    api_url = os.getenv("DEEPSEEK_API_URL")
    model = os.getenv("DEEPSEEK_MODEL_NAME")
    if not api_key or not api_url or not model:
        raise ValueError("DeepSeek API 配置缺失，请检查 .env 文件")

    system_prompt = (
        "你是一个专业发票审核分析师，追求发票审核的严谨性和正确性。"
        "请严格按以下步骤处理：\n"
        "1. 识别要求：\n"
        "    1. 识别【发票信息】中的JSON内容，这是系统从发票图片OCR提取的字段。\n"
        "    2. 如提供【随单附件】，识别其中的签批/审核要求文本。\n"
        "2. 审核要求：\n"
        "    1. 如随单附件中有支出要求（预算、签批限额等），对照审核发票的"
        "支出金额、数量、单价、税额是否超出限制。\n"
        "    2. 审核发票字段是否存在异常项：商品名称、数量、单价、金额、税额、"
        "买卖双方信息等是否合理、自洽。\n"
        "    3. 如无随单附件，仅按发票本身的真实性、完整性与合理性审核。\n"
        "3. 输出要求：\n"
        "    1. 输出内容为 markdown 格式，包含：\n"
        "        一、发票总体情况\n"
        "        二、发票审核结果（对发票中的支出条目分点回答）\n"
        "        三、异常项检查\n"
        "        四、审核结论与建议\n"
        "    2. 以专业发票审核师的角度给出详细内容，结尾加上审核时间。\n"
        "    3. 报告的最后一行必须且只能是以下三者之一（机器可读）：\n"
        "        审查结论：通过\n"
        "        审查结论：预警\n"
        "        审查结论：驳回\n"
    )
    user_prompt = f"请分析以下内容：\n{content}"

    client = OpenAI(api_key=api_key, base_url=api_url)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            timeout=200,
            max_tokens=3000,
        )
        return (response.choices[0].message.content or "").strip()
    except APIConnectionError as e:
        raise Exception(f"DeepSeek 连接失败: {e}") from e
    except APIError as e:
        raise Exception(f"DeepSeek API错误: {e.status_code} - {e.message}") from e


def _parse_result(report_md: str) -> tuple:
    """解析机器可读结论与驳回原因；解析失败按预警（人工复核兜底）。

    Returns:
        (result, reason)：reason 仅驳回/预警时有值，供三期报表聚合。
    """
    text = report_md or ""
    matched = re.search(r"审查结论[:：]\s*(通过|预警|驳回)", text)
    if not matched:
        logger.warning("报告中未解析到「审查结论」，按预警处理")
        return "预警", "报告未输出机器可读结论，请人工复核"
    reason = None
    reason_matched = re.search(r"驳回原因[:：]\s*(.+)", text)
    if reason_matched:
        reason = reason_matched.group(1).strip()
    return matched.group(1), reason


def _save_report(invoice_id: int, result: str, content_md: str,
                 reason: str = None) -> int:
    conn = db.get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO audit_reports (invoice_id, result, reason, content_md)"
            " VALUES (?, ?, ?, ?)",
            (invoice_id, result, reason, content_md),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_reports(invoice_no: str = None, result: str = None,
                 limit: int = 100) -> list:
    """审查归档流水：按发票号（模糊）/结论筛选，新→旧，联发票带出关键字段。"""
    conn = db.get_conn()
    try:
        sql = (
            "SELECT r.id, r.invoice_id, r.result, r.reason, r.created_at,"
            " i.invoice_no, i.seller, i.amount, i.category"
            " FROM audit_reports r JOIN invoices i ON i.id = r.invoice_id"
            " WHERE 1=1"
        )
        params: list = []
        if invoice_no:
            sql += " AND i.invoice_no LIKE ?"
            params.append(f"%{invoice_no}%")
        if result:
            sql += " AND r.result = ?"
            params.append(result)
        sql += " ORDER BY r.id DESC LIMIT ?"
        params.append(limit)
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def get_report(report_id: int):
    """报告详情 + 关联发票信息（按单据追溯），无则 None。"""
    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT r.*, i.invoice_no, i.seller, i.amount, i.category,"
            " i.kind, i.invoice_date"
            " FROM audit_reports r JOIN invoices i ON i.id = r.invoice_id"
            " WHERE r.id = ?",
            (report_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
