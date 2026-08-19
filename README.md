# 🤖 Autonomous Agentic Lesson Generator

An advanced, self-evaluating AI content generation system that **autonomously generates, evaluates, and iteratively refines** educational content using a multi-agent architecture and Reinforcement Learning.

> Built for the GenAI Engineer Assessment — demonstrating production-grade agentic workflows, fault tolerance, and continuous learning.

---

## 📌 Table of Contents
- [Problem Statement](#-problem-statement)
- [How It Works](#-how-it-works)
- [System Architecture](#-system-architecture)
- [Tech Stack & Why](#-tech-stack--why)
- [Project Structure](#-project-structure)
- [Setup & Installation](#-setup--installation)
- [Sharing the n8n Workflow](#-sharing-the-n8n-workflow)
- [Evaluation Rubric](#-evaluation-rubric)
- [Key Engineering Highlights](#-key-engineering-highlights)
- [Demo Screenshots](#-demo-screenshots)

---

## ❓ Problem Statement
Standard AI chatbots operate on a **"single-shot" paradigm** — you give them a prompt, they generate one answer, and you're stuck with whatever they produce. If the output hallucinates, uses too much jargon, or misses key requirements, there's no built-in self-correction.

This project solves that by implementing a **closed-loop Agentic Workflow** where multiple specialized AI agents collaborate autonomously to guarantee high-quality output.

---

## ⚙️ How It Works

### The Agentic Loop (Step-by-Step)
```
User enters topic → RL Bandit picks best prompt style → AI Generator writes Draft 1
    → AI Evaluator grades it against 6-point rubric
        → PASS? → Return lesson to user ✅
        → FAIL? → AI Regenerator rewrites it using failure feedback
            → AI Evaluator grades Draft 2 → Return final lesson + Rejection Log ✅
```

### The 3 AI Agents
| Agent | Role | Simple Analogy |
|-------|------|----------------|
| **AI Generator** | Writes the first draft of the lesson | The Writer |
| **AI Evaluator** | Grades the draft against a strict rubric | The Strict Teacher |
| **AI Regenerator** | Reads the feedback and rewrites to fix mistakes | The Fixer |

### Reinforcement Learning (Thompson Sampling)
The system doesn't use a single hardcoded prompt. Instead, it has **4 teaching styles**:
1. `v1_structured` — Clear headers, bullet points, linear progression
2. `v2_storytelling` — Weaves concepts into a relatable narrative
3. `v3_analogy_heavy` — Uses real-world metaphors to explain abstract ideas
4. `v4_socratic` — Guides learning through questions

A **Multi-Armed Bandit algorithm** (Thompson Sampling) mathematically decides which style to use based on historical success rates, balancing exploration (trying new styles) and exploitation (using what works best).

---

## 🧠 System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│   Streamlit UI  │────▶│  FastAPI Backend  │────▶│  SQLite Database    │
│   (Frontend)    │◀────│  (RL Engine)      │◀────│  (Memory/Logging)   │
└────────┬────────┘     └──────────────────┘     └─────────────────────┘
         │
         │ HTTP POST (Webhook)
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    n8n Workflow (Docker)                        │
│                                                                 │
│  Webhook → Get RL Prompt → AI Generator → AI Evaluator          │
│       → Compute Reward → Did it pass?                           │
│           ├─ YES → Respond to Webhook                           │
│           └─ NO  → Wait → Prepare Prompt → AI Regenerator       │
│                   → AI Evaluator 1 → Compute Reward 1           │
│                   → Respond to Webhook 1                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack & Why

| Technology | Purpose | Why This Choice? |
|-----------|---------|-----------------|
| **n8n (Docker)** | Orchestration & Agentic Loop | Visual node-based graph makes debugging agent states intuitive. Native Auto-Retry and conditional routing eliminates spaghetti code. |
| **FastAPI (Python)** | Backend API & RL Engine | Lightning-fast async API with strict Pydantic data validation. Handles Thompson Sampling math without blocking. |
| **Streamlit (Python)** | Frontend Dashboard | Rapid Python-native UI prototyping. Focus on AI logic, not React/HTML. |
| **SQLite** | Persistent Memory | Lightweight, file-based storage for RL states and lesson logs. No cloud database needed. |
| **Groq API** | LLM Inference | LPU hardware provides near-instant inference. Critical for multi-agent loops that need 4+ sequential AI calls. |
| **Docker** | Containerization | Isolates n8n and its Node.js dependencies. Reproducible environment across any machine. |

---

## 📁 Project Structure
```
lesson-content-generator/
├── backend/
│   ├── main.py                 # FastAPI server (5 API endpoints)
│   ├── models/
│   │   └── schemas.py          # Pydantic data validation schemas
│   ├── rl/
│   │   ├── bandit.py           # Thompson Sampling Multi-Armed Bandit
│   │   └── reward.py           # Weighted rubric score calculator
│   ├── memory/
│   │   └── store.py            # SQLite database setup & logging
│   └── prompts/
│       └── variants/           # 4 prompt template files (one per style)
├── frontend/
│   └── app.py                  # Streamlit dashboard with Rejection Logs
├── n8n/
│   └── workflows/
│       └── lesson_generator.json   # Importable n8n workflow (14 nodes)
├── docker-compose.yml          # Docker config for n8n
├── .env                        # API keys (not committed to Git)
├── .gitignore                  # Protects secrets and databases
├── PROJECT_DETAILS_EXTENDED.md # Full technical deep-dive document
└── README.md                   # This file
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- Docker Desktop (for n8n)
- A free [Groq API Key](https://console.groq.com)

### Step 1: Clone the Repository
```bash
git clone https://github.com/Jeetshewale/Agentic-Lesson-Generator.git
cd Agentic-Lesson-Generator
```

### Step 2: Create Environment Variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### Step 3: Install Python Dependencies
```bash
pip install fastapi uvicorn streamlit pydantic numpy requests python-dotenv
```

### Step 4: Start All 3 Services
Open **3 separate terminal windows** and run one command in each:

**Terminal 1 — n8n (Docker):**
```bash
docker-compose up -d
```

**Terminal 2 — FastAPI Backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 3 — Streamlit Frontend:**
```bash
cd frontend
streamlit run app.py
```

### Step 5: Import the n8n Workflow
1. Open your browser and go to the n8n dashboard (default: port 5678).
2. Click **"Add workflow"** → **"Import from File"**.
3. Select `n8n/workflows/lesson_generator.json`.
4. Add your Groq API credentials to the AI nodes.
5. Click **"Save"** and activate the webhook!

---

## 🔗 Sharing the n8n Workflow

### For Assessors & Collaborators
The complete n8n workflow is saved as a JSON file in this repository:
```
n8n/workflows/lesson_generator.json
```

**To view or use it:**
1. Install n8n locally (`npx -y n8n`) or use [n8n.cloud](https://n8n.cloud).
2. Open the n8n editor.
3. Click **"Add workflow"** → **"Import from File"**.
4. Upload `lesson_generator.json` from this repo.
5. The entire 14-node agentic graph will appear on your canvas!

> **Note:** You will need to add your own Groq API credentials to the AI nodes after importing.

---

## 📊 Evaluation Rubric
The AI Evaluator grades every lesson against these 6 weighted checkpoints:

| Checkpoint | Weight | What It Checks |
|-----------|--------|----------------|
| Accurate & Grounded | 25% | Are all facts correct and verifiable? |
| Beginner-Friendly Language | 20% | Is the language simple enough for a complete beginner? |
| Teaches by Example | 15% | Does it include real-world examples and analogies? |
| No Unexplained Jargon | 15% | Is every technical term explained immediately when introduced? |
| Covers Key Points | 15% | Does the lesson cover all essential concepts of the topic? |
| Coherent Teaching Flow | 10% | Does the lesson flow logically from introduction to conclusion? |

---

## 🛡️ Key Engineering Highlights

### 1. Unrolled Loop Architecture
To prevent infinite loops where two AIs argue endlessly, the regeneration loop is "unrolled" into a straight line — limiting the system to exactly **one** regeneration attempt. This guarantees the workflow always terminates.

### 2. Rate Limit Mitigation
Free-tier Groq APIs crash under multi-agent loads. Strategic **12-second Wait nodes** and **3x Auto-Retries with 5000ms backoffs** handle `429 Too Many Requests` errors gracefully.

### 3. Regex Hallucination Stripping
Reasoning models (like Qwen) often output unclosed `<think>` tags that break JSON parsers. Custom JavaScript Code nodes use advanced Regex to strip these hallucinations:
```javascript
text.replace(/<think>[\s\S]*?(<\/think>|$)/g, '').trim()
```

### 4. Safe Catch Blocks
All JavaScript Code nodes are wrapped in `try/catch` blocks. If the AI hallucinates invalid JSON, the system returns a graceful "failed" score (0) instead of crashing.

### 5. Transparent Rejection Logs
The Streamlit UI doesn't hide failures. When regeneration occurs, users can click the **"🚨 Rejection Log"** expander to see the original bad draft and the exact reasons it was rejected.

---

## 🎥 Demo Screenshots
> Run the system and toggle "Inject Deliberate Error" ON to see the full regeneration loop in action!

---

## 📄 Additional Documentation
- **[PROJECT_DETAILS_EXTENDED.md](PROJECT_DETAILS_EXTENDED.md)** — Full 8-page technical deep-dive covering every backend file, frontend component, Docker setup, and n8n node explained in simple terms.

---

## 👤 Author
**Vishwajeet Shewale**  
[GitHub](https://github.com/Jeetshewale)

---

## 📝 License
This project was built as part of a GenAI Engineer assessment submission.
