from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import get_ingestion_service
from app.application.services.ingestion_service import IngestionService
from app.domain.exceptions import DomainError, FileTooLargeError
from app.schemas.documents import DocumentResponse

router = APIRouter(prefix="/documents", tags=["documents"])

ERROR_STATUS_CODES = {
    "collection_not_found": 404,
    "unsupported_file": 400,
    "file_too_large": 413,
    "duplicate_document": 409,
    "empty_document": 422,
    "indexing_failed": 503,
}


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
        file: UploadFile = File(...),
        service: IngestionService = Depends(get_ingestion_service),
) -> DocumentResponse:
    safe_name = Path(file.filename or "").name
    if not safe_name:
        raise HTTPException(status_code=400, detail="A filename is required")

    temporary_path: Path | None = None
    try:
        service.temp_upload_directory.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
                mode="wb",
                suffix=".pdf",
                delete=False,
                dir=service.temp_upload_directory,
        ) as temporary:
            temporary_path = Path(temporary.name)
            total_size = 0
            while block := await file.read(1024 * 1024):
                total_size += len(block)
                if total_size > service.max_upload_size_bytes:
                    raise FileTooLargeError(
                        "The uploaded document exceeds the size limit"
                    )
                temporary.write(block)
        document = service.ingest(
            path=temporary_path,
            filename=safe_name,
            content_type=file.content_type or "application/octet-stream",
        )
        return DocumentResponse.model_validate(document, from_attributes=True)
    except DomainError as exc:
        raise HTTPException(
            status_code=ERROR_STATUS_CODES.get(getattr(exc, "code", ""), 400),
            detail={"code": getattr(exc, "code", "domain_error"), "message": str(exc)},
        ) from exc
    finally:
        await file.close()
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()
