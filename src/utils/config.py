"""Configuration management using Pydantic Settings"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o", description="OpenAI model name")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model"
    )

    # Groq Configuration
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key")
    groq_model: str = Field(
        default="llama-3.1-70b-versatile",
        description="Groq model name"
    )

    # Qdrant Configuration
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_collection_name: str = Field(
        default="llm_research_papers",
        description="Qdrant collection name"
    )
    qdrant_api_key: Optional[str] = Field(default=None, description="Qdrant API key")

    # PostgreSQL Configuration
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(
        default="llm_research_hub",
        description="PostgreSQL database name"
    )
    postgres_user: str = Field(default="postgres", description="PostgreSQL user")
    postgres_password: str = Field(
        default="postgres",
        description="PostgreSQL password"
    )

    # Airflow Configuration
    airflow_home: str = Field(default="/opt/airflow", description="Airflow home")

    # Application Configuration
    app_env: str = Field(default="development", description="Application environment")
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode")

    # Data Ingestion Settings
    initial_paper_count: int = Field(
        default=50,
        description="Initial number of papers to load"
    )
    daily_ingestion_schedule: str = Field(
        default="0 2 * * *",
        description="Cron schedule for daily ingestion"
    )
    arxiv_search_query: str = Field(
        default="cat:cs.CL AND (ti:large language model OR abs:large language model OR ti:LLM OR abs:LLM)",
        description="arXiv search query"
    )
    semantic_scholar_query: str = Field(
        default="large language models",
        description="Semantic Scholar search query"
    )

    # RAG Configuration
    chunk_size: int = Field(default=1000, description="Text chunk size")
    chunk_overlap: int = Field(default=200, description="Text chunk overlap")
    top_k_retrieval: int = Field(default=10, description="Top K results for retrieval")
    similarity_threshold: float = Field(
        default=0.7,
        description="Similarity threshold"
    )
    enable_hybrid_search: bool = Field(
        default=True,
        description="Enable hybrid search"
    )
    enable_reranking: bool = Field(default=True, description="Enable reranking")
    enable_query_rewriting: bool = Field(
        default=True,
        description="Enable query rewriting"
    )

    # Agent Configuration
    agent_max_iterations: int = Field(
        default=5,
        description="Maximum agent iterations"
    )
    agent_timeout: int = Field(default=300, description="Agent timeout in seconds")

    # Monitoring Configuration
    enable_monitoring: bool = Field(default=True, description="Enable monitoring")
    metrics_port: int = Field(default=9090, description="Metrics port")

    # Blog Scraping URLs
    openai_blog_url: str = Field(
        default="https://openai.com/blog",
        description="OpenAI blog URL"
    )
    anthropic_blog_url: str = Field(
        default="https://www.anthropic.com/news",
        description="Anthropic blog URL"
    )

    @property
    def postgres_connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def qdrant_url(self) -> str:
        """Generate Qdrant URL"""
        return f"http://{self.qdrant_host}:{self.qdrant_port}"

    @property
    def project_root(self) -> Path:
        """Get project root directory"""
        return Path(__file__).parent.parent.parent

    @property
    def data_dir(self) -> Path:
        """Get data directory"""
        return self.project_root / "data"

    @property
    def raw_data_dir(self) -> Path:
        """Get raw data directory"""
        return self.data_dir / "raw"

    @property
    def processed_data_dir(self) -> Path:
        """Get processed data directory"""
        return self.data_dir / "processed"


# Global settings instance
settings = Settings()
