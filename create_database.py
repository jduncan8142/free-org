from database import get_db_url
from sqlmodel import SQLModel


if __name__ == "__main__":
    engine = get_db_url()
    SQLModel.metadata.create_all(engine)
