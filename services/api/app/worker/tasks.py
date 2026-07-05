from datetime import date

from app.core.db import session_scope
from app.features.recurring.service import generate_recurring_expenses


async def generate_recurring_expenses_task(ctx: dict) -> int:
    """Generate this month's Expense rows for active recurring rules.

    Runs monthly via the arq cron schedule in WorkerSettings. Safe to
    re-run or trigger manually (e.g. `arq app.worker.settings.WorkerSettings
    generate_recurring_expenses_task`) since generation is idempotent per
    (recurring_expense_id, spent_on).
    """
    del ctx
    today = date.today()
    with session_scope() as db:
        return generate_recurring_expenses(db, today.year, today.month)
