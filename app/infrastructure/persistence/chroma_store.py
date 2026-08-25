from collections.abc import Sequence
from pathlib import Path

from app.domain.entities import DocumentChunk, RetrievedChunk
from app.domain.exceptions import IndexingError


class ChromaVectorStore:
    def __init__(
        self, persist_directory: Path, collection_name: str = "rag_documents"
    ) -> None:
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import chromadb

                self.persist_directory.mkdir(parents=True, exist_ok=True)
                self._client = chromadb.PersistentClient(
                    path=str(self.persist_directory)
                )
            except Exception as exc:
                raise IndexingError("ChromaDB is not available") from exc
        return self._client

    def ensure_collection(self) -> None:
        self._get_client().get_or_create_collection(name=self.collection_name)

    def clear(self) -> None:
        try:
            client = self._get_client()
            for collection in client.list_collections():
                client.delete_collection(collection.name)
        except Exception as exc:
            raise IndexingError("Unable to clear ChromaDB") from exc

    def add_chunks(
        self,
        chunks: Sequence[DocumentChunk],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise IndexingError("Chunk and embedding counts do not match")
        try:
            collection = self._get_client().get_or_create_collection(
                name=self.collection_name
            )
            collection.add(
                ids=[chunk.id for chunk in chunks],
                documents=[chunk.text for chunk in chunks],
                embeddings=[list(embedding) for embedding in embeddings],
                metadatas=[
                    {
                        "document_id": chunk.document_id,
                        "filename": chunk.filename,
                        "page_number": chunk.page_number,
                    }
                    for chunk in chunks
                ],
            )
        except IndexingError:
            raise
        except Exception as exc:
            raise IndexingError("Unable to persist document vectors") from exc

    def delete_document(self, document_id: str) -> None:
        try:
            for collection in self._get_client().list_collections():
                collection.delete(where={"document_id": document_id})
        except Exception as exc:
            raise IndexingError("Unable to replace the existing document") from exc

    def search(
        self,
        embedding,
        top_k: int,
    ) -> list[RetrievedChunk]:
        try:
            matches: list[RetrievedChunk] = []
            for collection in self._get_client().list_collections():
                count = collection.count()
                if count == 0:
                    continue
                result = collection.query(
                    query_embeddings=[list(embedding)],
                    n_results=min(top_k, count),
                    include=["documents", "metadatas", "distances"],
                )
                documents = result.get("documents", [[]])[0]
                metadatas = result.get("metadatas", [[]])[0]
                distances = result.get("distances", [[]])[0]
                ids = result.get("ids", [[]])[0]
                matches.extend(
                    RetrievedChunk(
                        id=ids[index],
                        text=documents[index],
                        document_id=str(metadatas[index]["document_id"]),
                        filename=str(metadatas[index]["filename"]),
                        page_number=int(metadatas[index]["page_number"]),
                        relevance_score=1.0 / (1.0 + float(distances[index])),
                    )
                    for index in range(len(documents))
                )
            return sorted(
                matches, key=lambda chunk: chunk.relevance_score, reverse=True
            )[:top_k]
        except Exception as exc:
            raise IndexingError("Unable to search document vectors") from exc
