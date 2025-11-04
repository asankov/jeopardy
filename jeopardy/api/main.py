import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session

from jeopardy.db import get_database_url
from jeopardy.db.models import JeopardyQuestion

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


class QuestionResponse(BaseModel):
    question_id: int
    round: str
    category: str
    value: str
    question: str


def format_value(value_in_dollars: int | None) -> str:
    """Format integer value to dollar string."""
    if value_in_dollars is None:
        return "None"
    return f"${value_in_dollars}"


@app.get("/question/", response_model=QuestionResponse)
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

    return QuestionResponse(
        question_id=question.id,
        round=question.round,
        category=question.category,
        value=format_value(question.value_in_dollars),
        question=question.question
    )
