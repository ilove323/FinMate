from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.response import success
from app.models.base import AccountBalance
from app.models.reconciliation import BankTransaction
from app.models.cost_alloc import CostPool
from app.services import tax_service

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

DEFAULT_PERIOD = "2024-03"


@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    period = DEFAULT_PERIOD

    # Reconciliation status
    total_txns = (await db.execute(
        select(func.count()).select_from(BankTransaction).where(
            func.strftime("%Y-%m", BankTransaction.transaction_date) == period
        )
    )).scalar() or 0
    matched_txns = (await db.execute(
        select(func.count()).select_from(BankTransaction).where(
            and_(
                func.strftime("%Y-%m", BankTransaction.transaction_date) == period,
                BankTransaction.matched_status.in_(["matched", "confirmed"]),
            )
        )
    )).scalar() or 0
    match_rate = round(matched_txns / total_txns * 100, 1) if total_txns else 0

    # Tax estimates
    estimates = await tax_service.get_estimate(db, period)
    vat_estimate = next((e for e in estimates if e.get("tax_type") == "增值税"), {})
    estimated_vat = vat_estimate.get("tax_amount", 0)
    revenue_for_tax = vat_estimate.get("taxable_amount", 0)
    tax_burden_rate = round(estimated_vat / revenue_for_tax * 100, 2) if revenue_for_tax else 0

    # Financial snapshot
    bank_bal = (await db.execute(
        select(AccountBalance.closing_balance).where(
            and_(AccountBalance.account_code == "1002", AccountBalance.period == period)
        )
    )).scalar() or 0
    total_assets_q = await db.execute(
        select(func.sum(AccountBalance.closing_balance)).where(
            and_(AccountBalance.account_code.in_(["1001", "1002", "1122", "1123", "1403", "1405", "1601", "1701"]),
                 AccountBalance.period == period)
        )
    )
    total_assets = total_assets_q.scalar() or 0

    # Net profit = revenue - expenses (from account balances)
    revenue = (await db.execute(
        select(func.sum(AccountBalance.credit_amount)).where(
            and_(AccountBalance.account_code.startswith("5001"), AccountBalance.period == period)
        )
    )).scalar() or 0
    expenses = (await db.execute(
        select(func.sum(AccountBalance.debit_amount)).where(
            and_(AccountBalance.account_code.startswith("5"), AccountBalance.period == period,
                 AccountBalance.account_code >= "5401")
        )
    )).scalar() or 0
    net_profit = float(revenue) - float(expenses)

    # Cost allocation status
    total_pools = (await db.execute(
        select(func.sum(CostPool.amount)).where(CostPool.period == period)
    )).scalar() or 0
    allocated_pools = (await db.execute(
        select(func.sum(CostPool.amount)).where(
            and_(CostPool.period == period, CostPool.is_allocated == True)
        )
    )).scalar() or 0

    return success({
        "period": period,
        "reconciliation": {
            "match_rate": match_rate,
            "unmatched_count": total_txns - matched_txns,
        },
        "tax": {
            "estimated_vat": float(estimated_vat),
            "tax_burden_rate": tax_burden_rate,
        },
        "financial": {
            "total_assets": float(total_assets),
            "cash_balance": float(bank_bal),
            "net_profit": net_profit,
        },
        "cost_allocation": {
            "total_pending": float(total_pools - allocated_pools),
            "progress": round(float(allocated_pools / total_pools * 100), 1) if total_pools else 0,
        },
    })
