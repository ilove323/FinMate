from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TaxMapping(Base):
    __tablename__ = "tax_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_code: Mapped[str] = mapped_column(String(20), index=True)
    account_name: Mapped[str] = mapped_column(String(100))
    tax_form_type: Mapped[str] = mapped_column(String(30))  # vat_general/cit_quarterly
    tax_line_no: Mapped[str] = mapped_column(String(20))
    tax_line_name: Mapped[str] = mapped_column(String(200))
    data_source: Mapped[str] = mapped_column(String(50))  # current_debit/current_credit/closing_balance/cumulative


class TaxFilingTemplate(Base):
    __tablename__ = "tax_filing_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    form_type: Mapped[str] = mapped_column(String(30))  # vat_general/cit_quarterly
    form_name: Mapped[str] = mapped_column(String(100))
    period_type: Mapped[str] = mapped_column(String(10))  # monthly/quarterly


class TaxLineItem(Base):
    __tablename__ = "tax_line_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(Integer, index=True)
    line_no: Mapped[str] = mapped_column(String(20))
    line_name: Mapped[str] = mapped_column(String(200))
    formula: Mapped[str] = mapped_column(Text, default="")
    current_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    adjusted_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    period: Mapped[str] = mapped_column(String(7), index=True)  # YYYY-MM


class TaxEstimate(Base):
    __tablename__ = "tax_estimates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tax_type: Mapped[str] = mapped_column(String(30))
    period: Mapped[str] = mapped_column(String(7), index=True)
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    previous_period: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    yoy_change: Mapped[float] = mapped_column(Float, default=0.0)


class TaxValidationRule(Base):
    __tablename__ = "tax_validation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    form_type: Mapped[str] = mapped_column(String(30))
    rule_name: Mapped[str] = mapped_column(String(200))
    rule_expression: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(10))  # error/warning
