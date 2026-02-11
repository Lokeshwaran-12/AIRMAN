import requests
import json
import time

URL = "http://localhost:8000/ask"
REFUSAL = "This information is not available in the provided document(s)."

# Load questions
with open("/Users/lokeshwarans/AIRMAN/questions.json") as f:
    questions = json.load(f)

print("="*70)
print("LEVEL 1 vs LEVEL 2 COMPARISON EVALUATION")
print("="*70)
print(f"\nTotal Questions: {len(questions)}")
print("\nRunning both evaluations...")
print("  - Level 1: Vector-only retrieval (baseline)")
print("  - Level 2: Hybrid (BM25 + Vector + Reranker)")
print("="*70)

# Store results for both modes
results_level1 = []
results_level2 = []

# Run evaluation for LEVEL 1 (vector-only)
print("\n\n🔵 EVALUATING LEVEL 1 (Vector-Only Retrieval)")
print("-"*70)

for idx, q_obj in enumerate(questions, 1):
    question = q_obj["q"]
    q_type = q_obj.get("type", "unknown")
    
    print(f"[{idx}/{len(questions)}] {question[:60]}...")
    
    try:
        response = requests.post(
            URL, 
            json={"question": question, "debug": True, "use_hybrid": False},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            results_level1.append({
                "question": question,
                "type": q_type,
                "answer": data.get("answer", ""),
                "citations": data.get("citations", []),
                "retrieved_chunks": data.get("retrieved_chunks", []),
                "is_refusal": REFUSAL in data.get("answer", ""),
                "retrieval_method": data.get("retrieval_method", "vector-only")
            })
        else:
            results_level1.append({"question": question, "type": q_type, "error": True})
            
        time.sleep(1.5)
        
    except Exception as e:
        print(f"  Error: {e}")
        results_level1.append({"question": question, "type": q_type, "error": True})

# Run evaluation for LEVEL 2 (hybrid)
print("\n\n🟢 EVALUATING LEVEL 2 (Hybrid: BM25 + Vector + Reranker)")
print("-"*70)

for idx, q_obj in enumerate(questions, 1):
    question = q_obj["q"]
    q_type = q_obj.get("type", "unknown")
    
    print(f"[{idx}/{len(questions)}] {question[:60]}...")
    
    try:
        response = requests.post(
            URL, 
            json={"question": question, "debug": True, "use_hybrid": True},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            results_level2.append({
                "question": question,
                "type": q_type,
                "answer": data.get("answer", ""),
                "citations": data.get("citations", []),
                "retrieved_chunks": data.get("retrieved_chunks", []),
                "is_refusal": REFUSAL in data.get("answer", ""),
                "retrieval_method": data.get("retrieval_method", "hybrid")
            })
        else:
            results_level2.append({"question": question, "type": q_type, "error": True})
            
        time.sleep(1.5)
        
    except Exception as e:
        print(f"  Error: {e}")
        results_level2.append({"question": question, "type": q_type, "error": True})

# Calculate metrics for both levels
def calculate_metrics(results, level_name):
    total = len(results)
    refusals = sum(1 for r in results if r.get("is_refusal", False))
    errors = sum(1 for r in results if r.get("error", False))
    answered = [r for r in results if not r.get("is_refusal", False) and not r.get("error", False)]
    
    hits = sum(1 for r in answered if len(r.get("retrieved_chunks", [])) > 0)
    
    return {
        "level": level_name,
        "total": total,
        "answered": len(answered),
        "refusals": refusals,
        "errors": errors,
        "hits": hits,
        "refusal_rate": (refusals / total) * 100 if total > 0 else 0,
        "hit_rate": (hits / total) * 100 if total > 0 else 0,
        "answer_rate": (len(answered) / total) * 100 if total > 0 else 0
    }

metrics_l1 = calculate_metrics(results_level1, "Level 1 (Vector-Only)")
metrics_l2 = calculate_metrics(results_level2, "Level 2 (Hybrid)")

# Generate comparison report
with open("level_comparison_report.md", "w") as report:
    report.write("# Level 1 vs Level 2 - Hybrid Retrieval Comparison\n\n")
    
    report.write("## System Architecture\n\n")
    report.write("### Level 1 (Baseline): Vector-Only Retrieval\n")
    report.write("- Uses FAISS vector search with Azure OpenAI embeddings\n")
    report.write("- Retrieves top 8 chunks based on semantic similarity\n")
    report.write("- Direct passage to LLM for answer generation\n\n")
    
    report.write("### Level 2 (Enhanced): Hybrid Retrieval\n")
    report.write("- **Step 1**: Vector search (FAISS) retrieves top 20 candidates\n")
    report.write("- **Step 2**: BM25 keyword search retrieves top 20 candidates\n")
    report.write("- **Step 3**: Union of both result sets\n")
    report.write("- **Step 4**: Cross-encoder reranker scores all candidates\n")
    report.write("- **Step 5**: Top 8 reranked chunks passed to LLM\n\n")
    
    report.write("---\n\n")
    report.write("## Metrics Comparison\n\n")
    report.write("| Metric | Level 1 (Vector-Only) | Level 2 (Hybrid) | Improvement |\n")
    report.write("|--------|----------------------|------------------|-------------|\n")
    report.write(f"| Retrieval Hit-Rate | {metrics_l1['hit_rate']:.1f}% | {metrics_l2['hit_rate']:.1f}% | {metrics_l2['hit_rate'] - metrics_l1['hit_rate']:+.1f}% |\n")
    report.write(f"| Answer Rate | {metrics_l1['answer_rate']:.1f}% | {metrics_l2['answer_rate']:.1f}% | {metrics_l2['answer_rate'] - metrics_l1['answer_rate']:+.1f}% |\n")
    report.write(f"| Refusal Rate | {metrics_l1['refusal_rate']:.1f}% | {metrics_l2['refusal_rate']:.1f}% | {metrics_l2['refusal_rate'] - metrics_l1['refusal_rate']:+.1f}% |\n")
    report.write(f"| Questions Answered | {metrics_l1['answered']}/{metrics_l1['total']} | {metrics_l2['answered']}/{metrics_l2['total']} | {metrics_l2['answered'] - metrics_l1['answered']:+d} |\n\n")
    
    report.write("---\n\n")
    report.write("## Detailed Analysis\n\n")
    
    report.write("### Level 1 Performance\n")
    report.write(f"- **Retrieval Hit-Rate**: {metrics_l1['hit_rate']:.1f}%\n")
    report.write(f"- **Answered**: {metrics_l1['answered']} questions\n")
    report.write(f"- **Refused**: {metrics_l1['refusals']} questions\n")
    report.write(f"- **Errors**: {metrics_l1['errors']} questions\n\n")
    
    report.write("### Level 2 Performance\n")
    report.write(f"- **Retrieval Hit-Rate**: {metrics_l2['hit_rate']:.1f}%\n")
    report.write(f"- **Answered**: {metrics_l2['answered']} questions\n")
    report.write(f"- **Refused**: {metrics_l2['refusals']} questions\n")
    report.write(f"- **Errors**: {metrics_l2['errors']} questions\n\n")
    
    report.write("---\n\n")
    report.write("## Key Findings\n\n")
    
    if metrics_l2['hit_rate'] > metrics_l1['hit_rate']:
        improvement = metrics_l2['hit_rate'] - metrics_l1['hit_rate']
        report.write(f"✅ **Hybrid retrieval improved hit-rate by {improvement:.1f}%**\n\n")
        report.write("The combination of BM25 keyword search and cross-encoder reranking helps capture:\n")
        report.write("- Exact keyword matches that vector search might miss\n")
        report.write("- Better relevance ranking through cross-encoder scoring\n")
        report.write("- More diverse candidate pool before final selection\n\n")
    else:
        report.write("ℹ️ Hybrid retrieval showed similar performance to vector-only.\n\n")
    
    report.write("---\n\n")
    report.write("## Sample Comparison (First 5 Questions)\n\n")
    
    for i in range(min(5, len(questions))):
        report.write(f"### Question {i+1}: {questions[i]['q']}\n\n")
        report.write(f"**Type**: {questions[i].get('type', 'unknown')}\n\n")
        
        report.write(f"**Level 1 Answer** ({results_level1[i].get('retrieval_method', 'N/A')}):\n")
        report.write(f"{results_level1[i].get('answer', 'ERROR')[:300]}...\n\n")
        
        report.write(f"**Level 2 Answer** ({results_level2[i].get('retrieval_method', 'N/A')}):\n")
        report.write(f"{results_level2[i].get('answer', 'ERROR')[:300]}...\n\n")
        
        report.write("---\n\n")

print("\n\n" + "="*70)
print("EVALUATION COMPLETE")
print("="*70)
print(f"\n📊 LEVEL 1 Metrics:")
print(f"   Hit-Rate: {metrics_l1['hit_rate']:.1f}%")
print(f"   Answered: {metrics_l1['answered']}/{metrics_l1['total']}")
print(f"   Refusals: {metrics_l1['refusals']}")

print(f"\n📊 LEVEL 2 Metrics:")
print(f"   Hit-Rate: {metrics_l2['hit_rate']:.1f}%")
print(f"   Answered: {metrics_l2['answered']}/{metrics_l2['total']}")
print(f"   Refusals: {metrics_l2['refusals']}")

print(f"\n📈 Improvement:")
print(f"   Hit-Rate: {metrics_l2['hit_rate'] - metrics_l1['hit_rate']:+.1f}%")
print(f"   Answers: {metrics_l2['answered'] - metrics_l1['answered']:+d}")

print(f"\n📄 Report saved to: level_comparison_report.md")
print("="*70)
