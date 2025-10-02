# Phase 1 Setup Guide - Data Ingestion Pipeline

This guide will help you set up and run the initial data ingestion pipeline for the LLM Research Intelligence Hub.

## 🎯 Phase 1 Objectives

- ✅ Set up project structure and dependencies
- ✅ Configure environment variables
- ✅ Initialize databases (PostgreSQL, Qdrant)
- ✅ Implement data ingestion from arXiv and Semantic Scholar
- ✅ Set up Airflow for orchestration
- ✅ Ingest initial 50 papers
- ✅ Set up CI/CD pipeline

---

## 📋 Prerequisites

Before starting, ensure you have:

1. **Python 3.11+** installed
2. **Docker Desktop** installed and running
3. **Git** installed
4. **OpenAI API Key** (required)
5. **Text Editor/IDE** (VS Code recommended)

---

## 🚀 Step-by-Step Setup

### Step 1: Environment Setup

```powershell
# Navigate to project directory
cd C:\Users\nitin\AIResearchAgent

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```powershell
# Copy example environment file
Copy-Item .env.example .env

# Edit .env file and add your API keys
notepad .env
```

**Required Variables:**
```env
# MUST CONFIGURE:
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# Optional (can keep defaults):
QDRANT_HOST=localhost
QDRANT_PORT=6333
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

### Step 3: Start Docker Services

```powershell
# Start all services (PostgreSQL, Qdrant, Airflow, Grafana)
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
Start-Sleep -Seconds 60

# Check service status
docker-compose ps
```

**Expected Output:**
```
NAME                           STATUS              PORTS
llm_research_postgres          Up (healthy)        0.0.0.0:5432->5432/tcp
llm_research_qdrant            Up (healthy)        0.0.0.0:6333->6333/tcp
llm_research_airflow_webserver Up (healthy)        0.0.0.0:8080->8080/tcp
llm_research_airflow_scheduler Up                  -
llm_research_streamlit         Up                  0.0.0.0:8501->8501/tcp
llm_research_grafana           Up                  0.0.0.0:3000->3000/tcp
```

### Step 4: Initialize Database

```powershell
# Run database initialization script
python scripts/init_db.py
```

**Expected Output:**
```
==================================================
Database Initialization Script
==================================================
2025-10-01 10:00:00 | INFO | Checking database connection...
2025-10-01 10:00:01 | INFO | Database connection successful
2025-10-01 10:00:01 | INFO | Creating database tables...
2025-10-01 10:00:02 | INFO | Created tables: papers, chunks, user_queries, retrieval_metrics, llm_metrics, ingestion_logs
✅ Database initialization completed successfully!
```

### Step 5: Verify Services

#### Verify Qdrant
```powershell
# Test Qdrant connection
curl http://localhost:6333/health
```
Expected: `{"status":"ok"}`

#### Verify PostgreSQL
```powershell
# Test PostgreSQL connection
docker exec llm_research_postgres psql -U postgres -c "SELECT version();"
```

#### Verify Airflow
Open browser: http://localhost:8080
- Username: `admin`
- Password: `admin`

### Step 6: Test Data Ingestion (Manual)

Before running the full Airflow pipeline, let's test the scrapers:

```powershell
# Test arXiv scraper
python -c "from src.ingestion.arxiv_scraper import ArxivScraper; scraper = ArxivScraper(); papers = scraper.search_papers(max_results=5); print(f'Found {len(papers)} papers'); print(f'First paper: {papers[0][\"title\"]}')"

# Test Semantic Scholar scraper
python -c "from src.ingestion.semantic_scholar import SemanticScholarScraper; scraper = SemanticScholarScraper(); papers = scraper.search_papers(max_results=5); print(f'Found {len(papers)} papers'); print(f'First paper: {papers[0][\"title\"]}')"
```

### Step 7: Run Initial Ingestion via Airflow

1. **Access Airflow UI**: http://localhost:8080

2. **Find the DAG**: Look for `initial_paper_ingestion`

3. **Enable the DAG**: Toggle the switch to ON

4. **Trigger the DAG**: Click the "Play" button → "Trigger DAG"

5. **Monitor Progress**: Watch the task execution in real-time

**Task Flow:**
```
ingest_arxiv ──┐
               ├──> process_and_embed ──> index_to_qdrant ──> store_metadata
ingest_semantic_scholar ──┘
```

**Expected Duration:** 5-10 minutes

### Step 8: Verify Ingestion Success

#### Check Airflow Logs
1. Click on the DAG run
2. Click on each task to view logs
3. Verify all tasks show "success" status

#### Check Qdrant Collection
```powershell
# Check collection info
curl http://localhost:6333/collections/llm_research_papers
```

Expected: Collection with ~50 points (documents)

#### Check PostgreSQL
```powershell
# Connect to database
docker exec -it llm_research_postgres psql -U postgres -d llm_research_hub

# Check paper count
\c llm_research_hub
SELECT COUNT(*) FROM papers;
SELECT COUNT(*) FROM chunks;

# View sample papers
SELECT title, authors, published FROM papers LIMIT 5;

# Exit
\q
```

---

## 📊 Verification Checklist

After completing Phase 1, verify the following:

- [ ] Docker services are running
- [ ] PostgreSQL database is initialized with tables
- [ ] Qdrant collection `llm_research_papers` exists
- [ ] Airflow DAG `initial_paper_ingestion` completed successfully
- [ ] ~50 papers ingested (check `papers` table)
- [ ] Document chunks created (check `chunks` table)
- [ ] Embeddings stored in Qdrant
- [ ] No errors in Airflow logs

---

## 🐛 Troubleshooting

### Issue: Docker containers won't start

**Solution:**
```powershell
# Stop and remove all containers
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```

### Issue: Database connection error

**Solution:**
```powershell
# Check if PostgreSQL is running
docker ps | findstr postgres

# Check PostgreSQL logs
docker logs llm_research_postgres

# Verify connection details in .env file
```

### Issue: OpenAI API error

**Solution:**
- Verify your API key is correct in `.env`
- Check API key has sufficient credits
- Test API key: https://platform.openai.com/api-keys

### Issue: Airflow task fails

**Solution:**
```powershell
# View detailed logs
docker logs llm_research_airflow_scheduler

# Check task logs in Airflow UI
# Click on task → Logs

# Restart Airflow
docker-compose restart airflow-webserver airflow-scheduler
```

### Issue: Rate limiting from arXiv/Semantic Scholar

**Solution:**
- Reduce `max_results` in scraper calls
- Add delays between requests
- Check rate limit settings in scrapers

---

## 📈 Next Steps

After completing Phase 1:

1. **Review Ingested Data**
   - Check paper quality
   - Verify metadata completeness
   - Ensure embeddings are generated

2. **Set Up Daily Ingestion**
   - The `daily_paper_ingestion` DAG will run automatically at 2 AM
   - Monitor for a few days to ensure it works

3. **Move to Phase 2**: RAG Implementation
   - Implement retrieval strategies
   - Test query performance
   - Evaluate retrieval quality

---

## 🔧 Useful Commands

```powershell
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f streamlit
docker-compose logs -f airflow-scheduler

# Restart a service
docker-compose restart [service-name]

# Stop all services
docker-compose down

# Remove all data (fresh start)
docker-compose down -v

# Check resource usage
docker stats

# Access container shell
docker exec -it llm_research_postgres bash
```

---

## 📝 Phase 1 Summary

### What We've Built:
✅ **Infrastructure**: Docker-based microservices architecture  
✅ **Data Sources**: arXiv and Semantic Scholar scrapers  
✅ **Storage**: PostgreSQL + Qdrant vector database  
✅ **Orchestration**: Airflow DAGs for automated ingestion  
✅ **CI/CD**: GitHub Actions pipeline  
✅ **Monitoring**: Basic logging and health checks  

### Metrics:
- **Papers Ingested**: ~50 LLM research papers
- **Data Sources**: 2 (arXiv, Semantic Scholar)
- **Ingestion Time**: ~5-10 minutes
- **Storage**: Vector embeddings + structured metadata
- **Automation**: Daily updates scheduled

### Files Created:
- 30+ source files
- Complete Docker setup
- Airflow DAGs
- Database schema
- Configuration files
- Documentation

---

## 🎯 Ready for Phase 2?

Once Phase 1 is complete and verified, you're ready to proceed with:

**Phase 2: RAG Implementation**
- Hybrid search implementation
- Query rewriting
- Re-ranking
- Retrieval evaluation

Would you like to proceed with Phase 2? Please confirm once Phase 1 is working! 🚀
