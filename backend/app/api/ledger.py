from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.response import success
from app.models.base import ChartOfAccounts, BookEntry, AccountBalance

router = APIRouter(prefix="/api/v1/ledger", tags=["ledger"])


@router.get("/accounts")
async def get_accounts(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(ChartOfAccounts).order_by(ChartOfAccounts.code)
    )).scalars().all()
    return success([{
        "code": r.code, "name": r.name,
        "account_type": r.account_type, "direction": r.balance_direction,
        "level": r.level, "parent_code": r.parent_code,
    } for r in rows])


@router.get("/balances")
async def get_balances(period: str = Query(...), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(AccountBalance).where(AccountBalance.period == period)
        .order_by(AccountBalance.account_code)
    )).scalars().all()
    return success([{
        "account_code": r.account_code, "account_name": r.account_name,
        "period": r.period,
        "opening_balance": float(r.opening_balance),
        "debit_amount": float(r.debit_amount),
        "credit_amount": float(r.credit_amount),
        "closing_balance": float(r.closing_balance),
        "direction": r.balance_direction,
    } for r in rows])


@router.get("/entries")
async def get_entries(
    period: str = Query(...),
    account_code: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    q = select(BookEntry).where(
        func.strftime("%Y-%m", BookEntry.entry_date) == period
    )
    if account_code:
        q = q.where(BookEntry.account_code.startswith(account_code))
    q = q.order_by(BookEntry.voucher_no, BookEntry.id)
    rows = (await db.execute(q)).scalars().all()
    return success([{
        "id": r.id, "voucher_no": r.voucher_no,
        "entry_date": str(r.entry_date),
        "account_code": r.account_code, "account_name": r.account_name,
        "direction": r.balance_direction,
        "debit_amount": float(r.amount) if r.direction == "debit" else 0,
        "credit_amount": float(r.amount) if r.direction == "credit" else 0,
        "summary": r.summary, "auxiliary": r.auxiliary,
    } for r in rows])
