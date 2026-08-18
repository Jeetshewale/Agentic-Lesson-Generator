from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from contextlib import asynccontextmanager

from models.schemas import EvaluationResult, RewardUpdate, GenerateRequest
from rl.bandit import bandit
from rl.reward import compute_reward
from memory.store import init_db, log_run, log_rejection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup DB on startup
    init_db()
    yield
    # Cleanup on shutdown

app = FastAPI(title="Lesson Content Generator Backend", lifespan=lifespan)

@app.post("/select-prompt")
async def select_prompt(request: GenerateRequest):
    """Selects the best prompt variant based on the bandit's current knowledge."""
    selected_variant = bandit.select_variant()
    
    # Load the prompt content from file
    prompt_path = os.path.join("prompts", "variants", f"{selected_variant}.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_content = f.read()
    except FileNotFoundError:
        # Fallback if file doesn't exist yet
        prompt_content = "Please write a lesson."
        
    return {
        "variant_id": selected_variant,
        "prompt_content": prompt_content,
        "topic": request.topic
    }

@app.post("/update-reward")
async def update_reward(update: RewardUpdate):
    """Updates the bandit arm with the calculated reward."""
    bandit.update(update.variant_id, update.reward)
    return {"status": "success", "new_stats": bandit.get_stats()}

@app.post("/log-run")
async def log_run_endpoint(data: dict):
    """Logs the final result of a run."""
    run_id = log_run(
        topic=data.get("topic", ""),
        variant_id=data.get("variant_id", ""),
        reward=data.get("reward", 0.0),
        passed=data.get("passed", False),
        retry_count=data.get("retry_count", 0)
    )
    
    for failure in data.get("failures", []):
        log_rejection(
            run_id=run_id,
            checkpoint=failure.get("checkpoint", ""),
            reasoning=failure.get("reasoning", ""),
            suggestion=failure.get("suggestion", "")
        )
    return {"run_id": run_id}

@app.get("/stats")
async def get_stats():
    """Returns the current expected win rates for each variant."""
    return bandit.get_stats()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
