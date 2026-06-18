from __future__ import annotations

NOVEL_MONEYLINE_TERMS = [
    "reverse line movement",
    "travel rest disadvantage",
    "lineup role change",
    "weather venue conditions",
    "tactical matchup",
]

LEAGUE_TERMS = {
    "nba": [
        "starting lineup",
        "injury report",
        "inactive list",
        "minutes restriction",
        "back to back",
    ],
    "nfl": [
        "starting qb",
        "inactive list",
        "injury report",
        "offensive line injuries",
        "weather wind",
    ],
    "nhl": [
        "starting goalie",
        "projected goalie",
        "injury update",
        "travel back to back",
        "line rushes",
    ],
    "mlb": ["probable pitcher", "lineup", "injury report", "bullpen taxed", "umpire assignment"],
}


def expand_query(query: str, league: str | None) -> list[str]:
    if not league:
        return [query]
    terms = [*LEAGUE_TERMS.get(league.lower(), []), *NOVEL_MONEYLINE_TERMS]
    expanded = [query]
    for term in terms:
        expanded.append(f"{query} {term}")
    return expanded
