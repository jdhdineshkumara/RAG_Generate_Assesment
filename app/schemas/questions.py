from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class CitationResponse(BaseModel):
    document_id: str
    filename: str
    page_number: int
    relevance_score: float


class QuestionResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]
