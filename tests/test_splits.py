from __future__ import annotations

import numpy as np

from src.utils.splits import expanding_window_split


def test_expanding_window_split() -> None:
    n_samples = 100
    test_size = 20
    splits = list(expanding_window_split(n_samples, test_size))
    assert len(splits) == 1
    train_idx, test_idx = splits[0]
    assert train_idx[-1] == 79
    assert test_idx[0] == 80
    assert np.intersect1d(train_idx, test_idx).size == 0
