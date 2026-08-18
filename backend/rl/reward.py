CHECKPOINT_WEIGHTS = {
    "accurate_and_grounded": 0.25,
    "beginner_friendly_language": 0.20,
    "teaches_by_example": 0.15,
    "no_unexplained_jargon": 0.15,
    "covers_key_points": 0.15,
    "coherent_teaching_flow": 0.10,
}

def compute_reward(evaluation_results: list[dict]) -> float:
    """Returns a reward score between 0.0 and 1.0 based on passed checkpoints."""
    score = 0.0
    for result in evaluation_results:
        # result should be a dictionary with 'name' and 'passed'
        if result.get("passed"):
            checkpoint_name = result.get("name")
            if checkpoint_name in CHECKPOINT_WEIGHTS:
                score += CHECKPOINT_WEIGHTS[checkpoint_name]
    return score
