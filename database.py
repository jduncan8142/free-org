import os
from dotenv import load_dotenv
from models import Org, User, LocationType, Location, ItemType, Item
from sqlmodel import create_engine

load_dotenv()


def get_db_url():
    db_type = os.getenv('DB_TYPE', 'sqlite')
    db_name = os.getenv('DB_NAME', 'database')
    db_url = os.getenv('DB_URL', None)

    if db_url is None:
        match db_type:
            case 'sqlite':
                sqlite_file_name = f"{db_name}.db"
                db_url = f"sqlite:///{sqlite_file_name}"
            case 'postgresql':
                postgres_user = os.getenv('DB_POSTGRES_USER', 'user')
                postgres_password = os.getenv('DB_POSTGRES_PASSWORD', 'password')
                postgres_host = os.getenv('DB_POSTGRES_HOST', 'localhost')
                postgres_port = os.getenv('DB_POSTGRES_PORT', '5432')
                postgres_db = os.getenv('DB_POSTGRES_DB', 'database')
                postgres_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
            case _:
                raise ValueError(f"Unsupported DB_TYPE: {db_type}")

    return create_engine(db_url, echo=False)
