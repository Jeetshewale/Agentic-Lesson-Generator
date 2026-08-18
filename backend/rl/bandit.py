import numpy as np
from typing import Dict, List

class PromptBandit:
    """Multi-Armed Bandit for prompt variant selection using Thompson Sampling."""
    
    def __init__(self, variants: List[str]):
        # Beta distribution params (alpha=successes+1, beta=failures+1)
        self.alpha = {v: 1.0 for v in variants}
        self.beta = {v: 1.0 for v in variants}
    
    def select_variant(self) -> str:
        """Thompson Sampling: sample from each arm's Beta distribution."""
        samples = {
            v: np.random.beta(self.alpha[v], self.beta[v])
            for v in self.alpha
        }
        # Return variant with highest sampled value
        return max(samples, key=samples.get)
    
    def update(self, variant: str, reward: float):
        """Update arm based on reward (0-1 scale)."""
        if variant in self.alpha:
            self.alpha[variant] += reward
            self.beta[variant] += (1 - reward)
    
    def get_stats(self) -> Dict[str, float]:
        """Return expected win rate per variant."""
        return {
            v: self.alpha[v] / (self.alpha[v] + self.beta[v])
            for v in self.alpha
        }

# Global instance for the app
VARIANTS = ["v1_structured", "v2_storytelling", "v3_analogy_heavy", "v4_socratic"]
bandit = PromptBandit(VARIANTS)
