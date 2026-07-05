from fastapi import APIRouter, Depends, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user_id
from app.features.import_export import service

router = APIRouter(prefix="/import-export", tags=["import-export"])

_YEAR_PATTERN = r"^[1-9]\d{3}$"


@router.get("/export/{year}")
def export_expenses(
    year: str = Path(pattern=_YEAR_PATTERN),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    year_int = int(year)
    buffer = service.build_export_workbook(db, user_id, year_int)
    filename = service.export_filename(year_int)
    return StreamingResponse(
        buffer,
        media_type=service.EXPORT_MIME_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
