"""AI 模拟层：AI_MOCK=1 时以假 OCR / 假 DeepSeek 跑通全链路。

用途：环境缺 paddleocr / DeepSeek key 时演示与测试；查重、入库、预算对照等
业务逻辑仍走真实代码，只有模型输入输出被替换。置 AI_MOCK=0 恢复真实链路。

文件名约定（模拟模式）：文件名中的数字作为发票金额，命中的类目关键词作为
费用类别。例：发票-500-差旅.png → 500 元 / 差旅费；缺省 1300 元 / 办公费。
"""
import os
import re
import uuid
from datetime import datetime

CATEGORY_KEYWORDS = {
    "差旅费": ("差旅", "出行", "机票", "火车", "高铁"),
    "交通费": ("交通", "出租", "打车", "加油", "停车"),
    "住宿费": ("住宿", "酒店", "宾馆"),
    "招待费": ("招待", "餐饮", "宴请", "餐"),
    "办公费": ("办公", "文具", "采购", "设备", "耗材"),
}

DEFAULT_CATEGORY = "办公费"
DEFAULT_AMOUNT = 1300.0


def is_mock_enabled() -> bool:
    return os.getenv("AI_MOCK", "1").strip() == "1"


def guess_category(filename: str) -> str:
    for category, words in CATEGORY_KEYWORDS.items():
        if any(word in filename for word in words):
            return category
    return DEFAULT_CATEGORY


def guess_amount(filename: str) -> float:
    matched = re.search(r"(\d+(?:\.\d+)?)", filename)
    return float(matched.group(1)) if matched else DEFAULT_AMOUNT


def fake_fields(original_name: str) -> dict:
    """模拟 DeepSeek 提取结果，键名与真实提示词（need.txt 约定）保持同构。

    发票号 = 时间戳 + 6 位随机后缀：Windows 时钟精度只有几毫秒，
    连续两次上传时间戳可能相同，必须靠随机段保证唯一。
    """
    now = datetime.now()
    amount = guess_amount(original_name)
    return {
        "发票号码": f"MOCK-{now:%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6].upper()}",
        "开票日期": now.strftime("%Y年%m月%d日"),
        "销售方名称": "模拟供应商有限公司",
        "购买方名称": "示例科技有限公司",
        "发票名称": "增值税电子普通发票（模拟）",
        "价税合计(小写)": f"¥{amount:,.2f}",
        "合计税额": f"¥{amount / 1.01 * 0.01:,.2f}",
        "费用类别": guess_category(original_name),
    }


def fake_report(invoice: dict, budget_lines: list, conclusion: str,
                reason: str = None) -> str:
    """模拟 DeepSeek 审查报告。

    budget_lines 由 audit_service 的真实预算对照逻辑生成——模拟的只是
    模型文案，预算规则、扣减、状态回写全部走真实代码。
    """
    lines = [
        "# AI 审查报告（模拟模式）",
        "",
        "## 一、发票总体情况",
        f"- 发票号码：{invoice['invoice_no']}（用途：{invoice['kind']}）",
        f"- 销售方：{invoice['seller'] or '未识别'}　开票日期：{invoice['invoice_date'] or '未识别'}",
        f"- 金额：{invoice['amount']:.2f} 元　费用类别：{invoice['category'] or '未识别'}",
        "",
        "## 二、预算对照（真实规则执行）",
        *(budget_lines or ["- 未启用预算对照"]),
        "",
        "## 三、异常项检查",
        "- 模拟模式：字段完整性、税率合理性校验默认通过",
        "",
        "## 四、审核结论与建议",
        "本报告由模拟模式生成，仅用于链路演示与测试。",
        "",
        f"审查结论：{conclusion}",
    ]
    if reason:
        lines.append(f"驳回原因：{reason}")
    return "\n".join(lines)
