from datetime import date

from typing import Optional
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column


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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    show_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    air_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    round: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    value_in_dollars: Mapped[Optional[int]] = mapped_column(Integer)
    question: Mapped[str] = mapped_column(String, nullable=False)
    answer: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self):
        return f"<JeopardyQuestion(show={self.show_number}, date={self.air_date}, category='{self.category}', value={self.value_in_dollars})>"


def create_tables(engine):
    """
    Create all tables defined in the models.

    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.create_all(engine)
    print("Tables created successfully!")
