from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class DocumentStatus(str, Enum):
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    text: str
    document_id: str
    filename: str
    page_number: int


@dataclass
class Document:
    id: str
    filename: str
    content_type: str
    size_bytes: int
    checksum: str
    page_count: int = 0
    chunk_count: int = 0
    status: DocumentStatus = DocumentStatus.INDEXING
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    indexed_at: datetime | None = None


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    text: str
    document_id: str
    filename: str
    page_number: int
    relevance_score: float


@dataclass(frozen=True)
class Citation:
    document_id: str
    filename: str
    page_number: int
    relevance_score: float


@dataclass(frozen=True)
class GroundedAnswer:
    answer: str
    citations: list[Citation]
