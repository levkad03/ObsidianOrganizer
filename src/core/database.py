import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_PATH = os.environ.get("VAULT_DB_PATH", str(Path(__file__).parents[2] / "db.sqlite3"))

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db():
    from .models import Base

    Base.metadata.create_all(bind=engine)
