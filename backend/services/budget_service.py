"""预算服务：预算文件解析入库 → 余额 / 执行率计算。

期间约定：period 统一为 "YYYY-MM"，未指定时取当前月。
文件支持 .csv / .xlsx / .xls，表头需含：类目、限额（期间由参数或当前月决定）。
"""
import csv
import os
from datetime import datetime

from models import budget


def current_period() -> str:
    return datetime.now().strftime("%Y-%m")


def import_rules(path: str, period: str | None = None) -> dict:
    """解析预算文件逐行入库（同类目覆盖限额），返回导入统计。

    Raises:
        ValueError: 文件类型不支持 / 无有效行
    """
    period = period or current_period()
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        rows = _read_csv(path)
    elif ext in (".xlsx", ".xls"):
        rows = _read_excel(path)
    else:
        raise ValueError("仅支持 xlsx / xls / csv 预算文件")

    count = 0
    for row in rows:
        category = str(_pick(row, "类目", "category", "费用类别") or "").strip()
        limit_raw = _pick(row, "限额", "limit_amount", "limit", "金额")
        if not category or limit_raw in (None, ""):
            continue
        try:
            limit_amount = float(str(limit_raw).replace(",", "").replace("¥", "").replace("￥", ""))
        except ValueError:
            continue  # 跳过非法行，不让单行脏数据中断整批导入
        budget.upsert_rule(category, limit_amount, period)
        count += 1

    if count == 0:
        raise ValueError("预算文件未解析到有效行（表头需含：类目 / 限额）")
    return {"period": period, "count": count}


def list_with_remaining(period: str | None = None) -> list:
    """规则清单 + 剩余额度 + 执行率（%），前端余额一览直接消费。"""
    rules = budget.list_all(period)
    for rule in rules:
        limit = rule["limit_amount"] or 0
        used = rule["used_amount"] or 0
        rule["remaining"] = round(limit - used, 2)
        rule["usage_rate"] = round(used / limit * 100, 1) if limit > 0 else None
    return rules


def _pick(row: dict, *keys):
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


def _read_csv(path: str) -> list:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _read_excel(path: str) -> list:
    try:
        import pandas as pd
    except ImportError:
        raise ValueError("读取 Excel 需要 pandas 环境（或改用 csv 上传）")
    return pd.read_excel(path).to_dict("records")
