from __future__ import annotations

LEAGUE_TERMS = {
    "nba": ["starting lineup", "injury report", "inactive list"],
    "nfl": ["starting qb", "inactive list", "injury report"],
    "nhl": ["starting goalie", "projected goalie", "injury update"],
    "mlb": ["probable pitcher", "lineup", "injury report"],
}


def expand_query(query: str, league: str | None) -> list[str]:
    if not league:
        return [query]
    terms = LEAGUE_TERMS.get(league.lower(), [])
    expanded = [query]
    for term in terms:
        expanded.append(f"{query} {term}")
    return expanded
