from pathlib import Path
from typing import Protocol, Sequence

from app.domain.entities import Document, DocumentChunk, ExtractedPage, RetrievedChunk


class DocumentLoader(Protocol):
    def load(self, path: Path) -> list[ExtractedPage]:
        ...


class EmbeddingProvider(Protocol):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...


class VectorStore(Protocol):
    def clear(self) -> None:
        ...

    def ensure_collection(self) -> None:
        ...

    def add_chunks(
        self,
        chunks: Sequence[DocumentChunk],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        ...

    def delete_document(self, document_id: str) -> None:
        ...

    def search(
        self, embedding: Sequence[float], top_k: int
    ) -> list[RetrievedChunk]:
        ...


class ChatProvider(Protocol):
    def answer(self, question: str, context: Sequence[RetrievedChunk]) -> str:
        ...


class DocumentRepository(Protocol):
    def clear(self) -> None:
        ...

    def collection_exists(self) -> bool:
        ...

    def save(self, document: Document) -> None:
        ...

    def find_by_checksum(self, checksum: str) -> Document | None:
        ...

    def find_by_filename(self, filename: str) -> Document | None:
        ...

    def delete(self, document_id: str) -> None:
        ...
