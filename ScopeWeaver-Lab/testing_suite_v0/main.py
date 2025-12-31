import time
import google.generativeai as genai
import json

# Import local modules
import config
from utils import load_json_file, load_text_file
from validator import Validator
import stats

def run_test_suite():
    print(f"--- Initializing ChristmasWeaver Test Suite (Model: {config.MODEL_NAME}) ---")
    
    try:
        test_cases = load_json_file("tests/v1_test_cases.json")
        system_prompt_text = load_text_file("prompts/v1_system_prompt.md")
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        return

    # Gemma does NOT support 'system_instruction', so we configure standard generation
    model = genai.GenerativeModel(
        model_name=config.MODEL_NAME,
        generation_config={"temperature": config.TEMPERATURE}
    )

    results_db = []
    print(f"--- Loaded {len(test_cases)} entries. Starting execution... ---\n")

    for test in test_cases:
        if "id" not in test: continue

        print(f"Running {test['id']}...", end="", flush=True)
        
        max_retries = 3
        raw_output = "{}"
        call_success = False

        for attempt in range(max_retries):
            try:
                # === SPEED OPTIMIZATION ===
                # Gemma 3 Limit: 30 RPM = 1 req / 2s.
                # We use 2.2s to be fast but safe.
                time.sleep(2.2)
                
                # Manual Prompt Injection for Gemma
                full_prompt = f"{system_prompt_text}\n\nUser Input: {test['input']}"
                
                response = model.generate_content(full_prompt)
                raw_output = response.text
                call_success = True
                break 
            
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "quota" in err_msg.lower():
                    wait_time = 60 
                    print(f"\n   [!] Rate Limit Hit. Sleeping {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f" [API ERROR: {e}]", end="")
                    break 

        if not call_success:
            print(" [SKIPPED - API FAILURE]")
            continue

        # Validation
        report_card = Validator.validate(test.get('expected_json', {}), raw_output)

        # Logging
        status = "PASS" if report_card["passed_all"] else "FAIL"
        print(f" [{status}]")
        
        if not report_card["passed_all"]:
            # Truncate raw output in logs if it's huge
            short_output = (raw_output[:75] + '..') if len(raw_output) > 75 else raw_output
            # print(f"   > Output: {repr(short_output)}") # Uncomment to debug raw string
            print(f"   > Errors: {report_card['diff_log']}")

        # Store Record (Safe defaults for stats.py)
        results_db.append({
            "id": test.get("id"),
            "category": test.get("category", "Uncategorized"),
            "type": test.get("type", "General"),
            "rank": test.get("rank", "Medium"),
            "passed": report_card["passed_all"],
            "errors": report_card,
            "raw_output": raw_output,
            "perf": { "latency": 0 }
        })

    # Stats
    stats.print_hierarchical_report(results_db)
    stats.save_to_csv("final_stratified_results.csv", results_db)
    
    # === SAVING FOR DASHBOARD ===
    with open("results_deep_dive.json", "w", encoding='utf-8') as f:
        json.dump(results_db, f, indent=2)
    print("[INFO] Deep-dive data saved to results_deep_dive.json")

if __name__ == "__main__":
    run_test_suite()