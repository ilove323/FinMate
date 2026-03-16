"""Mock data seeder for 星辰科技有限公司 — 2024-01 to 2024-03."""

import asyncio
import random
from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, init_db
from app.models.base import ChartOfAccounts, BookEntry, AccountBalance
from app.models.reconciliation import BankTransaction, ReconciliationRule
from app.models.tax import TaxMapping, TaxFilingTemplate, TaxValidationRule
from app.models.reports import ReportTemplate
from app.models.cost_alloc import CostCenter, CostPool, AllocationRule
from app.mock.chart_of_accounts import CHART_OF_ACCOUNTS

random.seed(42)  # Reproducible data

PERIODS = ["2024-01", "2024-02", "2024-03"]
BANK_ACCOUNT = "6222021234567890"
ACCT_NAME_MAP = {a["code"]: a["name"] for a in CHART_OF_ACCOUNTS}


async def seed_chart_of_accounts(session: AsyncSession):
    for acct in CHART_OF_ACCOUNTS:
        session.add(ChartOfAccounts(**acct))
    await session.flush()


async def seed_bank_transactions(session: AsyncSession) -> list[BankTransaction]:
    """Generate ~200 bank transactions across 3 months."""
    transactions = []
    serial_counter = 1000

    counterparties_in = [
        ("星河集团", "软件开发服务费"),
        ("云图科技", "技术服务费"),
        ("蓝海数据", "产品销售款"),
        ("星河集团", "项目尾款"),
        ("云图科技", "维护服务费"),
    ]
    counterparties_out = [
        ("天宇科技", "采购服务器设备"),
        ("华芯电子", "采购电子元器件"),
        ("中国电信", "网络服务费"),
        ("物业管理公司", "办公场地租金"),
        ("自来水公司", "水费"),
        ("国家电网", "电费"),
    ]
    misc_out = [
        ("文具供应商", "办公用品采购"),
        ("差旅报销", "员工差旅费报销"),
        ("快递公司", "快递物流费"),
        ("保洁公司", "保洁服务费"),
    ]
    salary_items = [
        ("工资代发", "员工工资"),
        ("社保中心", "社会保险费"),
        ("公积金中心", "住房公积金"),
    ]
    tax_items = [
        ("税务局", "增值税"),
        ("税务局", "企业所得税"),
    ]

    for period_idx, period in enumerate(PERIODS):
        year, month = 2024, period_idx + 1
        days_in_month = 28 if month == 2 else 31

        # Customer receipts: 18-22 per month
        for _ in range(random.randint(18, 22)):
            cp, summary = random.choice(counterparties_in)
            day = random.randint(1, days_in_month)
            amount = Decimal(str(random.randint(15000, 350000)))
            serial_counter += 1
            txn = BankTransaction(
                account_no=BANK_ACCOUNT,
                transaction_date=date(year, month, day),
                amount=amount, counterparty=cp, summary=summary,
                serial_no=f"TXN{year}{month:02d}{serial_counter}",
                currency="CNY", matched_status="unmatched",
            )
            session.add(txn)
            transactions.append(txn)

        # Supplier payments: 12-16 per month
        for _ in range(random.randint(12, 16)):
            cp, summary = random.choice(counterparties_out)
            day = random.randint(1, days_in_month)
            amount = Decimal(str(-random.randint(5000, 120000)))
            serial_counter += 1
            txn = BankTransaction(
                account_no=BANK_ACCOUNT,
                transaction_date=date(year, month, day),
                amount=amount, counterparty=cp, summary=summary,
                serial_no=f"TXN{year}{month:02d}{serial_counter}",
                currency="CNY", matched_status="unmatched",
            )
            session.add(txn)
            transactions.append(txn)

        # Misc expenses: 4-6 per month
        for _ in range(random.randint(4, 6)):
            cp, summary = random.choice(misc_out)
            day = random.randint(1, days_in_month)
            amount = Decimal(str(-random.randint(200, 5000)))
            serial_counter += 1
            txn = BankTransaction(
                account_no=BANK_ACCOUNT,
                transaction_date=date(year, month, day),
                amount=amount, counterparty=cp, summary=summary,
                serial_no=f"TXN{year}{month:02d}{serial_counter}",
                currency="CNY", matched_status="unmatched",
            )
            session.add(txn)
            transactions.append(txn)

        # Salary & benefits: 3 entries per month (around 10th)
        for cp, summary in salary_items:
            amount_val = -180000 if "工资" in summary else (-45000 if "社保" in summary else -25000)
            serial_counter += 1
            txn = BankTransaction(
                account_no=BANK_ACCOUNT,
                transaction_date=date(year, month, min(10, days_in_month)),
                amount=Decimal(str(amount_val)), counterparty=cp, summary=summary,
                serial_no=f"TXN{year}{month:02d}{serial_counter}",
                currency="CNY", matched_status="unmatched",
            )
            session.add(txn)
            transactions.append(txn)

        # Tax payments: around 15th
        for cp, summary in tax_items:
            amount_val = -random.randint(20000, 80000)
            serial_counter += 1
            txn = BankTransaction(
                account_no=BANK_ACCOUNT,
                transaction_date=date(year, month, min(15, days_in_month)),
                amount=Decimal(str(amount_val)), counterparty=cp, summary=summary,
                serial_no=f"TXN{year}{month:02d}{serial_counter}",
                currency="CNY", matched_status="unmatched",
            )
            session.add(txn)
            transactions.append(txn)

        # Bank fees: 3-4 per month (deliberately hard to match)
        for _ in range(random.randint(3, 4)):
            serial_counter += 1
            txn = BankTransaction(
                account_no=BANK_ACCOUNT,
                transaction_date=date(year, month, random.randint(1, days_in_month)),
                amount=Decimal(str(-random.randint(10, 200))),
                counterparty="工商银行", summary="账户管理费/转账手续费",
                serial_no=f"TXN{year}{month:02d}{serial_counter}",
                currency="CNY", matched_status="unmatched",
            )
            session.add(txn)
            transactions.append(txn)

    await session.flush()
    return transactions


async def seed_book_entries(session: AsyncSession) -> list[BookEntry]:
    """Generate ~180+ book entries across 3 months.
    All vouchers are balanced (total debit == total credit).
    """
    entries = []
    voucher_counter = 0

    for period_idx, period in enumerate(PERIODS):
        year, month = 2024, period_idx + 1
        days_in_month = 28 if month == 2 else 31

        # === Revenue entries: VAT-inclusive amount split correctly ===
        # Debit Bank (gross) = Credit Revenue (net) + Credit VAT Output (tax)
        revenue_items = [
            ("星河集团", "5001.01", "软件开发服务费"),
            ("云图科技", "5001.02", "技术服务费"),
            ("蓝海数据", "5001.03", "产品销售款"),
        ]
        for customer, acct_code, summary in revenue_items:
            for _ in range(random.randint(3, 5)):
                voucher_counter += 1
                vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
                day = random.randint(1, days_in_month)
                gross_amt = Decimal(str(random.randint(15000, 350000)))
                vat_amt = (gross_amt * Decimal("0.13") / Decimal("1.13")).quantize(Decimal("0.01"))
                net_amt = gross_amt - vat_amt
                # Debit: bank (gross)
                entries.append(BookEntry(
                    entry_date=date(year, month, day), amount=gross_amt,
                    account_code="1002.01", account_name="银行存款-工商银行",
                    voucher_no=vno, summary=summary, auxiliary=customer, direction="debit",
                ))
                # Credit: revenue (net of VAT)
                entries.append(BookEntry(
                    entry_date=date(year, month, day), amount=net_amt,
                    account_code=acct_code, account_name=ACCT_NAME_MAP.get(acct_code, ""),
                    voucher_no=vno, summary=summary, auxiliary=customer, direction="credit",
                ))
                # Credit: VAT output tax
                entries.append(BookEntry(
                    entry_date=date(year, month, day), amount=vat_amt,
                    account_code="2221.01", account_name="应交税费-应交增值税(销项)",
                    voucher_no=vno, summary=f"销项税额-{summary}", auxiliary="", direction="credit",
                ))

        # === Salary payment: Debit AP-salary / Credit Bank ===
        voucher_counter += 1
        vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
        entries.append(BookEntry(
            entry_date=date(year, month, min(10, days_in_month)), amount=Decimal("180000"),
            account_code="2211", account_name="应付职工薪酬",
            voucher_no=vno, summary="支付本月工资", auxiliary="", direction="debit",
        ))
        entries.append(BookEntry(
            entry_date=date(year, month, min(10, days_in_month)), amount=Decimal("180000"),
            account_code="1002.01", account_name="银行存款-工商银行",
            voucher_no=vno, summary="支付本月工资", auxiliary="", direction="credit",
        ))

        # === Salary accrual: Debit Expense / Credit AP-salary ===
        voucher_counter += 1
        vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
        entries.append(BookEntry(
            entry_date=date(year, month, min(28, days_in_month)), amount=Decimal("180000"),
            account_code="5602", account_name="管理费用",
            voucher_no=vno, summary="计提本月工资", auxiliary="", direction="debit",
        ))
        entries.append(BookEntry(
            entry_date=date(year, month, min(28, days_in_month)), amount=Decimal("180000"),
            account_code="2211", account_name="应付职工薪酬",
            voucher_no=vno, summary="计提本月工资", auxiliary="", direction="credit",
        ))

        # === Rent: Debit Expense / Credit Bank ===
        voucher_counter += 1
        vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
        rent_amt = Decimal("35000")
        entries.append(BookEntry(
            entry_date=date(year, month, 1), amount=rent_amt,
            account_code="5602.01", account_name="管理费用-办公租金",
            voucher_no=vno, summary="本月办公室租金", auxiliary="", direction="debit",
        ))
        entries.append(BookEntry(
            entry_date=date(year, month, 1), amount=rent_amt,
            account_code="1002.01", account_name="银行存款-工商银行",
            voucher_no=vno, summary="支付办公室租金", auxiliary="物业管理公司", direction="credit",
        ))

        # === Utilities: Debit Expense / Credit Bank ===
        voucher_counter += 1
        vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
        util_amt = Decimal(str(random.randint(3000, 6000)))
        entries.append(BookEntry(
            entry_date=date(year, month, min(20, days_in_month)), amount=util_amt,
            account_code="5602.02", account_name="管理费用-水电费",
            voucher_no=vno, summary="本月水电费", auxiliary="", direction="debit",
        ))
        entries.append(BookEntry(
            entry_date=date(year, month, min(20, days_in_month)), amount=util_amt,
            account_code="1002.01", account_name="银行存款-工商银行",
            voucher_no=vno, summary="支付水电费", auxiliary="", direction="credit",
        ))

        # === Supplier payments: Debit AP / Credit Bank (VAT was on purchase invoice) ===
        supplier_items = [("天宇科技", "2202.01"), ("华芯电子", "2202.02")]
        for supplier, acct in supplier_items:
            voucher_counter += 1
            vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
            pay_amt = Decimal(str(random.randint(20000, 100000)))
            entries.append(BookEntry(
                entry_date=date(year, month, random.randint(1, days_in_month)), amount=pay_amt,
                account_code=acct, account_name=f"应付账款-{supplier}",
                voucher_no=vno, summary=f"支付{supplier}货款", auxiliary=supplier, direction="debit",
            ))
            entries.append(BookEntry(
                entry_date=date(year, month, random.randint(1, days_in_month)), amount=pay_amt,
                account_code="1002.01", account_name="银行存款-工商银行",
                voucher_no=vno, summary=f"支付{supplier}货款", auxiliary=supplier, direction="credit",
            ))

        # === Purchase invoice (separate from payment): Debit Cost+VAT / Credit AP ===
        for supplier, acct in supplier_items:
            voucher_counter += 1
            vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
            invoice_amt = Decimal(str(random.randint(20000, 100000)))
            vat_in = (invoice_amt * Decimal("0.13") / Decimal("1.13")).quantize(Decimal("0.01"))
            net_cost = invoice_amt - vat_in
            entries.append(BookEntry(
                entry_date=date(year, month, random.randint(1, days_in_month)), amount=net_cost,
                account_code="5401", account_name="主营业务成本",
                voucher_no=vno, summary=f"采购-{supplier}", auxiliary=supplier, direction="debit",
            ))
            entries.append(BookEntry(
                entry_date=date(year, month, random.randint(1, days_in_month)), amount=vat_in,
                account_code="2221.02", account_name="应交税费-应交增值税(进项)",
                voucher_no=vno, summary=f"进项税额-{supplier}", auxiliary="", direction="debit",
            ))
            entries.append(BookEntry(
                entry_date=date(year, month, random.randint(1, days_in_month)), amount=invoice_amt,
                account_code=acct, account_name=f"应付账款-{supplier}",
                voucher_no=vno, summary=f"采购-{supplier}", auxiliary=supplier, direction="credit",
            ))

        # === Depreciation: Debit Expense / Credit Accumulated Depreciation ===
        voucher_counter += 1
        vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
        dep_amt = Decimal("8000")
        entries.append(BookEntry(
            entry_date=date(year, month, min(28, days_in_month)), amount=dep_amt,
            account_code="5602.03", account_name="管理费用-折旧摊销",
            voucher_no=vno, summary="本月折旧", auxiliary="", direction="debit",
        ))
        entries.append(BookEntry(
            entry_date=date(year, month, min(28, days_in_month)), amount=dep_amt,
            account_code="1602", account_name="累计折旧",
            voucher_no=vno, summary="本月折旧", auxiliary="", direction="credit",
        ))

        # === IT expenses: Debit Expense / Credit Bank ===
        voucher_counter += 1
        vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
        it_amt = Decimal(str(random.randint(10000, 15000)))
        entries.append(BookEntry(
            entry_date=date(year, month, min(25, days_in_month)), amount=it_amt,
            account_code="5602.06", account_name="管理费用-IT运维费",
            voucher_no=vno, summary="IT运维服务费", auxiliary="", direction="debit",
        ))
        entries.append(BookEntry(
            entry_date=date(year, month, min(25, days_in_month)), amount=it_amt,
            account_code="1002.01", account_name="银行存款-工商银行",
            voucher_no=vno, summary="IT运维服务费", auxiliary="", direction="credit",
        ))

        # === Office supplies: Debit Expense / Credit Bank ===
        voucher_counter += 1
        vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
        office_amt = Decimal(str(random.randint(1000, 3000)))
        entries.append(BookEntry(
            entry_date=date(year, month, random.randint(1, days_in_month)), amount=office_amt,
            account_code="5602.04", account_name="管理费用-办公用品",
            voucher_no=vno, summary="办公用品采购", auxiliary="", direction="debit",
        ))
        entries.append(BookEntry(
            entry_date=date(year, month, random.randint(1, days_in_month)), amount=office_amt,
            account_code="1002.01", account_name="银行存款-工商银行",
            voucher_no=vno, summary="办公用品采购", auxiliary="", direction="credit",
        ))

        # === Travel: Debit Expense / Credit Bank ===
        voucher_counter += 1
        vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
        travel_amt = Decimal(str(random.randint(2000, 8000)))
        entries.append(BookEntry(
            entry_date=date(year, month, random.randint(1, days_in_month)), amount=travel_amt,
            account_code="5602.05", account_name="管理费用-差旅费",
            voucher_no=vno, summary="员工差旅费", auxiliary="", direction="debit",
        ))
        entries.append(BookEntry(
            entry_date=date(year, month, random.randint(1, days_in_month)), amount=travel_amt,
            account_code="1002.01", account_name="银行存款-工商银行",
            voucher_no=vno, summary="员工差旅费", auxiliary="", direction="credit",
        ))

    for e in entries:
        session.add(e)
    await session.flush()
    return entries


async def seed_account_balances(session: AsyncSession, book_entries: list[BookEntry]):
    """Derive account balances from BookEntry records per spec §2.5.
    Opening balances for 2024-01 are hardcoded; subsequent months carry forward.
    """
    opening_balances_jan = {
        "1001": Decimal("5000"), "1002": Decimal("2850000"), "1002.01": Decimal("2000000"),
        "1002.02": Decimal("850000"), "1122": Decimal("450000"), "1122.01": Decimal("200000"),
        "1122.02": Decimal("150000"), "1122.03": Decimal("100000"), "1123": Decimal("30000"),
        "1403": Decimal("120000"), "1405": Decimal("85000"),
        "1601": Decimal("560000"), "1602": Decimal("112000"),
        "1701": Decimal("80000"), "1801": Decimal("24000"),
        "2001": Decimal("500000"), "2202": Decimal("280000"),
        "2202.01": Decimal("150000"), "2202.02": Decimal("130000"),
        "2211": Decimal("180000"), "2221": Decimal("95000"),
        "2221.01": Decimal("60000"), "2221.02": Decimal("0"),
        "2221.03": Decimal("35000"),
        "3001": Decimal("2000000"), "3002": Decimal("500000"),
        "3101": Decimal("100000"), "3103": Decimal("0"), "3104": Decimal("437000"),
    }

    acct_map = {a["code"]: a for a in CHART_OF_ACCOUNTS}

    # Aggregate book entries by (account_code, period)
    entry_agg: dict[tuple[str, str], dict] = defaultdict(lambda: {"debit": Decimal("0"), "credit": Decimal("0")})
    for e in book_entries:
        period = str(e.entry_date)[:7]  # YYYY-MM
        key = (e.account_code, period)
        if e.direction == "debit":
            entry_agg[key]["debit"] += e.amount
        else:
            entry_agg[key]["credit"] += e.amount

    # Track closing balances to carry forward
    prev_closing: dict[str, Decimal] = {}

    for period_idx, period in enumerate(PERIODS):
        for acct in CHART_OF_ACCOUNTS:
            code = acct["code"]
            # Opening balance: Jan uses hardcoded, others carry forward
            if period_idx == 0:
                opening = opening_balances_jan.get(code, Decimal("0"))
            else:
                opening = prev_closing.get(code, Decimal("0"))

            agg = entry_agg.get((code, period), {"debit": Decimal("0"), "credit": Decimal("0")})
            debit_amt = agg["debit"]
            credit_amt = agg["credit"]

            if acct["balance_direction"] == "debit":
                closing = opening + debit_amt - credit_amt
            else:
                closing = opening - debit_amt + credit_amt

            prev_closing[code] = closing

            session.add(AccountBalance(
                account_code=code, account_name=acct["name"],
                account_level=acct["level"], parent_code=acct.get("parent_code") or "",
                period=period, opening_balance=opening,
                debit_amount=debit_amt, credit_amount=credit_amt,
                closing_balance=closing, balance_direction=acct["balance_direction"],
            ))
    await session.flush()


async def seed_cost_centers(session: AsyncSession):
    """5 departments for 星辰科技有限公司."""
    centers = [
        {"code": "CC01", "name": "研发部", "center_type": "department", "parent_id": None, "headcount": 35, "area": 400.0, "revenue_ratio": 0.45},
        {"code": "CC02", "name": "销售部", "center_type": "department", "parent_id": None, "headcount": 15, "area": 150.0, "revenue_ratio": 0.30},
        {"code": "CC03", "name": "运营部", "center_type": "department", "parent_id": None, "headcount": 10, "area": 120.0, "revenue_ratio": 0.15},
        {"code": "CC04", "name": "财务部", "center_type": "department", "parent_id": None, "headcount": 5, "area": 60.0, "revenue_ratio": 0.05},
        {"code": "CC05", "name": "行政部", "center_type": "department", "parent_id": None, "headcount": 5, "area": 70.0, "revenue_ratio": 0.05},
    ]
    for c in centers:
        session.add(CostCenter(**c))
    await session.flush()


async def seed_cost_pools(session: AsyncSession):
    """5 cost pools x 3 months."""
    pool_defs = [
        ("办公租金", "rent", "5602.01", [35000, 35000, 35000]),
        ("水电费", "utilities", "5602.02", [4200, 4800, 5100]),
        ("IT运维费", "it", "5602.06", [12000, 13500, 11000]),
        ("管理层薪资", "management", "5602", [60000, 60000, 60000]),
        ("折旧摊销", "other", "5602.03", [8000, 8000, 8000]),
    ]
    for name, cost_type, acct_code, amounts in pool_defs:
        for period_idx, period in enumerate(PERIODS):
            session.add(CostPool(
                name=name, cost_type=cost_type, account_code=acct_code,
                period=period, amount=Decimal(str(amounts[period_idx])),
                is_allocated=False,
            ))
    await session.flush()


async def seed_reconciliation_rules(session: AsyncSession):
    """Preset matching rules."""
    rules = [
        {"name": "精确匹配-金额日期", "match_fields": {"amount": "exact", "date": "exact"}, "tolerance_days": 0, "tolerance_amount": Decimal("0"), "priority": 1},
        {"name": "模糊匹配-金额一致日期容差", "match_fields": {"amount": "exact", "date": "fuzzy", "summary": "similar"}, "tolerance_days": 3, "tolerance_amount": Decimal("0"), "priority": 2},
        {"name": "智能匹配-拆分合并", "match_fields": {"amount": "split", "date": "fuzzy"}, "tolerance_days": 5, "tolerance_amount": Decimal("0.01"), "priority": 3},
    ]
    for r in rules:
        session.add(ReconciliationRule(**r))
    await session.flush()


async def seed_tax_mappings(session: AsyncSession):
    """VAT and CIT mappings."""
    mappings = [
        # VAT 主表
        {"account_code": "5001", "account_name": "主营业务收入", "tax_form_type": "vat_general", "tax_line_no": "1", "tax_line_name": "（一）按适用税率计税销售额", "data_source": "current_credit"},
        {"account_code": "2221.01", "account_name": "应交税费-应交增值税(销项)", "tax_form_type": "vat_general", "tax_line_no": "11", "tax_line_name": "销项税额", "data_source": "current_credit"},
        {"account_code": "2221.02", "account_name": "应交税费-应交增值税(进项)", "tax_form_type": "vat_general", "tax_line_no": "12", "tax_line_name": "进项税额", "data_source": "current_debit"},
        # CIT quarterly
        {"account_code": "5001", "account_name": "主营业务收入", "tax_form_type": "cit_quarterly", "tax_line_no": "1", "tax_line_name": "营业收入", "data_source": "cumulative"},
        {"account_code": "5401", "account_name": "主营业务成本", "tax_form_type": "cit_quarterly", "tax_line_no": "2", "tax_line_name": "营业成本", "data_source": "cumulative"},
        {"account_code": "5801", "account_name": "所得税费用", "tax_form_type": "cit_quarterly", "tax_line_no": "4", "tax_line_name": "实际利润额", "data_source": "cumulative"},
    ]
    for m in mappings:
        session.add(TaxMapping(**m))
    await session.flush()


async def seed_tax_templates(session: AsyncSession):
    """Filing templates."""
    templates = [
        {"form_type": "vat_general", "form_name": "增值税纳税申报表（一般纳税人适用）主表", "period_type": "monthly"},
        {"form_type": "vat_general", "form_name": "增值税纳税申报表附列资料（一）", "period_type": "monthly"},
        {"form_type": "vat_general", "form_name": "增值税纳税申报表附列资料（二）", "period_type": "monthly"},
        {"form_type": "cit_quarterly", "form_name": "企业所得税月（季）度预缴纳税申报表", "period_type": "quarterly"},
    ]
    for t in templates:
        session.add(TaxFilingTemplate(**t))
    await session.flush()


async def seed_tax_validation_rules(session: AsyncSession):
    """Tax validation rules."""
    rules = [
        {"form_type": "vat_general", "rule_name": "销项税额 = 销售额 × 税率", "rule_expression": "line_11 == line_1 * 0.13", "severity": "error"},
        {"form_type": "vat_general", "rule_name": "应纳税额 = 销项税额 - 进项税额", "rule_expression": "line_19 == line_11 - line_12", "severity": "error"},
        {"form_type": "cit_quarterly", "rule_name": "利润总额 = 营业收入 - 营业成本 - 期间费用", "rule_expression": "line_3 == line_1 - line_2", "severity": "warning"},
    ]
    for r in rules:
        session.add(TaxValidationRule(**r))
    await session.flush()


async def seed_report_templates(session: AsyncSession):
    """Report line templates for balance sheet, income statement, cash flow."""
    # Balance Sheet (simplified)
    bs_lines = [
        ("1", "流动资产：", "", 0, False, 1),
        ("2", "  货币资金", "SUM(1001,1002)", 1, False, 2),
        ("3", "  应收账款", "SUM(1122)", 1, False, 3),
        ("4", "  预付款项", "SUM(1123)", 1, False, 4),
        ("5", "  存货", "SUM(1403,1405)", 1, False, 5),
        ("6", "  流动资产合计", "SUM(L2:L5)", 0, True, 6),
        ("7", "非流动资产：", "", 0, False, 7),
        ("8", "  固定资产", "1601-1602", 1, False, 8),
        ("9", "  无形资产", "SUM(1701)", 1, False, 9),
        ("10", "  非流动资产合计", "SUM(L8:L9)", 0, True, 10),
        ("11", "资产总计", "L6+L10", 0, True, 11),
        ("12", "流动负债：", "", 0, False, 12),
        ("13", "  短期借款", "SUM(2001)", 1, False, 13),
        ("14", "  应付账款", "SUM(2202)", 1, False, 14),
        ("15", "  应付职工薪酬", "SUM(2211)", 1, False, 15),
        ("16", "  应交税费", "SUM(2221)", 1, False, 16),
        ("17", "  流动负债合计", "SUM(L13:L16)", 0, True, 17),
        ("18", "负债合计", "L17", 0, True, 18),
        ("19", "所有者权益：", "", 0, False, 19),
        ("20", "  实收资本", "SUM(3001)", 1, False, 20),
        ("21", "  资本公积", "SUM(3002)", 1, False, 21),
        ("22", "  盈余公积", "SUM(3101)", 1, False, 22),
        ("23", "  未分配利润", "SUM(3103,3104)", 1, False, 23),
        ("24", "  所有者权益合计", "SUM(L20:L23)", 0, True, 24),
        ("25", "负债和所有者权益总计", "L18+L24", 0, True, 25),
    ]
    for ln, name, formula, indent, is_total, order in bs_lines:
        session.add(ReportTemplate(
            report_type="balance_sheet", line_no=ln, line_name=name,
            formula=formula, indent_level=indent, is_total=is_total, display_order=order,
        ))

    # Income Statement (simplified)
    is_lines = [
        ("1", "一、营业收入", "SUM(5001,5051)", 0, False, 1),
        ("2", "减：营业成本", "SUM(5401,5402)", 0, False, 2),
        ("3", "    营业税金及附加", "SUM(5403)", 1, False, 3),
        ("4", "    销售费用", "SUM(5601)", 1, False, 4),
        ("5", "    管理费用", "SUM(5602)", 1, False, 5),
        ("6", "    财务费用", "SUM(5603)", 1, False, 6),
        ("7", "二、营业利润", "L1-L2-L3-L4-L5-L6", 0, True, 7),
        ("8", "加：营业外收入", "SUM(5301)", 0, False, 8),
        ("9", "减：营业外支出", "SUM(5711)", 0, False, 9),
        ("10", "三、利润总额", "L7+L8-L9", 0, True, 10),
        ("11", "减：所得税费用", "SUM(5801)", 0, False, 11),
        ("12", "四、净利润", "L10-L11", 0, True, 12),
    ]
    for ln, name, formula, indent, is_total, order in is_lines:
        session.add(ReportTemplate(
            report_type="income", line_no=ln, line_name=name,
            formula=formula, indent_level=indent, is_total=is_total, display_order=order,
        ))

    # Cash Flow (simplified, indirect method adjustments)
    cf_lines = [
        ("1", "一、经营活动产生的现金流量", "", 0, False, 1),
        ("2", "  销售商品收到的现金", "SUM(5001)*1.13", 1, False, 2),
        ("3", "  购买商品支付的现金", "SUM(5401)*1.13", 1, False, 3),
        ("4", "  支付给职工的现金", "SUM(2211_debit)", 1, False, 4),
        ("5", "  支付的各项税费", "SUM(2221_debit)", 1, False, 5),
        ("6", "  经营活动现金流量净额", "L2-L3-L4-L5", 0, True, 6),
        ("7", "二、投资活动产生的现金流量", "", 0, False, 7),
        ("8", "  购建固定资产支付的现金", "SUM(1601_debit)", 1, False, 8),
        ("9", "  投资活动现金流量净额", "-L8", 0, True, 9),
        ("10", "三、筹资活动产生的现金流量", "", 0, False, 10),
        ("11", "  取得借款收到的现金", "SUM(2001_credit)", 1, False, 11),
        ("12", "  偿还借款支付的现金", "SUM(2001_debit)", 1, False, 12),
        ("13", "  筹资活动现金流量净额", "L11-L12", 0, True, 13),
        ("14", "四、现金净增加额", "L6+L9+L13", 0, True, 14),
    ]
    for ln, name, formula, indent, is_total, order in cf_lines:
        session.add(ReportTemplate(
            report_type="cash_flow", line_no=ln, line_name=name,
            formula=formula, indent_level=indent, is_total=is_total, display_order=order,
        ))

    await session.flush()


async def seed_allocation_rules(session: AsyncSession):
    """Preset cost allocation rules."""
    rules = [
        {"name": "办公租金按面积分摊", "cost_pool_id": 0, "allocation_basis": "area", "condition_expr": "cost_type == 'rent'", "priority": 1, "effective_from": date(2024, 1, 1), "effective_to": None},
        {"name": "水电费按面积分摊", "cost_pool_id": 0, "allocation_basis": "area", "condition_expr": "cost_type == 'utilities'", "priority": 2, "effective_from": date(2024, 1, 1), "effective_to": None},
        {"name": "IT运维费按人数分摊", "cost_pool_id": 0, "allocation_basis": "headcount", "condition_expr": "cost_type == 'it'", "priority": 3, "effective_from": date(2024, 1, 1), "effective_to": None},
        {"name": "管理层薪资按收入占比分摊", "cost_pool_id": 0, "allocation_basis": "revenue", "condition_expr": "cost_type == 'management'", "priority": 4, "effective_from": date(2024, 1, 1), "effective_to": None},
        {"name": "折旧摊销按面积分摊", "cost_pool_id": 0, "allocation_basis": "area", "condition_expr": "cost_type == 'other'", "priority": 5, "effective_from": date(2024, 1, 1), "effective_to": None},
    ]
    for r in rules:
        session.add(AllocationRule(**r))
    await session.flush()


async def run_seed():
    """Main seed entry point."""
    await init_db()
    async with async_session() as session:
        async with session.begin():
            await seed_chart_of_accounts(session)
            await seed_bank_transactions(session)
            book_entries = await seed_book_entries(session)
            await seed_account_balances(session, book_entries)
            await seed_cost_centers(session)
            await seed_cost_pools(session)
            await seed_reconciliation_rules(session)
            await seed_tax_mappings(session)
            await seed_tax_templates(session)
            await seed_tax_validation_rules(session)
            await seed_report_templates(session)
            await seed_allocation_rules(session)
        print("Seed completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_seed())
