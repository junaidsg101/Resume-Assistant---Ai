"""
scorer.py - weight normalization utilities and aggregation helpers.
"""
from typing import Dict, List

DEFAULT_WEIGHTS: Dict[str, float] = {
    "Domain / Title Relevance": 15.0,
    "Education": 15.0,
    "Skills": 20.0,
    "Courses / Certifications": 10.0,
    "Experience": 20.0,
    "Hands-on Projects": 15.0,
    "Internal Projects / Hackathons": 5.0,
}


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """
    Normalize a dict of weights so they sum to 100. Returns a new dict.
    """
    total = sum(weights.values())
    if total == 0:
        # fallback to defaults
        return DEFAULT_WEIGHTS.copy()
    factor = 100.0 / total
    return {k: round(v * factor, 2) for k, v in weights.items()}


def compute_weighted_score(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    """
    Compute overall weighted score (0-100).
    Expect scores and weights to have matching keys. If a key is missing, treat as 0.
    """
    total = 0.0
    for k, w in weights.items():
        s = scores.get(k, 0)
        total += (s * (w / 100.0))
    return float(total)
