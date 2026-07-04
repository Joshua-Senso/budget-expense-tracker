from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.security import get_current_user_id
from app.features.budget.router import router as budget_router
from app.features.categories.router import router as categories_router
from app.features.dashboard.router import router as dashboard_router
from app.features.expenses.router import router as expenses_router


def create_app() -> FastAPI:
    app = FastAPI(title="Expense Tracker API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[get_settings().frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(categories_router)
    app.include_router(expenses_router)
    app.include_router(budget_router)
    app.include_router(dashboard_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/me")
    def read_current_user(
        user_id: str = Depends(get_current_user_id),
    ) -> dict[str, str]:
        return {"user_id": user_id}

    return app


app = create_app()
