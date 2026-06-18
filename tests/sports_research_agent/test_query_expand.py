from __future__ import annotations

from src.sports_research_agent.search.query_expand import expand_query


def test_expand_query_includes_novel_moneyline_terms() -> None:
    queries = expand_query("Celtics Knicks moneyline", "nba")
    assert "Celtics Knicks moneyline reverse line movement" in queries
    assert "Celtics Knicks moneyline minutes restriction" in queries
    assert "Celtics Knicks moneyline travel rest disadvantage" in queries
