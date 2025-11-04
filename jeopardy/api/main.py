from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

from jeopardy.db import get_database_url
from jeopardy.db.models import JeopardyQuestion
from jeopardy.ai.oracle import Oracle
from jeopardy.api.models import GetRandomQuestionResponse, VerifyAnswerRequest, VerifyAnswerResponse, VerifyAnswerRequest, VerifyAnswerResponse

load_dotenv()

app = FastAPI()

engine = create_engine(get_database_url(), echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_oracle():
    oracle = Oracle()
    yield oracle

def format_value(value_in_dollars: int | None) -> str:
    """Format integer value to dollar string."""
    if value_in_dollars is None:
        return "None"
    return f"${value_in_dollars}"


@app.get("/question/", response_model=GetRandomQuestionResponse)
def get_random_question(round: str, value: str, db: Session = Depends(get_db)):
    """
    Returns a random question based on the provided Round and Value.

    Example: GET /question/?round=Jeopardy!&value=$200
    """
    try:
        value_int = int(value.replace('$', '').replace(',', '')) if value != "None" else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid value format")

    # Query for a random question matching the criteria
    question = (
        db.query(JeopardyQuestion)
        .filter(JeopardyQuestion.round == round)
        .filter(JeopardyQuestion.value_in_dollars == value_int)
        .order_by(func.random())
        .first()
    )

    if not question:
        raise HTTPException(
            status_code=404,
            detail=f"No question found for round '{round}' and value '{value}'"
        )

    return GetRandomQuestionResponse(
        question_id=question.id,
        round=question.round,
        category=question.category,
        value=format_value(question.value_in_dollars),
        question=question.question
    )

@app.post("/verify-answer/", response_model=VerifyAnswerResponse)
def verify_answer(request: VerifyAnswerRequest, db: Session = Depends(get_db), oracle: Oracle = Depends(get_oracle)):
    question = db.get(JeopardyQuestion, request.question_id)
    if not question:
        raise HTTPException(
            status_code=404,
            detail=f"No question found for ID {request.question_id}"
        )

    response = oracle.determine_correctness(question=question.question, correct_answer=question.answer, given_answer=request.user_answer)

    return VerifyAnswerResponse(is_correct=response.is_correct, ai_response=response.reason)
