import pytest

from app.application.services.question_service import QuestionService
from app.domain.entities import RetrievedChunk
from app.domain.exceptions import QueryError


class Embeddings:
    def __init__(self, error=None):
        self.error = error

    def embed_query(self, text):
        if self.error:
            raise self.error
        return [1.0, 0.0]


class Vectors:
    def __init__(self, chunks):
        self.chunks = chunks

    def search(self, embedding, top_k):
        return self.chunks[:top_k]


class Chat:
    def __init__(self, answer="The policy starts on 2026-01-01 and runs for 30 days."):
        self.response = answer

    def answer(self, question, context):
        return self.response


def test_ask_returns_grounded_answer_and_citations():
    chunk = RetrievedChunk(
        id="chunk-1",
        text="The policy starts on 2026-01-01 and runs for 30 days.",
        document_id="doc-1",
        filename="policy.pdf",
        page_number=2,
        relevance_score=0.9,
    )
    service = QuestionService(
        Embeddings(),
        Vectors([chunk]),
        Chat(),
        5,
        0.5,
        "I cannot find the information you have requested",
    )

    result = service.ask("When does the policy start?")

    assert result.answer.startswith("The policy starts")
    assert result.citations[0].filename == "policy.pdf"
    assert result.citations[0].relevance_score == 0.9


def test_ask_returns_exact_fallback_when_no_context_is_relevant():
    service = QuestionService(
        Embeddings(),
        Vectors(
            [
                RetrievedChunk(
                    "chunk-1", "unrelated", "doc-1", "other.pdf", 1, 0.1
                )
            ]
        ),
        Chat(),
        5,
        0.5,
        "I cannot find the information you have requested",
    )

    result = service.ask("What is the escalation process?")

    assert result.answer == "I cannot find the information you have requested"
    assert result.citations == []


def test_ask_normalizes_question_and_limits_retrieval():
    class RecordingEmbeddings(Embeddings):
        def embed_query(self, text):
            self.question = text
            return super().embed_query(text)

    embeddings = RecordingEmbeddings()
    chunks = [
        RetrievedChunk(str(i), f"text-{i}", "doc", "file.pdf", i, 0.9)
        for i in range(3)
    ]
    service = QuestionService(
        embeddings, Vectors(chunks), Chat(), 2, 0.0, "fallback"
    )

    result = service.ask("  what   is this?  ")

    assert embeddings.question == "what is this?"
    assert len(result.citations) == 2


def test_ask_returns_fallback_when_chat_returns_blank():
    service = QuestionService(
        Embeddings(),
        Vectors(
            [RetrievedChunk("1", "text", "doc", "file.pdf", 1, 0.8)]
        ),
        Chat(""),
        5,
        0.0,
        "fallback",
    )

    assert service.ask("question").answer == "fallback"


def test_ask_rejects_blank_question():
    service = QuestionService(Embeddings(), Vectors([]), Chat(), 5, 0.0, "fallback")

    with pytest.raises(ValueError, match="cannot be blank"):
        service.ask(" \n\t ")


def test_ask_translates_embedding_failure():
    service = QuestionService(
        Embeddings(error=RuntimeError("embedding failed")),
        Vectors([]),
        Chat(),
        5,
        0.0,
        "fallback",
    )

    with pytest.raises(RuntimeError):
        service.ask("question")
