import csv
import statistics

def calculate_stats(records_subset):
    if not records_subset:
        return None
    
    count = len(records_subset)
    passed = sum(1 for r in records_subset if r["passed"])
    
    # Calculate Averages (Safe against None)
    latencies = [r["perf"]["latency"] for r in records_subset if r["perf"]["latency"] is not None]
    avg_latency = statistics.mean(latencies) if latencies else 0
    
    # Error Breakdown
    failed_records = [r for r in records_subset if not r["passed"]]
    fail_count = len(failed_records)
    
    # Access flags safely
    json_err = sum(1 for r in failed_records if not r["errors"].get("is_valid_json", False))
    
    # Logic error = Valid JSON but wrong function choice
    logic_err = sum(1 for r in failed_records if r["errors"].get("is_valid_json") 
                    and not r["errors"]["checks"].get("function_match"))

    return {
        "count": count,
        "accuracy": (passed / count) * 100,
        "avg_latency": avg_latency,
        "json_fail_rate": (json_err / fail_count * 100) if fail_count > 0 else 0,
        "logic_fail_rate": (logic_err / fail_count * 100) if fail_count > 0 else 0
    }

def print_hierarchical_report(results_db):
    print("\n" + "="*40)
    
    # 1. GLOBAL SUMMARY
    global_stats = calculate_stats(results_db)
    print(f"=== GLOBAL ACCURACY: {global_stats['accuracy']:.1f}% ===")
    print("="*40)

    # 2. CATEGORY BREAKDOWN
    # Force everything to string to prevent 'NoneType' sorting errors
    unique_categories = sorted(list(set(str(r.get("category", "Uncategorized")) for r in results_db)))

    for cat in unique_categories:
        cat_records = [r for r in results_db if str(r.get("category", "Uncategorized")) == cat]
        stats = calculate_stats(cat_records)
        
        print(f"\n--- Category: {cat} (Acc: {stats['accuracy']:.1f}%) ---")
        
        # 3. TYPE (SUBCATEGORY) BREAKDOWN
        unique_types = sorted(list(set(str(r.get("type", "General")) for r in cat_records)))
        
        for type_sub in unique_types:
            type_records = [r for r in cat_records if str(r.get("type", "General")) == type_sub]
            t_stats = calculate_stats(type_records)
            
            print(f"   [{type_sub}] Accuracy: {t_stats['accuracy']:.1f}%")
            
            # 4. RANK BREAKDOWN
            for rank in ["Easy", "Medium", "Hard"]:
                rank_records = [r for r in type_records if str(r.get("rank", "Medium")) == rank]
                if rank_records:
                    r_stats = calculate_stats(rank_records)
                    print(f"      > {rank}: {r_stats['accuracy']:.1f}% ({r_stats['count']} tests)")

def save_to_csv(filename, results_db):
    if not results_db: return
    
    # Define CSV columns
    keys = ["id", "category", "type", "rank", "passed", "latency", "raw_output"]
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in results_db:
            # Flatten only the keys we want
            row = {
                "id": r.get("id"),
                "category": r.get("category"),
                "type": r.get("type"),
                "rank": r.get("rank"),
                "passed": r.get("passed"),
                "latency": r.get("perf", {}).get("latency", 0),
                "raw_output": r.get("raw_output")
            }
            writer.writerow(row)
    print(f"\n[INFO] Detailed results saved to {filename}")