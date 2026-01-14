# Project: ScopeWeaver

**A structured guide on how to build your own AI agent prototype.**

## Overview
ScopeWeaver is an AI prototype project designed to create a file management agentic system. The goal is to move to a working prototype while maintaining a scientific approach to summarise our documentationa and findings as research reports and articles. This project will start out exploring two architectural approaches:
1.  **Version 1:** A naive single-agent system.
2.  **Version 2:** A multi-agent system (Parser + Classifier/Ranker).

**Note:** For the moment, the system restricts output to lines in a `.txt` (JSON) log file rather than executing actual file system changes. This allows for safer testing and easier validation of the LLM's logic.

## Documentation
We have migrated our full project documentation to **GitHub Discussions** to foster collaboration. Please read the documentation in the following order:

1.  [**Start Here: Project Roadmap & Index**](https://github.com/urai-group/scopeweaver/discussions/3)
2.  [**System Architecture (V1 & V2)**](https://github.com/urai-group/scopeweaver/discussions/4)
3.  [**Agent Tools & System Calls**](https://github.com/urai-group/scopeweaver/discussions/5)
4.  [**System Prompts**](hmm)
5.  [**Testing Suite & Validation**](https://github.com/urai-group/scopeweaver/discussions/6)

## 🚀 Priority (V1 Prototype)
1.  Outline all important Tools (Functions).
2.  Create tests for those tools
3.  Iterate on a System Prompt until the LLM passes tests reliably.
4.  Document Testing results and findings.
5.  Move on to Version 2.
---

## 🤝 How to Collaborate (GitHub Beginners' Guide)

We want everyone to contribute, regardless of your coding experience! Here is a cheat sheet on how to work with this repository.

### 🧠 For Non-Coders (Documentation & Planning & Testing/SPIteration)
* **Where to work:** The **Discussions** tab.
* **What to do:**
    * Read the pinned threads to understand the architecture.
    * If you see a blank space (e.g., missing UML or Logic), write a **Comment** with your suggestion.
    * Vote on ideas using the specific reactions (👍 / 👎).
    * **Workflow:**
        1.  Open the [**Agent Tools**](LINK_TO_THREAD) discussion.
        2.  Find a tool marked `TODO` (e.g., `DELETE_FILEPATH`).
        3.  Write a comment drafting how it should work (logic inputs/outputs).

[TODO] Soonish (end of March), the code will be refactored into an interface will be  that allows real-time creation of tests and iteration of system prompt from a streamlit browser application, so you will be able to contribute to System Prompt and Test development as well.

### 💻 For Coders (Developers)
* **Where to work:** The **Code** tab (Pull Requests).
* **The Golden Rule:** **NEVER push directly to the `main` branch.** Always use a feature branch.

#### Example Workflow
1.  **Get the Code:**
    * Open your terminal/command prompt.
    * `git clone <REPO_URL>` (Download the project).
    * `cd scopeweaver`

2.  **Start a Task:**
    * `git pull origin main` (Make sure you have the latest updates).
    * `git checkout -b feature/my-new-tool` (Create a new safe space/branch to work in).

3.  **Do the Work:**
    * Write your code in your IDE (VS Code, PyCharm, etc.).
    * `git status` (Check what files you changed).
    * `git add .` (Stage all your changes).
    * `git commit -m "(for example): Added logic for DELETE_FILEPATH"` (Save your changes with a note).

4.  **Submit your Contribution:**
    * `git push origin feature/my-new-tool` (Send your branch to GitHub).
    * Go to the repository page on GitHub.
    * Click the green **"Compare & pull request"** button.
    * Wait for a review!
