from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMExtractionPrompt:
    task: str
    instructions: str
    output_schema: str


def build_injury_prompt() -> LLMExtractionPrompt:
    return LLMExtractionPrompt(
        task="Extract injury updates with citations",
        instructions=(
            "Return a JSON list of injury updates. Each item must include player, team, "
            "status, injury, update_time, source_url, snippet (<=25 words), retrieved_at."
        ),
        output_schema="[{player, team, status, injury, update_time, source_url, snippet, retrieved_at}]",
    )


def build_starters_prompt() -> LLMExtractionPrompt:
    return LLMExtractionPrompt(
        task="Extract starter confirmations with citations",
        instructions=(
            "Return JSON list of starters with player, team, role, confirmed, update_time, "
            "source_url, snippet (<=25 words), retrieved_at."
        ),
        output_schema="[{player, team, role, confirmed, update_time, source_url, snippet, retrieved_at}]",
    )
