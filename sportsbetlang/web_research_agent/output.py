"""Output formatting."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Dict, Iterable, List

from sportsbetlang.web_research_agent.extract import AnchoredFact


def build_summary(query: str, confirmed: List[AnchoredFact], unconfirmed: List[AnchoredFact]) -> str:
    if confirmed:
        return (
            f"Found {len(confirmed)} corroborated facts for '{query}' across multiple sources."
        )
    if unconfirmed:
        return (
            f"Found {len(unconfirmed)} facts for '{query}' but they lack corroboration."
        )
    return f"No relevant evidence found for '{query}'."


def format_markdown(
    query: str,
    facts: Iterable[AnchoredFact],
    contradictions: List[Dict[str, object]],
    confidence: float,
) -> str:
    lines = [f"# Research Summary: {query}", "", "## Evidence"]
    for fact in facts:
        lines.append(
            f"- {fact.claim} (Source: {fact.url})\n"
            f"  - Quote: \"{fact.snippet}\"\n"
            f"  - Retrieved: {fact.timestamp}"
        )
    if contradictions:
        lines.append("\n## Contradictions")
        for contradiction in contradictions:
            lines.append(f"- Attribute: {contradiction['attribute']}")
            for item in contradiction["values"]:
                lines.append(f"  - Value: {item['value']} Sources: {', '.join(item['sources'])}")
    lines.append(f"\n## Confidence\n{confidence:.2f}")
    return "\n".join(lines)


def format_json(
    query: str,
    summary: str,
    facts: Iterable[AnchoredFact],
    contradictions: List[Dict[str, object]],
    confidence: float,
) -> str:
    payload = {
        "query": query,
        "summary": summary,
        "facts": [asdict(fact) for fact in facts],
        "contradictions": contradictions,
        "confidence": confidence,
    }
    return json.dumps(payload, indent=2)
