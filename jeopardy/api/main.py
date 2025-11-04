from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
import logging

from jeopardy.db import get_database_url
from jeopardy.db.models import JeopardyQuestion
from jeopardy.ai.oracle import NotAbleToDetermineAnswer, Oracle
from jeopardy.api.models import GetRandomQuestionResponse, VerifyAnswerRequest, VerifyAnswerResponse, AgentPlayResponse
from jeopardy.observability import setup_phoenix_tracing

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set up Phoenix tracing on module load
setup_phoenix_tracing()

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

    try:
        response = oracle.determine_correctness(question=question.question, correct_answer=question.answer, given_answer=request.user_answer)
    except NotAbleToDetermineAnswer:
        # TODO: we need better handling here, we should be able to get more details on what went wrong
        logger.warning("Something went wrong with determining the correctness.")

        raise HTTPException(
            status_code=500,
            detail=f"Not able to determine if answer is correct or not"
        )

    return VerifyAnswerResponse(is_correct=response.is_correct, ai_response=response.reason)

@app.post("/agent-play/", response_model=AgentPlayResponse)
def agent_play(db: Session = Depends(get_db), oracle: Oracle = Depends(get_oracle)):
    """
    AI agent that selects a random question and attempts to answer it.

    This endpoint:
    1. Calls get_random_question to fetch a question
    2. Uses the Oracle to generate an answer
    3. Calls verify_answer to check if the answer is correct
    """
    import random
    # some random values i saw in the database,
    # this can be improved so that it's not hardcoded by:
        # 1. making rounds an enum
        # 2. existing a SELECT DISTINCT(values_in_dollars) query in the DB
    # this will also be a good improvement if we implement a UI
    # since that way, the UI will know what values exactly it needs to pass
    rounds = ["Jeopardy!", "Double Jeopardy!"]
    values = ["$200", "$400", "$600", "$800", "$1000"]

    selected_round = random.choice(rounds)
    selected_value = random.choice(values)

    question_response = get_random_question(round=selected_round, value=selected_value, db=db)

    try:
        ai_answer = oracle.answer_question(
            question=question_response.question,
            category=question_response.category
        )
    except Exception as e:
        logger.error(f"Failed to generate answer: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate answer"
        )

    verify_request = VerifyAnswerRequest(
        question_id=question_response.question_id,
        user_answer=ai_answer
    )
    verification_response = verify_answer(request=verify_request, db=db, oracle=oracle)

    return AgentPlayResponse(
        agent_name="AI-Bot",
        question=question_response.question,
        ai_answer=ai_answer,
        is_correct=verification_response.is_correct,
    )
