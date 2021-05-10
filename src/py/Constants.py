from typing import Tuple


class Constants:

    RICHNESS_NULL: int = 0
    RICHNESS_POOR: int = 1
    RICHNESS_OK: int = 2
    RICHNESS_LUSH: int = 3

    TREE_SEED: int = 0
    TREE_SMALL: int = 1
    TREE_MEDIUM: int = 2
    TREE_TALL: int = 3

    TREE_BASE_COST: Tuple[int] = (0, 1, 3, 7)
    TREE_COST_SCALE: int = 1
    LIFECYCLE_END_COST: int = 4
    DURATION_ACTION_PHASE: int = 1000
    DURATION_GATHER_PHASE: int = 2000
    DURATION_SUNMOVE_PHASE: int = 1000
    STARTING_TREE_COUNT: int = 2
    RICHNESS_BONUS_OK: int = 2
    RICHNESS_BONUS_LUSH: int = 4
