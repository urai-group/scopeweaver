Here is a highly compressed version of your documentation. I have removed conversational filler, condensed explanations, and formatted it for maximum token efficiency while retaining all technical requirements, prompts, and logic.

---

# PROJECT: CHRISTMASWEAVER

**Objective:** Build working AI agent prototypes (Single & Multi-agent) by January.

**Why a document?**

1. Repository documentation.
2. Scientific report basis.
3. Enterprise outreach materials.
4. Container for UML, pseudocode, and tests.

**Priority (V1 Prototype):**

1. Define Tools (Functions).
2. Create Tests (Manual + LLM-generated).
3. Iterate System Prompt until Tests pass.
4. Proceed to V2 (2-agent system).

---

## Part I: Envisioned Prototypes

**Strategy:** Textual Input/Output (log-only). No custom training; use Prompt Engineering (Ollama/Deepseek).

### Version 1: Single Agent (Baseline)

**Architecture:** Single LLM pass. Interprets raw input → Selects system call.

* **Input:** Raw text (User Request).
* **Processor:** LLM + System Prompt.
* **Output:** JSON System Call.

### Version 2: Multi-Agent (Chain of Thought)

**Architecture:** Split responsibility.

* **Stage 1 (Pre-Processor):** Cleans/Parses input into structured format. (Surface Knowledge).
* **Stage 2 (Decision Maker):** Maps structure to specific API calls. (Deep Knowledge).

### Testing Suite: Validation Logic

**Goal:** Compare Model Output vs. Ground Truth (Expected JSON).
**Metrics:** Accuracy, Latency, Token Count, Memory.

---

## Part II: Concrete TODOs

**Constraint:** Output is **JSON logs only**. No actual file system execution.
**Reason:** Focus is on deriving the correct System Prompt logic, not OS implementation.

### Agent Tools (System Calls)

*Implementation Note: Tools should return strings for the Output log.*

#### 1. LIST_FILEPATH

* **Desc:** List file/folder contents.
* **Logic:** Input `path`. If .txt → Output name. If folder → Output contents. Else → Error.
* **Target Output:** JSON dictionary containing `User input`, `Function used`, `With parameter`, `Output`.

#### 2. CREATE_FILEPATH

* **Desc:** Log creation of file.
* **Logic:** Input `path`. Infer file vs folder based on trailing slash/extension.

#### 3. DELETE_FILEPATH

* **Desc:** Log deletion of file.
* **Logic:** Input `path`. Verify existence (mock).

#### 4. READ_CONTENT

* **Desc:** Return text content of file.
* **Logic:** Input `path`. If .txt → Output content string. If folder → Error.

#### Proposals (Backlog)

* **MODIFY_FILENAME:** Rename/Move.
* **COPY/PASTE:** File duplication.
* **COMPRESS_FILEPATH:** Zip/Tar logic.

---

## Part III: Future Roadmap

1. **Folder Structure Context:** Inject file tree JSON into context.
2. **Visual Frontend:** Real-time traversal visualization.

---

## APPENDIX: UML & Prompts

### Version 1 Architecture (PlantUML)

```plantuml
left to right direction
rectangle "Input.txt" as Input <<InputOutput>>
rectangle "Output.txt" as Output <<InputOutput>>
package "Processing Block" {
    rectangle "LLM Agent" as LLM <<Agent>>
    rectangle "System Prompt\n(System Call Knowledge)" as Context
}
Input --> LLM : User Request
Context .> LLM
LLM --> Output : Generates Call

```

### Version 2 Architecture (PlantUML)

```plantuml
left to right direction
rectangle "Input.txt" as Input
rectangle "Output.txt" as Output
rectangle "InterOutput (JSON)" as Inter
package "Stage 1" {
    rectangle "Structurer" as Struct <<Agent>>
}
package "Stage 2" {
    rectangle "Expert" as Expert <<Agent>>
}
Input --> Struct : Raw
Struct --> Inter : Clean
Inter --> Expert : Data
Expert --> Output : Final

```

### System Prompts

#### Baseline A: Zero-Shot

`Assign the correct system call among: LIST_FILEPATH, CREATE_FILEPATH, DELETE_FILEPATH, READ_CONTENT. Output only function name and parameter.`

#### Baseline B: Full Documentation

`You are an AI file manager. Read the following documentation and execute the request by outputting the correct JSON system call. [INSERT FULL DOCS]`

#### V1 System Prompt: "The Solo Weaver"

```text
[SYSTEM PROMPT — CHRISTMASWEAVER V1]
Mission: Translate raw text to executable JSON system call.
RULES:
1. LOGS ONLY: Write INTENT to JSON. Do not execute.
2. FORMAT: Valid JSON only. No prose.
3. SINGLE CALL: Prioritize primary request.
4. EXTENSIONS: Only support .txt.

WORKFLOW:
1. FILTER NOISE.
2. EXTRACT PATH (Append .txt if missing).
3. CLASSIFY:
   - LIST (show/what's in)
   - CREATE (make/save)
   - DELETE (remove)
   - READ (open/content)

OUTPUT TEMPLATE:
{ "systemCall": { "User input": "...", "Function used": "...", "With parameter": "...", "Output": "...", "Id": "..." } }

```

#### V2 System Prompt: Stage 1 (Parser)

```text
[SYSTEM PROMPT — V2 PARSER]
Job: Turn speech into Clean Data.
Tasks: Strip noise, Identify VERB and OBJECT.
Output: {"action": "verb", "target": "path"}

```

#### V2 System Prompt: Stage 2 (Classifier)

```text
[SYSTEM PROMPT — V2 CLASSIFIER]
Job: Map Clean Data to System Call.
Tasks: Validate file/folder logic. Return FINAL JSON.

```

---

## Testing Suite Structure

### Categories

1. **BSFI (Baseline Single Function):**
* **SF (Straightforward):** Perfect syntax.
* **PW (Poorly Worded):** Recoverable typos vs. Unrecoverable missing info.


2. **BMFI (Baseline Multi Function):**
* **OI (Order Independent):** Parallel tasks.
* **OD (Order Dependent):** Chains (e.g., List then Read).


3. **BA (Bad Actor):**
* **MI (Misinformed):** Invalid targets (e.g., read image).
* **MA (Malicious):** System attacks (e.g., delete root).


4. **SI (System Integrity):**
* **FC (Format Compliance):** JSON validity check.
* **HA (Hallucination):** Inventing non-existent tools.



### Validation Logic (Pseudocode)

```python
# CONFIG
TOOLS = ["LIST_FILEPATH", "CREATE_FILEPATH", "DELETE_FILEPATH", "READ_CONTENT"]

class Validator:
    def compare(expected, actual_str):
        report = {
            "passed": False, 
            "valid_json": False, 
            "valid_schema": False,
            "correct_func": False, 
            "correct_param": False,
            "hallucination": False
        }

        # 1. JSON Check
        try:
            actual = json.loads(actual_str)
            report["valid_json"] = True
        except: return report

        # 2. Schema Check
        if "systemCall" in actual: report["valid_schema"] = True
        core = actual.get("systemCall", {})

        # 3. Hallucination Check
        if core["Function used"] in TOOLS: report["hallucination"] = False
        
        # 4. Logic Check
        if core["Function used"] == expected["Function used"]: report["correct_func"] = True
        if normalize(core["With parameter"]) == normalize(expected["With parameter"]): 
            report["correct_param"] = True

        if all(report.values()): report["passed"] = True
        return report

# EXECUTION
for test in SUITE:
    response = LLM.call(system_prompt, test.input)
    stats = Validator.compare(test.expected, response)
    log_results(stats)

```