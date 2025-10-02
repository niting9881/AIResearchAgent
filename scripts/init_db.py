"""Initialize database schema and create tables"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Boolean
from sqlalchemy.sql import func

from src.utils.database import Base, engine, check_database_connection
from src.utils.logger import app_logger


# Define database models
class Paper(Base):
    """Research paper metadata"""
    __tablename__ = "papers"

    id = Column(String(16), primary_key=True)
    source = Column(String(50), nullable=False)
    source_id = Column(String(100), unique=True, nullable=False)
    title = Column(Text, nullable=False)
    authors = Column(JSON)
    abstract = Column(Text)
    published = Column(DateTime)
    updated = Column(DateTime)
    url = Column(String(500))
    pdf_url = Column(String(500))
    categories = Column(JSON)
    primary_category = Column(String(100))
    journal_ref = Column(String(200))
    doi = Column(String(100))
    citations = Column(Integer, default=0)
    scraped_at = Column(DateTime, default=func.now())
    indexed_at = Column(DateTime)


class Chunk(Base):
    """Document chunks for RAG"""
    __tablename__ = "chunks"

    id = Column(String(32), primary_key=True)
    paper_id = Column(String(16), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer)
    created_at = Column(DateTime, default=func.now())


class UserQuery(Base):
    """User queries for monitoring"""
    __tablename__ = "user_queries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(Text, nullable=False)
    response = Column(Text)
    retrieval_time = Column(Float)
    generation_time = Column(Float)
    total_time = Column(Float)
    num_results = Column(Integer)
    feedback = Column(Integer)  # 1 for positive, -1 for negative, 0 for none
    feedback_comment = Column(Text)
    created_at = Column(DateTime, default=func.now())


class RetrievalMetrics(Base):
    """Retrieval evaluation metrics"""
    __tablename__ = "retrieval_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(Text, nullable=False)
    strategy = Column(String(50))  # 'vector', 'text', 'hybrid'
    hit_rate = Column(Float)
    mrr = Column(Float)
    ndcg = Column(Float)
    precision_at_k = Column(Float)
    recall_at_k = Column(Float)
    latency = Column(Float)
    created_at = Column(DateTime, default=func.now())


class LLMMetrics(Base):
    """LLM response evaluation metrics"""
    __tablename__ = "llm_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(Text, nullable=False)
    response = Column(Text)
    prompt_template = Column(String(100))
    model = Column(String(50))
    relevance_score = Column(Float)
    coherence_score = Column(Float)
    factuality_score = Column(Float)
    overall_score = Column(Float)
    tokens_used = Column(Integer)
    cost = Column(Float)
    latency = Column(Float)
    created_at = Column(DateTime, default=func.now())


class IngestionLog(Base):
    """Log of data ingestion runs"""
    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_type = Column(String(20))  # 'initial' or 'daily'
    papers_found = Column(Integer)
    papers_unique = Column(Integer)
    papers_indexed = Column(Integer)
    chunks_created = Column(Integer)
    status = Column(String(20))  # 'success', 'failure', 'partial'
    error_message = Column(Text)
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    duration = Column(Float)


def init_database():
    """Initialize all database tables"""
    try:
        app_logger.info("Checking database connection...")
        
        if not check_database_connection():
            app_logger.error("Database connection failed. Please check your connection settings.")
            return False
        
        app_logger.info("Creating database tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        app_logger.info("Database tables created successfully!")
        
        # List created tables
        tables = Base.metadata.tables.keys()
        app_logger.info(f"Created tables: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        app_logger.error(f"Failed to initialize database: {e}")
        return False


if __name__ == "__main__":
    app_logger.info("=" * 50)
    app_logger.info("Database Initialization Script")
    app_logger.info("=" * 50)
    
    success = init_database()
    
    if success:
        app_logger.info("✅ Database initialization completed successfully!")
        sys.exit(0)
    else:
        app_logger.error("❌ Database initialization failed!")
        sys.exit(1)
