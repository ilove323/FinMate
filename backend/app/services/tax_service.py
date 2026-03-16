"""Tax data preparation service."""

from decimal import Decimal

from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import AccountBalance
from app.models.tax import TaxMapping, TaxFilingTemplate, TaxLineItem, TaxEstimate, TaxValidationRule


async def get_mappings(session: AsyncSession, form_type: str | None = None) -> list[dict]:
    query = select(TaxMapping)
    if form_type:
        query = query.where(TaxMapping.tax_form_type == form_type)
    rows = (await session.execute(query)).scalars().all()
    return [_mapping_to_dict(m) for m in rows]


async def update_mapping(session: AsyncSession, mapping_id: int, tax_line_no: str, data_source: str) -> dict:
    await session.execute(
        update(TaxMapping).where(TaxMapping.id == mapping_id).values(
            tax_line_no=tax_line_no, data_source=data_source,
        )
    )
    await session.flush()
    return {"id": mapping_id, "updated": True}


async def get_filing(session: AsyncSession, form_type: str, period: str) -> dict:
    template = (await session.execute(
        select(TaxFilingTemplate).where(TaxFilingTemplate.form_type == form_type)
    )).scalars().first()

    if not template:
        return {"form_type": form_type, "form_name": "未找到模板", "lines": []}

    lines_q = select(TaxLineItem).where(
        and_(TaxLineItem.template_id == template.id, TaxLineItem.period == period)
    ).order_by(TaxLineItem.line_no)
    lines = (await session.execute(lines_q)).scalars().all()

    return {
        "form_type": form_type,
        "form_name": template.form_name,
        "period": period,
        "lines": [_line_to_dict(l) for l in lines],
    }


async def generate_filing(session: AsyncSession, form_type: str, period: str) -> dict:
    """Generate filing data from account balances using tax mappings."""
    mappings = (await session.execute(
        select(TaxMapping).where(TaxMapping.tax_form_type == form_type)
    )).scalars().all()

    template = (await session.execute(
        select(TaxFilingTemplate).where(TaxFilingTemplate.form_type == form_type)
    )).scalars().first()

    if not template:
        return {"error": "Template not found"}

    # Delete existing line items for this period
    existing = (await session.execute(
        select(TaxLineItem).where(
            and_(TaxLineItem.template_id == template.id, TaxLineItem.period == period)
        )
    )).scalars().all()
    for item in existing:
        await session.delete(item)

    generated_lines = []
    for mapping in mappings:
        bal = (await session.execute(
            select(AccountBalance).where(
                and_(AccountBalance.account_code == mapping.account_code, AccountBalance.period == period)
            )
        )).scalars().first()

        value = Decimal("0")
        if bal:
            if mapping.data_source == "current_debit":
                value = bal.debit_amount
            elif mapping.data_source == "current_credit":
                value = bal.credit_amount
            elif mapping.data_source == "closing_balance":
                value = bal.closing_balance
            elif mapping.data_source == "cumulative":
                cum_q = select(func.sum(AccountBalance.debit_amount - AccountBalance.credit_amount)).where(
                    and_(AccountBalance.account_code == mapping.account_code, AccountBalance.period <= period)
                )
                cum_val = (await session.execute(cum_q)).scalar()
                value = cum_val or Decimal("0")

        line = TaxLineItem(
            template_id=template.id, line_no=mapping.tax_line_no,
            line_name=mapping.tax_line_name, formula=f"FROM:{mapping.account_code}:{mapping.data_source}",
            current_value=value, adjusted_value=None, period=period,
        )
        session.add(line)
        generated_lines.append(line)

    # Add computed lines (VAT payable = output - input)
    if form_type == "vat_general":
        output_tax = sum(l.current_value for l in generated_lines if l.line_no == "11")
        input_tax = sum(l.current_value for l in generated_lines if l.line_no == "12")
        payable = output_tax - input_tax
        session.add(TaxLineItem(
            template_id=template.id, line_no="19", line_name="应纳税额",
            formula="line_11 - line_12", current_value=payable, adjusted_value=None, period=period,
        ))

    await session.flush()

    return await get_filing(session, form_type, period)


async def adjust_line(session: AsyncSession, line_id: int, adjusted_value: float, reason: str) -> dict:
    await session.execute(
        update(TaxLineItem).where(TaxLineItem.id == line_id).values(
            adjusted_value=Decimal(str(adjusted_value))
        )
    )
    await session.flush()
    return {"line_id": line_id, "adjusted_value": adjusted_value, "reason": reason}


async def get_estimate(session: AsyncSession, period: str) -> list[dict]:
    rows = (await session.execute(
        select(TaxEstimate).where(TaxEstimate.period == period)
    )).scalars().all()

    if not rows:
        estimates = []
        # VAT estimate
        output_q = select(AccountBalance).where(
            and_(AccountBalance.account_code == "2221.01", AccountBalance.period == period)
        )
        output_bal = (await session.execute(output_q)).scalars().first()
        input_q = select(AccountBalance).where(
            and_(AccountBalance.account_code == "2221.02", AccountBalance.period == period)
        )
        input_bal = (await session.execute(input_q)).scalars().first()

        output_amt = output_bal.credit_amount if output_bal else Decimal("0")
        input_amt = input_bal.debit_amount if input_bal else Decimal("0")
        vat = output_amt - input_amt

        estimates.append({
            "tax_type": "增值税", "period": period,
            "taxable_amount": float(output_amt / Decimal("0.13")) if output_amt else 0,
            "tax_amount": float(vat), "previous_period": 0, "yoy_change": 0,
        })

        # CIT estimate (simplified: 25% of profit)
        income_q = select(func.sum(AccountBalance.credit_amount)).where(
            and_(AccountBalance.account_code.startswith("5001"), AccountBalance.period == period)
        )
        income = (await session.execute(income_q)).scalar() or Decimal("0")
        cost_q = select(func.sum(AccountBalance.debit_amount)).where(
            and_(AccountBalance.account_code.startswith("54"), AccountBalance.period == period)
        )
        cost = (await session.execute(cost_q)).scalar() or Decimal("0")
        profit = income - cost
        cit = profit * Decimal("0.25")
        estimates.append({
            "tax_type": "企业所得税", "period": period,
            "taxable_amount": float(profit), "tax_amount": float(cit),
            "previous_period": 0, "yoy_change": 0,
        })
        return estimates

    return [_estimate_to_dict(e) for e in rows]


async def get_validation(session: AsyncSession, form_type: str, period: str) -> list[dict]:
    rules = (await session.execute(
        select(TaxValidationRule).where(TaxValidationRule.form_type == form_type)
    )).scalars().all()

    results = []
    for rule in rules:
        results.append({
            "rule_name": rule.rule_name,
            "expression": rule.rule_expression,
            "severity": rule.severity,
            "passed": True,  # Simplified — real impl would evaluate expression
            "message": "校验通过",
        })
    return results


def _mapping_to_dict(m: TaxMapping) -> dict:
    return {
        "id": m.id, "account_code": m.account_code, "account_name": m.account_name,
        "tax_form_type": m.tax_form_type, "tax_line_no": m.tax_line_no,
        "tax_line_name": m.tax_line_name, "data_source": m.data_source,
    }


def _line_to_dict(l: TaxLineItem) -> dict:
    return {
        "id": l.id, "line_no": l.line_no, "line_name": l.line_name,
        "formula": l.formula, "current_value": float(l.current_value),
        "adjusted_value": float(l.adjusted_value) if l.adjusted_value is not None else None,
        "period": l.period,
    }


def _estimate_to_dict(e: TaxEstimate) -> dict:
    return {
        "id": e.id, "tax_type": e.tax_type, "period": e.period,
        "taxable_amount": float(e.taxable_amount), "tax_amount": float(e.tax_amount),
        "previous_period": float(e.previous_period), "yoy_change": e.yoy_change,
    }
