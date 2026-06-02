import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bucket_harbour.domain.models import Base

# Agnostic configuration, but defaulting to a local SQLite database for development
METADATA_DB_PATH = os.environ.get("METADATA_DB_PATH", "sqlite:///metadata.db")

engine = create_engine(
    METADATA_DB_PATH, 
    connect_args={"check_same_thread": False} if METADATA_DB_PATH.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
