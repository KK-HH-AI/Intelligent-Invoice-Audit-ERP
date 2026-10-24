"""报表统计服务（三期 T20）：审查质量 / 发票概况 / 预算执行 / 总账概览一次聚合。

口径说明：
- 通过率 = 结论"通过"的报告数 / 全部报告数（按报告口径，重审各计一次）；
- 驳回/预警原因 TOP：reason 非空的报告按原因原文聚合（模拟模式下同一
  规则生成的原因文本一致，自然聚成一类）；
- 预算执行率复用 budget_service 的余额/执行率计算。
"""
from models import invoice as invoice_model
from models import voucher as voucher_model
from services import audit_service
from services import budget_service


def get_full_report() -> dict:
    """财务报表页一次性数据源。"""
    return {
        "audit": get_audit_summary(),
        "invoices": get_invoice_summary(),
        "budgets": budget_service.list_with_remaining(),
        "ledger": get_ledger_summary(),
    }


def get_audit_summary() -> dict:
    """审查质量：报告总数 / 结论分布 / 通过率 / 原因 TOP5。"""
    reports = audit_service.list_reports(limit=1000)
    total = len(reports)
    passed = sum(1 for r in reports if r["result"] == "通过")
    warned = sum(1 for r in reports if r["result"] == "预警")
    rejected = sum(1 for r in reports if r["result"] == "驳回")
    return {
        "total_reports": total,
        "passed": passed,
        "warned": warned,
        "rejected": rejected,
        "pass_rate": round(passed / total * 100, 1) if total else None,
        "top_reasons": _top_reasons(reports),
    }


def get_invoice_summary() -> dict:
    """发票概况：各状态数量 + 已通过发票金额合计。"""
    invoices = invoice_model.list_all()
    by_status = {"待审": 0, "已通过": 0, "已驳回": 0, "已入账": 0}
    approved_amount = 0.0
    for inv in invoices:
        status = inv["status"]
        if status in by_status:
            by_status[status] += 1
        if status in ("已通过", "已入账"):
            approved_amount += inv["amount"] or 0
    return {
        "total": len(invoices),
        "by_status": by_status,
        "approved_amount": round(approved_amount, 2),
    }


def get_ledger_summary() -> list:
    """总账六科目：期初 / 本期借 / 本期贷 / 期末。"""
    return [dict(row) for row in voucher_model.ledger_list()]


def _top_reasons(reports: list) -> list:
    """非空原因聚合计数，取前 5。"""
    counter: dict = {}
    for report in reports:
        reason = (report.get("reason") or "").strip()
        if not reason:
            continue
        counter[reason] = counter.get(reason, 0) + 1
    ranked = sorted(counter.items(), key=lambda kv: kv[1], reverse=True)[:5]
    return [{"reason": reason, "count": count} for reason, count in ranked]
