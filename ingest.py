import os
import pickle
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from rank_bm25 import BM25Okapi

PDF_PATH = "/Users/lokeshwarans/AIRMAN/data/Instruments.pdf"
VECTOR_DIR = "vectorstore"

os.makedirs(VECTOR_DIR, exist_ok=True)

model = SentenceTransformer("all-MiniLM-L6-v2")

# 1. Load PDF
reader = PdfReader(PDF_PATH)
pages = []

for i, page in enumerate(reader.pages):
    text = page.extract_text()
    if text:
        pages.append({"page": i+1, "text": text})

# 2. Chunking
def chunk_text(text, size=500, overlap=100):
    words = text.split()
    chunks = []
    for i in range(0, len(words), size-overlap):
        chunk = " ".join(words[i:i+size])
        chunks.append(chunk)
    return chunks

chunks = []
metadata = []

for p in pages:
    chs = chunk_text(p["text"])
    for c in chs:
        chunks.append(c)
        metadata.append({"page": p["page"]})

# 3. Embeddings
embeddings = model.encode(chunks)

# 4. FAISS
dim = embeddings.shape[1]
index = faiss.IndexFlatL2(dim)
index.add(np.array(embeddings))

faiss.write_index(index, f"{VECTOR_DIR}/index.faiss")

# 5. BM25 Index (for Level 2 - Hybrid Retrieval)
print("Creating BM25 index...")
tokenized_chunks = [chunk.lower().split() for chunk in chunks]
bm25 = BM25Okapi(tokenized_chunks)

with open(f"{VECTOR_DIR}/chunks.pkl", "wb") as f:
    pickle.dump({"chunks": chunks, "meta": metadata}, f)

with open(f"{VECTOR_DIR}/bm25.pkl", "wb") as f:
    pickle.dump(bm25, f)

print("✅ Ingestion completed (Vector + BM25 indexes created).")
