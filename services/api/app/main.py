from fastapi import Depends, FastAPI

from app.core.security import get_current_user_id
from app.features.categories.router import router as categories_router


def create_app() -> FastAPI:
    app = FastAPI(title="Expense Tracker API")
    app.include_router(categories_router)

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
