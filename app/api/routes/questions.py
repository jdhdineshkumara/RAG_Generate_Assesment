from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_question_service
from app.application.services.question_service import QuestionService
from app.domain.exceptions import QueryError
from app.schemas.questions import QuestionRequest, QuestionResponse

router = APIRouter(prefix="/questions", tags=["questions"])

QUERY_ERROR_STATUS = 503


@router.post("", response_model=QuestionResponse)
def ask_question(
        request: QuestionRequest,
        service: QuestionService = Depends(get_question_service),
) -> QuestionResponse:
    try:
        answer = service.ask(request.question)
        return QuestionResponse.model_validate(answer, from_attributes=True)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except QueryError as exc:
        raise HTTPException(
            status_code=QUERY_ERROR_STATUS,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
