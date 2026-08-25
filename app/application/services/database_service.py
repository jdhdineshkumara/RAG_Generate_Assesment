from app.domain.ports import DocumentRepository, VectorStore


class DatabaseService:
    def __init__(
        self, vector_store: VectorStore, documents: DocumentRepository
    ) -> None:
        self.vector_store = vector_store
        self.documents = documents

    def clear_database(self) -> None:
        self.vector_store.clear()
        self.documents.clear()
