import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

from app.domain.entities import Document, DocumentStatus


class JsonDocumentRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def collection_exists(self) -> bool:
        return True

    def save(self, document: Document) -> None:
        with self._lock:
            records = self._read()
            records[document.id] = self._serialize(document)
            self._write(records)

    def find_by_checksum(self, checksum: str) -> Document | None:
        with self._lock:
            for record in self._read().values():
                if record["checksum"] == checksum:
                    return self._deserialize(record)
        return None

    def find_by_filename(self, filename: str) -> Document | None:
        with self._lock:
            for record in self._read().values():
                if record["filename"].lower() == filename.lower():
                    return self._deserialize(record)
        return None

    def delete(self, document_id: str) -> None:
        with self._lock:
            records = self._read()
            records.pop(document_id, None)
            self._write(records)

    def clear(self) -> None:
        with self._lock:
            self._write({})

    def _read(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, records: dict[str, dict[str, Any]]) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(records, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    @staticmethod
    def _serialize(document: Document) -> dict[str, Any]:
        result = asdict(document)
        result["status"] = document.status.value
        result["created_at"] = document.created_at.isoformat()
        result["indexed_at"] = (
            document.indexed_at.isoformat() if document.indexed_at else None
        )
        return result

    @staticmethod
    def _deserialize(record: dict[str, Any]) -> Document:
        record = dict(record)
        record.pop("collection_id", None)
        record["status"] = DocumentStatus(record["status"])
        record["created_at"] = datetime.fromisoformat(record["created_at"])
        record["indexed_at"] = (
            datetime.fromisoformat(record["indexed_at"])
            if record["indexed_at"]
            else None
        )
        return Document(**record)
