# AIRMAN - Aviation Document RAG Chat

AI/ML Intern Technical Assignment - Document-Driven RAG with Hybrid Retrieval

## Overview

This system provides grounded answers to aviation questions using Retrieval-Augmented Generation (RAG) from aviation textbooks, with two levels of retrieval sophistication.

## Features

### Level 1 (Baseline) ✅
- **Vector-based retrieval** using FAISS with Azure OpenAI embeddings
- **Strict grounding**: Refuses to answer if information not in documents
- **Citations**: Page numbers and text snippets for every answer
- **Evaluation**: 50 questions across 3 difficulty levels
- **API**: FastAPI with `/ingest`, `/ask`, and `/health` endpoints

### Level 2 (Advanced) ✅
- **Hybrid Retrieval Pipeline**:
  1. BM25 keyword search (top 20 candidates)
  2. Vector semantic search (top 20 candidates)
  3. Union of both result sets
  4. Azure embedding reranking (final top 8)
- **Backward compatible**: Level 1 still works (use `use_hybrid: false`)
- **Comparison evaluation**: Side-by-side metrics

### Production Ready ✅
- **Docker**: Multi-stage Dockerfile + docker-compose
- **Logging**: Structured logging to file and console
- **Tests**: Comprehensive pytest suite with 20+ tests
- **Health Checks**: Built-in endpoint monitoring
- **Documentation**: Production deployment guide

## Architecture

### Level 1 Flow
```
Question → Azure Embeddings → FAISS Search → Top 8 Chunks → LLM → Answer
```

### Level 2 Flow
```
Question → BM25 Search (20) ──┐
         → Vector Search (20) ─┤→ Union → Cross-Encoder Reranker → Top 8 → LLM → Answer
```

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
Create `.env` file:
```
AZURE_OPENAI_ENDPOINT=https://your-endpoint.azure.com
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-model-name
AZURE_EMBEDDING_KEY=your-embedding-key
```

### 3. Ingest Documents
```bash
# Creates both FAISS vector index and BM25 index
python ingest.py
```

Or via API:
```bash
curl -X POST http://localhost:8000/ingest
```

### 4. Run Server
```bash
# Local development
uvicorn app:app --reload

# Production with Docker
docker-compose up -d
```

## Production Deployment

### Quick Start with Docker
```bash
# Build and run
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

See [PRODUCTION.md](PRODUCTION.md) for detailed deployment guide.

## Testing

```bash
# Install test dependencies
pip install pytest pytest-cov httpx

# Run tests
pytest test_app.py -v

# Run with coverage
pytest test_app.py --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Logging

Logs are written to:
- **Console**: Real-time output
- **File**: `app.log` in project root

Log format: `timestamp - logger - level - message`

## Usage

### API Endpoints

#### POST /ask (Level 1 - Vector Only)
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the function of the pitot head?",
    "debug": true,
    "use_hybrid": false
  }'
```

#### POST /ask (Level 2 - Hybrid Retrieval)
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the function of the pitot head?",
    "debug": true,
    "use_hybrid": true
  }'
```

Response:
```json
{
  "answer": "The pitot head senses total pressure...",
  "citations": [
    {"page": 5, "snippet": "An open-ended tube..."}
  ],
  "retrieval_method": "hybrid",
  "retrieved_chunks": ["chunk1", "chunk2", "chunk3"]
}
```

#### GET /health
```bash
curl http://localhost:8000/health
```

## Evaluation

### Run Level 1 Evaluation (50 questions)
```bash
python evaluate.py
```
Generates: `report.md`

### Run Level 1 vs Level 2 Comparison
```bash
python evaluate_comparison.py
```
Generates: `level_comparison_report.md`

This runs all 50 questions through both:
- Level 1 (vector-only)
- Level 2 (hybrid retrieval)

And compares:
- Retrieval hit-rate
- Answer rate
- Refusal rate
- Answer quality

## Question Set

50 questions based on `Instruments.pdf`:
- **20 Simple Factual**: Definitions, direct lookups
- **20 Applied**: Scenario-based, operational procedures
- **10 Higher-Order Reasoning**: Multi-step analysis, trade-offs

## File Structure

```
AIRMAN/
├── app.py                      # FastAPI server with Level 1 + Level 2
├── ingest.py                   # Document ingestion (FAISS + BM25)
├── evaluate.py                 # Level 1 evaluation
├── evaluate_comparison.py      # Level 1 vs Level 2 comparison
├── test_app.py                 # Test suite (pytest)
├── questions.json              # 50 evaluation questions
├── requirements.txt            # Dependencies
├── Dockerfile                  # Docker build configuration
├── docker-compose.yml          # Docker orchestration
├── .dockerignore               # Docker build optimization
├── .env                        # API keys (not committed)
├── README.md                   # Main documentation
├── PRODUCTION.md               # Production deployment guide
├── LEVEL2_IMPLEMENTATION.md    # Level 2 technical details
├── app.log                     # Application logs
├── data/
│   └── Instruments.pdf         # Source document
├── vectorstore/
│   ├── index.faiss            # Vector index
│   ├── bm25.pkl               # BM25 index
│   └── chunks.pkl             # Text chunks + metadata
├── report.md                   # Level 1 evaluation report
└── level_comparison_report.md  # Level 1 vs 2 comparison
```

```
AIRMAN/
├── app.py                      # FastAPI server with Level 1 + Level 2
├── ingest.py                   # Document ingestion (FAISS + BM25)
├── evaluate.py                 # Level 1 evaluation
├── evaluate_comparison.py      # Level 1 vs Level 2 comparison
├── questions.json              # 50 evaluation questions
├── requirements.txt            # Dependencies
├── .env                        # API keys (not committed)
├── data/
│   └── Instruments.pdf         # Source document
├── vectorstore/
│   ├── index.faiss            # Vector index
│   ├── bm25.pkl               # BM25 index
│   └── chunks.pkl             # Text chunks + metadata
├── report.md                   # Level 1 evaluation report
└── level_comparison_report.md  # Level 1 vs 2 comparison
```

## Key Design Decisions

### Chunking Strategy
- **Size**: 400 words per chunk
- **Overlap**: 100 words
- **Rationale**: Balances context preservation with retrieval granularity

### Hybrid Retrieval (Level 2)
- **BM25**: Captures exact keyword matches (e.g., technical terms)
- **Vector**: Captures semantic similarity
- **Azure Reranking**: Uses same embedding model for consistency
- **Top-k**: 20 candidates each → rerank → 8 final chunks

### Grounding Mechanism
- Distance threshold on FAISS search
- LLM prompt enforcement
- Post-generation validation
- Explicit refusal message if uncertain

### Production Features
- **Logging**: Structured logs for debugging and monitoring
- **Docker**: Containerized deployment with health checks
- **Testing**: 20+ unit and integration tests
- **Monitoring**: Health endpoint for uptime checks

## Dependencies

- `fastapi` - API framework
- `uvicorn` - ASGI server
- `openai` - Azure OpenAI client
- `faiss-cpu` - Vector search (Level 1)
- `rank-bm25` - Keyword search (Level 2)
- `PyPDF2` - PDF parsing
- `python-dotenv` - Environment variables
- `pytest` - Testing framework
- `pytest-cov` - Test coverage

## Performance

### Level 1 (Baseline)
- Retrieval: ~200ms per query
- End-to-end: ~2-3s (including LLM)

### Level 2 (Hybrid)
- Retrieval: ~500ms per query (BM25 + reranking overhead)
- End-to-end: ~2.5-3.5s
- **Trade-off**: +50% latency for improved relevance

## Evaluation Metrics

Both levels report:
- **Retrieval Hit-Rate**: % of questions with relevant chunks retrieved
- **Answer Rate**: % of questions successfully answered
- **Refusal Rate**: % of questions refused (info not available)
- **Faithfulness**: All answers include citations for verification

## Future Enhancements

- Query expansion/reformulation
- Document metadata filtering
- Semantic caching for repeated queries
- Multi-document support
- Confidence scoring

## Author

Assignment submission for AIRMAN AI/ML Internship

## License

Proprietary - AIRMAN Assignment
