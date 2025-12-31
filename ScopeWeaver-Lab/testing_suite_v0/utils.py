import json
import os
import re

def load_json_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_text_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def clean_json_output(raw_output):
    """
    Aggressively extracts JSON. Finds the first '{' and the last '}'.
    Ignores all conversational text before/after.
    """
    text = raw_output.strip()
    start_index = text.find('{')
    end_index = text.rfind('}')
    
    if start_index != -1 and end_index != -1 and end_index > start_index:
        return text[start_index : end_index + 1]
    
    return text

def normalize_path(path_str):
    """Normalizes file paths for fair comparison."""
    if not path_str: return ""
    return os.path.normpath(path_str).replace("\\", "/")