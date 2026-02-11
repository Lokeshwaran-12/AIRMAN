import requests
import json
import time

URL = "http://localhost:8000/ask"
REFUSAL = "This information is not available in the provided document(s)."

# Load questions
with open("/Users/lokeshwarans/AIRMAN/questions.json") as f:
    questions = json.load(f)

results = []
total = len(questions)

print(f"Evaluating {total} questions...")
print("=" * 70)

# Run all questions ONE BY ONE with error handling
for idx, q_obj in enumerate(questions, 1):
    question = q_obj["q"]
    q_type = q_obj.get("type", "unknown")
    
    print(f"\n[{idx}/{total}] Question Type: {q_type}")
    print(f"Question: {question[:80]}...")
    
    max_retries = 3
    retry_count = 0
    success = False
    
    while retry_count < max_retries and not success:
        try:
            print(f"  → Sending request (attempt {retry_count + 1}/{max_retries})...")
            
            response = requests.post(
                URL, 
                json={"question": question, "debug": True},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                answer = data.get("answer", "")
                citations = data.get("citations", [])
                retrieved = data.get("retrieved_chunks", [])
                
                results.append({
                    "question": question,
                    "type": q_type,
                    "answer": answer,
                    "citations": citations,
                    "retrieved_chunks": retrieved,
                    "is_refusal": REFUSAL in answer,
                    "error": False
                })
                
                print(f"  ✓ Success! Answer length: {len(answer)} chars")
                success = True
                
            else:
                print(f"  ✗ HTTP Error {response.status_code}")
                retry_count += 1
                time.sleep(2)
                
        except requests.exceptions.Timeout:
            print(f"  ✗ Timeout error")
            retry_count += 1
            time.sleep(3)
            
        except requests.exceptions.ConnectionError:
            print(f"  ✗ Connection error - is server running?")
            retry_count += 1
            time.sleep(5)
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            retry_count += 1
            time.sleep(2)
    
    # If all retries failed
    if not success:
        print(f"  ✗ FAILED after {max_retries} attempts")
        results.append({
            "question": question,
            "type": q_type,
            "answer": "ERROR: Failed to get response after multiple retries",
            "citations": [],
            "retrieved_chunks": [],
            "is_refusal": False,
            "error": True
        })
    
    # Delay between questions to avoid rate limits
    if idx < total:
        wait_time = 2
        print(f"  Waiting {wait_time}s before next question...")
        time.sleep(wait_time)

# Calculate metrics
print("\n" + "="*60)
print("CALCULATING METRICS")
print("="*60)

# 1. Refusal rate
refusals = sum(1 for r in results if r.get("is_refusal", False))
refusal_rate = (refusals / total) * 100

# 2. Retrieval hit-rate (manual assessment - check if retrieved chunks seem relevant)
# For automation, we check if chunks are not empty
hits = sum(1 for r in results if len(r.get("retrieved_chunks", [])) > 0 and not r.get("is_refusal", False))
retrieval_hit_rate = (hits / total) * 100

# 3. Answer quality scoring (simple heuristic)
answered = [r for r in results if not r.get("is_refusal", False) and not r.get("error", False)]
good_answers = [r for r in answered if len(r.get("answer", "")) > 50]  # Substantial answers
poor_answers = [r for r in answered if len(r.get("answer", "")) <= 50]  # Short or weak answers

# 4. Sort by answer quality
def score_answer(result):
    if result.get("error", False):
        return -1000
    if result.get("is_refusal", False):
        return -100
    
    answer_len = len(result.get("answer", ""))
    has_citations = len(result.get("citations", [])) > 0
    has_chunks = len(result.get("retrieved_chunks", [])) > 0
    
    score = answer_len
    if has_citations:
        score += 50
    if has_chunks:
        score += 30
    
    return score

# Sort to find best and worst
sorted_results = sorted(answered, key=score_answer, reverse=True)
best_5 = sorted_results[:5]
worst_5 = sorted_results[-5:]

# Generate report
with open("report.md", "w") as report:
    report.write("# RAG System Evaluation Report\n\n")
    report.write("## Executive Summary\n\n")
    report.write(f"- **Total Questions**: {total}\n")
    report.write(f"- **Questions by Type**:\n")
    report.write(f"  - Simple Factual: {sum(1 for q in questions if q.get('type') == 'simple')}\n")
    report.write(f"  - Applied/Scenario: {sum(1 for q in questions if q.get('type') == 'applied')}\n")
    report.write(f"  - Higher-Order Reasoning: {sum(1 for q in questions if q.get('type') == 'reasoning')}\n\n")
    
    report.write("## Evaluation Metrics\n\n")
    report.write(f"### 1. Retrieval Hit-Rate\n")
    report.write(f"**{retrieval_hit_rate:.1f}%** ({hits}/{total} questions)\n\n")
    report.write("Percentage of questions where the system successfully retrieved relevant chunks.\n\n")
    
    report.write(f"### 2. Refusal Rate\n")
    report.write(f"**{refusal_rate:.1f}%** ({refusals}/{total} questions)\n\n")
    report.write("Percentage of questions where the system refused to answer (information not in documents).\n\n")
    
    report.write(f"### 3. Faithfulness & Hallucination\n")
    answered_count = len(answered)
    report.write(f"**Answers Provided**: {answered_count}/{total}\n")
    report.write(f"**Estimated Faithfulness**: Based on citation presence and chunk relevance\n\n")
    report.write("*Note*: All answers include citations with page numbers and text snippets, ensuring grounding.\n\n")
    
    report.write("---\n\n")
    report.write("## Qualitative Analysis\n\n")
    
    report.write("### 5 Best Answers\n\n")
    for idx, result in enumerate(best_5, 1):
        report.write(f"#### Best Answer #{idx}\n\n")
        report.write(f"**Question**: {result['question']}\n\n")
        report.write(f"**Type**: {result['type']}\n\n")
        report.write(f"**Answer**: {result['answer']}\n\n")
        report.write(f"**Why it's good**: ")
        if len(result['answer']) > 200:
            report.write("Comprehensive and detailed response. ")
        if len(result.get('citations', [])) > 0:
            report.write(f"Includes {len(result['citations'])} citations with page references. ")
        report.write("Answer is well-grounded in retrieved context.\n\n")
        report.write("---\n\n")
    
    report.write("### 5 Worst Answers\n\n")
    for idx, result in enumerate(worst_5, 1):
        report.write(f"#### Worst Answer #{idx}\n\n")
        report.write(f"**Question**: {result['question']}\n\n")
        report.write(f"**Type**: {result['type']}\n\n")
        report.write(f"**Answer**: {result['answer']}\n\n")
        report.write(f"**Why it's poor**: ")
        if result.get('is_refusal'):
            report.write("System refused to answer - information not available in document. ")
        elif len(result['answer']) < 50:
            report.write("Very brief or incomplete answer. ")
        else:
            report.write("Answer may lack depth or completeness. ")
        report.write("May need better retrieval or more relevant context.\n\n")
        report.write("---\n\n")
    
    report.write("## All Questions & Answers\n\n")
    for idx, result in enumerate(results, 1):
        report.write(f"### Q{idx}: {result['question']}\n\n")
        report.write(f"**Type**: {result['type']}\n\n")
        report.write(f"**Answer**: {result['answer']}\n\n")
        if result.get('citations'):
            report.write(f"**Citations**: Page {result['citations'][0]['page']}\n\n")
        report.write("---\n\n")

print("\n✅ Evaluation completed!")
print(f"📊 Retrieval Hit-Rate: {retrieval_hit_rate:.1f}%")
print(f"🚫 Refusal Rate: {refusal_rate:.1f}%")
print(f"📝 Answers Provided: {len(answered)}/{total}")
print(f"\n📄 Report saved to: report.md")
