
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Default to SQLite if no URL provided
DEFAULT_SQLITE = f"sqlite:///{os.getenv('DATABASE_PATH', '/app/data/transcriptions.db')}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE)

connect_args = {}
pool_kwargs = {}

if "sqlite" in DATABASE_URL:
    # SQLite doesn't support connection pooling
    connect_args = {"check_same_thread": False}
else:
    # PostgreSQL - use connection pooling
    pool_kwargs = {
        "pool_size": 20,
        "max_overflow": 40,
        "pool_timeout": 60,
        "pool_pre_ping": True  # Verify connections before use
    }

engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args,
    **pool_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
