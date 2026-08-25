from collections.abc import Sequence

from app.domain.exceptions import IndexingError


class OpenAIEmbeddingProvider:
    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self._embeddings = None

    def _get_embeddings(self):
        if not self.api_key:
            raise IndexingError("OPENAI_API_KEY is not configured")
        if self._embeddings is None:
            try:
                from langchain_openai import OpenAIEmbeddings

                self._embeddings = OpenAIEmbeddings(
                    api_key=self.api_key,
                    model=self.model,
                )
            except Exception as exc:
                raise IndexingError("OpenAI embeddings are not available") from exc
        return self._embeddings

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        try:
            return self._get_embeddings().embed_documents(list(texts))
        except IndexingError:
            raise
        except Exception as exc:
            raise IndexingError("Unable to generate document embeddings") from exc

    def embed_query(self, text: str) -> list[float]:
        try:
            return self._get_embeddings().embed_query(text)
        except IndexingError:
            raise
        except Exception as exc:
            raise IndexingError("Unable to generate question embedding") from exc
