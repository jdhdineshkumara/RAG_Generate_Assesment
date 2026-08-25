from collections.abc import Sequence

from langchain_core.prompts import ChatPromptTemplate

from app.domain.entities import RetrievedChunk
from app.domain.exceptions import QueryError


class OpenAIChatProvider:
    def __init__(self, api_key: str | None, model: str, fallback_message: str) -> None:
        self.api_key = api_key
        self.model = model
        self.fallback_message = fallback_message
        self._chat = None
        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a verification assistant. Answer using only the supplied source text.

Every factual statement must be supported by the source text. Cite supporting sources inline
using the exact source labels provided in the context. You may perform basic logical reasoning,
date arithmetic, arithmetic, and direct common-sense deductions only when they follow from the
source text. Do not use outside knowledge or invent facts.

For questions about whether someone must work on a date, compare the requested date with any
stated last working day or employment date in the source. Answer yes or no directly when the
source supports that comparison, then explain the date-based conclusion with a citation.

If the source text does not contain enough information, return exactly:
{fallback_message}
""",
                ),
                (
                    "human",
                    "Question:\n{question}\n\nSource text:\n{context}",
                ),
            ]
        )

    def _get_chat(self):
        if not self.api_key:
            raise QueryError("OPENAI_API_KEY is not configured")
        if self._chat is None:
            try:
                from langchain_openai import ChatOpenAI

                self._chat = ChatOpenAI(
                    api_key=self.api_key,
                    model=self.model,
                    temperature=0,
                )
            except Exception as exc:
                raise QueryError("OpenAI chat model is not available") from exc
        return self._chat

    def answer(self, question: str, context: Sequence[RetrievedChunk]) -> str:
        context_text = "\n\n".join(
            f"[Source: {chunk.filename}, page {chunk.page_number}]\n{chunk.text}"
            for chunk in context
        )
        try:
            messages = self._prompt.invoke(
                {
                    "question": question,
                    "context": context_text,
                    "fallback_message": self.fallback_message,
                }
            )
            response = self._get_chat().invoke(messages)
            answer = str(response.content).strip()
            return self._normalize_answer(answer)
        except QueryError:
            raise
        except Exception as exc:
            raise QueryError("Unable to generate a grounded answer") from exc

    def _normalize_answer(self, answer: str) -> str:
        if not answer:
            return self.fallback_message
        normalized = answer.rstrip(" .!?").casefold()
        fallback = self.fallback_message.rstrip(" .!?").casefold()
        if normalized == fallback:
            return self.fallback_message
        return answer
