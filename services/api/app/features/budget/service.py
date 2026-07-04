from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.features.budget.models import UserMonthlySetting


class MonthlySettingNotFoundError(Exception):
    pass


def _own_setting_query(user_id: str, month_key: str):
    return select(UserMonthlySetting).where(
        UserMonthlySetting.user_id == user_id,
        UserMonthlySetting.household_id.is_(None),
        UserMonthlySetting.month_key == month_key,
    )


def get_monthly_setting(
    db: Session, user_id: str, month_key: str
) -> UserMonthlySetting:
    setting = db.execute(_own_setting_query(user_id, month_key)).scalar_one_or_none()
    if setting is None:
        raise MonthlySettingNotFoundError(month_key)
    return setting


def upsert_monthly_setting(
    db: Session,
    user_id: str,
    month_key: str,
    monthly_net_salary: Decimal,
    base_currency: str | None,
) -> UserMonthlySetting:
    stmt = insert(UserMonthlySetting).values(
        user_id=user_id,
        month_key=month_key,
        monthly_net_salary=monthly_net_salary,
        base_currency=base_currency,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "month_key"],
        index_where=text("household_id IS NULL"),
        set_={
            "monthly_net_salary": monthly_net_salary,
            "base_currency": base_currency,
        },
    )
    db.execute(stmt)
    db.commit()
    return get_monthly_setting(db, user_id, month_key)
