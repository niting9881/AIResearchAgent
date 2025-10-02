"""Database utilities for PostgreSQL"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from src.utils.config import settings
from src.utils.logger import app_logger

# Create database engine
engine = create_engine(
    settings.postgres_connection_string,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    
    Usage:
        with get_db_session() as session:
            # Use session here
            pass
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        app_logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()


def init_database():
    """Initialize database tables"""
    try:
        app_logger.info("Initializing database...")
        Base.metadata.create_all(bind=engine)
        app_logger.info("Database initialized successfully")
    except Exception as e:
        app_logger.error(f"Failed to initialize database: {e}")
        raise


def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        app_logger.info("Database connection successful")
        return True
    except Exception as e:
        app_logger.error(f"Database connection failed: {e}")
        return False
