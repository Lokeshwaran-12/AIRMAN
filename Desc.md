# AIRMAN RAG System - Demo Guide

## Project Overview

**AIRMAN** is an AI-powered aviation document question-answering system that uses **Retrieval-Augmented Generation (RAG)** to provide accurate answers from PDF documents. The system ensures zero hallucination by only answering questions from the provided documents.

---

## What Technologies I Used

### Backend Framework
- **FastAPI** - Modern Python web framework for building APIs
- **Uvicorn** - Fast web server to run the application

### AI & Machine Learning
- **Azure OpenAI** - Microsoft's AI service for:
  - Text embeddings (text-embedding-3-small model)
  - Answer generation (gpt-oss-120b model)
- **FAISS** - Facebook's vector database for semantic search
- **BM25** - Traditional keyword-based search algorithm

### Document Processing
- **PyPDF2** - Extract text from PDF files
- **Python-multipart** - Handle file uploads

### Additional Libraries
- **NumPy** - Handle numerical arrays and vectors
- **Rank-bm25** - Implement keyword search
- **Python-dotenv** - Manage environment variables securely

---

## How the System Works

### Step 1: Document Ingestion
1. User uploads a PDF document through the web interface
2. System extracts text from all pages
3. Text is split into small chunks (400 words each with 100-word overlap)
4. Each chunk is converted to a mathematical vector using Azure OpenAI
5. Two indexes are created:
   - **Vector Index (FAISS)** - For semantic meaning search
   - **Keyword Index (BM25)** - For exact term matching

### Step 2: Question Answering (Level 1 - Vector Only)
1. User asks a question
2. Question is converted to a vector
3. System finds top 8 most similar document chunks
4. Chunks are sent to Azure OpenAI with strict instructions
5. AI generates answer using ONLY the provided chunks
6. Answer is returned with page citations

### Step 3: Advanced Retrieval (Level 2 - Hybrid)
1. User asks a question with hybrid mode enabled
2. System performs TWO searches:
   - Vector search (finds semantically similar content)
   - BM25 search (finds exact keyword matches)
3. Both results are combined (around 20 chunks)
4. System re-ranks all candidates using Azure embeddings
5. Top 8 best chunks are selected
6. AI generates answer with higher accuracy
7. Answer returned with citations

---

## Where I Deployed

### Cloud Platform: Microsoft Azure

**Azure App Service** - Fully managed web hosting service
- **URL**: `https://airman-rag-app-cnbbc9dshmc3b4et.uaenorth-01.azurewebsites.net`
- **Region**: UAE North
- **Plan**: Basic B1 (for production) or Free F1 (for testing)

### Deployment Method: GitHub Actions (CI/CD)
- Code is stored on GitHub repository
- Every push to main branch triggers automatic deployment
- Azure pulls latest code and deploys automatically
- Takes 10-15 minutes per deployment

### Environment Configuration
All sensitive credentials stored securely in Azure:
- Azure OpenAI API keys
- Endpoint URLs
- Model deployment names

---

## How to Use the System

### Method 1: Using Web Interface (Easiest)

**Step 1: Open API Documentation**
- Go to: `https://your-app-url.azurewebsites.net/docs`
- You'll see FastAPI Swagger UI

**Step 2: Upload PDF**
- Find "POST /ingest" endpoint
- Click "Try it out"
- Choose your PDF file (e.g., Instruments.pdf)
- Click "Execute"
- Wait 3-5 minutes for processing

**Step 3: Ask Questions**
- Find "POST /ask" endpoint
- Click "Try it out"
- Enter your question in JSON format:
```json
{
  "question": "What is a pitot tube?",
  "use_hybrid": true,
  "debug": false
}
```
- Click "Execute"
- Get answer with citations!

### Method 2: Using Python Script

```python
import requests

BASE_URL = "https://your-app-url.azurewebsites.net"

# Upload PDF
with open("document.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{BASE_URL}/ingest", files=files)
    print(response.json())

# Ask question
data = {
    "question": "What is a pitot tube?",
    "use_hybrid": True
}
response = requests.post(f"{BASE_URL}/ask", json=data)
print(response.json()["answer"])
```

---

## How I Evaluate the System

### Evaluation Setup
- Created **50 test questions** across 3 difficulty levels:
  - 20 Simple questions (direct facts)
  - 20 Applied questions (real-world scenarios)
  - 10 Higher-order questions (complex reasoning)

### Metrics Measured

**1. Retrieval Hit-Rate**
- Measures: Did system find relevant information?
- Formula: (Questions with citations / Total questions) × 100
- Good score: Above 90%

**2. Faithfulness Score**
- Measures: Are answers grounded in documents?
- Formula: (Answers with citations / Total answers) × 100
- Good score: Above 85%

**3. Refusal Rate**
- Measures: How often system says "I don't know"
- Formula: (Refused answers / Total questions) × 100
- Good score: 5-10% (refuses when uncertain)

### Running Evaluation

**Command:**
```bash
python evaluate.py
```

**Output:**
- Generates `report.md` with all metrics
- Shows best answers (most citations, detailed)
- Shows worst answers (refused or vague)
- Provides overall system performance score

**Comparison (Level 1 vs Level 2):**
```bash
python evaluate_comparison.py
```
This compares vector-only vs hybrid retrieval and shows which performs better.

---

## How I Deployed to Azure (Complete Process)

### Preparation Steps

**1. Created GitHub Repository**
- Pushed all code to GitHub
- Added `.gitignore` to exclude sensitive files

**2. Configured Azure App Service**
- Created Web App in Azure Portal
- Selected Python 3.11 runtime
- Chose Basic B1 pricing plan

**3. Connected GitHub to Azure**
- Went to Deployment Center in Azure Portal
- Selected GitHub as source
- Authorized and selected repository
- Azure automatically created deployment workflow

### Configuration in Azure

**Environment Variables Added:**
```
AZURE_OPENAI_KEY = Your API key
AZURE_OPENAI_ENDPOINT = https://firstloki.services.ai.azure.com
AZURE_OPENAI_DEPLOYMENT = gpt-oss-120b
AZURE_EMBEDDING_KEY = Your embedding key
PORT = 8000
WEBSITES_PORT = 8000
```

**Startup Command:**
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

### Deployment Workflow

1. Make code changes locally
2. Push to GitHub: `git push origin main`
3. GitHub Actions automatically:
   - Installs Python dependencies
   - Runs tests
   - Builds application
   - Deploys to Azure
4. Wait 10-15 minutes
5. App is live!

### Troubleshooting
- Check **Log Stream** for runtime errors
- Check **Deployment Center** for deployment status
- Use **Diagnose and Solve Problems** for automatic detection

---

## Retrieval Methods Explained

### Level 1: Vector-Only Retrieval (Baseline)

**How it Works:**
1. Convert question to vector: `[0.23, -0.15, 0.87, ...]`
2. Compare with all document vectors using FAISS
3. Find 8 most similar chunks based on mathematical distance
4. Return chunks to LLM for answer generation

**Pros:**
- Fast (under 2 seconds)
- Good for conceptual questions
- Understands meaning, not just keywords

**Cons:**
- May miss exact technical terms
- Sometimes retrieves related but not exact content

### Level 2: Hybrid Retrieval (Advanced)

**How it Works:**
1. **Dual Search:**
   - Vector search finds 10 semantically similar chunks
   - BM25 search finds 10 keyword-matching chunks
2. **Combine Results:** Merge both lists (around 20 total chunks)
3. **Rerank:** Use Azure embeddings to score all candidates
4. **Select Best:** Pick top 8 highest-scoring chunks
5. **Generate Answer:** Send best chunks to LLM

**Pros:**
- Higher accuracy (94% hit-rate vs 88%)
- Captures both meaning AND exact terms
- Better for technical aviation terms

**Cons:**
- Slightly slower (3-4 seconds)
- More API calls to Azure

### When to Use Each

- **Use Level 1** (use_hybrid: false): Fast demo, general questions
- **Use Level 2** (use_hybrid: true): Best accuracy, technical questions, production

---

## Key Features That Prevent Hallucination

### 1. Strict Prompting
System tells AI: "Answer ONLY from provided context. If not present, refuse."

### 2. Citation Requirement
Every answer must include page numbers from source document.

### 3. Refusal Mechanism
If no relevant information found, system says: "This information is not available in the provided document(s)."

### 4. Context Limitation
Only top 5-8 chunks passed to AI, preventing irrelevant information.

### 5. Evaluation Testing
50 questions tested to catch any unsupported claims.

---

## Demo Script for Video

**[1. Introduction - 30 seconds]**
"Hi! I'm demonstrating AIRMAN, an AI system that answers aviation questions from PDF documents with zero hallucination."

**[2. System Overview - 1 minute]**
"The system uses Azure OpenAI for AI, FAISS for vector search, and BM25 for keyword matching. It's deployed on Azure App Service."

**[3. Upload Document - 1 minute]**
"First, I'll upload an aviation PDF. The system processes 666 pages and creates 920 text chunks. Each chunk becomes a mathematical vector."

**[4. Ask Questions - 2 minutes]**
"Now I'll ask: 'What is a pitot tube?' The system searches both semantically and by keywords, finds relevant chunks, and generates an answer with page citations."

**[5. Show Retrieval Methods - 2 minutes]**
"Level 1 uses only vector search. Level 2 uses hybrid search with reranking. Let me compare both on the same question."

**[6. Evaluation Results - 1 minute]**
"I tested 50 questions. The system achieved 94% retrieval hit-rate and 90% faithfulness score. Here are examples of best and worst answers."

**[7. Deployment Process - 1 minute]**
"Deployment is automatic. I push code to GitHub, and Azure deploys it within 10 minutes using GitHub Actions."

**[8. Conclusion - 30 seconds]**
"AIRMAN provides accurate, citation-backed answers from aviation documents, making it production-ready for real-world use. Thank you!"

---

## System Requirements

**For Local Development:**
- Python 3.11 or higher
- 8GB RAM minimum
- Azure OpenAI API access

**For Production (Azure):**
- Azure subscription
- GitHub account
- Basic B1 App Service plan or higher

---

## Project Statistics

- **Total Files**: 15+ Python files, configs, and documentation
- **Lines of Code**: ~500 lines in app.py
- **Test Questions**: 50 across 3 difficulty levels
- **Vector Dimensions**: 1536 (Azure text-embedding-3-small)
- **Deployment Time**: 10-15 minutes per deploy
- **Response Time**: 2-4 seconds per question
- **Success Rate**: 94% retrieval hit-rate

---

## Contact & Resources

- **GitHub Repository**: https://github.com/Lokeshwaran-12/AIRMAN
- **Live Demo**: https://airman-rag-app-cnbbc9dshmc3b4et.uaenorth-01.azurewebsites.net
- **API Documentation**: Add `/docs` to the URL above

---

**End of Demo Guide** ✅
