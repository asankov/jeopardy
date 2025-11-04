"""
Pytest fixtures for API tests.
"""
import pytest
from datetime import date
from unittest.mock import Mock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from jeopardy.db.models import Base, JeopardyQuestion
from jeopardy.ai.oracle import Oracle
from jeopardy.api.main import app, get_db, get_oracle


# Create in-memory SQLite database for testing
@pytest.fixture
def test_db():
    """Create an in-memory test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def sample_questions(test_db: Session):
    """Add sample questions to the test database."""
    questions = [
        JeopardyQuestion(
            id=1,
            show_number=4680,
            air_date=date(2004, 12, 31),
            round="Jeopardy!",
            category="HISTORY",
            value_in_dollars=200,
            question="For the last 8 years of his life, Galileo was under house arrest for espousing this man's theory",
            answer="Copernicus"
        ),
        JeopardyQuestion(
            id=2,
            show_number=4680,
            air_date=date(2004, 12, 31),
            round="Jeopardy!",
            category="SCIENCE",
            value_in_dollars=400,
            question="This planet is the largest in our solar system",
            answer="Jupiter"
        ),
        JeopardyQuestion(
            id=3,
            show_number=4680,
            air_date=date(2004, 12, 31),
            round="Double Jeopardy!",
            category="LITERATURE",
            value_in_dollars=800,
            question="This author wrote 'To Kill a Mockingbird'",
            answer="Harper Lee"
        ),
        # Add more questions to cover all the random selections in agent_play
        JeopardyQuestion(
            id=4,
            show_number=4680,
            air_date=date(2004, 12, 31),
            round="Jeopardy!",
            category="GEOGRAPHY",
            value_in_dollars=600,
            question="This is the capital of France",
            answer="Paris"
        ),
        JeopardyQuestion(
            id=5,
            show_number=4680,
            air_date=date(2004, 12, 31),
            round="Double Jeopardy!",
            category="SPORTS",
            value_in_dollars=1000,
            question="This sport is known as 'the beautiful game'",
            answer="Soccer"
        ),
    ]
    
    for question in questions:
        test_db.add(question)
    test_db.commit()
    
    return questions


@pytest.fixture
def mock_oracle():
    """Create a mock Oracle for testing."""
    oracle = Mock(spec=Oracle)
    
    # Mock answer_question method
    oracle.answer_question = Mock(return_value="Test Answer")
    
    # Mock determine_correctness method
    mock_response = Mock()
    mock_response.is_correct = True
    mock_response.reason = "The answer is correct"
    oracle.determine_correctness = Mock(return_value=mock_response)
    
    return oracle


@pytest.fixture
def client(test_db: Session, mock_oracle: Mock):
    """Create a test client with overridden dependencies."""
    
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    def override_get_oracle():
        yield mock_oracle
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_oracle] = override_get_oracle
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()
