from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .calibration import ProbabilityCalibrator
from .data_cleaning import DerbyDataCleaner
from .evaluation import DerbyEvaluator
from .feature_generation import DerbyFeatureGenerator
from .modeling import DerbyWinModel
from .odds import OddsConverter


@dataclass
class PipelineOutput:
    scored_runners: pd.DataFrame
    metrics: dict
    value_bet_summary: pd.DataFrame


class DerbyValueBetPipeline:
    def __init__(self):
        self.cleaner = DerbyDataCleaner()
        self.features = DerbyFeatureGenerator()
        self.model = DerbyWinModel()
        self.calibrator = ProbabilityCalibrator()
        self.evaluator = DerbyEvaluator()

    def run_from_dataframe(self, df: pd.DataFrame, cutoff_date: str) -> PipelineOutput:
        clean_df = self.cleaner.clean(df)
        feat_df = self.features.transform(clean_df)
        cols = self.features.feature_columns()

        cutoff = pd.Timestamp(cutoff_date)
        train = feat_df[feat_df["race_date"] < cutoff].copy()
        score = feat_df[feat_df["race_date"] >= cutoff].copy()
        if train.empty or score.empty:
            raise ValueError("Need both train and scoring rows around cutoff_date")

        self.model.fit(train[cols], train["won"])
        train_raw = self.model.predict_win_probability(train[cols])
        self.calibrator.fit(train_raw, train["won"])

        score_raw = self.model.predict_win_probability(score[cols])
        score["true_win_probability"] = self.calibrator.predict(score_raw)

        scored = OddsConverter.compare_market_vs_true_odds(score)
        metrics = self.evaluator.evaluate(score["won"], score["true_win_probability"])
        summary = self.evaluator.value_bet_summary(scored)

        preferred_cols = [
            "race_date",
            "horse",
            "market_odds_decimal",
            "market_implied_prob",
            "true_win_probability",
            "true_decimal_odds",
            "edge_probability",
            "edge_odds_decimal",
            "is_value_bet",
        ]
        existing_cols = [c for c in preferred_cols if c in scored.columns]
        return PipelineOutput(scored_runners=scored[existing_cols], metrics=metrics, value_bet_summary=summary)
