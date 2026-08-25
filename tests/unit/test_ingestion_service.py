from pathlib import Path

import pytest

from app.application.services.ingestion_service import IngestionService
from app.domain.entities import ExtractedPage, DocumentStatus
from app.domain.exceptions import (
    FileTooLargeError,
    IndexingError,
    UnsupportedFileError,
)


class Loader:
    def __init__(self, pages=None, error=None):
        self.pages = pages or [ExtractedPage(page_number=1, text="A" * 12)]
        self.error = error

    def load(self, path):
        if self.error:
            raise self.error
        return self.pages


class Embeddings:
    def __init__(self, error=None):
        self.error = error

    def embed_documents(self, texts):
        if self.error:
            raise self.error
        return [[float(len(text))] for text in texts]


class Vectors:
    def __init__(self):
        self.chunks = []

    def ensure_collection(self):
        pass

    def add_chunks(self, chunks, embeddings):
        self.chunks.extend(chunks)

    def delete_document(self, document_id):
        self.chunks = [
            chunk for chunk in self.chunks if chunk.document_id != document_id
        ]

    def clear(self):
        self.chunks.clear()


class Documents:
    def __init__(self):
        self.records = {}

    def collection_exists(self):
        return True

    def save(self, document):
        self.records[document.id] = document

    def find_by_checksum(self, checksum):
        return next(
            (
                document
                for document in self.records.values()
                if document.checksum == checksum
            ),
            None,
        )

    def find_by_filename(self, filename):
        return next(
            (
                document
                for document in self.records.values()
                if document.filename.lower() == filename.lower()
            ),
            None,
        )

    def delete(self, document_id):
        self.records.pop(document_id, None)

    def clear(self):
        self.records.clear()


@pytest.fixture
def service_factory(tmp_path):
    def create(loader=None, embeddings=None, max_size=1024):
        vectors = Vectors()
        repository = Documents()
        service = IngestionService(
            loader=loader or Loader(),
            embeddings=embeddings or Embeddings(),
            vector_store=vectors,
            documents=repository,
            max_upload_size_bytes=max_size,
            chunk_size=5,
            chunk_overlap=1,
            temp_upload_directory=tmp_path,
        )
        return service, vectors, repository

    return create


def test_ingest_indexes_chunks_and_marks_document_indexed(
    tmp_path: Path, service_factory
):
    path = tmp_path / "guide.pdf"
    path.write_bytes(b"pdf bytes")
    service, vectors, repository = service_factory()

    document = service.ingest(
        path=path,
        filename="guide.pdf",
        content_type="application/pdf",
    )

    assert document.status is DocumentStatus.INDEXED
    assert document.page_count == 1
    assert document.chunk_count == 3
    assert len(vectors.chunks) == 3


def test_ingest_replaces_existing_document(tmp_path: Path):
    path = tmp_path / "guide.pdf"
    path.write_bytes(b"pdf bytes")
    vectors = Vectors()
    repository = Documents()
    service = IngestionService(
        Loader(), Embeddings(), vectors, repository, 1024, 5, 1, tmp_path
    )

    first = service.ingest(path, "guide.pdf", "application/pdf")
    path.write_bytes(b"updated pdf bytes")
    second = service.ingest(path, "guide.pdf", "application/pdf")

    assert second.id != first.id
    assert first.id not in repository.records
    assert repository.records[second.id].status is DocumentStatus.INDEXED
    assert len(vectors.chunks) == second.chunk_count


def test_ingest_rejects_non_pdf(tmp_path: Path, service_factory):
    path = tmp_path / "guide.txt"
    path.write_bytes(b"not a pdf")
    service, _, _ = service_factory()

    with pytest.raises(UnsupportedFileError):
        service.ingest(path, "guide.txt", "text/plain")


def test_ingest_rejects_oversized_file(tmp_path: Path, service_factory):
    path = tmp_path / "guide.pdf"
    path.write_bytes(b"12345")
    service, _, _ = service_factory(max_size=4)

    with pytest.raises(FileTooLargeError):
        service.ingest(path, "guide.pdf", "application/pdf")


def test_ingest_marks_document_failed_when_loader_fails(tmp_path: Path, service_factory):
    path = tmp_path / "guide.pdf"
    path.write_bytes(b"pdf bytes")
    service, _, repository = service_factory(loader=Loader(error=ValueError("bad pdf")))

    with pytest.raises(IndexingError):
        service.ingest(path, "guide.pdf", "application/pdf")

    failed = next(iter(repository.records.values()))
    assert failed.status is DocumentStatus.FAILED
    assert failed.error == "bad pdf"


def test_ingest_marks_document_failed_when_embeddings_fail(
    tmp_path: Path, service_factory
):
    path = tmp_path / "guide.pdf"
    path.write_bytes(b"pdf bytes")
    service, _, repository = service_factory(
        embeddings=Embeddings(error=RuntimeError("provider unavailable"))
    )

    with pytest.raises(IndexingError):
        service.ingest(path, "guide.pdf", "application/pdf")

    assert next(iter(repository.records.values())).status is DocumentStatus.FAILED
