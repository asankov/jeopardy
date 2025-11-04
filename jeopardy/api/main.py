import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session

from ingester.models import JeopardyQuestion

app = FastAPI()


# Database setup
def get_database_url():
    """Get database URL from environment or use default."""
    db_url = os.getenv('DATABASE_URL')

    if not db_url:
        db_user = os.getenv('POSTGRES_USER', 'postgres')
        db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        db_host = os.getenv('POSTGRES_HOST', 'localhost')
        db_port = os.getenv('POSTGRES_PORT', '5432')
        db_name = os.getenv('POSTGRES_DB', 'jeopardy')
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    return db_url


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
    # Parse value from string to integer
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
