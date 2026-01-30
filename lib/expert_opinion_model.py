"""
Expert opinion consensus model.

This model fetches expert writeups from the web, extracts pick signals,
weights them by source, and outputs a consensus pick.

Only Python standard library is used.
"""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Dict, Iterable, List, Optional, Tuple
import re
import urllib.request


KEYWORD_PATTERNS = (
    "pick",
    "prediction",
    "best bet",
    "lean",
    "take",
    "play",
    "back",
    "lock",
)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: List[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            text = data.strip()
            if text:
                self._chunks.append(text)

    def text(self) -> str:
        return " ".join(self._chunks)


@dataclass
class ExpertSource:
    name: str
    url: str
    weight: float = 1.0
    user_agent: str = "SportsBetLang/1.0 (expert-opinion-model)"


@dataclass
class ExpertOpinion:
    source: str
    url: str
    pick: str
    confidence: float
    weight: float
    snippet: str


class ExpertConsensusModel:
    """Aggregate expert opinions from the web into a weighted pick."""

    def __init__(self, sources: Iterable[ExpertSource]) -> None:
        self.sources = list(sources)

    def make_pick(self, candidates: Iterable[str]) -> Dict[str, object]:
        candidates_list = [c for c in candidates if c]
        opinions = self._collect_opinions(candidates_list)
        weighted = self._weight_opinions(opinions, candidates_list)
        best_pick = None
        if weighted:
            best_pick = max(weighted.items(), key=lambda kv: kv[1])[0]
        return {
            "best_pick": best_pick,
            "scores": weighted,
            "opinions": opinions,
        }

    def _collect_opinions(self, candidates: List[str]) -> List[ExpertOpinion]:
        opinions: List[ExpertOpinion] = []
        for source in self.sources:
            text = self._fetch_text(source)
            if not text:
                continue
            pick, confidence, snippet = self._extract_pick(text, candidates)
            if pick:
                opinions.append(
                    ExpertOpinion(
                        source=source.name,
                        url=source.url,
                        pick=pick,
                        confidence=confidence,
                        weight=source.weight,
                        snippet=snippet,
                    )
                )
        return opinions

    def _fetch_text(self, source: ExpertSource) -> str:
        request = urllib.request.Request(
            source.url,
            headers={"User-Agent": source.user_agent},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            html = response.read().decode("utf-8", errors="ignore")
        parser = _TextExtractor()
        parser.feed(html)
        return parser.text()

    def _extract_pick(self, text: str, candidates: List[str]) -> Tuple[Optional[str], float, str]:
        if not candidates:
            return None, 0.0, ""
        lowered = text.lower()
        scores: Dict[str, float] = {c: 0.0 for c in candidates}
        snippets: Dict[str, str] = {}

        for candidate in candidates:
            candidate_lower = candidate.lower()
            if candidate_lower not in lowered:
                continue
            scores[candidate] += 0.1
            snippet = self._find_snippet(text, candidate)
            if snippet:
                snippets[candidate] = snippet

            for pattern in KEYWORD_PATTERNS:
                regex = re.compile(
                    rf"{pattern}\s+(?:the\s+)?{re.escape(candidate_lower)}",
                    re.IGNORECASE,
                )
                matches = list(regex.finditer(lowered))
                if matches:
                    scores[candidate] += 0.6 + 0.1 * (len(matches) - 1)
                    if candidate not in snippets:
                        snippets[candidate] = self._find_snippet(text, candidate)

        best_candidate = max(scores.items(), key=lambda kv: kv[1])[0]
        best_score = scores[best_candidate]
        if best_score <= 0.0:
            return None, 0.0, ""
        confidence = min(1.0, best_score)
        snippet = snippets.get(best_candidate, self._find_snippet(text, best_candidate))
        return best_candidate, confidence, snippet

    @staticmethod
    def _find_snippet(text: str, candidate: str) -> str:
        pattern = re.compile(rf"(.{{0,60}}{re.escape(candidate)}.{{0,60}})", re.IGNORECASE)
        match = pattern.search(text)
        if not match:
            return ""
        snippet = match.group(1).strip()
        return re.sub(r"\s+", " ", snippet)

    @staticmethod
    def _weight_opinions(opinions: List[ExpertOpinion], candidates: List[str]) -> Dict[str, float]:
        scores: Dict[str, float] = {c: 0.0 for c in candidates}
        for opinion in opinions:
            scores[opinion.pick] = scores.get(opinion.pick, 0.0) + (
                opinion.weight * opinion.confidence
            )
        return scores
