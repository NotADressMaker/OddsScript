from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression


class ProbabilityCalibrator:
    def __init__(self):
        self._iso = IsotonicRegression(out_of_bounds="clip")
        self._is_fitted = False

    def fit(self, raw_probs, outcomes):
        raw = np.asarray(raw_probs)
        y = np.asarray(outcomes)
        self._iso.fit(raw, y)
        self._is_fitted = True
        return self

    def predict(self, raw_probs):
        raw = np.asarray(raw_probs)
        if not self._is_fitted:
            return raw
        return self._iso.predict(raw)
