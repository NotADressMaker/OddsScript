"""Reproducibility helpers for analytics and modeling."""

from __future__ import annotations

import os
import random
from typing import Any


def set_global_seed(seed: int) -> None:
    """Set global random seeds for reproducible analytics workflows."""

    random.seed(seed)
    if "PYTHONHASHSEED" not in os.environ:
        os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
    except ImportError:
        return
    np.random.seed(seed)


def ensure_random_state(kwargs: dict[str, Any], seed: int) -> dict[str, Any]:
    """Return kwargs with a random_state value set when missing."""

    if "random_state" not in kwargs:
        kwargs = dict(kwargs)
        kwargs["random_state"] = seed
    return kwargs
