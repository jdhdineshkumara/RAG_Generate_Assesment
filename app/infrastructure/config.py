from functools import lru_cache
from pathlib import Path
import os

from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    app_name: str = "rag-generator"
    api_prefix: str = "/api/v1"
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"
    chroma_persist_directory: Path = Path("data/chroma")
    chroma_collection_name: str = "rag_documents"
    metadata_file: Path = Path("data/documents.json")
    temp_upload_directory: Path = Path("data/uploads")
    max_upload_size_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    max_document_pages: int = Field(default=500, gt=0)
    chunk_size: int = Field(default=1000, gt=0)
    chunk_overlap: int = Field(default=150, ge=0)
    retrieval_top_k: int = Field(default=5, gt=0, le=20)
    retrieval_score_threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    answer_not_found_message: str = (
        "I cannot find the information you have requested"
    )

    def model_post_init(self, __context: object) -> None:
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")


def _env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=_env("APP_NAME", "rag-generator"),
        api_prefix=_env("API_PREFIX", "/api/v1"),
        openai_api_key=_env("OPENAI_API_KEY"),
        openai_embedding_model=_env(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        ),
        openai_chat_model=_env("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        chroma_persist_directory=Path(
            _env("CHROMA_PERSIST_DIRECTORY", "data/chroma") or "data/chroma"
        ),
        chroma_collection_name=_env(
            "CHROMA_COLLECTION_NAME", "rag_documents"
        ) or "rag_documents",
        metadata_file=Path(
            _env("METADATA_FILE", "data/documents.json") or "data/documents.json"
        ),
        temp_upload_directory=Path(
            _env("TEMP_UPLOAD_DIRECTORY", "data/uploads") or "data/uploads"
        ),
        max_upload_size_bytes=int(
            _env("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024))
        ),
        max_document_pages=int(_env("MAX_DOCUMENT_PAGES", "500")),
        chunk_size=int(_env("CHUNK_SIZE", "1000")),
        chunk_overlap=int(_env("CHUNK_OVERLAP", "150")),
        retrieval_top_k=int(_env("RETRIEVAL_TOP_K", "5")),
        retrieval_score_threshold=float(_env("RETRIEVAL_SCORE_THRESHOLD", "0.0")),
    )
