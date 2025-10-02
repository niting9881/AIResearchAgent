# 🚀 Quick Reference Guide

Your go-to cheat sheet for the LLM Research Intelligence Hub.

---

## 📍 Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Airflow** | http://localhost:8080 | admin / admin |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Qdrant** | http://localhost:6333/dashboard | None |
| **Streamlit** | http://localhost:8501 | None |
| **PostgreSQL** | localhost:5432 | postgres / postgres |

---

## ⚡ Common Commands

### Virtual Environment
```powershell
# Activate
.\venv\Scripts\activate

# Deactivate
deactivate

# Reinstall dependencies
pip install -r requirements.txt
```

### Docker Operations
```powershell
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs (all)
docker-compose logs -f

# View specific service logs
docker-compose logs -f streamlit
docker-compose logs -f airflow-scheduler

# Restart a service
docker-compose restart [service-name]

# Check status
docker-compose ps

# Rebuild images
docker-compose build --no-cache

# Fresh start (removes volumes)
docker-compose down -v
docker-compose up -d
```

### Database Commands
```powershell
# Initialize database
python scripts/init_db.py

# Connect to PostgreSQL
docker exec -it llm_research_postgres psql -U postgres -d llm_research_hub

# Inside PostgreSQL:
\dt                          # List tables
\d papers                    # Describe table
SELECT COUNT(*) FROM papers; # Count papers
\q                          # Quit
```

### Qdrant Operations
```powershell
# Check health
curl http://localhost:6333/health

# List collections
curl http://localhost:6333/collections

# Collection info
curl http://localhost:6333/collections/llm_research_papers

# Count vectors
curl http://localhost:6333/collections/llm_research_papers/points/count
```

### Testing Commands
```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_scrapers.py

# Run specific test
pytest tests/unit/test_scrapers.py::test_arxiv_scraper
```

### Code Quality
```powershell
# Format code
black src/ tests/
isort src/ tests/

# Check formatting
black --check src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

### Scraper Testing
```powershell
# Test arXiv scraper
python -c "from src.ingestion.arxiv_scraper import ArxivScraper; s = ArxivScraper(); papers = s.search_papers(max_results=3); print(f'Found {len(papers)} papers')"

# Test Semantic Scholar scraper
python -c "from src.ingestion.semantic_scholar import SemanticScholarScraper; s = SemanticScholarScraper(); papers = s.search_papers(max_results=3); print(f'Found {len(papers)} papers')"
```

---

## 📂 Key File Locations

### Configuration
- **Environment Variables:** `.env`
- **Main Config:** `src/utils/config.py`
- **Docker Compose:** `docker-compose.yml`
- **Requirements:** `requirements.txt`

### Source Code
- **Scrapers:** `src/ingestion/`
- **Processing:** `src/processing/`
- **RAG:** `src/rag/`
- **Agents:** `src/agents/`
- **App:** `src/app/`
- **Utils:** `src/utils/`

### Airflow
- **DAGs:** `airflow/dags/`
- **Logs:** `airflow/logs/`
- **Plugins:** `airflow/plugins/`

### Documentation
- **Main README:** `README.md`
- **Architecture:** `docs/architecture.md`
- **Setup Guide:** `docs/PHASE1_SETUP.md`
- **Project Summary:** `PROJECT_SUMMARY.md`

### Data
- **Raw Data:** `data/raw/`
- **Processed:** `data/processed/`
- **Logs:** `logs/`

---

## 🔍 Useful SQL Queries

### Check Data
```sql
-- Count papers by source
SELECT source, COUNT(*) 
FROM papers 
GROUP BY source;

-- Recent papers
SELECT title, published, source 
FROM papers 
ORDER BY published DESC 
LIMIT 10;

-- Papers by category
SELECT primary_category, COUNT(*) 
FROM papers 
WHERE primary_category IS NOT NULL
GROUP BY primary_category
ORDER BY COUNT(*) DESC;

-- Check chunks
SELECT paper_id, COUNT(*) as chunk_count
FROM chunks
GROUP BY paper_id
LIMIT 10;

-- Check user queries
SELECT query, feedback, created_at
FROM user_queries
ORDER BY created_at DESC
LIMIT 10;

-- Ingestion logs
SELECT run_type, papers_found, papers_indexed, status, started_at
FROM ingestion_logs
ORDER BY started_at DESC;
```

---

## 🐛 Troubleshooting

### Docker Issues
```powershell
# Check Docker is running
docker --version
docker ps

# Restart Docker Desktop
# (Use GUI or system tray)

# Remove all containers and volumes
docker-compose down -v
docker system prune -a --volumes
```

### Database Connection Issues
```powershell
# Check PostgreSQL logs
docker logs llm_research_postgres

# Verify it's running
docker ps | findstr postgres

# Test connection
docker exec llm_research_postgres pg_isready -U postgres
```

### Airflow Issues
```powershell
# Check scheduler logs
docker logs llm_research_airflow_scheduler

# Check webserver logs
docker logs llm_research_airflow_webserver

# Restart Airflow
docker-compose restart airflow-webserver airflow-scheduler

# Clear Airflow metadata
docker-compose down
docker volume rm airesearchagent_postgres_data
docker-compose up -d
```

### Python Import Issues
```powershell
# Verify virtual environment is activated
# Should see (venv) in prompt

# Reinstall packages
pip install --upgrade -r requirements.txt

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### API Issues
```powershell
# Test OpenAI API
python -c "import openai; from src.utils.config import settings; openai.api_key = settings.openai_api_key; print('API key configured')"

# Check .env file
notepad .env
# Verify OPENAI_API_KEY is set
```

---

## 📊 Monitoring Queries

### System Health
```sql
-- Total papers
SELECT COUNT(*) FROM papers;

-- Papers by date
SELECT DATE(published) as date, COUNT(*) 
FROM papers 
GROUP BY DATE(published) 
ORDER BY date DESC 
LIMIT 7;

-- Recent queries
SELECT COUNT(*) FROM user_queries WHERE created_at > NOW() - INTERVAL '24 hours';

-- Average response time
SELECT AVG(total_time) as avg_time FROM user_queries WHERE total_time IS NOT NULL;

-- Feedback summary
SELECT 
    SUM(CASE WHEN feedback = 1 THEN 1 ELSE 0 END) as positive,
    SUM(CASE WHEN feedback = -1 THEN 1 ELSE 0 END) as negative,
    COUNT(*) as total
FROM user_queries;
```

---

## 🎯 Airflow DAG Triggers

### Via UI
1. Go to http://localhost:8080
2. Login (admin/admin)
3. Find DAG
4. Click play button → "Trigger DAG"

### Via CLI (inside Airflow container)
```bash
# Trigger initial ingestion
docker exec llm_research_airflow_scheduler airflow dags trigger initial_paper_ingestion

# Trigger daily ingestion
docker exec llm_research_airflow_scheduler airflow dags trigger daily_paper_ingestion

# List DAGs
docker exec llm_research_airflow_scheduler airflow dags list

# Test a task
docker exec llm_research_airflow_scheduler airflow tasks test initial_paper_ingestion ingest_arxiv 2025-10-01
```

---

## 🔐 Environment Variables

### Required
```env
OPENAI_API_KEY=sk-...    # Required for embeddings and LLM
```

### Optional but Recommended
```env
GROQ_API_KEY=gsk_...     # For alternative LLM
```

### Database (default values)
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=llm_research_hub
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=llm_research_papers
```

---

## 🚀 Next Steps After Phase 1

1. **Verify Everything Works**
   - [ ] Run checklist in `SETUP_CHECKLIST.md`
   - [ ] Confirm 50 papers ingested
   - [ ] Check all services healthy

2. **Understand the Architecture**
   - [ ] Review `docs/architecture.md`
   - [ ] Understand data flow
   - [ ] Review code structure

3. **Prepare for Phase 2**
   - [ ] Read about RAG implementation
   - [ ] Understand retrieval strategies
   - [ ] Review evaluation metrics

4. **Confirm Ready**
   - [ ] Inform team lead Phase 1 complete
   - [ ] Request Phase 2 tasks
   - [ ] Begin RAG implementation

---

## 📞 Getting Help

### Documentation
1. `README.md` - Project overview
2. `docs/architecture.md` - Architecture details
3. `docs/PHASE1_SETUP.md` - Setup guide
4. `PROJECT_SUMMARY.md` - Project summary
5. `SETUP_CHECKLIST.md` - Setup checklist

### Logs to Check
1. Docker logs: `docker-compose logs -f`
2. Airflow logs: UI or `docker logs llm_research_airflow_scheduler`
3. Application logs: `logs/app_YYYY-MM-DD.log`
4. Error logs: `logs/errors_YYYY-MM-DD.log`

### Common Solutions
- **Service won't start:** Check Docker Desktop is running
- **Database error:** Verify PostgreSQL is healthy
- **API error:** Check .env has correct API key
- **Import error:** Activate virtual environment
- **Port conflict:** Stop other services using same ports

---

## 💡 Tips & Best Practices

1. **Always activate virtual environment** before running Python commands
2. **Check logs** when something goes wrong
3. **Use Docker Compose** for consistent environment
4. **Keep .env secure** - never commit to Git
5. **Monitor Airflow** for ingestion status
6. **Check database** regularly for data quality
7. **Review documentation** when stuck
8. **Test incrementally** - don't skip verification steps

---

## 🎓 Learning Resources

### arXiv API
- Docs: https://info.arxiv.org/help/api/index.html
- Python lib: https://github.com/lukasschwab/arxiv.py

### Semantic Scholar API
- Docs: https://api.semanticscholar.org/

### Airflow
- Docs: https://airflow.apache.org/docs/
- Concepts: https://airflow.apache.org/docs/apache-airflow/stable/concepts/

### Qdrant
- Docs: https://qdrant.tech/documentation/
- Python client: https://python-client.qdrant.tech/

### LangGraph
- Docs: https://langchain-ai.github.io/langgraph/

---

**Keep this reference handy! Bookmark this page for quick access.** 🔖
