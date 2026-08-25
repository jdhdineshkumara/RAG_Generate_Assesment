from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_database_service
from app.application.services.database_service import DatabaseService
from app.domain.exceptions import IndexingError

router = APIRouter(prefix="/database", tags=["database"])


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_database(
        service: DatabaseService = Depends(get_database_service),
) -> None:
    try:
        service.clear_database()
    except IndexingError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
