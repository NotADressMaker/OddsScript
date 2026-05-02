from __future__ import annotations

import pandas as pd


class DerbyDataCleaner:
    REQUIRED_COLUMNS = {
        "horse",
        "jockey",
        "trainer",
        "finish_position",
        "speed_figure",
        "distance_furlongs",
        "track_condition",
        "market_odds_decimal",
        "race_date",
    }

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        data.columns = [c.strip().lower() for c in data.columns]
        missing = self.REQUIRED_COLUMNS - set(data.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        data = data.dropna(subset=["horse", "market_odds_decimal", "finish_position"])
        data["finish_position"] = pd.to_numeric(data["finish_position"], errors="coerce")
        data["speed_figure"] = pd.to_numeric(data["speed_figure"], errors="coerce")
        data["market_odds_decimal"] = pd.to_numeric(data["market_odds_decimal"], errors="coerce")
        data["distance_furlongs"] = pd.to_numeric(data["distance_furlongs"], errors="coerce")
        data["race_date"] = pd.to_datetime(data["race_date"], errors="coerce")

        data = data.dropna(subset=["race_date", "distance_furlongs", "market_odds_decimal"])
        data["won"] = (data["finish_position"] == 1).astype(int)
        data = data.sort_values(["race_date", "horse"]).reset_index(drop=True)
        return data
