"""Airflow DAG for initial paper ingestion (50 papers)"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# Default arguments
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def ingest_arxiv_papers(**context):
    """Ingest papers from arXiv"""
    import sys
    sys.path.insert(0, '/opt/airflow')
    
    from src.ingestion.arxiv_scraper import ArxivScraper
    from src.utils.logger import app_logger
    
    try:
        scraper = ArxivScraper()
        papers = scraper.search_papers(max_results=50)
        
        app_logger.info(f"Successfully scraped {len(papers)} papers from arXiv")
        
        # Push to XCom for next task
        context['task_instance'].xcom_push(key='arxiv_papers', value=papers)
        
        return len(papers)
    except Exception as e:
        app_logger.error(f"Error in arXiv ingestion: {e}")
        raise


def ingest_semantic_scholar_papers(**context):
    """Ingest papers from Semantic Scholar"""
    import sys
    sys.path.insert(0, '/opt/airflow')
    
    from src.ingestion.semantic_scholar import SemanticScholarScraper
    from src.utils.logger import app_logger
    
    try:
        scraper = SemanticScholarScraper()
        papers = scraper.search_papers(max_results=50, min_citations=5)
        
        app_logger.info(f"Successfully scraped {len(papers)} papers from Semantic Scholar")
        
        # Push to XCom for next task
        context['task_instance'].xcom_push(key='ss_papers', value=papers)
        
        return len(papers)
    except Exception as e:
        app_logger.error(f"Error in Semantic Scholar ingestion: {e}")
        raise


def process_and_embed_papers(**context):
    """Process papers and generate embeddings"""
    import sys
    sys.path.insert(0, '/opt/airflow')
    
    from src.processing.chunking import chunk_documents
    from src.processing.embeddings import generate_embeddings
    from src.utils.logger import app_logger
    
    try:
        # Get papers from previous tasks
        ti = context['task_instance']
        arxiv_papers = ti.xcom_pull(key='arxiv_papers', task_ids='ingest_arxiv')
        ss_papers = ti.xcom_pull(key='ss_papers', task_ids='ingest_semantic_scholar')
        
        # Combine papers
        all_papers = (arxiv_papers or []) + (ss_papers or [])
        app_logger.info(f"Processing {len(all_papers)} total papers")
        
        # Chunk documents
        chunks = chunk_documents(all_papers)
        app_logger.info(f"Created {len(chunks)} chunks")
        
        # Generate embeddings
        embeddings = generate_embeddings(chunks)
        app_logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Push to XCom
        context['task_instance'].xcom_push(key='chunks', value=chunks)
        context['task_instance'].xcom_push(key='embeddings', value=embeddings)
        
        return len(chunks)
    except Exception as e:
        app_logger.error(f"Error in processing: {e}")
        raise


def index_to_qdrant(**context):
    """Index embeddings to Qdrant"""
    import sys
    sys.path.insert(0, '/opt/airflow')
    
    from src.vector_db.qdrant_client import QdrantManager
    from src.utils.logger import app_logger
    
    try:
        # Get chunks and embeddings
        ti = context['task_instance']
        chunks = ti.xcom_pull(key='chunks', task_ids='process_and_embed')
        embeddings = ti.xcom_pull(key='embeddings', task_ids='process_and_embed')
        
        # Initialize Qdrant
        qdrant = QdrantManager()
        qdrant.create_collection_if_not_exists()
        
        # Index documents
        qdrant.index_documents(chunks, embeddings)
        
        app_logger.info(f"Successfully indexed {len(chunks)} documents to Qdrant")
        
        return len(chunks)
    except Exception as e:
        app_logger.error(f"Error in Qdrant indexing: {e}")
        raise


def store_metadata(**context):
    """Store paper metadata in PostgreSQL"""
    import sys
    sys.path.insert(0, '/opt/airflow')
    
    from src.utils.database import get_db_session
    from src.utils.logger import app_logger
    
    try:
        # Get papers from previous tasks
        ti = context['task_instance']
        arxiv_papers = ti.xcom_pull(key='arxiv_papers', task_ids='ingest_arxiv')
        ss_papers = ti.xcom_pull(key='ss_papers', task_ids='ingest_semantic_scholar')
        
        all_papers = (arxiv_papers or []) + (ss_papers or [])
        
        # Store in database (implementation depends on your schema)
        with get_db_session() as session:
            # TODO: Implement actual database storage
            app_logger.info(f"Storing {len(all_papers)} papers in database")
        
        return len(all_papers)
    except Exception as e:
        app_logger.error(f"Error storing metadata: {e}")
        raise


# Create DAG
with DAG(
    "initial_paper_ingestion",
    default_args=default_args,
    description="Initial ingestion of 50 LLM research papers",
    schedule_interval=None,  # Manual trigger only
    start_date=datetime(2025, 10, 1),
    catchup=False,
    tags=["ingestion", "initial"],
) as dag:

    # Task 1: Ingest from arXiv
    task_arxiv = PythonOperator(
        task_id="ingest_arxiv",
        python_callable=ingest_arxiv_papers,
        provide_context=True,
    )

    # Task 2: Ingest from Semantic Scholar
    task_semantic_scholar = PythonOperator(
        task_id="ingest_semantic_scholar",
        python_callable=ingest_semantic_scholar_papers,
        provide_context=True,
    )

    # Task 3: Process and embed
    task_process = PythonOperator(
        task_id="process_and_embed",
        python_callable=process_and_embed_papers,
        provide_context=True,
    )

    # Task 4: Index to Qdrant
    task_index = PythonOperator(
        task_id="index_to_qdrant",
        python_callable=index_to_qdrant,
        provide_context=True,
    )

    # Task 5: Store metadata
    task_store = PythonOperator(
        task_id="store_metadata",
        python_callable=store_metadata,
        provide_context=True,
    )

    # Define task dependencies
    [task_arxiv, task_semantic_scholar] >> task_process >> task_index >> task_store
