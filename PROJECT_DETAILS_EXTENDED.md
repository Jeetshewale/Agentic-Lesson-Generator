# Autonomous Agentic Lesson Generator: Comprehensive Technical Architecture & Project Documentation

## 1. Introduction and Problem Statement
In the rapidly evolving landscape of Generative AI, traditional "single-shot" Large Language Model (LLM) applications are increasingly proving inadequate for complex, high-stakes tasks. When an LLM is asked to generate educational content, it often produces hallucinations, fails to adapt to specific pedagogical styles, or misses critical requirements outlined by the user. 

The objective of the **Agentic Lesson Generator** is to solve this problem by moving from a single-prompt paradigm to a **closed-loop Agentic Workflow**. Instead of relying on a single AI generation, this system introduces an autonomous workforce of specialized AI agents. These agents generate content, strictly evaluate it against a predefined rubric, and autonomously regenerate the content to fix identified failures before the final output is ever presented to the end user. 

Furthermore, to ensure the system is continuously improving, it is augmented with a **Reinforcement Learning (RL)** engine. This engine mathematically optimizes the prompt strategies over time, allowing the system to "learn" which teaching styles yield the highest evaluation scores.

---

## 2. High-Level System Architecture
The system is built on a modern, robust, and highly scalable technology stack divided into three distinct operational domains: Orchestration, Backend Memory/RL, and Frontend Visualization.

### 2.1 The Tech Stack
*   **Orchestration Engine:** n8n (Self-hosted via Docker)
*   **Backend API & RL Engine:** FastAPI (Python)
*   **Persistent Storage:** SQLite
*   **Frontend Dashboard:** Streamlit (Python)
*   **Inference Provider:** Groq API (Utilizing Qwen/Llama 3 models on LPUs)

### 2.2 Architectural Justification
*   **n8n over LangChain/Custom Python:** While agentic loops can be written in raw Python, handling API rate limits, complex JSON parsing, and conditional routing quickly leads to fragile "spaghetti code." n8n provides a visual, node-based graph that makes debugging agent states intuitive and natively supports enterprise-grade fault tolerance (like Auto-Retries and Wait nodes).
*   **FastAPI + SQLite:** FastAPI was selected for its asynchronous capabilities and strict type-validation via Pydantic, ensuring that the heavy mathematical computations required for the RL Bandit do not block the UI or webhook responses. SQLite was chosen over heavier databases (like PostgreSQL) because the RL state data is lightweight and file-based persistence is ideal for local, portable deployments.
*   **Groq LPU Inference:** Multi-agent workflows require the LLM to process and generate text multiple times sequentially. Using standard GPU inference would result in wait times of several minutes. Groq's Language Processing Units (LPUs) provide near-instantaneous inference, allowing the entire Generate-Evaluate-Regenerate loop to complete in under 15 seconds.

---

## 3. The Reinforcement Learning Engine (Thompson Sampling)
A critical innovation in this project is the integration of Reinforcement Learning to dynamically select the optimal prompt strategy. Rather than hardcoding a single prompt, the system tests four distinct pedagogical variants:
1.  `v1_structured`: Focuses on clear headers, bullet points, and linear progression.
2.  `v2_storytelling`: Weaves technical concepts into a relatable narrative.
3.  `v3_analogy_heavy`: Relies heavily on real-world metaphors to explain abstract concepts.
4.  `v4_socratic`: Uses guided questions to prompt the learner to think critically.

### 3.1 The Multi-Armed Bandit Algorithm
The FastAPI backend implements a **Thompson Sampling Multi-Armed Bandit** algorithm. For each prompt variant, the system maintains a Beta distribution characterized by two parameters: Alpha ($\alpha$, representing successes) and Beta ($\beta$, representing failures).

When a new request is initiated, the algorithm samples a random value from the Beta distribution of each variant. The variant with the highest sampled value is selected. This mathematical approach elegantly balances **Exploration** (trying out prompt variants that haven't been tested much) and **Exploitation** (reusing prompt variants that have historically produced the highest evaluation scores).

### 3.2 Reward Calculation and Updates
When the AI Evaluator grades a lesson, it checks it against 6 specific criteria. The backend's `/update-reward` endpoint receives this JSON evaluation and calculates a normalized float score (0.0 to 1.0) based on weighted importance. If a lesson passes 4 out of 6 checks, it might receive a score of `0.66`. This float is then used to update the $\alpha$ and $\beta$ values in the SQLite database, perpetually shifting the probability distribution.

---

## 4. Deep Dive: The n8n Agentic Workflow
The orchestration graph in n8n is the operational core of the project. It is designed to be highly resilient and fault-tolerant.

### Phase 1: Initialization and Generation
*   **Webhook Node:** The entry point. It receives a POST request from the Streamlit frontend containing the user's `topic` and the RL engine's chosen `variant`.
*   **Get RL Prompt (HTTP Request):** Queries the FastAPI backend to fetch the actual text of the chosen prompt variant.
*   **AI Generator (LLM Node):** Takes the retrieved prompt and the user's topic to generate **Draft 1**. It is instructed to return only the raw lesson text.

### Phase 2: Evaluation
*   **AI Evaluator (LLM Node):** This agent is given a strict system prompt acting as a pedagogical judge. It reads Draft 1 and evaluates it against a strict rubric. It is forced to output a JSON object containing a boolean `passed` flag and an array of `failures` (detailing exactly what was wrong and how to fix it).
*   **Compute Reward (Code Node):** A JavaScript execution node that parses the Evaluator's JSON. It calculates the total reward score. Critically, this node implements custom Regex (`/<think>[\s\S]*?(<\/think>|$)/g`) to strip out unclosed hallucination tags (common in reasoning models like Qwen) to prevent JSON parsing errors.

### Phase 3: The Decision Matrix
*   **Did it pass? (IF Node):** Evaluates if `allPassed` is true.
    *   **True Branch:** Bypasses regeneration, updates the RL backend via an HTTP Request, and returns Draft 1 to the user.
    *   **False Branch:** Routes the execution to the Regeneration phase.

### Phase 4: Regeneration (The Unrolled Loop)
To prevent catastrophic failure scenarios where two AIs get stuck in an infinite loop of failing evaluations, the workflow utilizes an **unrolled architecture**. This means the loop is laid out as a straight line, limiting the system to exactly *one* regeneration attempt.
*   **Prepare Prompt (Code Node):** Injects the failed Draft 1 and the specific JSON failure reasons into a new prompt.
*   **AI Regenerator (LLM Node):** Acting as a "Master Content Editor," this agent reads the failed draft and explicitly rewrites it to satisfy the Evaluator's previous critiques.
*   **Final Evaluation:** The new draft is evaluated one final time to compute the final reward score.

### Phase 5: Payload Aggregation and Delivery
*   **Final Response Node:** A JavaScript object is constructed that combines the polished Draft 2 with the *original* failure logs. This combined payload is sent back to Streamlit, allowing the UI to display exactly what the system fixed behind the scenes.

---

## 5. Resiliency and Error Handling Mechanisms
Autonomous agents are inherently unpredictable. To make this system production-ready, several robust engineering constraints were applied:

1.  **Rate Limit Mitigation:** Free-tier AI APIs (like Groq) easily crash under multi-agent loads (Error 429). Strategic 12-second **Wait nodes** were placed between inference steps. Additionally, LLM nodes were configured with 3x Auto-Retries and 5000ms exponential backoffs.
2.  **Unclosed Tag Handling:** Reasoning models frequently exceed their `max_tokens` limits while generating internal `<think>` processes, resulting in unclosed tags that corrupt API responses. The regex implemented in the custom Code nodes guarantees that these hallucinations are stripped even if the closing tag is missing.
3.  **Fallback Safe States:** All JavaScript Code nodes are wrapped in `try/catch` blocks. If an LLM completely fails to generate valid JSON, the catch block intercepts the crash and outputs a standardized "failed" payload (Score: 0), ensuring the workflow gracefully continues rather than terminating abruptly.

---

## 6. Frontend Visualization (Streamlit)
The Streamlit frontend serves as the control center and transparency layer for the user. 
*   **Interactive Controls:** Users input their topic and can trigger a "Deliberate Error" toggle to force the Evaluator to fail Draft 1, demonstrating the Regenerator's capabilities.
*   **The Rejection Log:** When a regeneration occurs, Streamlit parses the combined payload and generates an interactive dropdown expander titled "🚨 Rejection Log." This displays the original bad draft and the exact evaluator critiques, providing total transparency into the AI's internal reasoning process.
*   **RL Leaderboard:** A live progress bar visualizes the current win-rate of the 4 prompt variants by polling the FastAPI backend, proving that the system is actively learning.

## 7. Conclusion
The Agentic Lesson Generator is a comprehensive demonstration of advanced AI engineering. By combining visual orchestration, multi-agent evaluation, resilient error handling, and mathematical optimization via Reinforcement Learning, the system transcends basic prompt engineering to become a true, self-correcting autonomous application.
