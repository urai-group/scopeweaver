import time
import google.generativeai as genai
import json
import os

# Import local modules
import config
from utils import load_json_file, load_text_file
from validator import Validator
import stats

# Try importing transformers for local token counting
try:
    from transformers import AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("[WARNING] 'transformers' library not found. Install it (`pip install transformers`) for accurate local token counting.")

# --- Helper Functions for Metrics ---

# Global cache for the tokenizer so we don't reload it every loop
_GEMMA_TOKENIZER = None

def get_tokenizer():
    """Loads and caches the Gemma tokenizer."""
    global _GEMMA_TOKENIZER
    if _GEMMA_TOKENIZER is None and TRANSFORMERS_AVAILABLE:
        try:
            # FIX: We use 'Xenova/gemma-tokenizer' instead of 'google/gemma-2b'.
            # The official Google repo is "gated" (requires login/license acceptance).
            # Xenova's repo is an official public mirror by HF staff that requires no login.
            print(" [INFO] Loading local tokenizer (Xenova/gemma-tokenizer)...")
            _GEMMA_TOKENIZER = AutoTokenizer.from_pretrained("Xenova/gemma-tokenizer")
        except Exception as e:
            print(f" [WARNING] Could not load local tokenizer: {e}")
            # Fallback to GPT-2 tokenizer (standard public one) if Xenova fails
            try:
                print(" [INFO] Falling back to GPT-2 tokenizer for estimation...")
                _GEMMA_TOKENIZER = AutoTokenizer.from_pretrained("gpt2")
            except:
                pass
    return _GEMMA_TOKENIZER

def count_tokens_locally(text):
    """Counts tokens locally using the cached tokenizer."""
    if not text:
        return 0
    tokenizer = get_tokenizer()
    if tokenizer:
        return len(tokenizer.encode(text, add_special_tokens=False))
    else:
        # Fallback: Rough estimate (4 chars per token) if transformers fails
        return len(text) // 4

def analyze_text_complexity(text):
    """Calculates granular text statistics."""
    if not text:
        return {
            "char_count": 0,
            "char_count_no_space": 0,
            "word_count": 0,
            "special_char_percent": 0.0
        }
    
    char_count = len(text)
    # Count without spaces, tabs, or newlines
    char_count_no_space = len("".join(text.split()))
    
    # Word count estimation
    word_count = len(text.split())
    
    # Count special characters (anything not alphanumeric and not whitespace)
    special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
    special_char_percent = (special_chars / char_count) * 100 if char_count > 0 else 0.0
    
    return {
        "char_count": char_count,
        "char_count_no_space": char_count_no_space,
        "word_count": word_count,
        "special_char_percent": round(special_char_percent, 2)
    }

def calculate_cost(input_tokens, output_tokens, model_name):
    """
    Calculates cost based on model pricing (USD per 1M tokens).
    Adjust rates below as needed.
    """
    # Defaults for Free Tier / Gemma on AI Studio
    cost_input_per_1m = 0.0
    cost_output_per_1m = 0.0

    # Example: If you switch to Gemini 1.5 Flash Paid
    if "flash" in model_name.lower() and "gemma" not in model_name.lower():
        cost_input_per_1m = 0.075 
        cost_output_per_1m = 0.30
    
    # Example: If you switch to Gemini 1.5 Pro Paid
    if "pro" in model_name.lower() and "gemma" not in model_name.lower():
         cost_input_per_1m = 1.25
         cost_output_per_1m = 5.00

    input_cost = (input_tokens / 1_000_000) * cost_input_per_1m
    output_cost = (output_tokens / 1_000_000) * cost_output_per_1m
    
    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost
    }

# --- Main Suite ---

def run_test_suite():
    print(f"--- Initializing ChristmasWeaver Test Suite (Model: {config.MODEL_NAME}) ---")
    
    try:
        test_cases = load_json_file(r"tests\v1_test_cases.json")
        system_prompt_text = load_text_file(r"prompts\v1_system_prompt.md")
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        return

    # Gemma configuration
    model = genai.GenerativeModel(
        model_name=config.MODEL_NAME,
        generation_config={"temperature": config.TEMPERATURE}
    )

    results_db = []
    print(f"--- Loaded {len(test_cases)} entries. Starting execution... ---\n")

    # Pre-load tokenizer to avoid delay during first test
    if TRANSFORMERS_AVAILABLE:
        get_tokenizer()

    for test in test_cases:
        if "id" not in test: continue

        print(f"Running {test['id']}...", end="", flush=True)
        
        max_retries = 3
        raw_output = "{}"
        call_success = False
        
        # Metrics placeholders
        latency = 0.0
        usage_meta = None
        full_prompt = ""

        for attempt in range(max_retries):
            try:
                # Speed Optimization / Rate Limit Handling
                time.sleep(2.2)
                
                # Construct Prompt
                full_prompt = f"{system_prompt_text}\n\nUser Input: {test['input']}"
                
                # === Start Timer ===
                t_start = time.perf_counter()
                
                response = model.generate_content(full_prompt)
                
                # === Stop Timer ===
                t_end = time.perf_counter()
                latency = t_end - t_start
                
                raw_output = response.text
                
                # Extract Google API Token counts if available
                if hasattr(response, 'usage_metadata'):
                    usage_meta = response.usage_metadata

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

        # --- Data Enrichment & Analysis ---
        
        # 1. Analyze Input (Prompt)
        input_stats = analyze_text_complexity(full_prompt)
        
        # 2. Analyze Output (Response)
        output_stats = analyze_text_complexity(raw_output)
        
        # 3. Token Counts (Hybrid: API first, Local fallback)
        in_tokens = 0
        out_tokens = 0
        total_tokens = 0

        # Try getting from API
        if usage_meta:
            in_tokens = usage_meta.prompt_token_count
            out_tokens = usage_meta.candidates_token_count
            total_tokens = usage_meta.total_token_count

        # Fallback: If API returned 0 output tokens (common with Gemma), count locally
        if out_tokens == 0:
            in_tokens = count_tokens_locally(full_prompt)
            out_tokens = count_tokens_locally(raw_output)
            total_tokens = in_tokens + out_tokens
        
        # 4. Cost Calculation
        costs = calculate_cost(in_tokens, out_tokens, config.MODEL_NAME)

        # Validation
        report_card = Validator.validate(test.get('expected_json', {}), raw_output)

        # Logging
        status = "PASS" if report_card["passed_all"] else "FAIL"
        print(f" [{status}] ({latency:.2f}s | {out_tokens} toks)")
        
        if not report_card["passed_all"]:
            # Truncate raw output in logs if it's huge
            # short_output = (raw_output[:75] + '..') if len(raw_output) > 75 else raw_output
            print(f"   > Errors: {report_card['diff_log']}")

        # Store Record
        results_db.append({
            "id": test.get("id"),
            "category": test.get("category", "Uncategorized"),
            "type": test.get("type", "General"),
            "rank": test.get("rank", "Medium"),
            "passed": report_card["passed_all"],
            "errors": report_card,
            "raw_output": raw_output,
            
            # === META INFORMATION ===
            "perf": {
                # CRITICAL: Keeping key as "latency" so stats.py does not crash
                "latency": round(latency, 4), 
                "total_time_elapsed": round(latency, 4), # Redundant but descriptive
                "total_tokens": total_tokens
            },
            "input_metrics": {
                "char_count": input_stats['char_count'],
                "char_count_no_space": input_stats['char_count_no_space'],
                "word_count": input_stats['word_count'],
                "special_char_percent": input_stats['special_char_percent'],
                "token_count": in_tokens
            },
            "output_metrics": {
                "char_count": output_stats['char_count'],
                "char_count_no_space": output_stats['char_count_no_space'],
                "word_count": output_stats['word_count'],
                "special_char_percent": output_stats['special_char_percent'],
                "token_count": out_tokens
            },
            "cost": {
                "currency": "USD",
                "inference_cost": costs['input_cost'],
                "output_cost": costs['output_cost'],
                "total_cost": costs['total_cost']
            }
        })

    # Stats
    # Ensure stats.py is robust enough to handle the data passed
    try:
        stats.print_hierarchical_report(results_db)
    except Exception as e:
        print(f"\n[ERROR] stats.py crashed: {e}")
        print("Continuing to save data...")

    stats.save_to_csv("final_stratified_results_dumb.csv", results_db)
    
    # === SAVING FOR DASHBOARD ===
    with open("results_deep_dive_all.json", "w", encoding='utf-8') as f:
        json.dump(results_db, f, indent=2)
    print("[INFO] Deep-dive data saved to results_deep_dive.json")

if __name__ == "__main__":
    run_test_suite()