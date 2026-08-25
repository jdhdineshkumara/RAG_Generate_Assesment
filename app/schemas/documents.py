from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    page_count: int
    chunk_count: int
    status: str
    error: str | None = None
    created_at: datetime
    indexed_at: datetime | None = None
