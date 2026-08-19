# 🧠 Autonomous Agentic Lesson Generator: Project Documentation

## 1. Executive Summary
The Agentic Lesson Generator is an advanced AI system designed to autonomously generate, evaluate, and iteratively refine educational content. Moving beyond traditional "single-shot" LLM wrappers, this system implements a closed-loop **Agentic Workflow** paired with a **Reinforcement Learning (RL)** engine. The system evaluates its own outputs against strict pedagogical rubrics and mathematically optimizes its prompt strategies over time.

## 2. Core Agentic Workflow
The system is orchestrated using n8n to manage the complex flow between multiple specialized AI agents:

*   **AI Generator (The Creator):** Takes the user's topic and a specific prompt strategy (e.g., Socratic, Storytelling) and generates a rough draft of the lesson.
*   **AI Evaluator (The Judge):** Receives the generated draft and acts as a strict quality-control reviewer. It scores the lesson against a 6-point weighted rubric (Accuracy, Beginner-Friendly, Examples, Jargon, Key Points, Flow) and outputs a pass/fail grade along with specific feedback for any failures.
*   **AI Regenerator (The Fixer):** If the Evaluator fails the draft, the Regenerator receives the original bad draft *and* the specific failure reasons. It rewrites the lesson to explicitly address the Evaluator's critiques.

## 3. Reinforcement Learning (Thompson Sampling)
Instead of hardcoding a single system prompt, the system learns which teaching styles work best dynamically.

*   **Multi-Armed Bandit:** The FastAPI backend runs a Thompson Sampling algorithm using Beta distributions. 
*   **Exploration vs. Exploitation:** It tests 4 different prompt variants (`v1_structured`, `v2_storytelling`, `v3_analogy_heavy`, `v4_socratic`).
*   **Feedback Loop:** Every time the Evaluator grades a lesson, the backend calculates a normalized float score (0.0 to 1.0) based on the rubric weights. This score is fed back into the SQLite database, updating the mathematical probability of that prompt variant being chosen in the future.

## 4. Tech Stack Breakdown
*   **Orchestration (n8n via Docker):** Provides a visual node-based graph for routing the agents. Chosen for its ability to handle complex conditional logic (IF nodes) and native Auto-Retry capabilities.
*   **Backend & RL Engine (FastAPI + Python):** Chosen for lightning-fast, asynchronous API routing. Handles the complex math for Thompson Sampling and manages the SQLite persistent memory.
*   **Frontend UI (Streamlit):** Allows for rapid Python-native dashboard creation. Visualizes the RL Bandit Leaderboard in real-time and dynamically extracts the `rejection_log` from the webhook payload to provide transparency to the user.
*   **Database (SQLite):** Lightweight, file-based database ideal for storing RL states, success rates, and prompt variants without cloud dependency overhead.
*   **LLM Engine (Groq + Qwen/Llama):** Utilizing LPU hardware for extreme inference speeds, which is critical for multi-agent loops that require multiple sequential AI generations.

## 5. Resiliency & Fault Tolerance Engineering
Building autonomous agents requires strict error handling. This project implements several advanced resiliency patterns:

*   **Straight-Line Loop Unrolling:** To prevent "infinite loops" where an AI constantly fails evaluation, the regeneration loop was intentionally unrolled into a straight line in n8n. This places a hard constraint of exactly *one* regeneration attempt, ensuring the system eventually terminates.
*   **Rate Limit Mitigation (Wait Nodes & Auto-Retries):** Free-tier AI APIs easily crash under multi-agent loads. Strategic 12-second Wait nodes and 3x Auto-Retries with 5000ms backoffs were engineered to gracefully bypass `429 Too Many Requests` limits.
*   **Regex Hallucination Stripping:** Reasoning models (like Qwen) often hallucinate unclosed `<think>` tags that crash JSON parsers. Custom JavaScript Code nodes were built with advanced Regex (`/<think>[\s\S]*?(<\/think>|$)/g`) to surgically strip out inner thoughts, guaranteeing clean payload parsing.
*   **Safe Catch Blocks:** JavaScript `try/catch` blocks were implemented in the formatting nodes to ensure that even if the AI completely hallucinates the JSON structure, the workflow returns a graceful "failed" score rather than crashing the execution.

## 6. Step-by-Step Data Flow
1.  **User Request:** User enters "Topic" in Streamlit.
2.  **RL Request:** Streamlit hits FastAPI (`/get-prompt`) to get the statistically optimal prompt variant.
3.  **Webhook Trigger:** Streamlit sends the Topic and Variant to the n8n Webhook.
4.  **Generation Phase:** n8n formats the prompt and triggers Groq to write Draft 1.
5.  **Evaluation Phase:** Groq evaluates Draft 1 and outputs JSON scores.
6.  **Decision Node:** n8n calculates if the score is perfect (100%).
    *   *Pass:* Returns Draft 1 to Streamlit.
    *   *Fail:* Sends Draft 1 + Failure JSON to the Regenerator.
7.  **Regeneration Phase:** Groq reads the failures and rewrites Draft 2.
8.  **Final Evaluation:** Draft 2 is evaluated.
9.  **Payload Combination:** A custom JS expression combines Draft 2 and the original failure logs into a single JSON object.
10. **Delivery:** The combined payload is returned to Streamlit to render the final UI.
11. **Memory Update:** A background API call is sent to FastAPI (`/update-reward`) to log the final score and adjust the Bandit algorithm.
