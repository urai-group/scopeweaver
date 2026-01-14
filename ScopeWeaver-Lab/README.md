# 🧪 ScopeWeaver Lab Dashboard

**ScopeWeaver Lab** is a visual analytics dashboard designed to analyze, debug, and visualize the performance of our LLM-based agents. It transforms the raw JSON testing logs into interactive visualizations to perform Root Cause Analysis (RCA) on agent failures.

## TODOs

Feature additions/changes/fixes:

- [ ] Add back labels to multivariate flows (and add different metrics as well)
- [ ] Reinstate markdown and non markdown render in the prompt markdown visualization
- [ ] Add export for database snapshot as csv
- [ ] Right now it works with comparisons between 1/2 tests, check how it behaves for more, and fix that.

Small refactor:
- [ ] Make the app run from main.py run instead of command line
- [ ] Make the app take the default test cases directly from the test case file in `scopeweaver\Tester\tests\v1_test_cases.json`, to avoid having to upkeep the same file in different locations (right now, the app requires a copy of the file in the same directory)

Medium refactor:
- [ ] Incorporate test editing, system prompt iteration, and testing itself within the visualization (therefore have the python app add/remove/edit files in your file system)

Big refactor
- [ ] All the above, but everything should be on shared ("cloud") resources (with the necessary  checks/handling, and version control).

---

## 📂 Expected File Structure

The tool consists of a single Python script (`app.py`) which reads from folders containing specific JSON result files of `scopeweaver/Tester` runs given Prompt and Test pairs.

```text
ScopeWeaver-Lab/
├── tests/                   # Folder containing all test runs with corresponding system prompt
│   ├── test_run_1/          # Folder containing a json file and a markdown file
│   │   ├── results_deep_dive_rich.json
│   │   └── system_prompt_used.md
│   ├── test_run_2/          # Same as above
│   └── ...                  # ...
├── app.py             # The Streamlit Application
├── README.md                # This file
├── requirements.txt         # Dependencies
└── v1_test_cases.json                # This file
```

---

## 🚀 Features & Interface

The application is divided into 7 core tabs to handle different layers of analysis (You can also load different tests, and focus on a specific one through the side panel):

### 1. 📈 KPIs
* **High-Level Summary:** A comparison table showing Pass Rates, Average Latency, and Total Cost across selected runs.
* **Grid Breakdown:** A discrete color-coded grid that breaks down pass rates by `Category` and `Test Type`. It highlights success in green and failure in red, allowing you to instantly spot specific subgroups that are underperforming.

### 2. 📊 Comparative Viz
* **Tool Confusion Matrix:** A heat-mapped matrix (small multiples) that compares `Expected Tool` vs. `Actual Tool`. Use this to spot when the model uses the wrong tool or hallucinates non-existent functions.
* **Pipeline of Failure (Sankey):** A flow diagram tracking exactly *where* tests drop off. It visualizes the funnel:
    * `JSON Parsing` ➝ `Schema Validation` ➝ `Hallucination Check` ➝ `Logic/Parameter Check`.

### 3. 🧬 Input Analysis
* **Scatter Explorer:** Interactive scatter plots to correlate input complexity (e.g., token count, special characters) against performance metrics (latency, cost).
* **Multivariate Flow (Parallel Coordinates):** A complex flow chart connecting multiple dimensions (using color to distinguish different test runs). It traces relationships between input complexity, token usage, latency, and total costs.

### 4. 🔎 Single Inspector
* **Hierarchical Flows:**
    * **Sunburst Chart:** A radial view of the test hierarchy (`Category` ➝ `Type` ➝ `Status`).
    * **Sankey:** Traces the flow of specific tests.
* **Deep Dive Explorer:** A granular list of every test case. Click to expand and view the **raw LLM JSON output**, detailed error logs, performance stats, and full record details.

### 5. 🗄️ Global Error DB
* **Filterable Database:** A master view of all tests across all loaded runs.
* **Custom Coloring:** Toggle row coloring by Status (Pass/Fail), Category, or Run ID to visually scan large datasets for patterns.
* **Filtering:** Multi-select filters for specific Run IDs, Statuses, or Error Types (e.g., "Show me all `Hallucination` errors in `Run A`").
* **TODO:** New filtering options, csv exporting.

### 6. 🐞 Error Artifacts
* **Artifact Inspector:** A focused view that only shows failed tests.
* **JSON Dumps:** Provides immediate access to the full JSON payload of failed tests, making it easier to copy/paste error cases for debugging or regression testing.

### 7. 📝 Prompts
* **Diff Viewer:** Highlights added/removed lines in (git-like) green/red, helping you correlate changes in your prompt engineering with changes in performance.
* **System Prompt Diff:** Proposes both system prompts used in different runs.

---

## 🛠️ Installation

1. **Install Dependencies:** Run the following command in your terminal:

```bash
pip install -r requirements.txt
```

---

## 📊 How to Run

1. Ensure any new test results and system prompts are added accordingly (no problem if you're cloning the repository or pulling the folder directly).
2. Launch the dashboard:

```bash
streamlit run dashboard.py
```

3. The dashboard will open in your default web browser (`http://localhost:8501`).

---

## 📝 Input Data Format

The dashboard expects `results_deep_dive.json` to be a list of objects with the following schema:

```json
[
  {
    "id": "BSFI-LIST-001",
    "category": "BSFI",
    "type": "SF",
    "rank": "Easy",
    "passed": true,
    "errors": {
      "passed_all": true,
      "is_valid_json": true,
      "is_valid_schema": true,
      "checks": {
        "function_match": true,
        "param_match": true,
        "no_hallucination": true,
        "error_code_match": false
      },
      "diff_log": {}
    },
    "raw_output": "```json\n{ \"systemCall\": { \"User input\": \"what files are there at filepath user/folder/\", \"Function used\": \"LIST_FILEPATH\", \"With parameter\": \"user/folder/\", \"Output\": \"Error: Path is a folder, cannot list contents directly.\", \"Id\": \"1\" } }\n```",
    "perf": {
      "latency": 9.5455,
      "total_time_elapsed": 9.5455,
      "total_tokens": 1954
    },
    "input_metrics": {
      "char_count": 7049,
      "char_count_no_space": 5758,
      "word_count": 925,
      "special_char_percent": 14.46,
      "token_count": 1885
    },
    "output_metrics": {
      "char_count": 243,
      "char_count_no_space": 210,
      "word_count": 34,
      "special_char_percent": 20.58,
      "token_count": 69
    },
    "cost": {
      "currency": "USD",
      "inference_cost": 0.0,
      "output_cost": 0.0,
      "total_cost": 0.0
    }
  }  
]

```
