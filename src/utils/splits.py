"""Time series splitting utilities for leakage prevention."""

from __future__ import annotations

from typing import Iterator, Tuple

import numpy as np


def expanding_window_split(n_samples: int, test_size: int) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
    """Yield expanding window splits with a fixed test size."""

    if n_samples <= test_size:
        raise ValueError("Not enough samples for the requested test size.")
    start = n_samples - test_size
    train_idx = np.arange(0, start)
    test_idx = np.arange(start, n_samples)
    yield train_idx, test_idx
