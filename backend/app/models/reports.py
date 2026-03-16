from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, Float, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReportTemplate(Base):
    __tablename__ = "report_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_type: Mapped[str] = mapped_column(String(20))  # balance_sheet/income/cash_flow
    line_no: Mapped[str] = mapped_column(String(20))
    line_name: Mapped[str] = mapped_column(String(100))
    formula: Mapped[str] = mapped_column(Text, default="")
    indent_level: Mapped[int] = mapped_column(Integer, default=0)
    is_total: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)


class ReportData(Base):
    __tablename__ = "report_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_type: Mapped[str] = mapped_column(String(20), index=True)
    period: Mapped[str] = mapped_column(String(7), index=True)
    line_no: Mapped[str] = mapped_column(String(20))
    current_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    previous_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    yoy_change: Mapped[float] = mapped_column(Float, default=0.0)


class FinancialIndicator(Base):
    __tablename__ = "financial_indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period: Mapped[str] = mapped_column(String(7), index=True)
    indicator_name: Mapped[str] = mapped_column(String(100))
    indicator_value: Mapped[float] = mapped_column(Float, default=0.0)
    benchmark_value: Mapped[float] = mapped_column(Float, default=0.0)
    health_status: Mapped[str] = mapped_column(String(10), default="good")  # good/warning/danger
    description: Mapped[str] = mapped_column(Text, default="")
