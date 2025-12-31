import json
from utils import clean_json_output, normalize_path

class Validator:
    DEFINED_TOOLS = ["LIST_FILEPATH", "CREATE_FILEPATH", "DELETE_FILEPATH", "READ_CONTENT"]
    
    @staticmethod
    def validate(expected, actual_raw):
        report = {
            "passed_all": False,
            "is_valid_json": False,
            "is_valid_schema": False,
            "checks": { "function_match": False, "param_match": False, "no_hallucination": True, "error_code_match": False },
            "diff_log": {}
        }

        # A. PARSE JSON
        try:
            cleaned_str = clean_json_output(actual_raw)
            actual_obj = json.loads(cleaned_str)
            report["is_valid_json"] = True
        except json.JSONDecodeError:
            report["diff_log"]["json"] = "Failed to parse JSON"
            return report

        # B. HANDLE ERROR ID CHECKS
        if "error_id" in expected:
            actual_error = actual_obj.get("error_id") or actual_obj.get("Output")
            if actual_error == expected["error_id"]:
                report["checks"]["error_code_match"] = True
                report["passed_all"] = True
            else:
                report["diff_log"]["error"] = f"Expected {expected['error_id']}, got {actual_error}"
            return report

        # C. HANDLE STANDARD CALLS
        if "systemCall" not in actual_obj:
            report["diff_log"]["schema"] = "Missing 'systemCall' key"
            core_response = actual_obj 
        else:
            report["is_valid_schema"] = True
            core_response = actual_obj["systemCall"]

        actual_func = core_response.get("Function used")
        actual_param = core_response.get("With parameter")
        expected_core = expected.get("systemCall", expected)

        # Check Hallucination
        if actual_func not in Validator.DEFINED_TOOLS:
            report["checks"]["no_hallucination"] = False
            report["diff_log"]["hallucination"] = f"Invented tool: {actual_func}"

        # Check Function Match
        expected_f = expected_core.get("Function used")
        if actual_func == expected_f:
            report["checks"]["function_match"] = True
        else:
            report["diff_log"]["function"] = f"Expected {expected_f}, got {actual_func}"

        # Check Parameter Match
        expected_p = expected_core.get("With parameter")
        if normalize_path(actual_param) == normalize_path(expected_p):
            report["checks"]["param_match"] = True
        else:
             report["diff_log"]["param"] = f"Expected {expected_p}, got {actual_param}"

        # Final Verdict
        if (report["is_valid_json"] and report["checks"]["no_hallucination"] and 
            report["checks"]["function_match"] and report["checks"]["param_match"]):
            report["passed_all"] = True

        return report