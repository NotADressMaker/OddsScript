from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_extract_injuries_from_table() -> None:
    pytest.importorskip("bs4")
    from src.sports_research_agent.extract.rule_extractors import extract_injuries_from_html

    html = load_fixture("injury_report.html")
    results = extract_injuries_from_html(html, "https://example.com/injuries", datetime.utcnow())
    assert len(results) == 2
    assert results[0].player == "Alex Smith"
    assert results[0].status.value == "OUT"


def test_extract_goalies_from_text() -> None:
    pytest.importorskip("bs4")
    from src.sports_research_agent.extract.rule_extractors import extract_goalies_from_text

    html = load_fixture("goalie_report.html")
    results = extract_goalies_from_text(html, "https://example.com/goalies", datetime.utcnow())
    assert len(results) == 2
    assert results[0].confirmed is True


def test_extract_line_moves() -> None:
    pytest.importorskip("bs4")
    from src.sports_research_agent.extract.rule_extractors import extract_line_moves

    html = load_fixture("line_move.html")
    results = extract_line_moves(html, "https://example.com/lines", datetime.utcnow())
    assert len(results) == 1
    assert results[0].open == "210.5"
    assert results[0].current == "212.0"


def test_extract_qb_starters() -> None:
    pytest.importorskip("bs4")
    from src.sports_research_agent.extract.rule_extractors import extract_qb_starters

    html = load_fixture("qb_report.html")
    results = extract_qb_starters(html, "https://example.com/qb", datetime.utcnow())
    assert len(results) == 1
    assert results[0].player == "Taylor Swift"


def test_extract_novel_moneyline_signals() -> None:
    pytest.importorskip("bs4")
    from src.sports_research_agent.extract.rule_extractors import extract_novel_moneyline_signals

    html = """
    <html><body><main>
    BOS is playing its third game in four nights after a late arrival from the West Coast.
    Market screens also showed reverse line movement and buyback on the underdog moneyline.
    </main></body></html>
    """
    results = extract_novel_moneyline_signals(
        html, "https://example.com/context", datetime.utcnow()
    )
    assert len(results) == 2
    assert results[0].category == "travel_rest"
    assert results[0].team == "BOS"
    assert results[1].category == "market_microstructure"
