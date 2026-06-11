
from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import DATABASE_URL

# pool_pre_ping: Neon closes idle connections; without this a stale connection
# hangs/errors on the next request. pool_recycle keeps connections fresh.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Session:

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
