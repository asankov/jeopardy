"""
Database initialization script.

This script creates or drops the database tables for the Jeopardy application.
"""
import os
import csv
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import create_tables, JeopardyQuestion


def get_database_url():
    db_url = os.getenv('DATABASE_URL')

    if not db_url:
        # Default local PostgreSQL configuration
        db_user = os.getenv('POSTGRES_USER', 'postgres')
        db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        db_host = os.getenv('POSTGRES_HOST', 'localhost')
        db_port = os.getenv('POSTGRES_PORT', '5432')
        db_name = os.getenv('POSTGRES_DB', 'jeopardy')

        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    return db_url


def parse_value(value_str):
    """
    Parse the dollar value string to integer.

    Args:
        value_str: String like "$200" or "None"

    Returns:
        Integer value or None
    """
    if not value_str or value_str == "None":
        return None
    # Remove $ and commas, then convert to int
    return int(value_str.replace('$', '').replace(',', ''))


def ingest_csv_data(engine, csv_path):
    """
    Read CSV file and insert data into database.

    Args:
        engine: SQLAlchemy engine instance
        csv_path: Path to the CSV file
    """
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            # CSV has header: Show Number, Air Date, Round, Category, Value, Question, Answer
            csv_reader = csv.reader(csvfile)

            # Skip header row
            next(csv_reader)

            batch = []
            batch_size = 1000
            total_rows = 0

            for row in csv_reader:
                if len(row) != 7:
                    print(f"Skipping malformed row: {row}")
                    continue

                show_number, air_date, round_name, category, value, question, answer = row

                # Parse the date
                try:
                    parsed_date = datetime.strptime(air_date, '%Y-%m-%d').date()
                except ValueError:
                    print(f"Skipping row with invalid date: {air_date}")
                    continue

                # Create question object
                question_obj = JeopardyQuestion(
                    show_number=int(show_number),
                    air_date=parsed_date,
                    round=round_name,
                    category=category,
                    value_in_dollars=parse_value(value),
                    question=question,
                    answer=answer
                )

                batch.append(question_obj)
                total_rows += 1

                # Insert in batches for better performance
                if len(batch) >= batch_size:
                    session.bulk_save_objects(batch)
                    session.commit()
                    print(f"Inserted {total_rows} rows...")
                    batch = []

            # Insert remaining rows
            if batch:
                session.bulk_save_objects(batch)
                session.commit()

            print(f"Successfully inserted {total_rows} total rows!")

    except Exception as e:
        session.rollback()
        print(f"Error during ingestion: {e}")
        raise
    finally:
        session.close()


def main():
    db_url = get_database_url()
    print(f"Connecting to database...")

    engine = create_engine(db_url, echo=False)

    print("Creating tables...")
    create_tables(engine)

    csv_path_str = os.getenv('DATASET_PATH', "dataset.csv")
    csv_path = Path(csv_path_str)

    if not csv_path.exists():
        raise ValueError(f"CSV file {csv_path} does not exist")

    print(f"\nIngesting data from {csv_path}...")
    ingest_csv_data(engine, csv_path)

    print("\nDone!")


if __name__ == '__main__':
    main()
