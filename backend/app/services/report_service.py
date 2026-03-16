"""Financial report generation service."""

from decimal import Decimal

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import AccountBalance, BookEntry
from app.models.reports import ReportTemplate, ReportData, FinancialIndicator


async def get_report(session: AsyncSession, report_type: str, period: str) -> dict:
    """Get report data — generate if not exists."""
    data_q = select(ReportData).where(
        and_(ReportData.report_type == report_type, ReportData.period == period)
    ).order_by(ReportData.line_no)
    data_rows = (await session.execute(data_q)).scalars().all()

    template_q = select(ReportTemplate).where(
        ReportTemplate.report_type == report_type
    ).order_by(ReportTemplate.display_order)
    templates = (await session.execute(template_q)).scalars().all()

    # Merge template structure with data
    data_map = {d.line_no: d for d in data_rows}
    lines = []
    for t in templates:
        d = data_map.get(t.line_no)
        lines.append({
            "line_no": t.line_no,
            "line_name": t.line_name,
            "indent_level": t.indent_level,
            "is_total": t.is_total,
            "current_amount": float(d.current_amount) if d else 0,
            "previous_amount": float(d.previous_amount) if d else 0,
            "yoy_change": d.yoy_change if d else 0,
        })

    return {"report_type": report_type, "period": period, "lines": lines}


async def generate_reports(session: AsyncSession, period: str) -> dict:
    """Generate all three reports from account balances."""
    results = {}
    for report_type in ["balance_sheet", "income", "cash_flow"]:
        templates = (await session.execute(
            select(ReportTemplate).where(ReportTemplate.report_type == report_type).order_by(ReportTemplate.display_order)
        )).scalars().all()

        # Delete existing report data for this period
        existing = (await session.execute(
            select(ReportData).where(and_(ReportData.report_type == report_type, ReportData.period == period))
        )).scalars().all()
        for item in existing:
            await session.delete(item)

        # Compute line values from account balances
        line_values = {}
        prev_line_values = {}

        # First pass: compute prev period values
        prev_period = _prev_period(period)
        for t in templates:
            pv = await _compute_formula(session, t.formula, prev_period, prev_line_values)
            prev_line_values[t.line_no] = pv

        # Second pass: compute current values and save
        for t in templates:
            value = await _compute_formula(session, t.formula, period, line_values)
            line_values[t.line_no] = value

            prev_value = prev_line_values.get(t.line_no, Decimal("0"))
            yoy = 0.0
            if prev_value != 0:
                yoy = float((value - prev_value) / abs(prev_value) * 100)

            session.add(ReportData(
                report_type=report_type, period=period, line_no=t.line_no,
                current_amount=value, previous_amount=prev_value, yoy_change=yoy,
            ))

        results[report_type] = len(templates)

    await session.flush()

    # Also generate financial indicators
    await _generate_indicators(session, period)

    return {"period": period, "reports_generated": results}


async def drill_down(session: AsyncSession, report_type: str, line_no: str, period: str, level: int) -> dict:
    """Three-level drill-down: L1 report line → L2 sub-accounts → L3 voucher entries."""
    template = (await session.execute(
        select(ReportTemplate).where(
            and_(ReportTemplate.report_type == report_type, ReportTemplate.line_no == line_no)
        )
    )).scalars().first()

    if not template:
        return {"error": "Line not found"}

    if level == 1:
        # Show sub-account balances
        codes = _parse_account_codes(template.formula)
        balances = []
        for code in codes:
            rows = (await session.execute(
                select(AccountBalance).where(
                    and_(AccountBalance.account_code.startswith(code), AccountBalance.period == period)
                )
            )).scalars().all()
            for b in rows:
                balances.append({
                    "account_code": b.account_code, "account_name": b.account_name,
                    "level": b.account_level, "opening_balance": float(b.opening_balance),
                    "debit_amount": float(b.debit_amount), "credit_amount": float(b.credit_amount),
                    "closing_balance": float(b.closing_balance),
                })
        return {"level": 1, "type": "account_balances", "items": balances}

    elif level == 2:
        # Show voucher entries for a specific account
        account_code = line_no  # In level 2, line_no is actually the account_code
        entries = (await session.execute(
            select(BookEntry).where(
                and_(
                    BookEntry.account_code == account_code,
                    func.strftime("%Y-%m", BookEntry.entry_date) == period,
                )
            ).order_by(BookEntry.entry_date)
        )).scalars().all()
        return {
            "level": 2, "type": "voucher_entries",
            "items": [{
                "id": e.id, "entry_date": str(e.entry_date), "voucher_no": e.voucher_no,
                "summary": e.summary, "amount": float(e.amount), "direction": e.direction,
                "auxiliary": e.auxiliary,
            } for e in entries],
        }

    return {"level": level, "items": []}


async def get_indicators(session: AsyncSession, period: str) -> list[dict]:
    rows = (await session.execute(
        select(FinancialIndicator).where(FinancialIndicator.period == period)
    )).scalars().all()
    return [{
        "indicator_name": i.indicator_name, "indicator_value": i.indicator_value,
        "benchmark_value": i.benchmark_value, "health_status": i.health_status,
        "description": i.description,
    } for i in rows]


async def get_trend(session: AsyncSession, report_type: str, line_no: str, periods: list[str]) -> list[dict]:
    rows = (await session.execute(
        select(ReportData).where(
            and_(ReportData.report_type == report_type, ReportData.line_no == line_no,
                 ReportData.period.in_(periods))
        ).order_by(ReportData.period)
    )).scalars().all()
    return [{"period": r.period, "amount": float(r.current_amount)} for r in rows]


async def _compute_formula(session: AsyncSession, formula: str, period: str, line_values: dict) -> Decimal:
    """Simplified formula evaluator."""
    if not formula:
        return Decimal("0")

    # Handle SUM(account_codes)
    if formula.startswith("SUM(") and formula.endswith(")"):
        inner = formula[4:-1]
        # Check if referencing lines (L2:L5) or accounts (1001,1002)
        if inner.startswith("L"):
            # Sum of lines: SUM(L2:L5)
            if ":" in inner:
                start, end = inner.split(":")
                start_no = int(start[1:])
                end_no = int(end[1:])
                return sum(line_values.get(str(i), Decimal("0")) for i in range(start_no, end_no + 1))
            return line_values.get(inner[1:], Decimal("0"))
        else:
            # Sum of account balances
            codes = [c.strip() for c in inner.split(",")]
            total = Decimal("0")
            for code in codes:
                bal = (await session.execute(
                    select(AccountBalance).where(
                        and_(AccountBalance.account_code == code, AccountBalance.period == period, AccountBalance.account_level == 1)
                    )
                )).scalars().first()
                if bal:
                    total += bal.closing_balance
            return total

    # Handle line arithmetic: L1-L2-L3
    if formula.startswith("L") or ("L" in formula and not formula.startswith("1") and not formula.startswith("2")):
        try:
            result = Decimal("0")
            parts = formula.replace("+", " + ").replace("-", " - ").split()
            op = "+"
            for p in parts:
                if p in ("+", "-"):
                    op = p
                elif p.startswith("L"):
                    val = line_values.get(p[1:], Decimal("0"))
                    if op == "+":
                        result += val
                    else:
                        result -= val
            return result
        except Exception:
            return Decimal("0")

    # Handle subtraction: 1601-1602
    if "-" in formula and not formula.startswith("-") and not formula.startswith("L"):
        parts = formula.split("-")
        if len(parts) == 2 and parts[0].strip().lstrip("-").isdigit() or (parts[0].strip() and parts[0].strip()[0].isdigit()):
            b1 = (await session.execute(
                select(AccountBalance).where(
                    and_(AccountBalance.account_code == parts[0].strip(), AccountBalance.period == period)
                )
            )).scalars().first()
            b2 = (await session.execute(
                select(AccountBalance).where(
                    and_(AccountBalance.account_code == parts[1].strip(), AccountBalance.period == period)
                )
            )).scalars().first()
            v1 = b1.closing_balance if b1 else Decimal("0")
            v2 = b2.closing_balance if b2 else Decimal("0")
            return v1 - v2

    return Decimal("0")


async def _generate_indicators(session: AsyncSession, period: str):
    """Generate key financial indicators."""
    # Delete existing
    existing = (await session.execute(
        select(FinancialIndicator).where(FinancialIndicator.period == period)
    )).scalars().all()
    for item in existing:
        await session.delete(item)

    async def _get_balance(code: str) -> Decimal:
        b = (await session.execute(
            select(AccountBalance).where(
                and_(AccountBalance.account_code == code, AccountBalance.period == period)
            )
        )).scalars().first()
        return b.closing_balance if b else Decimal("0")

    # Current ratio
    current_assets = sum([await _get_balance(c) for c in ["1001", "1002", "1122", "1123", "1403", "1405"]])
    current_liabs = sum([await _get_balance(c) for c in ["2001", "2202", "2211", "2221"]])
    cr = float(current_assets / current_liabs) if current_liabs else 0
    session.add(FinancialIndicator(
        period=period, indicator_name="流动比率", indicator_value=round(cr, 2),
        benchmark_value=1.5, health_status="good" if cr >= 1.5 else ("warning" if cr >= 1.0 else "danger"),
        description=f"流动比率为{cr:.2f}，{'高于' if cr >= 1.5 else '低于'}行业均值1.5",
    ))

    # Asset-liability ratio
    total_assets = current_assets + await _get_balance("1601") - await _get_balance("1602") + await _get_balance("1701")
    total_liabs = current_liabs
    alr = float(total_liabs / total_assets * 100) if total_assets else 0
    session.add(FinancialIndicator(
        period=period, indicator_name="资产负债率", indicator_value=round(alr, 1),
        benchmark_value=50.0, health_status="good" if alr <= 60 else ("warning" if alr <= 75 else "danger"),
        description=f"资产负债率为{alr:.1f}%，{'处于安全范围' if alr <= 60 else '偏高'}",
    ))

    # Gross margin (simplified)
    revenue = await _get_balance("5001")
    cost = await _get_balance("5401")
    gm = float((revenue - cost) / revenue * 100) if revenue else 0
    session.add(FinancialIndicator(
        period=period, indicator_name="毛利率", indicator_value=round(abs(gm), 1),
        benchmark_value=35.0, health_status="good" if abs(gm) >= 30 else "warning",
        description=f"毛利率为{abs(gm):.1f}%",
    ))

    await session.flush()


def _parse_account_codes(formula: str) -> list[str]:
    """Extract account codes from formula like SUM(1001,1002)."""
    if formula.startswith("SUM(") and formula.endswith(")"):
        inner = formula[4:-1]
        if not inner.startswith("L"):
            return [c.strip() for c in inner.split(",")]
    if "-" in formula and not formula.startswith("L"):
        return [p.strip() for p in formula.split("-") if p.strip() and not p.strip().startswith("L")]
    return []


def _prev_period(period: str) -> str:
    year, month = int(period[:4]), int(period[5:])
    if month == 1:
        return f"{year - 1}-12"
    return f"{year}-{month - 1:02d}"
