from functools import lru_cache

from app.application.services.database_service import DatabaseService
from app.application.services.ingestion_service import IngestionService
from app.application.services.question_service import QuestionService
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.loaders.pdf_loader import PdfPlumberDocumentLoader
from app.infrastructure.persistence.chroma_store import ChromaVectorStore
from app.infrastructure.persistence.metadata_store import JsonDocumentRepository
from app.infrastructure.providers.openai_chat import OpenAIChatProvider
from app.infrastructure.providers.openai_embeddings import OpenAIEmbeddingProvider


def _create_vector_store(settings: Settings) -> ChromaVectorStore:
    return ChromaVectorStore(
        settings.chroma_persist_directory,
        settings.chroma_collection_name,
    )


@lru_cache
def get_ingestion_service() -> IngestionService:
    settings = get_settings()
    return IngestionService(
        loader=PdfPlumberDocumentLoader(settings.max_document_pages),
        embeddings=OpenAIEmbeddingProvider(
            settings.openai_api_key, settings.openai_embedding_model
        ),
        vector_store=_create_vector_store(settings),
        documents=JsonDocumentRepository(settings.metadata_file),
        max_upload_size_bytes=settings.max_upload_size_bytes,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        temp_upload_directory=settings.temp_upload_directory,
    )


@lru_cache
def get_question_service() -> QuestionService:
    settings = get_settings()
    return QuestionService(
        embeddings=OpenAIEmbeddingProvider(
            settings.openai_api_key, settings.openai_embedding_model
        ),
        vector_store=_create_vector_store(settings),
        chat=OpenAIChatProvider(
            settings.openai_api_key,
            settings.openai_chat_model,
            settings.answer_not_found_message,
        ),
        top_k=settings.retrieval_top_k,
        score_threshold=settings.retrieval_score_threshold,
        fallback_message=settings.answer_not_found_message,
    )


@lru_cache
def get_database_service() -> DatabaseService:
    settings = get_settings()
    return DatabaseService(
        vector_store=_create_vector_store(settings),
        documents=JsonDocumentRepository(settings.metadata_file),
    )
