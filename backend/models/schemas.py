from pydantic import BaseModel
from typing import List, Optional, Dict

class CheckpointResult(BaseModel):
    name: str
    passed: bool
    reasoning: str
    evidence: Optional[str] = None
    suggestion: Optional[str] = None

class EvaluationResult(BaseModel):
    checkpoints: List[CheckpointResult]
    overall_passed: bool
    total_score: float

class RewardUpdate(BaseModel):
    variant_id: str
    reward: float

class GenerateRequest(BaseModel):
    topic: str
