from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from app.domain.entities import Document, DocumentChunk, DocumentStatus
from app.domain.exceptions import (
    FileTooLargeError,
    IndexingError,
    UnsupportedFileError,
)
from app.domain.ports import (
    DocumentLoader,
    DocumentRepository,
    EmbeddingProvider,
    VectorStore,
)


class IngestionService:
    def __init__(
        self,
        loader: DocumentLoader,
        embeddings: EmbeddingProvider,
        vector_store: VectorStore,
        documents: DocumentRepository,
        max_upload_size_bytes: int,
        chunk_size: int,
        chunk_overlap: int,
        temp_upload_directory: Path,
    ) -> None:
        self.loader = loader
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.documents = documents
        self.max_upload_size_bytes = max_upload_size_bytes
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.temp_upload_directory = temp_upload_directory

    def ingest(
        self,
        path: Path,
        filename: str,
        content_type: str,
    ) -> Document:
        if Path(filename).suffix.lower() != ".pdf" or content_type not in (
            "application/pdf",
            "application/octet-stream",
        ):
            raise UnsupportedFileError("Only PDF documents are supported")
        size = path.stat().st_size
        if size > self.max_upload_size_bytes:
            raise FileTooLargeError("The uploaded document exceeds the size limit")

        checksum = self._checksum(path)
        existing_document = self.documents.find_by_checksum(checksum)
        if existing_document is None:
            existing_document = self.documents.find_by_filename(filename)

        document = Document(
            id=f"doc_{uuid4().hex}",
            filename=filename,
            content_type="application/pdf",
            size_bytes=size,
            checksum=checksum,
        )
        self.documents.save(document)
        try:
            pages = self.loader.load(path)
            chunks = self._chunks(document, pages)
            embeddings = self.embeddings.embed_documents([chunk.text for chunk in chunks])
            self.vector_store.ensure_collection()
            self.vector_store.add_chunks(chunks, embeddings)
            if existing_document is not None:
                self.vector_store.delete_document(existing_document.id)
                self.documents.delete(existing_document.id)
            document.page_count = len(pages)
            document.chunk_count = len(chunks)
            document.status = DocumentStatus.INDEXED
            document.indexed_at = datetime.now(timezone.utc)
        except Exception as exc:
            document.status = DocumentStatus.FAILED
            document.error = str(exc)
            self.documents.save(document)
            if isinstance(exc, (IndexingError,)):
                raise
            raise IndexingError("Document indexing failed") from exc
        self.documents.save(document)
        return document

    def _chunks(self, document: Document, pages) -> list[DocumentChunk]:
        result: list[DocumentChunk] = []
        for page in pages:
            text = page.text
            start = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                result.append(
                    DocumentChunk(
                        id=f"{document.id}_{len(result)}",
                        text=text[start:end],
                        document_id=document.id,
                        filename=document.filename,
                        page_number=page.page_number,
                    )
                )
                if end == len(text):
                    break
                start = end - self.chunk_overlap
        return result

    @staticmethod
    def _checksum(path: Path) -> str:
        digest = sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
