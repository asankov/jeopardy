from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass

class JeopardyQuestion(Base):
    """
    Model representing a Jeopardy question.

    Attributes:
        id: Primary key (auto-generated)
        show_number: Unique identifier for the show
        air_date: The show air date (YYYY-MM-DD)
        round: One of "Jeopardy!", "Double Jeopardy!", "Final Jeopardy!"
        category: The question category (e.g., "HISTORY")
        value_in_dollars: The monetary value of the question as integer (e.g., 200)
        question: The trivia question
        answer: The correct answer
    """
    __tablename__ = 'jeopardy_questions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    show_number = Column(Integer, nullable=False, index=True)
    air_date = Column(Date, nullable=False, index=True)
    round = Column(String(50), nullable=False)
    category = Column(String(255), nullable=False)
    value_in_dollars = Column(Integer)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)

    def __repr__(self):
        return f"<JeopardyQuestion(show={self.show_number}, date={self.air_date}, category='{self.category}', value={self.value})>"


def create_tables(engine):
    """
    Create all tables defined in the models.

    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.create_all(engine)
    print("Tables created successfully!")
