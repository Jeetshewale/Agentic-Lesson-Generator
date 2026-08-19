# 🎬 Agentic Lesson Generator: 10-15 Minute Presentation Script

> **Director's Note:** Speak at a calm, professional pace. A 10-15 minute video requires you to walk through the architecture deeply. Don't just read the script; use it as a guide while you actively click through your Streamlit UI and n8n canvas.

---

## ⏱️ [0:00 - 1:30] Introduction & The Problem
**[On Screen: Your face or a title slide, then switch to the Streamlit UI]**

"Hi, my name is [Your Name], and today I am presenting my submission for the GenAI Engineer assessment: The **Autonomous Agentic Lesson Generator**."

"When we look at standard AI tools today, like ChatGPT, they operate on a 'single-shot' paradigm. You give them a prompt, they generate an answer, and you're stuck with whatever it produces—even if it hallucinates, uses too much jargon, or completely ignores your pedagogical requirements."

"To solve this, I didn't just build a prompt wrapper. I built a **closed-loop Agentic Workflow** augmented by a **Reinforcement Learning Engine**. Instead of relying on one AI, my system utilizes a workforce of specialized agents that generate content, strictly evaluate it against a custom rubric, and autonomously regenerate it until it is perfect—before the user ever sees it."

---

## ⏱️ [1:30 - 4:00] Live Demonstration (The 'Happy Path')
**[On Screen: Streamlit UI]**

"Let’s start with a quick demonstration of the frontend, which I built using Streamlit. I chose Streamlit because it allows for rapid, Python-native UI prototyping so I could focus entirely on the complex backend AI logic."

"I'm going to enter a topic here—let's use 'Introduction to RAG'. I'm going to leave 'Inject Deliberate Error' toggled OFF for now."

**[Action: Click Generate]**

"While this is generating, let me explain what’s happening in the background. My Streamlit app just hit my FastAPI backend. The backend is running a Thompson Sampling Reinforcement Learning algorithm. It mathematically decided which of my 4 teaching styles—Structured, Storytelling, Analogy-Heavy, or Socratic—has the highest historical success rate, and injected that into the system prompt."

"The prompt was then sent to my orchestration engine—n8n—which coordinates the AI generation."

**[Action: Scroll down to the finished lesson]**

"And here is the result. We have a pristine, beautifully formatted lesson. But this wasn't just generated; it was *evaluated*. The AI Evaluator graded this draft on a 6-point rubric, gave it a perfect score, and returned it."

---

## ⏱️ [4:00 - 7:30] The Deep Dive: Architecture & n8n
**[On Screen: Switch tabs to the n8n Workflow Canvas]**

"Let's look under the hood at how this actually works. I chose n8n running via Docker for my orchestration rather than writing raw Python spaghetti code. n8n gives me a visual node-based graph that makes debugging agent states incredibly intuitive, and it natively handles API retries and complex conditional routing."

"Here is the core Agentic Loop:"

1.  **"First, the Webhook receives the payload."**
2.  **"Second, the AI Generator."** *(Point to the node)* "This agent writes the initial draft using the Llama 3 model running on Groq's LPUs for lightning-fast inference."
3.  **"Third, the AI Evaluator."** *(Point to the node)* "This is the strict judge. It receives the draft and grades it based on criteria like beginner-friendly language, lack of jargon, and accurate analogies. It is forced to output its grade as strict JSON."

**[Action: Point to the 'IF' Node]**

"Next, we hit the decision matrix. This IF node calculates if the Evaluator gave the lesson a 100% perfect score. If yes, it routes it back to the user. But what happens if it fails?"

---

## ⏱️ [7:30 - 10:30] Autonomy in Action: The Regeneration Loop
**[On Screen: Switch back to Streamlit UI]**

"To show you the true power of an agentic workflow, I built this 'Inject Deliberate Error' toggle. I'm going to turn it ON and hit Generate again."

**[Action: Toggle ON, Click Generate, then switch back to n8n Canvas]**

"This toggle forces the AI Generator to write a terrible first draft—full of complex jargon and missing explanations. When the AI Evaluator reads it, it will immediately fail it."

"Instead of crashing or sending garbage to the user, the IF node routes the failed draft down here to the **AI Regenerator**."

"This is the most critical part of the architecture: I intentionally **unrolled the loop**. A common failure in agentic systems is infinite looping, where two AIs get stuck endlessly arguing. By unrolling the loop into a straight line, I place a hard constraint on the system: exactly *one* regeneration attempt. This guarantees the workflow will always terminate."

"The Regenerator takes the bad draft *and* the exact JSON failure logs, rewrites the lesson to fix those specific errors, and passes it through one final evaluation."

---

## ⏱️ [10:30 - 12:30] Transparency & Rejection Logs
**[On Screen: Switch back to Streamlit UI. Scroll down to the completed lesson and click open the 'Rejection Log' expander]**

"The new lesson has finished generating. As you can see, the final text is clean and professional. But scroll down, and you’ll see the **Rejection Log**."

"In production AI systems, transparency is key. You can't just hide failures. I built the system to aggregate the payload from both passes. Here, the user can see exactly what the first, terrible draft looked like, and exactly which checkpoints it failed. The Regenerator successfully fixed these behind the scenes."

---

## ⏱️ [12:30 - 14:00] Engineering Resiliency & Reinforcement Learning
**[On Screen: Switch to VS Code showing backend/main.py or just point to the RL stats on Streamlit]**

"Before I conclude, I want to highlight two major engineering hurdles I overcame to make this production-ready."

1.  **"Resiliency against Hallucinations:"** "When using reasoning models, they often exceed their token limits while in their `<think>` tags, which breaks JSON formatting. I wrote custom JavaScript Code nodes with Regex (`/<think>[\s\S]*?(<\/think>|$)/g`) that dynamically detects and strips out unclosed hallucination tags, guaranteeing my JSON parses cleanly every time."
2.  **"The RL Bandit:"** *(Point to the RL stats on the Streamlit sidebar)* "Notice this leaderboard? Every time the Evaluator grades a lesson, my FastAPI backend calculates a normalized float score and updates a SQLite database. Using Thompson Sampling and Beta distributions, the system learns over time which prompt styles produce the best results, continuously optimizing its own performance."

---

## ⏱️ [14:00 - 15:00] Conclusion
**[On Screen: Your face or a 'Thank You' slide]**

"In conclusion, the Agentic Lesson Generator is not just a prompt wrapper. It is a resilient, self-correcting, learning system."

"By leveraging n8n for fault-tolerant orchestration, Groq for high-speed inference, and a custom Reinforcement Learning backend for prompt optimization, I’ve built a pipeline that guarantees high-quality, pedagogical content at scale."

"Thank you for your time, and I look forward to your feedback!"
