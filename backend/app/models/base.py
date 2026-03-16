from decimal import Decimal

from sqlalchemy import String, Integer, Date, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ChartOfAccounts(Base):
    __tablename__ = "chart_of_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    account_type: Mapped[str] = mapped_column(String(20))  # asset/liability/equity/cost/income/expense
    parent_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=1)
    balance_direction: Mapped[str] = mapped_column(String(10))  # debit/credit


class BookEntry(Base):
    __tablename__ = "book_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_date: Mapped[str] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    account_code: Mapped[str] = mapped_column(String(20), index=True)
    account_name: Mapped[str] = mapped_column(String(100))
    voucher_no: Mapped[str] = mapped_column(String(50), index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    auxiliary: Mapped[str] = mapped_column(String(200), default="")
    direction: Mapped[str] = mapped_column(String(10))  # debit/credit


class AccountBalance(Base):
    __tablename__ = "account_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_code: Mapped[str] = mapped_column(String(20), index=True)
    account_name: Mapped[str] = mapped_column(String(100))
    account_level: Mapped[int] = mapped_column(Integer, default=1)
    parent_code: Mapped[str] = mapped_column(String(20), default="")
    period: Mapped[str] = mapped_column(String(7), index=True)  # YYYY-MM
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    debit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    closing_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    balance_direction: Mapped[str] = mapped_column(String(10))  # debit/credit
