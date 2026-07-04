from decimal import Decimal

from pydantic import BaseModel


class CategoryBreakdown(BaseModel):
    category_id: str
    name: str
    color: str
    total: Decimal


class ExpenseGroupBreakdown(BaseModel):
    total: Decimal
    categories: list[CategoryBreakdown]


class DashboardSummaryResponse(BaseModel):
    month_key: str
    card: ExpenseGroupBreakdown
    other: ExpenseGroupBreakdown
    month_total: Decimal
    monthly_net_salary: Decimal | None
    remaining: Decimal | None
    percent_used: Decimal | None
