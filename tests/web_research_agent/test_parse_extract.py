from __future__ import annotations

from pathlib import Path

from sportsbetlang.web_research_agent.extract import extract_facts
from sportsbetlang.web_research_agent.parse import is_soft_404, parse_html


def test_extract_facts_from_fixture() -> None:
    fixture = Path("tests/fixtures/sample_page.html").read_bytes()
    parsed = parse_html(fixture, "file://sample")
    facts = extract_facts("revenue", parsed, "2024-06-02T00:00:00Z")
    assert facts
    assert all(len(fact.snippet.split()) <= 25 for fact in facts)


def test_soft_404_detection() -> None:
    html = b"<html><head><title>404 Not Found</title></head><body>Not found</body></html>"
    parsed = parse_html(html, "file://soft404")
    assert is_soft_404(parsed) is True
