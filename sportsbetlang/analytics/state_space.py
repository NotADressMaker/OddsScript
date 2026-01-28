"""
SportsBetLang Analytics - State Space Models

Implements simple state space models such as a univariate local level model
with a Kalman filter and smoother for time-series analytics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class KalmanState:
    """Kalman filter state for a univariate local level model."""

    level: float
    variance: float


class LocalLevelModel:
    """
    Univariate local level state space model.

    State: level_t = level_{t-1} + w_t, w_t ~ N(0, process_var)
    Observation: y_t = level_t + v_t, v_t ~ N(0, obs_var)
    """

    def __init__(self, process_var: float, obs_var: float) -> None:
        if process_var <= 0 or obs_var <= 0:
            raise ValueError("process_var and obs_var must be positive")
        self.process_var = process_var
        self.obs_var = obs_var

    def filter(
        self,
        observations: List[float],
        initial_state: Optional[KalmanState] = None,
    ) -> List[KalmanState]:
        if not observations:
            raise ValueError("observations must not be empty")

        if initial_state is None:
            initial_state = KalmanState(level=observations[0], variance=1.0)

        states: List[KalmanState] = []
        level = initial_state.level
        variance = initial_state.variance

        for obs in observations:
            # Predict step
            pred_level = level
            pred_variance = variance + self.process_var

            # Update step
            innovation = obs - pred_level
            innovation_var = pred_variance + self.obs_var
            kalman_gain = pred_variance / innovation_var

            level = pred_level + kalman_gain * innovation
            variance = (1 - kalman_gain) * pred_variance

            states.append(KalmanState(level=level, variance=variance))

        return states

    def smooth(
        self,
        observations: List[float],
        initial_state: Optional[KalmanState] = None,
    ) -> Tuple[List[KalmanState], List[KalmanState]]:
        filtered = self.filter(observations, initial_state)
        smoothed = filtered.copy()

        for idx in range(len(filtered) - 2, -1, -1):
            current = smoothed[idx]
            next_state = smoothed[idx + 1]
            filtered_next = filtered[idx + 1]

            pred_variance = filtered[idx].variance + self.process_var
            if pred_variance <= 0:
                continue
            smoother_gain = filtered[idx].variance / pred_variance

            current.level = current.level + smoother_gain * (next_state.level - filtered_next.level)
            current.variance = current.variance + smoother_gain * (
                next_state.variance - pred_variance
            ) * smoother_gain
            smoothed[idx] = current

        return filtered, smoothed
