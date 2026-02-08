"""Fact extraction and LLM prompt templates."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from sportsbetlang.web_research_agent.parse import ParsedDocument

PROMPT_TEMPLATES: Dict[str, str] = {
    "query_expansion": (
        "Generate 5 alternative search queries for: '{query}'. Focus on official sources."
    ),
    "relevance_classification": (
        "Determine if the page is relevant to '{query}'. Answer yes/no and explain briefly."
    ),
    "fact_extraction": (
        "Extract factual claims supported by exact quotes. Provide claim, quote, and URL."
    ),
    "synthesis": (
        "Synthesize anchored facts into a summary. Highlight conflicts and confidence."
    ),
}


@dataclass
class AnchoredFact:
    claim: str
    url: str
    snippet: str
    timestamp: str
    snippet_char_range: Optional[tuple[int, int]] = None
    attribute: Optional[str] = None
    value: Optional[float] = None


def clip_quote(snippet: str, max_words: int = 25) -> str:
    words = snippet.split()
    if len(words) <= max_words:
        return snippet
    return " ".join(words[:max_words])


def extract_patterns(text: str) -> List[Dict[str, str]]:
    patterns = []
    for match in re.finditer(r"\b\d{4}-\d{2}-\d{2}\b", text):
        patterns.append({"type": "date", "value": match.group(0)})
    for match in re.finditer(r"\$\s?\d+(?:\.\d+)?", text):
        patterns.append({"type": "price", "value": match.group(0)})
    for match in re.finditer(r"\b\d+(?:\.\d+)?\b", text):
        patterns.append({"type": "number", "value": match.group(0)})
    return patterns


def extract_facts(query: str, document: ParsedDocument, timestamp: str) -> List[AnchoredFact]:
    tokens = [token.lower() for token in query.split() if token.strip()]
    sentences = _split_sentences(document.text)
    facts: List[AnchoredFact] = []
    for sentence in sentences:
        lowered = sentence.lower()
        if tokens and not any(token in lowered for token in tokens):
            continue
        snippet = clip_quote(sentence)
        facts.append(
            AnchoredFact(
                claim=sentence.strip(),
                url=document.url,
                snippet=snippet,
                timestamp=timestamp,
            )
        )
    if not facts and sentences:
        snippet = clip_quote(sentences[0])
        facts.append(
            AnchoredFact(
                claim=sentences[0].strip(),
                url=document.url,
                snippet=snippet,
                timestamp=timestamp,
            )
        )
    _attach_numeric_attributes(facts)
    return facts


def _split_sentences(text: str) -> List[str]:
    pieces = re.split(r"(?<=[.!?])\s+", text)
    return [piece.strip() for piece in pieces if piece.strip()]


def _attach_numeric_attributes(facts: List[AnchoredFact]) -> None:
    for fact in facts:
        match = re.search(r"(\b\d+(?:\.\d+)?\b)", fact.claim)
        if not match:
            continue
        value = float(match.group(1))
        words = fact.claim.split()
        attribute = "value"
        if words:
            attribute = words[0].lower()
        fact.attribute = attribute
        fact.value = value
