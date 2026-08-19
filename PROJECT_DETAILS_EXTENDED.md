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

---

## 7. Backend Deep Dive: File-by-File Breakdown

### 7.1 `main.py` — The API Server
This is the central FastAPI server that exposes 5 endpoints (doors) for other parts of the system to communicate with:

*   **`POST /select-prompt` (The Advisor):** When n8n starts a new lesson, it knocks on this door and asks "Which teaching style should I use today?" The backend runs the Thompson Sampling math, picks the best prompt variant (e.g., Storytelling or Socratic), opens the matching prompt template file from disk, and hands it back to n8n.
*   **`POST /update-reward` (The Scorekeeper):** After the lesson is graded by the Evaluator, n8n sends the score (a float between 0.0 and 1.0) to this endpoint. The backend records this reward to make smarter prompt choices in the future.
*   **`POST /log-run` (The Diary):** Saves a permanent record of every lesson run — what topic was requested, which prompt style was used, the final score, whether it passed or failed, and how many retries were needed.
*   **`GET /stats` (The Leaderboard):** The Streamlit frontend calls this endpoint to fetch the current win-rate of each prompt variant and display them as live progress bars on the dashboard.
*   **`GET /health` (The Heartbeat):** A simple check that returns "healthy" — used to verify the server is running.

### 7.2 `rl/bandit.py` — The Reinforcement Learning Brain
This file contains the `PromptBandit` class, which implements the Thompson Sampling Multi-Armed Bandit algorithm. In simple terms, think of it like a gambler with 4 slot machines:

*   Each slot machine represents a different prompt style (Structured, Storytelling, Analogy-Heavy, Socratic).
*   Every time a machine "wins" (the lesson passes evaluation), the gambler remembers and plays that machine more often.
*   But the gambler is smart — it doesn't ONLY play the winning machine. It sometimes tries the other machines too, just in case they are secretly better. This balance between "trying new things" (Exploration) and "using what works" (Exploitation) is what makes Thompson Sampling powerful.
*   Internally, it maintains two numbers per variant: Alpha (successes) and Beta (failures). When `select_variant()` is called, it samples a random value from each variant's Beta distribution and picks the highest one. When `update()` is called with a reward, it adjusts the Alpha/Beta values accordingly.

### 7.3 `rl/reward.py` — The Score Calculator
This file takes the raw evaluation JSON from the AI Evaluator (a list of 6 rubric checkpoints, each marked as passed or failed) and converts it into a single float score between 0.0 and 1.0 using weighted averages. For example, "Accuracy" is weighted at 25% while "Teaching Flow" is weighted at 10%, so failing accuracy hurts the score much more.

### 7.4 `models/schemas.py` — The Data Validator
This file defines Pydantic models (strict data shapes) for every API request. Pydantic automatically rejects malformed data before it ever reaches the backend logic, preventing crashes. It defines schemas for `GenerateRequest`, `EvaluationResult`, and `RewardUpdate`.

### 7.5 `memory/store.py` — The Database (Filing Cabinet)
This file creates and manages a lightweight SQLite database (`memory.db`) with 2 tables:

*   **`runs` table:** Every time a lesson is generated, it saves one row containing the topic, variant ID, reward score, pass/fail status, retry count, and timestamp.
*   **`rejections` table:** Every time a lesson fails a specific checkpoint (like "too much jargon"), it saves the failure reason, the checkpoint name, and a suggestion for improvement. Each rejection is linked to a specific run via `run_id`.

---

## 8. Frontend Deep Dive: Streamlit (`app.py`)

The Streamlit frontend is the user-facing dashboard. It is built entirely in Python and serves as the control center and transparency layer:

### 8.1 Configuration and Environment Variables
The app reads `N8N_WEBHOOK_URL` and `FASTAPI_BACKEND_URL` from environment variables, falling back to `localhost` for local development. This makes the app deployment-ready without code changes.

### 8.2 Interactive Controls
*   **Topic Input Box:** A text field where the user types their desired lesson topic (e.g., "Introduction to RAG").
*   **Inject Deliberate Error Toggle:** A switch that, when turned ON, tells the AI Generator to intentionally write a bad lesson. This is used purely for demonstration purposes to showcase the regeneration loop.
*   **Generate Button:** Triggers the entire agentic pipeline by sending an HTTP POST to the n8n Webhook.

### 8.3 Lesson Display
When n8n finishes processing, the app receives the JSON payload and renders:
*   The final, polished lesson text using `st.markdown()`.
*   If the lesson was regenerated (i.e., the payload contains a `rejection_log`), it shows a clickable "🚨 Rejection Log" expander containing: the original bad first draft, the exact checkpoints that failed, and the evaluator's reasoning for each failure.

### 8.4 RL Bandit Leaderboard
On the right side of the page, Streamlit polls the FastAPI `/stats` endpoint and renders 4 live progress bars — one for each prompt variant — showing their current win-rate percentage. This visually proves that the system is learning over time.

---

## 9. Docker Setup: Why and How

### 9.1 Why Docker?
n8n is built in Node.js. Instead of installing Node.js, npm, and a bunch of dependencies directly on your computer (which could conflict with other software), Docker wraps n8n inside a completely isolated virtual container. Everything n8n needs is already inside the container — it cannot interfere with anything else on your system.

### 9.2 The `docker-compose.yml` File
This file is a recipe that tells Docker exactly how to set up n8n:
*   **Image:** Downloads the official `n8nio/n8n` image from Docker Hub.
*   **Port Mapping:** Maps port `5678` inside the container to port `5678` on your computer, so you can access the n8n dashboard via your browser.
*   **Volume Mounting:** Saves n8n's internal data (your workflows, credentials, etc.) to a folder on your computer so nothing is lost when Docker restarts.
*   **Environment Variables:** Sets `NODE_TLS_REJECT_UNAUTHORIZED=0` to fix a Windows-specific SSL certificate bug that was preventing n8n from connecting to external APIs.
*   **`WEBHOOK_URL`:** Tells n8n its own public address so webhooks can be routed correctly.

### 9.3 The `host.docker.internal` Bridge
Since n8n lives inside a Docker container and FastAPI lives outside it (on your actual computer), n8n cannot use `localhost` to reach the backend — because `localhost` inside the container refers to the container itself, not your PC. Docker provides a special hostname called `host.docker.internal` that means "talk to the computer that is running me." This is how n8n communicates with FastAPI.

### 9.4 Key Docker Commands
*   `docker-compose up -d` — Starts n8n in the background. The `-d` flag means "detached" (don't block the terminal).
*   `docker-compose down` — Stops and removes the n8n container.
*   `docker-compose logs` — View n8n's console output for debugging.

---

## 10. n8n Workflow: Node-by-Node Breakdown

### Node 1: Webhook (The Front Door)
Catches the topic and settings from Streamlit and starts the entire workflow.

### Node 2: Get RL Prompt (The Strategist)
Asks the FastAPI backend: "Which teaching style is working best today?" and fetches the matching prompt template.

### Node 3: AI Generator (The Writer)
Takes the topic and the chosen prompt, and writes the very first rough draft of the lesson.

### Node 4: AI Evaluator (The Strict Teacher)
A second AI reads the draft and grades it against a 6-point rubric. If anything is wrong (too much jargon, missing analogies, etc.), it writes down exactly what failed and why.

### Node 5: Compute Reward (The Translator)
Takes the teacher's grade, converts it into a math score (0 to 1), and cleans up any weird AI formatting using custom Regex.

### Node 6: Update RL Backend (The Memory)
Sends the final grade back to the database so the system "learns" which prompts work best over time.

### Node 7: Did it pass? (The Bouncer)
A simple YES/NO gate. Did the lesson get a perfect score? If Yes, give it to the user. If No, send it down to get fixed.

### Node 8: Wait (The Coffee Break)
A 12-second pause. Free AI servers crash if you hit them too fast, so this tells the system to chill before the next API call.

### Node 9: Prepare Prompt (The Messenger)
Takes the bad first draft AND the teacher's feedback, and packages them together into a new prompt for the Regenerator.

### Node 10: AI Regenerator (The Fixer)
Reads the terrible draft, reads the specific feedback, and completely rewrites the lesson to fix all the mistakes.

### Node 11: Wait1 (Coffee Break #2)
Another quick pause to prevent rate-limit crashes before the final evaluation.

### Node 12: AI Evaluator 1 (The Final Inspector)
Grades the brand-new draft to verify that the Fixer actually fixed the mistakes.

### Node 13: Compute Reward 1 (Final Cleanup)
Calculates the final score and bundles the polished lesson together with the original Rejection Logs of what went wrong the first time.

### Node 14: Respond to Webhook 1 (The Delivery Guy)
Takes the perfect lesson and the rejection logs, and sends them all back to Streamlit for the user to see.

---

## 11. Conclusion
The Agentic Lesson Generator is a comprehensive demonstration of advanced AI engineering. By combining visual orchestration (n8n + Docker), multi-agent evaluation (Generator + Evaluator + Regenerator), resilient error handling (Regex stripping, try/catch blocks, Wait nodes), a transparent frontend (Streamlit with Rejection Logs), and mathematical optimization via Reinforcement Learning (Thompson Sampling), the system transcends basic prompt engineering to become a true, self-correcting, continuously learning autonomous application.
