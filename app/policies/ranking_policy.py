"""Recommendation Agent ranking 정책."""

MIN_SCORE = 0.1
BASE_SCORE = 1.0
RANK_DECAY = 0.05


def score_for_rank(rank: int) -> float:
    if rank < 1:
        raise ValueError("rank must be greater than 0")
    return round(max(MIN_SCORE, BASE_SCORE - ((rank - 1) * RANK_DECAY)), 2)
