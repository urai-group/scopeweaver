# 🧪 ScopeWeaver Lab Dashboard

**ScopeWeaver Lab** is a visual analytics dashboard designed to analyze, debug, and visualize the performance of our LLM-based agents. It transforms the raw JSON testing logs into interactive visualizations to perform Root Cause Analysis (RCA) on agent failures.

---

## 🚀 Features

* **Pipeline of Failure (Sankey):** Visualize exactly where and how many tests drop off (be it for JSON parsing, Schema Validation, Hallucination, Logic).
* **Component Analysis:** Toggle between Stacked and Grouped bar charts (by category, type and rank) to dissect failure rates by subcategory.
* **Failure Heatmaps:** Intensity grids to spot hotspots of failure across different error types.
* **Confusion Matrix:** Toggle to analyze tool usage confusion and error type.
* **Hierarchy:** Toggle to analyze overall sunburst based on broad test category performance, and detailed test performance throug Sankey flow chart (TODO: make the sankey show the IDs of the tests in eachs section; possibly show a tooltip with the information of the granular view)
* **Deep Dive:** Granular explorer always present; click to view raw LLM inputs/outputs and detailed error logs for every test case.

---

## 📂 Expected File Structure

The tool consists of a single Python script (`dashboard.py`) which reads from a specific JSON results file.

```text
ScopeWeaver-Lab/
├── dashboard.py             # The Streamlit Application
├── results_deep_dive.json   # Input Data (The Test Results)
├── requirements.txt         # Dependencies
└── README.md                # This file

```

---

## 🛠️ Installation

1. **Install Dependencies:** Run the following command in your terminal:

```bash
pip install -r requirements.txt

```

---

## 📊 How to Run

1. Ensure the test results are saved as **`results_deep_dive.json`** in the same directory (no problem if you're cloning the repository or pulling the folder directly).
2. Launch the dashboard:

```bash
streamlit run dashboard.py

```

3. The dashboard will automatically open in your default web browser (typically at `http://localhost:8501`).

---

## 📝 Input Data Format

The dashboard expects `results_deep_dive.json` to be a list of objects with the following schema:

```json
[
  {
    "id": "TEST-001",
    "category": "BSFI",
    "type": "SF",
    "rank": "Easy",
    "passed": false,
    "raw_output": "{ ... }",
    "errors": {
      "is_valid_json": true,
      "checks": {
        "no_hallucination": false,
        "function_match": true
      },
      "diff_log": {}
    }
  }
]

```

These were produced through a testing suite which hopefully will be available shortly. 

TODO:
- [ ] Incorporate view of what System Prompt (on which API) was used to obtain the Data
- [ ] Incorporate ability to switch between different json files (corresponding to different system prompts)
- [ ] Incorporate comparisons of performance between different json files (system prompts)
- [ ] Share testing suite as well
