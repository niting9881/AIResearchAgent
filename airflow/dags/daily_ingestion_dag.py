"""Airflow DAG for daily paper ingestion (incremental updates)"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# Default arguments
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": True,
    "email": ["admin@example.com"],
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=10),
}


def check_new_papers(**context):
    """Check for new papers published in the last day"""
    import sys
    sys.path.insert(0, '/opt/airflow')
    
    from src.ingestion.arxiv_scraper import ArxivScraper
    from src.ingestion.semantic_scholar import SemanticScholarScraper
    from src.utils.logger import app_logger
    
    try:
        # Check arXiv for papers from last 1 day
        arxiv_scraper = ArxivScraper()
        arxiv_papers = arxiv_scraper.get_recent_papers(days=1, max_results=100)
        
        app_logger.info(f"Found {len(arxiv_papers)} new papers on arXiv")
        
        # Check Semantic Scholar for papers from last 7 days (they update less frequently)
        ss_scraper = SemanticScholarScraper()
        ss_papers = ss_scraper.get_recent_papers(days=7, max_results=50, min_citations=0)
        
        app_logger.info(f"Found {len(ss_papers)} new papers on Semantic Scholar")
        
        # Combine papers
        all_papers = arxiv_papers + ss_papers
        
        # Push to XCom
        context['task_instance'].xcom_push(key='new_papers', value=all_papers)
        context['task_instance'].xcom_push(key='paper_count', value=len(all_papers))
        
        return len(all_papers)
    except Exception as e:
        app_logger.error(f"Error checking for new papers: {e}")
        raise


def deduplicate_papers(**context):
    """Remove duplicate papers and papers already in database"""
    import sys
    sys.path.insert(0, '/opt/airflow')
    
    from src.utils.database import get_db_session
    from src.utils.logger import app_logger
    
    try:
        # Get new papers
        ti = context['task_instance']
        papers = ti.xcom_pull(key='new_papers', task_ids='check_new_papers')
        
        if not papers:
            app_logger.info("No new papers to process")
            return 0
        
        # TODO: Implement deduplication logic
        # Check against existing papers in database
        unique_papers = papers  # Placeholder
        
        app_logger.info(f"After deduplication: {len(unique_papers)} papers")
        
        # Push to XCom
        context['task_instance'].xcom_push(key='unique_papers', value=unique_papers)
        
        return len(unique_papers)
    except Exception as e:
        app_logger.error(f"Error in deduplication: {e}")
        raise


def process_new_papers(**context):
    """Process new papers and generate embeddings"""
    import sys
    sys.path.insert(0, '/opt/airflow')
    
    from src.processing.chunking import chunk_documents
    from src.processing.embeddings import generate_embeddings
    from src.utils.logger import app_logger
    
    try:
        # Get unique papers
        ti = context['task_instance']
        papers = ti.xcom_pull(key='unique_papers', task_ids='deduplicate_papers')
        
        if not papers:
            app_logger.info("No new papers to process")
            return 0
        
        # Chunk documents
        chunks = chunk_documents(papers)
        app_logger.info(f"Created {len(chunks)} chunks from {len(papers)} papers")
        
        # Generate embeddings
        embeddings = generate_embeddings(chunks)
        app_logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Push to XCom
        context['task_instance'].xcom_push(key='chunks', value=chunks)
        context['task_instance'].xcom_push(key='embeddings', value=embeddings)
        
        return len(chunks)
    except Exception as e:
        app_logger.error(f"Error in processing new papers: {e}")
        raise


def update_vector_db(**context):
    """Update Qdrant vector database with new papers"""
    import sys
    sys.path.insert(0, '/opt/airflow')
    
    from src.vector_db.qdrant_client import QdrantManager
    from src.utils.logger import app_logger
    
    try:
        # Get chunks and embeddings
        ti = context['task_instance']
        chunks = ti.xcom_pull(key='chunks', task_ids='process_new_papers')
        embeddings = ti.xcom_pull(key='embeddings', task_ids='process_new_papers')
        
        if not chunks:
            app_logger.info("No new chunks to index")
            return 0
        
        # Initialize Qdrant
        qdrant = QdrantManager()
        
        # Index new documents
        qdrant.index_documents(chunks, embeddings)
        
        app_logger.info(f"Successfully indexed {len(chunks)} new chunks to Qdrant")
        
        return len(chunks)
    except Exception as e:
        app_logger.error(f"Error updating vector database: {e}")
        raise


def update_metadata_db(**context):
    """Update PostgreSQL with new paper metadata"""
    import sys
    sys.path.insert(0, '/opt/airflow')
    
    from src.utils.database import get_db_session
    from src.utils.logger import app_logger
    
    try:
        # Get unique papers
        ti = context['task_instance']
        papers = ti.xcom_pull(key='unique_papers', task_ids='deduplicate_papers')
        
        if not papers:
            app_logger.info("No new papers to store")
            return 0
        
        # Store in database
        with get_db_session() as session:
            # TODO: Implement actual database storage
            app_logger.info(f"Storing {len(papers)} new papers in database")
        
        return len(papers)
    except Exception as e:
        app_logger.error(f"Error updating metadata database: {e}")
        raise


def send_summary_notification(**context):
    """Send summary notification about daily ingestion"""
    import sys
    sys.path.insert(0, '/opt/airflow')
    
    from src.utils.logger import app_logger
    
    try:
        ti = context['task_instance']
        new_count = ti.xcom_pull(key='paper_count', task_ids='check_new_papers')
        unique_count = ti.xcom_pull(task_ids='deduplicate_papers')
        
        message = f"""
        Daily Ingestion Summary:
        - Papers found: {new_count}
        - Unique papers: {unique_count}
        - Papers indexed: {unique_count}
        - Date: {datetime.now().strftime('%Y-%m-%d')}
        """
        
        app_logger.info(message)
        
        # TODO: Send email/Slack notification
        
        return message
    except Exception as e:
        app_logger.error(f"Error sending notification: {e}")
        raise


# Create DAG
with DAG(
    "daily_paper_ingestion",
    default_args=default_args,
    description="Daily incremental ingestion of new LLM research papers",
    schedule_interval="0 2 * * *",  # Run at 2 AM daily
    start_date=datetime(2025, 10, 1),
    catchup=False,
    tags=["ingestion", "daily"],
) as dag:

    # Task 1: Check for new papers
    task_check = PythonOperator(
        task_id="check_new_papers",
        python_callable=check_new_papers,
        provide_context=True,
    )

    # Task 2: Deduplicate
    task_dedupe = PythonOperator(
        task_id="deduplicate_papers",
        python_callable=deduplicate_papers,
        provide_context=True,
    )

    # Task 3: Process new papers
    task_process = PythonOperator(
        task_id="process_new_papers",
        python_callable=process_new_papers,
        provide_context=True,
    )

    # Task 4: Update vector DB
    task_vector = PythonOperator(
        task_id="update_vector_db",
        python_callable=update_vector_db,
        provide_context=True,
    )

    # Task 5: Update metadata DB
    task_metadata = PythonOperator(
        task_id="update_metadata_db",
        python_callable=update_metadata_db,
        provide_context=True,
    )

    # Task 6: Send notification
    task_notify = PythonOperator(
        task_id="send_summary_notification",
        python_callable=send_summary_notification,
        provide_context=True,
    )

    # Define task dependencies
    task_check >> task_dedupe >> task_process >> [task_vector, task_metadata] >> task_notify
