import os
import sys
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
import logging

# Add the parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Database URL - using SQLite
DATABASE_URL = "sqlite:///./data/concession.db"

# Create the engine
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    connect_args={"check_same_thread": False},  # Needed for SQLite
)


def create_db_and_tables():
    """Create database and tables."""
    # Ensure data directory exists
    os.makedirs("./data", exist_ok=True)

    # Import models to register them with SQLModel
    # This ensures they're included in the metadata
    from free_org.db.models import stand, inventory, menu, transaction

    logging.info("Creating database tables")
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get SQLModel session for dependency injection."""
    with Session(engine) as session:
        yield session


def init_db():
    """Initialize the database with tables and seed data if needed."""
    create_db_and_tables()

    # Import seed data function and run it if needed
    # from free_org.db.seed import seed_initial_data
    # seed_initial_data()
