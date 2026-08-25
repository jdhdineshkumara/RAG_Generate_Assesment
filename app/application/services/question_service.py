from collections.abc import Sequence

from app.domain.entities import Citation, GroundedAnswer, RetrievedChunk
from app.domain.exceptions import IndexingError, QueryError
from app.domain.ports import ChatProvider, EmbeddingProvider, VectorStore


class QuestionService:
    def __init__(
        self,
        embeddings: EmbeddingProvider,
        vector_store: VectorStore,
        chat: ChatProvider,
        top_k: int,
        score_threshold: float,
        fallback_message: str,
    ) -> None:
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.chat = chat
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.fallback_message = fallback_message

    def ask(self, question: str) -> GroundedAnswer:
        normalized_question = " ".join(question.split())
        if not normalized_question:
            raise ValueError("Question cannot be blank")

        retrieved_chunks = self._retrieve(normalized_question)
        relevant_chunks = self._filter_relevant(retrieved_chunks)
        if not relevant_chunks:
            return GroundedAnswer(self.fallback_message, [])

        answer = self.chat.answer(normalized_question, relevant_chunks).strip()
        citations = self._citations(relevant_chunks)
        return GroundedAnswer(answer or self.fallback_message, citations)

    def _retrieve(self, question: str) -> list[RetrievedChunk]:
        try:
            embedding = self.embeddings.embed_query(question)
            return self.vector_store.search(embedding, self.top_k)
        except (IndexingError, QueryError) as exc:
            raise QueryError(str(exc)) from exc

    def _filter_relevant(
        self, retrieved: Sequence[RetrievedChunk]
    ) -> list[RetrievedChunk]:
        return [
            chunk
            for chunk in retrieved
            if chunk.relevance_score >= self.score_threshold
        ]

    @staticmethod
    def _citations(retrieved: Sequence[RetrievedChunk]) -> list[Citation]:
        return [
            Citation(
                chunk.document_id,
                chunk.filename,
                chunk.page_number,
                round(chunk.relevance_score, 4),
            )
            for chunk in retrieved
        ]
