from arq.cron import cron

from app.core.redis import get_arq_redis_settings
from app.worker.tasks import generate_recurring_expenses_task


class WorkerSettings:
    redis_settings = get_arq_redis_settings()
    # Runs on the 1st of every month; idempotent, so a missed/re-run tick is safe.
    cron_jobs = [
        cron(generate_recurring_expenses_task, day=1, hour=0, minute=5),
    ]
