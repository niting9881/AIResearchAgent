# LLM Research Intelligence Hub - Architecture

## System Architecture

This document provides a detailed overview of the system architecture for the LLM Research Intelligence Hub.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE LAYER                      │
│                        (Streamlit Web App)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                        APPLICATION LAYER                         │
│                     (RAG + AI Agents)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Query       │  │  Retrieval   │  │  LLM         │         │
│  │  Processing  │→ │  Engine      │→ │  Generation  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                         DATA LAYER                               │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │  Qdrant Vector DB    │  │  PostgreSQL          │            │
│  │  (Embeddings)        │  │  (Metadata/Logs)     │            │
│  └──────────────────────┘  └──────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                             ▲
┌────────────────────────────┴────────────────────────────────────┐
│                      INGESTION LAYER                             │
│                    (Apache Airflow)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  arXiv       │  │  Semantic    │  │  Blog        │         │
│  │  Scraper     │  │  Scholar     │  │  Scraper     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Data Ingestion Layer

#### 1.1 arXiv Scraper
- **Technology**: Python + arxiv library
- **Function**: Fetch papers from arXiv API
- **Search Query**: `cat:cs.CL AND (ti:large language model OR abs:large language model)`
- **Frequency**: 
  - Initial: 50 papers
  - Daily: New papers from last 24 hours

#### 1.2 Semantic Scholar Scraper
- **Technology**: Python + requests
- **Function**: Fetch papers from Semantic Scholar API
- **Rate Limiting**: 100 requests per 5 minutes
- **Features**: Citation counts, author information
- **Frequency**: Daily updates

#### 1.3 Blog Scraper (Agent-based)
- **Sources**: OpenAI Blog, Anthropic Blog
- **Technology**: BeautifulSoup + LangGraph Agent
- **Trigger**: On-demand via user query
- **Function**: Fetch latest AI development posts

#### 1.4 Orchestration (Airflow)
- **DAGs**:
  - `initial_ingestion_dag.py`: One-time initial load
  - `daily_ingestion_dag.py`: Scheduled daily updates (2 AM)
- **Task Flow**:
  1. Scrape data sources
  2. Process and chunk documents
  3. Generate embeddings
  4. Index to Qdrant
  5. Store metadata in PostgreSQL

### 2. Processing Layer

#### 2.1 Document Chunking
- **Strategy**: Recursive character splitting
- **Chunk Size**: 1000 characters
- **Overlap**: 200 characters
- **Purpose**: Maintain context while fitting LLM context windows

#### 2.2 Embedding Generation
- **Model**: OpenAI text-embedding-3-small
- **Dimensions**: 1536
- **Batch Size**: 100 documents
- **Cost Optimization**: Caching, deduplication

#### 2.3 Metadata Extraction
- **Fields**: Title, authors, abstract, publication date, citations
- **Cleaning**: Text normalization, special character removal
- **Validation**: URL validation, date parsing

### 3. Storage Layer

#### 3.1 Qdrant Vector Database
- **Purpose**: Store document embeddings
- **Collection**: `llm_research_papers`
- **Distance Metric**: Cosine similarity
- **Features**:
  - Vector search
  - Payload filtering (metadata)
  - Hybrid search support
- **Scaling**: Horizontal scaling via clustering

#### 3.2 PostgreSQL Database
- **Purpose**: Store structured metadata and logs
- **Tables**:
  - `papers`: Paper metadata
  - `chunks`: Document chunks
  - `user_queries`: Query logs
  - `retrieval_metrics`: Evaluation metrics
  - `llm_metrics`: LLM performance metrics
  - `ingestion_logs`: Ingestion run logs

### 4. RAG (Retrieval-Augmented Generation) Layer

#### 4.1 Query Processing
- **Query Rewriting**: Enhance queries using LLM
- **Query Expansion**: Add synonyms and related terms
- **Spelling Correction**: Auto-correct typos

#### 4.2 Retrieval Engine
- **Search Strategies**:
  1. **Vector Search**: Semantic similarity using embeddings
  2. **Text Search**: BM25 keyword matching (via Qdrant)
  3. **Hybrid Search**: Combine vector + text (weighted)
- **Ranking**: Reciprocal Rank Fusion (RRF)
- **Re-ranking**: Cross-encoder model (optional)
- **Top-K**: Default 10 results

#### 4.3 Context Building
- **Prompt Construction**: Combine retrieved documents with query
- **Token Management**: Truncate context to fit model limits
- **Source Attribution**: Track document sources for citations

#### 4.4 LLM Generation
- **Primary Model**: OpenAI GPT-4o
- **Fallback**: Groq (Llama 3.1 70B) for faster responses
- **Local Option**: Ollama for offline usage
- **Prompt Templates**: Multiple tested strategies
- **Parameters**: Temperature, top_p, max_tokens

### 5. AI Agent Layer (LangGraph)

#### 5.1 Research Agent
- **Role**: Answer research-related queries
- **Tools**:
  - Vector search
  - Metadata filtering
  - Paper recommendations
- **Flow**:
  1. Analyze query intent
  2. Search vector DB
  3. Synthesize response
  4. Provide citations

#### 5.2 Blog Fetcher Agent
- **Role**: Fetch latest blog posts from OpenAI/Anthropic
- **Tools**:
  - Web scraping
  - Content extraction
  - Summarization
- **Trigger**: Keywords like "latest", "blog", "news"

#### 5.3 Synthesis Agent
- **Role**: Combine information from multiple sources
- **Flow**:
  1. Query research papers
  2. Query blog posts
  3. Synthesize comprehensive answer
  4. Provide sources

#### 5.4 Agent Orchestration
- **Framework**: LangGraph
- **State Management**: Shared memory
- **Control Flow**: Conditional routing based on query type
- **Error Handling**: Graceful fallback to basic RAG

### 6. Application Layer

#### 6.1 Streamlit Web Interface
- **Pages**:
  - **Chat**: Conversational Q&A interface
  - **Search**: Advanced search with filters
  - **Analytics**: Usage statistics and insights
- **Features**:
  - Session management
  - Query history
  - Feedback collection (thumbs up/down)
  - Source document display

#### 6.2 API (Optional)
- **Framework**: FastAPI
- **Endpoints**:
  - `/api/v1/query`: Submit queries
  - `/api/v1/papers`: List papers
  - `/api/v1/feedback`: Submit feedback
- **Authentication**: API key

### 7. Monitoring Layer

#### 7.1 Metrics Collection
- **Query Metrics**: Latency, throughput
- **Retrieval Metrics**: Hit rate, MRR, NDCG
- **LLM Metrics**: Token usage, cost, quality scores
- **System Metrics**: CPU, memory, database connections

#### 7.2 Grafana Dashboard
- **Panels** (5+):
  1. Query volume over time
  2. Average response time (P50, P95, P99)
  3. User feedback sentiment
  4. Retrieval quality (hit rate trend)
  5. System health (uptime, errors)
  6. Daily ingestion statistics
  7. Token usage and costs

#### 7.3 Feedback Collection
- **Method**: Thumbs up/down with optional comments
- **Storage**: PostgreSQL `user_queries` table
- **Analysis**: Sentiment analysis, improvement areas

### 8. Evaluation Framework

#### 8.1 Retrieval Evaluation
- **Metrics**:
  - Hit Rate: % of queries with relevant results
  - MRR (Mean Reciprocal Rank): Ranking quality
  - NDCG (Normalized Discounted Cumulative Gain): Relevance scores
- **Test Set**: 100+ human-labeled query-document pairs

#### 8.2 LLM Evaluation
- **Metrics**:
  - Relevance: Does it answer the question?
  - Coherence: Is the response well-structured?
  - Factuality: Is the information accurate?
- **Methods**:
  - Human evaluation
  - LLM-as-judge (GPT-4)
  - RAGAS framework

#### 8.3 A/B Testing
- **Variables**: Prompt templates, retrieval strategies
- **Metrics**: User satisfaction, response quality
- **Duration**: 1-2 weeks per experiment

## Data Flow

### Query Flow
```
User Query → Query Rewriting → Retrieval (Hybrid Search) → 
Re-ranking → Context Building → LLM Generation → Response → 
Feedback Collection → Metrics Storage
```

### Ingestion Flow
```
Data Source → Scraping → Deduplication → Chunking → 
Embedding Generation → Vector DB Indexing → 
Metadata Storage → Logging
```

### Agent Flow
```
User Query → Intent Detection → Agent Selection → 
Tool Execution → Information Synthesis → Response
```

## Scalability Considerations

1. **Horizontal Scaling**: Qdrant clustering, PostgreSQL replication
2. **Caching**: Redis for frequently accessed data
3. **Load Balancing**: Nginx for Streamlit instances
4. **Async Processing**: Celery for background tasks
5. **Rate Limiting**: Prevent API abuse

## Security

1. **API Keys**: Stored in environment variables, never in code
2. **Database**: Password-protected connections
3. **Network**: Internal services communicate via Docker network
4. **HTTPS**: SSL/TLS for production deployment
5. **Input Validation**: Sanitize user inputs

## Deployment

### Development
- Local setup with Docker Compose
- All services on localhost

### Production
- Cloud deployment (AWS/GCP/Azure)
- Kubernetes for orchestration
- Managed services (RDS, managed Qdrant)
- CDN for static assets
- Auto-scaling based on load

## CI/CD Pipeline

1. **Code Quality**: Linting, type checking
2. **Testing**: Unit, integration, E2E tests
3. **Build**: Docker image creation
4. **Security Scan**: Vulnerability detection
5. **Deploy**: Staged rollout (dev → staging → prod)
6. **Monitoring**: Post-deployment health checks

---

This architecture ensures:
- ✅ **Scalability**: Handle growing data and users
- ✅ **Reliability**: Fault tolerance and recovery
- ✅ **Maintainability**: Modular, well-documented code
- ✅ **Performance**: Fast query response times
- ✅ **Observability**: Comprehensive monitoring and logging
