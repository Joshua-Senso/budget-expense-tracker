from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user_id
from app.features.import_export import service
from app.features.import_export.schemas import ImportSummary

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


@router.post("/import/{year}", response_model=ImportSummary)
def import_expenses(
    year: str = Path(pattern=_YEAR_PATTERN),
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> ImportSummary:
    try:
        return service.import_workbook(
            db, user_id, file.file.read(), file.filename or "", int(year)
        )
    except service.WorkbookParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except service.ImportValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors)
