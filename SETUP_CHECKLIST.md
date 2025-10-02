# ✅ Setup Checklist - LLM Research Intelligence Hub

Use this checklist to track your progress through Phase 1 setup.

---

## 🔧 Pre-Setup Requirements

- [ ] Windows 10/11 with PowerShell
- [ ] Python 3.11 or higher installed
- [ ] Docker Desktop installed and running
- [ ] Git installed
- [ ] Visual Studio Code (or preferred IDE)
- [ ] OpenAI API key obtained
- [ ] Sufficient disk space (minimum 10GB)

---

## 📦 Phase 1: Initial Setup

### Step 1: Project Setup
- [ ] Navigated to `C:\Users\nitin\AIResearchAgent`
- [ ] Reviewed `README.md`
- [ ] Reviewed `PROJECT_SUMMARY.md`
- [ ] Reviewed `docs/architecture.md`

### Step 2: Python Environment
- [ ] Created virtual environment (`python -m venv venv`)
- [ ] Activated virtual environment (`.\venv\Scripts\activate`)
- [ ] Upgraded pip (`python -m pip install --upgrade pip`)
- [ ] Installed dependencies (`pip install -r requirements.txt`)
- [ ] Verified installation (no errors)

### Step 3: Configuration
- [ ] Copied `.env.example` to `.env`
- [ ] Added OpenAI API key to `.env`
- [ ] Reviewed all configuration options
- [ ] Saved `.env` file

### Step 4: Docker Services
- [ ] Started Docker Desktop
- [ ] Ran `docker-compose up -d`
- [ ] Waited for services to start (60 seconds)
- [ ] Verified all 6 containers are running (`docker-compose ps`)
- [ ] All containers show "healthy" or "up" status

### Step 5: Database Initialization
- [ ] Ran `python scripts/init_db.py`
- [ ] Saw success message
- [ ] Verified 6 tables created
- [ ] No errors in output

---

## 🧪 Testing & Verification

### Test Individual Components
- [ ] Tested Qdrant health: `curl http://localhost:6333/health`
- [ ] Accessed Qdrant dashboard: http://localhost:6333/dashboard
- [ ] Tested PostgreSQL connection
- [ ] Accessed Airflow UI: http://localhost:8080
- [ ] Logged into Airflow (admin/admin)
- [ ] Accessed Grafana: http://localhost:3000
- [ ] Logged into Grafana (admin/admin)

### Test Data Scrapers
- [ ] Tested arXiv scraper (5 papers)
- [ ] Reviewed sample paper metadata
- [ ] Tested Semantic Scholar scraper (5 papers)
- [ ] Reviewed sample paper metadata
- [ ] No errors in scraper tests

---

## 🚀 Initial Data Ingestion

### Airflow DAG Execution
- [ ] Opened Airflow UI (http://localhost:8080)
- [ ] Found `initial_paper_ingestion` DAG
- [ ] Enabled the DAG (toggle switch)
- [ ] Triggered the DAG manually
- [ ] Monitored task execution (5-10 minutes)
- [ ] All tasks completed successfully (green)
- [ ] Reviewed task logs (no errors)

### Task Success Verification
- [ ] `ingest_arxiv` task - Success
- [ ] `ingest_semantic_scholar` task - Success
- [ ] `process_and_embed` task - Success
- [ ] `index_to_qdrant` task - Success
- [ ] `store_metadata` task - Success

---

## ✅ Post-Ingestion Verification

### Verify Qdrant
- [ ] Checked collection exists: `curl http://localhost:6333/collections/llm_research_papers`
- [ ] Collection shows ~50 points (vectors)
- [ ] Verified vector dimensions (1536)

### Verify PostgreSQL
- [ ] Connected to database
- [ ] Ran: `SELECT COUNT(*) FROM papers;`
- [ ] Saw ~50 papers
- [ ] Ran: `SELECT COUNT(*) FROM chunks;`
- [ ] Saw multiple chunks created
- [ ] Ran: `SELECT title FROM papers LIMIT 5;`
- [ ] Viewed sample paper titles

### Verify Airflow Logs
- [ ] Checked ingestion log table
- [ ] Verified ingestion run recorded
- [ ] Status shows "success"
- [ ] Papers count matches expected

---

## 📊 Service Health Check

### All Services Running
- [ ] PostgreSQL - Port 5432 - Healthy
- [ ] Qdrant - Port 6333 - Healthy
- [ ] Airflow Webserver - Port 8080 - Healthy
- [ ] Airflow Scheduler - Running
- [ ] Streamlit - Port 8501 - Running
- [ ] Grafana - Port 3000 - Running

### Log Files
- [ ] Checked `logs/` directory created
- [ ] Reviewed application logs
- [ ] No critical errors
- [ ] All services logging properly

---

## 🔍 Quality Checks

### Data Quality
- [ ] Papers have titles
- [ ] Papers have authors
- [ ] Papers have abstracts
- [ ] Papers have publication dates
- [ ] Papers have URLs
- [ ] No duplicate papers (verify sample)

### Metadata Completeness
- [ ] Source (arXiv/Semantic Scholar) recorded
- [ ] Categories/fields populated
- [ ] Citation counts present (when available)
- [ ] Timestamps (scraped_at) present

---

## 📚 Documentation Review

### Read Documentation
- [ ] Read `README.md` completely
- [ ] Read `docs/architecture.md`
- [ ] Read `docs/PHASE1_SETUP.md`
- [ ] Read `PROJECT_SUMMARY.md`
- [ ] Understand project structure

### Understand Codebase
- [ ] Reviewed `src/utils/config.py`
- [ ] Reviewed `src/ingestion/arxiv_scraper.py`
- [ ] Reviewed `src/ingestion/semantic_scholar.py`
- [ ] Reviewed `airflow/dags/initial_ingestion_dag.py`
- [ ] Reviewed `scripts/init_db.py`

---

## 🔄 Daily Ingestion Setup

### Verify Daily DAG
- [ ] Found `daily_paper_ingestion` DAG in Airflow
- [ ] Reviewed DAG schedule (2 AM daily)
- [ ] Enabled the DAG
- [ ] DAG will run automatically tomorrow

### Test Daily DAG (Optional)
- [ ] Manually triggered `daily_paper_ingestion`
- [ ] Monitored execution
- [ ] Verified deduplication works
- [ ] Verified incremental updates

---

## 🛠️ Useful Commands Tested

### Docker Commands
- [ ] `docker-compose ps` - Check status
- [ ] `docker-compose logs -f` - View logs
- [ ] `docker-compose restart [service]` - Restart service
- [ ] `docker-compose down` - Stop services
- [ ] `docker-compose up -d` - Start services

### Database Commands
- [ ] Connected to PostgreSQL via Docker
- [ ] Ran sample queries
- [ ] Checked table schemas

### Python Commands
- [ ] Ran scrapers manually
- [ ] Imported modules in Python shell
- [ ] Tested configuration loading

---

## 🚨 Troubleshooting Completed

### Resolved Issues (if any)
- [ ] Fixed Docker container issues
- [ ] Fixed database connection issues
- [ ] Fixed API key issues
- [ ] Fixed Airflow DAG issues
- [ ] All services working

---

## 📸 Screenshots Captured (Optional)

- [ ] Airflow DAG success screen
- [ ] Qdrant collection dashboard
- [ ] PostgreSQL paper list
- [ ] Docker containers running
- [ ] Grafana dashboard (if configured)

---

## 🎯 Phase 1 Complete!

### Final Verification
- [ ] All checklist items above completed
- [ ] No blocking issues
- [ ] Services running smoothly
- [ ] Data ingestion successful
- [ ] Documentation understood

### Phase 1 Metrics
- Papers Ingested: ______ (target: ~50)
- Time Taken: ______ minutes
- Errors Encountered: ______
- Errors Resolved: ______

---

## 🚀 Ready for Phase 2?

### Before Proceeding
- [ ] Phase 1 fully functional
- [ ] All tests passing
- [ ] Data quality verified
- [ ] Daily ingestion scheduled
- [ ] Understanding of architecture

### Confirmation
- [ ] I confirm Phase 1 is complete
- [ ] I'm ready to proceed to Phase 2
- [ ] I understand the next steps

---

## 📝 Notes & Issues

Use this space to note any issues encountered or observations:

```
Issue 1: _______________________________________________
Solution: _______________________________________________

Issue 2: _______________________________________________
Solution: _______________________________________________

Observations: ___________________________________________
________________________________________________________
________________________________________________________
```

---

## 📧 Support Needed?

If you're stuck on any step:

1. Review `docs/PHASE1_SETUP.md` troubleshooting section
2. Check Docker logs: `docker-compose logs [service-name]`
3. Check Airflow task logs in UI
4. Review error messages carefully
5. Ask for help with specific error details

---

## ✅ Sign-Off

**Phase 1 Setup Completed By:** ________________  
**Date:** ________________  
**Time Taken:** ________________  
**Status:** ✅ Complete / 🔄 In Progress / ❌ Issues

**Ready for Phase 2:** ✅ Yes / ❌ No

---

**Once all items are checked, inform your team lead to proceed to Phase 2!** 🎉
