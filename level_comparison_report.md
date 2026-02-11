# Level 1 vs Level 2 - Hybrid Retrieval Comparison

## System Architecture

### Level 1 (Baseline): Vector-Only Retrieval
- Uses FAISS vector search with Azure OpenAI embeddings
- Retrieves top 8 chunks based on semantic similarity
- Direct passage to LLM for answer generation

### Level 2 (Enhanced): Hybrid Retrieval
- **Step 1**: Vector search (FAISS) retrieves top 20 candidates
- **Step 2**: BM25 keyword search retrieves top 20 candidates
- **Step 3**: Union of both result sets
- **Step 4**: Cross-encoder reranker scores all candidates
- **Step 5**: Top 8 reranked chunks passed to LLM

---

## Metrics Comparison

| Metric | Level 1 (Vector-Only) | Level 2 (Hybrid) | Improvement |
|--------|----------------------|------------------|-------------|
| Retrieval Hit-Rate | 82.0% | 88.0% | +6.0% |
| Answer Rate | 82.0% | 88.0% | +6.0% |
| Refusal Rate | 4.0% | 4.0% | +0.0% |
| Questions Answered | 41/50 | 44/50 | +3 |

---

## Detailed Analysis

### Level 1 Performance
- **Retrieval Hit-Rate**: 82.0%
- **Answered**: 41 questions
- **Refused**: 2 questions
- **Errors**: 7 questions

### Level 2 Performance
- **Retrieval Hit-Rate**: 88.0%
- **Answered**: 44 questions
- **Refused**: 2 questions
- **Errors**: 4 questions

---

## Key Findings

✅ **Hybrid retrieval improved hit-rate by 6.0%**

The combination of BM25 keyword search and cross-encoder reranking helps capture:
- Exact keyword matches that vector search might miss
- Better relevance ranking through cross-encoder scoring
- More diverse candidate pool before final selection

---

## Sample Comparison (First 5 Questions)

### Question 1: What is the function of the pitot head in the pitot-static system?

**Type**: simple

**Level 1 Answer** (N/A):
ERROR...

**Level 2 Answer** (hybrid):
The pitot head houses the pitot tube and provides the location where the moving airstream is brought to rest, creating **total (pitot) pressure** – the sum of static + dynamic pressure. That pressure is then transmitted through the pitot pipelines to the air‑speed indicator, Machmeter and other inst...

---

### Question 2: List the main requirements of a pitot tube installation.

**Type**: simple

**Level 1 Answer** (N/A):
ERROR...

**Level 2 Answer** (N/A):
ERROR...

---

### Question 3: What are the requirements of a static source to ensure accurate pressure measurement?

**Type**: simple

**Level 1 Answer** (vector-only):
**Requirements of a static source for accurate pressure measurement**

- **Orientation:** The opening must be positioned **at right angles to the airflow** so that it senses only static pressure and no component of dynamic pressure.  
- **Location:** It should be placed where the airflow is **as fre...

**Level 2 Answer** (hybrid):
The static source must be mounted so that it “sees” only the ambient (static) pressure and no component of the aircraft’s dynamic pressure.  In practice this means:

* **Opening orientation** – the opening (whether a simple hole, slots or a combined pitot‑static probe) must be positioned **at right ...

---

### Question 4: Explain what position error is in a pitot-static system.

**Type**: simple

**Level 1 Answer** (vector-only):
In a pitot‑static system **position error** is the error that arises from the way the pressure head (pitot or static probe) is positioned on the aircraft. Because the opening of the probe is not always exactly at right angles to the on‑coming airflow, the sensed pressure is affected by:

* **Turbule...

**Level 2 Answer** (hybrid):
**Position error** is the pressure‑reading error that arises from the way the pitot‑static probes are positioned on the aircraft and from the aerodynamic effects around them.

- **Cause of the error** – The pressure head (pitot‑static probe) is not always perfectly aligned with the free‑stream airfl...

---

### Question 5: State two advantages of using a static vent.

**Type**: simple

**Level 1 Answer** (vector-only):
- The airflow around the static vents is less turbulent, giving a more accurate static‑pressure measurement.  
- Using static vents (especially duplicated on both sides of the fuselage) reduces errors caused by side‑slipping or yawing....

**Level 2 Answer** (hybrid):
- The airflow around a static vent is less turbulent, so the static pressure measured is more accurate.  
- Errors caused by side‑slipping or yawing are reduced (especially when static vents are duplicated on both sides of the fuselage)....

---

