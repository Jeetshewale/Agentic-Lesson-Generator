# 🚀 Autonomous Agentic Lesson Generator

An advanced, self-evaluating AI content generation system built with **n8n**, **FastAPI**, and **Streamlit**. This system employs a multi-agent architecture and a Reinforcement Learning (RL) Multi-Armed Bandit to autonomously generate, evaluate, and refine educational content.

## 🧠 System Architecture

This project moves beyond basic LLM wrappers by implementing a true agentic workflow with closed-loop feedback:

1. **AI Generator**: Generates educational content based on dynamic prompt strategies selected by the RL backend.
2. **AI Evaluator**: Acts as a strict quality-control judge, evaluating the generated lesson against a weighted 6-point rubric (e.g., beginner-friendly language, use of analogies, no unexplained jargon).
3. **AI Regenerator**: If the lesson fails the evaluation, the feedback is routed to the Regenerator, which iteratively refines the content until it passes the quality threshold. (Includes a hard-coded unrolled loop breaker to prevent infinite API consumption).
4. **RL Bandit (Thompson Sampling)**: The system learns over time. It tests 4 different pedagogical prompt variants (Structured, Storytelling, Analogy-Heavy, Socratic). The Evaluator's scores are fed back into the Python backend, adjusting the probability of selecting each prompt variant based on historical success rates.

## 🛠️ Technology Stack

- **Orchestration**: n8n (Visual Node-based Agentic Workflow)
- **Backend & RL Engine**: Python, FastAPI, Pydantic, NumPy
- **Frontend UI**: Streamlit
- **Database**: SQLite (Persistent memory for RL states and lesson logs)
- **LLM Provider**: Groq (Llama 3.1 / Allam models for high-speed inference)

## 🚀 Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/agentic-lesson-generator.git
cd agentic-lesson-generator
```

### 2. Environment Variables
Create a `.env` file in the root directory and add your Groq API key:
```env
GROQ_API_KEY=your_api_key_here
```

### 3. Start the Backend & Frontend
Install the required Python dependencies and start the servers:
```bash
# Install dependencies
pip install fastapi uvicorn streamlit pydantic numpy requests python-dotenv

# Start the FastAPI RL Backend (Port 8000)
cd backend
uvicorn main:app --reload --port 8000

# In a new terminal, start the Streamlit UI (Port 8501)
cd frontend
streamlit run app.py
```

### 4. Import the n8n Workflow
1. Start n8n (either locally or on your cloud host).
2. Open your n8n dashboard.
3. Import the `n8n/workflows/lesson_generator.json` file.
4. Add your Groq API credentials to the AI nodes.
5. Activate the webhook!

## 📊 Evaluation Rubric
The AI Evaluator grades lessons based on:
- Accuracy and Grounding (25%)
- Beginner-Friendly Language (20%)
- Teaches by Example (15%)
- No Unexplained Jargon (15%)
- Covers Key Points (15%)
- Coherent Teaching Flow (10%)

## 🤝 Fault Tolerance & Resiliency
Built with production-grade resiliency, this system includes:
- **Auto-Retries & Wait Nodes**: Strategically placed to handle free-tier API rate limits gracefully.
- **Regex Fallbacks**: Code nodes designed to strip `<think>` tags and force strict JSON parsing from reasoning models.
- **State Logging**: All failed attempts and evaluation scores are permanently logged to SQLite for analytics.
