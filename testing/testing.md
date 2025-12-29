# ScopeWeaver Testing Suite

> **Documentation Path:** `Testing Suite · urai-group/scopeweaver · Discussion #6`

This repository maintains the standardized test suite for the File System Agent. The tests are designed to cover performance benchmarking, ambiguity resolution, safety guardrails, and system integrity.

## 1. Test Classification Tree

All tests are organized into four major buckets (Categories), each with their own types (and sub-types), to be denoated in the json as "type-subtype"

### [BSFI] Baseline Single Function Input
Tests the model's ability to handle the atomic unit of work: a request with a single tool usage.
* **[SF] Straightforward:** The "Happy Path". Used to establish baseline latency and token usage.
* **[PW] Poorly Worded:**
    * **[RE] Recoverable:** Messy syntax (missing extensions), but intent is clear.
    * **[UR] Unrecoverable:** Critical info missing (e.g., "Delete the file" with no path).

### [BMFI] Baseline Multiple Function Input
Tests the model's ability to parse complex or compounded requests.
* **[SF] Straightforward:**
    * **[OI] Order-Independent:** Parallel actions (e.g., "Delete A and create B").
    * **[OD] Order-Dependent:** Chains where Action B relies on Action A (e.g., "List... then read").
* **[PW] Poorly Worded:**
    * **[RE] Recoverable:** Ambiguous references (e.g., "...and read the config one").
    *   **[OI]**
    *   **[OD]**
    * **[UR] Unrecoverable:** Impossible logic chains.

### [BA] Bad Actor & Boundary Testing
Tests the safety and constraints of the system.
* **[MI] Misinformed:**
    * **[RE] Recoverable:** Wrong verb usage (e.g., "Read folder").
    * **[UR] Unrecoverable:** Wrong type usage (e.g., "Read image").
* **[MA] Malicious:**
    * **[UR] Unrecoverable:** Safety violations (e.g., "Delete /System32/").

### [SI] System Integrity
Tests compliance with the technical interface.
* **[FC] Format Compliance:** Handling "Chatty" inputs/outputs (prose surrounding JSON).
* **[HA] Hallucination Check:** Ensuring the model does not invent tools (e.g., `RENAME_FILE`).

---

## 2. Agent Tools (System Calls)

The following functions are defined for the agent and supported by the current test suite:

1.  **LIST_FILEPATH**

2.  **READ_CONTENT**

3.  **CREATE_FILEPATH**

4.  **DELETE_FILEPATH**

5.  **COMPRESS_FILEPATH**

*Note: Future tools (Modify, Copy, Paste) are currently in Proposals/Backlog.*

Check the Testing Suite discussion for the up-to-date documentation of the Tools

---

## 3. Adding New Tests

To add a new test, follow the workflow below:

1.  **Pick a Problem Branch:** Identify the feature or bug you are working on, or come up with a scenario from scratch
2.  **Identify the Leaf:** Consult the Classification Tree above to determine where the test belongs (e.g., Is it a `BA` [Bad Actor] issue regarding a `MI` [Misinformed] input?).
3.  **Add to JSON:** Navigate to the corresponding JSON file in the folder structure and append your test case.
4.  **Label:** Ensure the test is labeled with the correct Category and Type ID.

---

## 4. Testing Suite Code

TODO >> check pseudocode in Testing Suite discussion
