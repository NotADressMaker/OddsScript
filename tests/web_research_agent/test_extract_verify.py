from __future__ import annotations

from sportsbetlang.web_research_agent.extract import AnchoredFact, clip_quote
from sportsbetlang.web_research_agent.verify import detect_contradictions


def test_clip_quote_limits_words() -> None:
    snippet = "one " * 40
    clipped = clip_quote(snippet.strip())
    assert len(clipped.split()) == 25


def test_detect_contradictions() -> None:
    facts = [
        AnchoredFact(
            claim="Value is 10 units",
            url="https://example.com/a",
            snippet="Value is 10 units",
            timestamp="2024-01-01T00:00:00Z",
            attribute="value",
            value=10.0,
        ),
        AnchoredFact(
            claim="Value is 12 units",
            url="https://example.com/b",
            snippet="Value is 12 units",
            timestamp="2024-01-02T00:00:00Z",
            attribute="value",
            value=12.0,
        ),
    ]
    contradictions = detect_contradictions(facts)
    assert contradictions
    assert contradictions[0]["attribute"] == "value"
