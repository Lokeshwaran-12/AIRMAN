import os
import pickle
import faiss
import numpy as np
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from openai import AzureOpenAI
import time
from rank_bm25 import BM25Okapi
import logging
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()
logger.info("Application starting...")

REFUSAL = "This information is not available in the provided document(s)."

VECTOR_DIR = "vectorstore"
os.makedirs(VECTOR_DIR, exist_ok=True)

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-02-15-preview"
)

DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

embedding_client = AzureOpenAI(
    api_key=os.getenv("AZURE_EMBEDDING_KEY") or os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-02-15-preview"
)

EMBEDDING_DEPLOYMENT = "text-embedding-3-small"

def get_embeddings(texts):
    """Get embeddings from Azure OpenAI with batching and rate limiting"""
    all_embeddings = []
    batch_size = 10  # Process 10 chunks at a time
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            response = embedding_client.embeddings.create(
                model=EMBEDDING_DEPLOYMENT,
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            
            # Add delay to avoid rate limit
            if i + batch_size < len(texts):
                time.sleep(1)  # Wait 1 second between batches
        except Exception as e:
            print(f"Error in batch {i}: {e}")
            # Retry with smaller batch or individual items
            for text in batch:
                time.sleep(0.5)
                response = embedding_client.embeddings.create(
                    model=EMBEDDING_DEPLOYMENT,
                    input=[text]
                )
                all_embeddings.append(response.data[0].embedding)
    
    return np.array(all_embeddings)

app = FastAPI()

index = None
chunks = []
meta = []
bm25 = None  # BM25 index for Level 2


class Ask(BaseModel):
    question: str
    debug: bool = False
    use_hybrid: bool = False  # Level 2: Enable hybrid retrieval


# ---------------- CHUNKING ----------------

def chunk_text(text, size=400, overlap=100):
    words = text.split()
    out = []
    for i in range(0, len(words), size - overlap):
        out.append(" ".join(words[i:i + size]))
    return out


# ---------------- INGEST ----------------

@app.post("/ingest")
async def ingest_documents(file: UploadFile = File(...)):
    """
    Upload and ingest a PDF document.
    
    Args:
        file: PDF file to process
    
    Returns:
        Status with processing details
    """
    logger.info(f"Starting document ingestion for file: {file.filename}")
    global index, chunks, meta, bm25

    # Validate file type
    if not file.filename.endswith('.pdf'):
        logger.error(f"Invalid file type: {file.filename}")
        return {"status": "error", "message": "Only PDF files are supported"}

    try:
        # Read uploaded file content
        contents = await file.read()
        pdf_file = io.BytesIO(contents)
        
        # Read PDF
        reader = PdfReader(pdf_file)
        logger.info(f"Reading PDF: {file.filename} ({len(reader.pages)} pages)")

        pages = []
        for i, p in enumerate(reader.pages):
            t = p.extract_text()
            if t:
                pages.append({"page": i + 1, "text": t})

        chunks = []
        meta = []

        for p in pages:
            for c in chunk_text(p["text"]):
                chunks.append(c)
                meta.append({"page": p["page"]})

        embeddings = get_embeddings(chunks)

        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(np.array(embeddings))

        faiss.write_index(index, f"{VECTOR_DIR}/index.faiss")

        # Level 2: Create BM25 index
        tokenized_chunks = [chunk.lower().split() for chunk in chunks]
        bm25 = BM25Okapi(tokenized_chunks)
        
        with open(f"{VECTOR_DIR}/chunks.pkl", "wb") as f:
            pickle.dump({"chunks": chunks, "meta": meta}, f)
        
        with open(f"{VECTOR_DIR}/bm25.pkl", "wb") as f:
            pickle.dump(bm25, f)

        logger.info(f"Ingestion completed: {len(pages)} pages, {len(chunks)} chunks")
        return {
            "status": "success", 
            "filename": file.filename,
            "pages": len(pages), 
            "chunks": len(chunks), 
            "bm25_created": True
        }
    
    except Exception as e:
        logger.error(f"Error during ingestion: {str(e)}")
        return {"status": "error", "message": str(e)}


# ---------------- HEALTH ----------------

@app.get("/health")
def health():
    logger.debug("Health check requested")
    return {"status": "ok"}


# ---------------- LEVEL 2: HYBRID RETRIEVAL ----------------

def hybrid_retrieve(question, top_k=20, final_k=8):
    """
    Level 2: Hybrid Retrieval with BM25 + Vector + Azure Embedding Reranker
    
    Args:
        question: User query
        top_k: Number of candidates to retrieve from each method
        final_k: Number of chunks to return after reranking
    
    Returns:
        List of chunk indices
    """
    global index, chunks, meta, bm25
    
    # 1. Vector Search (LEVEL 1 baseline)
    q_emb = get_embeddings([question])
    D, I = index.search(q_emb, top_k)
    vector_results = set(I[0].tolist())
    
    # 2. BM25 Keyword Search (LEVEL 2)
    tokenized_query = question.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)
    bm25_top_indices = np.argsort(bm25_scores)[-top_k:][::-1]
    bm25_results = set(bm25_top_indices.tolist())
    
    # 3. Combine candidates (union of both methods)
    combined_indices = list(vector_results.union(bm25_results))
    
    # 4. Rerank using Azure Embeddings (LEVEL 2)
    # Get embeddings for candidate chunks
    candidate_chunks = [chunks[idx] for idx in combined_indices]
    
    # Compute embeddings for candidates (in batches to handle rate limits)
    candidate_embeddings = get_embeddings(candidate_chunks)
    
    # Compute cosine similarity between query and each candidate
    q_emb_normalized = q_emb / np.linalg.norm(q_emb)
    candidate_embeddings_normalized = candidate_embeddings / np.linalg.norm(candidate_embeddings, axis=1, keepdims=True)
    
    # Cosine similarity scores
    rerank_scores = np.dot(candidate_embeddings_normalized, q_emb_normalized.T).flatten()
    
    # Sort by reranking score
    ranked = sorted(
        zip(combined_indices, rerank_scores),
        key=lambda x: x[1],
        reverse=True
    )
    
    # Return top final_k
    return [idx for idx, score in ranked[:final_k]]


# ---------------- ASK ----------------

@app.post("/ask")
def ask(data: Ask):
    logger.info(f"Question received: {data.question[:50]}... (hybrid={data.use_hybrid})")
    global index, chunks, meta, bm25

    if index is None:
        logger.warning("Documents not ingested - cannot answer")
        return {"answer": "Documents not ingested yet."}

    # LEVEL 2: Use hybrid retrieval if enabled
    if data.use_hybrid and bm25 is not None:
        logger.info("Using Level 2 hybrid retrieval")
        retrieved_indices = hybrid_retrieve(data.question, top_k=20, final_k=8)
        retrieved = [chunks[i] for i in retrieved_indices]
        retrieved_meta = [meta[i] for i in retrieved_indices]
        retrieval_method = "hybrid"
    else:
        logger.info("Using Level 1 vector-only retrieval")
        # LEVEL 1: Vector-only retrieval (baseline)
        q_emb = get_embeddings([data.question])
        D, I = index.search(q_emb, 8)
        
        # FAISS distance guard
        if D[0][0] > 1.5:
            logger.info(f"Distance threshold exceeded: {D[0][0]} > 1.5, refusing answer")
            return {"answer": REFUSAL}
        
        retrieved = [chunks[i] for i in I[0]]
        retrieved_meta = [meta[i] for i in I[0]]
        retrieval_method = "vector-only"

    context = "\n\n".join(retrieved)

    prompt = f"""
You are a strict aviation document assistant.

Use ONLY the context.

If answer is not present reply exactly:
{REFUSAL}

Context:
{context}

Question:
{data.question}
"""

    response = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response.choices[0].message.content.strip()

    if REFUSAL in answer:
        logger.info("LLM returned refusal message")
        return {"answer": REFUSAL}

    logger.info(f"Answer generated successfully using {retrieval_method}")
    citations = []
    for i in range(3):
        citations.append({
            "page": retrieved_meta[i]["page"],
            "snippet": retrieved[i][:200]
        })

    result = {
        "answer": answer, 
        "citations": citations,
        "retrieval_method": retrieval_method  # Level 1 vs Level 2 indicator
    }

    if data.debug:
        result["retrieved_chunks"] = retrieved[:3]

    return result
